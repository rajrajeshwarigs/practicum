import os
import azure.functions as func
import logging
import pandas as pd
from io import BytesIO
import json
import re

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", path="bronze/{name}",
                               connection="4cf1e2_STORAGE") 
@app.blob_output(arg_name="outputblob", path="silver/{name}", 
                 connection="AzureWebJobsStorage")
def process_files(myblob: func.InputStream,outputblob: func.Out[str]):
    logging.info(f"Processing blob: {myblob.name}")
    blob_name = myblob.name.split('/')[-1]
    file_ext = os.path.splitext(blob_name)[1].lower()
    
    try:
        if file_ext == '.json':
            cleaned_data = process_json(myblob)
            output = save_to_silver(cleaned_data, blob_name, 'csv')
            outputblob.set(output)
        elif file_ext == '.csv':
            cleaned_data = process_csv(myblob)
            output = save_to_silver(cleaned_data, blob_name, 'csv')
            outputblob.set(output)
        else:
            logging.error(f"Unsupported file type: {file_ext}")
    except Exception as e:
            import traceback
            print("Error processing")
            traceback.print_exc()
            return False

def process_csv(myblob):
    # Read CSV content
    content = myblob.read()
    CHUNK_SIZE = 50000
    skip_rows = 2 
    reader = pd.read_csv(BytesIO(content), skiprows=skip_rows, chunksize=CHUNK_SIZE, low_memory=False)
    result_chunks = []
    for i, chunk in enumerate(reader):
        logging.info(f"Processing chunk {i + 1}")
        if len(chunk.columns) > 30:
            cleaned_chunk = process_wide_format(chunk)
        else:
            cleaned_chunk = process_long_format(chunk)

        result_chunks.append(cleaned_chunk)
    
    # Concatenate all processed chunks
    final_df = pd.concat(result_chunks, ignore_index=True)
    logging.info(f"Final cleaned DataFrame shape: {final_df.shape}")
    return final_df

def process_wide_format(df):
    logging.info(f"Starting process_wide_format")
    df = df[df.get('code|1|type') == 'CPT']
    df = df.sort_values(by='code|1').drop_duplicates(subset='code|1', keep='first')
    df = df.drop(columns=[col for col in ['code|2', 'code|2|type', 'modifiers'] if col in df.columns])
    logging.info(f"Starting column cleaning")
    df.columns = df.columns.str.replace('standard_charge|', '', case=False, regex=False).str.strip('_')
    unique_cpt_count = df['code|1'].nunique()

    df = df.loc[:, df.isna().sum() != unique_cpt_count]

    for col in df.select_dtypes(include='object').columns:
        if df[col].apply(lambda x: isinstance(x, str) and not any(char.isdigit() for char in str(x))).all():
            df.drop(columns=[col], inplace=True)

    df.drop(columns=[col for col in df.columns if col.startswith('additional_')], inplace=True)
    logging.info(f"Starting data melting")
    id_vars = df.columns[:4].tolist() + df.columns[-2:].tolist()

    df_melted = df.melt(id_vars=id_vars, var_name='combined', value_name='value')

    value_types = ['negotiated_percentage', 'negotiated_dollar', 'estimated_amount']

    def extract_parts(col):
        for vt in value_types:
            if vt in col:
                parts = col.replace(vt, '').split('|')
                parts = [p for p in parts if p]
                return pd.Series([parts[0] if len(parts) > 0 else None,
                                  parts[1] if len(parts) > 1 else None,
                                  vt])
        return pd.Series([None, None, None])

    df_melted[['payer', 'plan', 'value_type']] = df_melted['combined'].apply(extract_parts)

    df_cleaned = df_melted.pivot_table(
        index=id_vars + ['payer', 'plan'],
        columns='value_type',
        values='value',
        aggfunc='first'
    ).reset_index()

    df_cleaned.columns.name = None
    logging.info(f"Performing data validation")
    if 'negotiated_percentage' in df_cleaned.columns:
        mask = df_cleaned['negotiated_percentage'].isna() & df_cleaned.get('estimated_amount').notna() & df_cleaned.get('max').notna()
        df_cleaned.loc[mask, 'negotiated_percentage'] = (
            (pd.to_numeric(df_cleaned.loc[mask, 'estimated_amount'], errors='coerce') /
             pd.to_numeric(df_cleaned.loc[mask, 'max'], errors='coerce')) * 100
        )

    df_cleaned.drop(columns=[col for col in df_cleaned.columns if col.startswith('negotiated_dollar')], inplace=True)

    df_cleaned['payer'] = df_cleaned['payer'].apply(clean_text)
    df_cleaned['plan'] = df_cleaned['plan'].apply(clean_text)
    logging.info(f"Cleaning complete")
    return df_cleaned

def clean_text(val):
    if pd.isna(val):
        return val
    val = re.sub(r'[^a-zA-Z\s]', '', str(val))  
    val = val.lower().strip()                   
    val = re.sub(r'\s+', ' ', val)               
    return val.title()

def process_long_format(df):
    logging.info(f"Starting process_long_format")
    df.columns = df.columns.str.replace('standard_charge|', '', case=False, regex=False).str.strip('_')

    cpt_mask_1 = (df['code|1|type'].str.upper() == 'CPT') if 'code|1|type' in df.columns else pd.Series([False] * len(df), index=df.index)
    cpt_mask_2 = (df['code|2|type'].str.upper() == 'CPT') if 'code|2|type' in df.columns else pd.Series([False] * len(df), index=df.index)
    cpt_mask = cpt_mask_1 | cpt_mask_2
    df = df[cpt_mask].copy()

    if 'code|2' in df.columns and 'code|2|type' in df.columns:
        condition = df['code|1|type'].str.upper() != 'CPT'
        df.loc[condition & cpt_mask_2, 'code|1'] = df.loc[condition & cpt_mask_2, 'code|2']
        df.loc[condition & cpt_mask_2, 'code|1|type'] = 'CPT'
        df.drop(columns=['code|2', 'code|2|type'], inplace=True)

    df.dropna(axis=1, how='all', inplace=True)

    columns_to_keep = [
        'description', 'code|1', 'gross', 'discounted_cash', 'payer_name',
        'plan_name', 'negotiated_dollar', 'negotiated_percentage',
        'estimated_amount', 'min', 'max'
    ]
    df = df[[col for col in columns_to_keep if col in df.columns]]

    df.rename(columns={'payer_name': 'payer', 'plan_name': 'plan'}, inplace=True)
    df['payer'] = df['payer'].apply(clean_text)
    df['plan'] = df['plan'].apply(clean_text)

    if 'negotiated_percentage' in df.columns and 'negotiated_dollar' in df.columns and 'max' in df.columns:
        df['negotiated_percentage'] = df['negotiated_percentage'].fillna(
            (pd.to_numeric(df['negotiated_dollar'], errors='coerce') /
             pd.to_numeric(df['max'], errors='coerce')) * 100
        )

    if 'negotiated_dollar' in df.columns:
        df.drop(columns=['negotiated_dollar'], inplace=True)
    return df

def process_json(myblob):
    content = myblob.read()
    data = json.loads(content)
    rows = []

    # Traverse the JSON structure
    for sci in data['standard_charge_information']:
        description = sci.get('description')
        # There may be multiple code_information entries
        for code_info in sci.get('code_information', []):
            code = code_info.get('code')
            code_type = code_info.get('type')
            # There may be multiple standard_charges
            for charge in sci.get('standard_charges', []):
                minimum = charge.get('minimum')
                maximum = charge.get('maximum')
                setting = charge.get('setting')
                gross=charge.get('gross_charge')
                discounted_cash=charge.get('discounted_cash')
                # There may be multiple payers_information
                for payer in charge.get('payers_information', []):
                    row = {
                        'description': description,
                        'code|1': code,
                        'code_type': code_type,
                        'gross':gross,
                        'discounted_cash':discounted_cash,
                        'min': minimum,
                        'max': maximum,
                        'payer': payer.get('payer_name'),
                        'plan': payer.get('plan_name'),
                        'negotiated_percentage': payer.get('standard_charge_percentage'),
                        'negotaited_dollar': payer.get('standard_charge_dollar'),
                        'estimated_amount': payer.get('estimated_amount'),
                    }
                    rows.append(row)
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    
    # Filter rows for 'CPT'
    df = df[df['code_type'] == 'CPT']

    df['payer'] = df['payer'].apply(clean_text)
    df['plan'] = df['plan'].apply(clean_text)
    df['description'] = df['description'].apply(clean_text)
    df = df.drop(columns=[col for col in ['code_type'] if col in df.columns])

    cols_to_check = [col for col in df.columns if col not in ['negotiated_percentage', 'negotiated_dollar', 'estimated_amount']]
    while df[cols_to_check].isnull().any().any():
        df = df.dropna(subset=cols_to_check)
    df = df.dropna(subset=['negotiated_dollar'])
    
    # Fill null negotiated_percentage using the formula
    df['negotiated_percentage'] = df['negotiated_percentage'].fillna(
        ((df['negotaited_dollar'] / df['max']) * 100).round(2))
   
    df = df.drop(columns=['estimated_dollar'])
    df = df.rename(columns={
    'negotaited_dollar': 'estimated_amount',})
    
    return df

def save_to_silver(data, filename, data_type):
    output_name = f"{data_type}_{filename}"
    if isinstance(data, pd.DataFrame):
        return data.to_csv(index=False)
    else:
        return json.dumps(data)

