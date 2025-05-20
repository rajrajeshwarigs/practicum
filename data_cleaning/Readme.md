# Azure Functions Healthcare Data Cleaning and Transformation

This repository contains an Azure Functions app that automatically ingests, cleans, and transforms healthcare pricing data files (CSV and JSON) uploaded to Azure Blob Storage.

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

This Azure Functions app is triggered by new file uploads to the `bronze` container in Azure Blob Storage. It processes healthcare pricing data in CSV or JSON format, cleans and transforms the data, and outputs the results to the `silver` container for further use or analytics.

---

## Features

- **Automatic Trigger:** Runs when files are uploaded to the `bronze` container.
- **File Type Support:** Handles both CSV and JSON files.
- **Data Cleaning:** Cleans, standardizes, and transforms data, handling both wide and long CSV formats.
- **Output:** Saves cleaned data to the `silver` container in the appropriate format.

---

## File Structure

| File                | Purpose                                                      |
|---------------------|-------------------------------------------------------------|
| `function_app.py`   | Main Azure Functions code: triggers, processing, output.     |
| `host.json`         | Azure Functions host configuration.                          |
| `requirements.txt`  | Python dependencies.                                         |

---

## How It Works

1. **Trigger:**  
   The function is triggered when a file is uploaded to the `bronze` container.

2. **File Detection:**  
   Determines file type by extension (`.csv` or `.json`).

3. **CSV Processing:**  
   - Reads large files in 50,000-row chunks.
   - Handles both wide and long formats.
   - Cleans columns, filters for CPT codes, removes unnecessary fields, and normalizes payer/plan names.
   - Calculates missing negotiated percentages when possible.

4. **JSON Processing:**  
   - Reads and flattens nested JSON pricing data, extracting all relevant fields for each CPT code and payer-plan combination.
   - Cleans and standardizes text fields, and filters to include only CPT-coded records.
   - Drops rows missing essential data and calculates missing negotiated percentages when possible.
   - Outputs a consistent, tabular DataFrame ready for downstream processing in the silver container.

5. **Output:**  
   Cleaned data is saved to the `silver` container, preserving the file type.

---

## Setup & Deployment

1. **Install Dependencies**
- pip install -r requirements.txt


2. **Configure Azure Function App**
- Set up Blob Storage triggers and outputs in Azure.
- Update connection strings as needed in the function bindings.

3. **Deploy to Azure**
- Use Azure CLI or VS Code Azure Functions extension for deployment.

---

## Dependencies

- azure-functions
- pandas
- azure-storage-blob
- azure-identity
- numpy

(See `requirements.txt` for details.)

---

## Configuration

- **host.json:** Sets function runtime version, logging, and extension bundles.
- **Blob connections:** Update connection strings in the function bindings as required.

---

## Notes

- Only `.csv` and `.json` files are supported; unsupported file types are logged and skipped.
- Large CSVs are processed in chunks for memory efficiency.
- The function expects specific column naming conventions for correct operation.

---

## License

MIT License.

---

_For questions or contributions, please open an issue or pull request._
