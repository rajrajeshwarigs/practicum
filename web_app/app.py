from flask import Flask, jsonify, render_template
from flask_cors import CORS
import pyodbc
from dotenv import load_dotenv
import os
from datetime import datetime

# Connection string for Azure SQL Database
AZURE_CONNECTION_STRING="Driver={ODBC Driver 18 for SQL Server};Server=tcp:practicum.database.windows.net,1433;Database=masterdata;Uid=practicum;Pwd=Yash0407;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;" 

def log(message):
    print(f"[{datetime.now()}] {message}")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
log("Flask app initialized with CORS")

# Get database connection
def get_db_connection():
    log("Attempting database connection")
    try:
        conn = pyodbc.connect(AZURE_CONNECTION_STRING)
        log("Database connection successful")
        return conn
    except pyodbc.Error as e:
        log(f"Database connection failed: {e}")
        return None

# Serve the main page
@app.route('/')
def index():
    log("Serving index page")
    return render_template('practicum.html')

# Get list of hospitals by region
@app.route('/api/hospitals/<region>', methods=['GET'])
def get_hospitals(region):
    log(f"Starting hospitals request for region: {region}")
    
    conn = get_db_connection()
    if not conn:
        log("Database connection failed in get_hospitals")
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        log("Executing hospitals query")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT HospitalID, HospitalName 
            FROM Hospital
            WHERE Region = ?
        """, region)
        
        hospitals = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        log(f"Retrieved {len(hospitals)} hospitals for region {region}")
        return jsonify(hospitals)
    
    except pyodbc.Error as e:
        log(f"Database error in get_hospitals: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()
        log("Connection closed in get_hospitals")

# Get hospital prices
@app.route('/api/hospital-prices/<int:hospital_id>', methods=['GET'])
def get_hospital_prices(hospital_id):
    log(f"Starting hospital prices request for hospital_id: {hospital_id}")
    
    conn = get_db_connection()
    if not conn:
        log("Database connection failed in get_hospital_prices")
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        log("Executing prices query")

        cursor.execute("""
            WITH avg_prices AS (
            SELECT 
                p.PayerName,
                pl.PlanName,
                ROUND(AVG(pr.EstimatedAmount), 2) AS avg_estimated_amount, 
                ROUND(MIN(pr.EstimatedAmount), 2) AS min_estimated_amount,
                ROUND(MAX(pr.EstimatedAmount), 2) AS max_estimated_amount,
                ROUND(AVG(pr.NegotiatedPercentage), 2) AS avg_negotiated_percentage 
            FROM Price pr
            INNER JOIN Payer p ON pr.PayerID = p.PayerID
            INNER JOIN Plan_ pl ON pr.PlanID = pl.PlanID
            WHERE pr.HospitalID = ?
            GROUP BY p.PayerName, pl.PlanName
        )
        SELECT TOP 10 
            PayerName as payer, 
            PlanName as [plan], 
            avg_estimated_amount,
            min_estimated_amount,
            max_estimated_amount,
            avg_negotiated_percentage
            FROM avg_prices
            ORDER BY avg_estimated_amount ASC;
        """, hospital_id)
        
        prices = [{
            'payer': row[0],
            'plan': row[1],
            'estimated_amount': float(row[2]) if row[2] is not None else None,
            'min_estimated_amount': float(row[3]) if row[3] is not None else None,
            'max_estimated_amount': float(row[4]) if row[4] is not None else None,
            'negotiated_percentage': float(row[5]) if row[5] is not None else None
        } for row in cursor.fetchall()]
        
        log(f"Retrieved {len(prices)} price entries for hospital {hospital_id}")
        return jsonify(prices)
    
    except pyodbc.Error as e:
        log(f"Database error in get_hospital_prices: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()
        log("Connection closed in get_hospital_prices")

# Get list of regions
@app.route('/api/regions', methods=['GET'])
def get_regions():
    log("Starting regions request")
    
    conn = get_db_connection()
    if not conn:
        log("Database connection failed in get_regions")
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        log("Executing regions query")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Region FROM Hospital")
        
        regions = [row[0] for row in cursor.fetchall()]
        log(f"Retrieved {len(regions)} regions")
        return jsonify(regions)
    
    except pyodbc.Error as e:
        log(f"Database error in get_regions: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()
        log("Connection closed in get_regions")

if __name__ == '__main__':
    log("Starting Flask application")
    app.run(debug=True)