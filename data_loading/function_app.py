import azure.functions as func
import logging
import pandas as pd
import pyodbc
import os
from io import BytesIO

gold_app = func.FunctionApp()

@gold_app.blob_trigger(arg_name="silverblob", 
                      path="silver/{name}",
                      connection="hospitaldatayash_STORAGE")
def process_silver_to_gold(silverblob: func.InputStream):
    logging.info(f"Processing silver file: {silverblob.name}")
    
    # Get filename and hospital ID
    filename = os.path.basename(silverblob.name)
    content = silverblob.read()
    df = pd.read_csv(BytesIO(content),low_memory=False)
    
    # Connect to SQL Database
    conn = pyodbc.connect(os.getenv("SQL_CONNECTION_STRING"))
    cursor = conn.cursor()
    hospital_id = extract_hospital_id(filename,cursor)
    
    cursor.execute("SELECT COUNT(*) FROM Price WHERE HospitalID = ?", (hospital_id,))
    if cursor.fetchone()[0] > 0:
        logging.warning(f"Price data for HospitalID {hospital_id} already exists. Terminating to avoid duplication.")
        cursor.close()
        conn.close()
        return
    try:        
        # Process dimensions and get mapping dictionaries
        payer_map = process_payers(df, cursor)
        plan_map = process_plans(df, cursor,payer_map)
        code_map = process_codes(df, cursor)
        
        # Verify hospital exists
        verify_hospital(hospital_id, cursor)
        
        # Transform dataframe with IDs
        df_transformed = transform_data(df, payer_map, plan_map, code_map, hospital_id)
        
        # Load into price table
        load_price_data(df_transformed, cursor)
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error processing {filename}: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def process_payers(df, cursor):
    # Get unique payers from dataframe
    payers = df['payer'].unique().tolist()
    insert_query = "INSERT INTO Payer (PayerName) OUTPUT INSERTED.PayerID, INSERTED.PayerName VALUES (?)"
    # Check if table is empty
    cursor.execute("SELECT COUNT(*) FROM Payer")
    if cursor.fetchone()[0] == 0:
        # Bulk insert new payers
        params = [(payer,) for payer in payers]
    else:
        # Filter existing payers
        existing_payers = pd.read_sql("SELECT PayerName FROM Payer", cursor.connection)
        new_payers = [p for p in payers if p not in existing_payers['PayerName'].values]
        params = [(payer,) for payer in new_payers]
        if not params:
            return get_payer_map(cursor)
            
    # Insert new payers and return mapping
    cursor.executemany(insert_query, params)
    return get_payer_map(cursor)

def get_payer_map(cursor):
    return {row[1]: row[0] for row in cursor.execute("SELECT PayerID, PayerName FROM Payer")}

def transform_data(df, payer_map, plan_map, code_map, hospital_id):
    df['PayerID'] = df['payer'].map(payer_map)
    df['PlanID'] = df.apply(lambda row: plan_map.get((row['plan'], payer_map.get(row['payer']))), axis=1)
    df['CodeID'] = df['code|1'].map(code_map)
    df['HospitalID'] = hospital_id

    price_columns = [
        'CodeID', 'gross', 'discounted_cash', 'min', 'max',
        'estimated_amount', 'negotiated_percentage', 'PayerID', 'PlanID', 'HospitalID'
    ]
    df = df[[col for col in price_columns if col in df.columns]]
    return df.dropna(subset=['CodeID', 'PayerID', 'PlanID'])


def load_price_data(df, cursor):
    insert_query = """
    INSERT INTO Price (
        CodeID, Gross, DiscountedCash, MinPrice, MaxPrice,
        EstimatedAmount, NegotiatedPercentage, PayerID, PlanID, HospitalID
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    data = [
        (
            row['CodeID'],
            row['gross'],
            row['discounted_cash'],
            row['min'],
            row['max'],
            row['estimated_amount'],
            row['negotiated_percentage'],
            row['PayerID'],
            row['PlanID'],
            row['HospitalID']
        )
        for _, row in df.iterrows()
    ]
    cursor.fast_executemany = True
    cursor.executemany(insert_query, data)


def extract_hospital_id(filename, cursor):
    # Clean filename to match database format
    hospital_name = os.path.splitext(filename)[0].replace('-', ' ')
    
    # Query database
    cursor.execute("SELECT HospitalID FROM Hospital WHERE HospitalName = ?", (hospital_name,))
    result = cursor.fetchone()
    
    if result:
        logging.info(f"Hospital ID found:{result}")
        return result[0]
    else:
        logging.warning(f"No hospital ID found for: {hospital_name}")
        return 0 


def verify_hospital(hospital_id, cursor):
    cursor.execute("SELECT 1 FROM Hospital WHERE HospitalID = ?", hospital_id)
    if not cursor.fetchone():
        raise ValueError(f"HospitalID {hospital_id} not found in Hospital table")

def read_silver_file(blob):
    content = blob.read()
    if blob.name.endswith('.csv'):
        return pd.read_csv(BytesIO(content),low_memory=False)
    elif blob.name.endswith('.json'):
        return pd.read_json(content)
    else:
        raise ValueError("Unsupported file format")

def process_plans(df, cursor, payer_map):
    # Get unique plan-payer combinations
    plans = df[['plan', 'payer']].rename(columns={'plan': 'PlanName'}).drop_duplicates()
    plans['PayerID'] = plans['payer'].map(payer_map)
    
    # Check existing plans
    existing_plans = pd.read_sql(
        "SELECT PlanName, PayerID FROM Plan_", 
        cursor.connection
    )
    
    # Find new plans
    merged = plans.merge(
        existing_plans, 
        on=['PlanName', 'PayerID'], 
        how='left', 
        indicator=True
    )
    new_plans = merged[merged['_merge'] == 'left_only'][['PlanName', 'PayerID']]

    # Insert new plans
    if not new_plans.empty:
        insert_query = """
        INSERT INTO Plan_ (PlanName, PayerID) 
        OUTPUT INSERTED.PlanID, INSERTED.PlanName, INSERTED.PayerID
        VALUES (?, ?)
        """
        cursor.executemany(
            insert_query, 
            new_plans.itertuples(index=False, name=None)
        )
    
    return get_plan_map(cursor)

def get_plan_map(cursor):
    return {
        (row.PlanName, row.PayerID): row.PlanID 
        for row in cursor.execute("""
            SELECT p.PlanID, p.PlanName, py.PayerID 
            FROM Plan_ p
            INNER JOIN Payer py ON p.PayerID = py.PayerID
        """)
    }

def process_codes(df, cursor):
    # Get unique code-description pairs
    df['description'] = df['description'].str.slice(0, 495)
    codes = df[['code|1', 'description']].rename(columns={
        'code|1': 'CPTCode',
        'description': 'Description'
    }).drop_duplicates()
    
    # Check existing codes
    existing_codes = pd.read_sql(
        "SELECT CPTCode, Description FROM CodeDescription", 
        cursor.connection
    )
    
    # Find new codes
    merged = codes.merge(
        existing_codes, 
        on=['CPTCode', 'Description'], 
        how='left', 
        indicator=True
    )
    new_codes = merged[merged['_merge'] == 'left_only'][['CPTCode', 'Description']]

    # Insert new codes
    if not new_codes.empty:
        insert_query = """
        INSERT INTO CodeDescription (CPTCode, Description) 
        OUTPUT INSERTED.CodeID, INSERTED.CPTCode
        VALUES (?, ?)
        """
        cursor.executemany(
            insert_query, 
            new_codes.itertuples(index=False, name=None)
        )
    
    return get_code_map(cursor)

def get_code_map(cursor):
    return {
        row.CPTCode: row.CodeID 
        for row in cursor.execute("SELECT CodeID, CPTCode FROM CodeDescription")
    }
