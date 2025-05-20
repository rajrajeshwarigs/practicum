# Azure Functions: Database Loading

This repository contains an Azure Functions app that automates the loading of cleaned healthcare pricing data (from the "silver" container) into a SQL database, mapping all relevant dimensions and ensuring data integrity.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [File Structure](#file-structure)
- [How It Works](#how-it-works)
- [Setup & Deployment](#setup--deployment)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Notes](#notes)
- [License](#license)

---

## Overview

This Azure Functions app is triggered when a processed data file is uploaded to the `silver` container in Azure Blob Storage. It reads the data, maps payers, plans, and codes to their respective IDs in the SQL database, and loads the transformed data into the `Price` table, ensuring no duplicate entries for the same hospital.

---

## Features

- **Automatic Trigger:** Runs when files are uploaded to the `silver` container.
- **SQL Integration:** Loads data into a normalized SQL schema with dimension mapping.
- **Dimension Handling:** Inserts new payers, plans, and code descriptions as needed.
- **Duplicate Protection:** Checks for existing data to prevent duplicate price records for each hospital.
- **Robust Logging:** Logs key steps and warnings for traceability.

---

## File Structure

| File                | Purpose                                                      |
|---------------------|-------------------------------------------------------------|
| `function_app.py`   | Main Azure Functions code: triggers, processing, SQL loading|
| `host.json`         | Azure Functions host configuration.                         |
| `requirements.txt`  | Python dependencies.                                        |

---

## How It Works

1. **Trigger:**  
   The function is triggered when a file is uploaded to the `silver` container.

2. **Read and Parse Data:**  
   Reads the CSV file into a pandas DataFrame.

3. **Database Connection:**  
   Connects to the SQL database using connection details from environment variables.

4. **Check for Existing Data:**  
   Determines if price data for the hospital (from the file name) already exists. If so, processing stops to avoid duplication.

5. **Dimension Mapping and Insertion:**  
   - **Payers:** Inserts any new payers and retrieves payer IDs.
   - **Plans:** Inserts any new plans (linked to payers) and retrieves plan IDs.
   - **Codes:** Inserts any new CPT codes and descriptions, retrieves code IDs.

6. **Hospital Verification:**  
   Verifies the hospital exists in the database.

7. **Data Transformation:**  
   Transforms the DataFrame to replace names with IDs and add the hospital ID.

8. **Load Data:**  
   Inserts the transformed data into the `Price` table.

9. **Cleanup:**  
   Commits or rolls back the transaction, closes the database connection.

---

## Setup & Deployment

1. **Install Dependencies**
- pip install -r requirements.txt


2. **Configure Azure Function App**
- Set up Blob Storage triggers for the `silver` container.
- Set the `SQL_CONNECTION_STRING` environment variable with your database credentials.

3. **Deploy to Azure**
- Use Azure CLI or VS Code Azure Functions extension for deployment.

---

## Dependencies

- azure-functions
- pandas
- pyodbc
- python-dotenv

(See `requirements.txt` for details.)

---

## Configuration

- **host.json:** Sets function runtime version, logging, and extension bundles.
- **SQL Connection:** Set the `SQL_CONNECTION_STRING` environment variable for database access.

---

## Notes

- Only `.csv` files are supported; unsupported file types should be handled as needed.
- The function expects the file name to match the hospital name for mapping.
- Dimension tables (`Payer`, `Plan_`, `CodeDescription`, `Hospital`,`Price`) must exist in the SQL database.
- The function prevents duplicate price data loading for each hospital.

---

## License

MIT License.

---

_For questions or contributions, please open an issue or pull request._
