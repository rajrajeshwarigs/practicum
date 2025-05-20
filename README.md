# Healthcare-Price-Transparency

This repository contains a complete end-to-end solution for ingesting, processing, storing, and visualizing healthcare pricing data using Azure Functions, Azure Blob Storage, a SQL database, and a web-based frontend.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Components](#components)
  - [1. Data Processing Functions App](#1-Data-Processing-functions-app)
  - [2. Database Loading Functions App](#2-Database-loading-functions-app)
  - [3. Webpage Frontend](#3-webpage-frontend)
- [Folder Structure](#folder-structure)
- [Setup & Deployment](#setup--deployment)
- [Technologies Used](#technologies-used)
- [License](#license)

---

## Project Overview

This project automates the flow of healthcare pricing data from raw files to a cleaned, queryable database and exposes the data via a user-friendly web interface. The pipeline is built on Azure Functions for serverless automation and leverages Azure Blob Storage and SQL for scalable data management.

---

## Architecture

The project follows a **Bronze-Silver-Gold data pipeline** architecture using Azure services and a web frontend.

![image](https://github.com/user-attachments/assets/7ce505dc-d2af-4276-9d06-777d906fc64b)


**Component Flow:**

- **Raw Data Files (CSV/JSON):** Healthcare pricing data files are uploaded by users or automated sources.
- **Bronze Blob Storage:** Raw files are stored in the `bronze` container.
- **Data Processing Azure Function:** Triggered by new uploads, this function cleans and transforms the data, outputting standardized files.
- **Silver Blob Storage:** Cleaned data is stored in the `silver` container.
- **Database Loading Azure Function:** Triggered by new files in `silver`, this function maps data to dimension tables and loads it into the SQL database, ensuring no duplicates.
- **SQL Database:** Stores all processed and relationally mapped pricing data, ready for querying.
- **Webpage Frontend:** Connects to the SQL database and provides a user interface for searching, viewing, and analyzing the data.
  
---

## Components

### 1. Data Processing Functions App

- **Purpose:** Cleans and standardizes raw healthcare pricing data (CSV/JSON) uploaded to the `bronze` container.
- **Output:** Cleaned data files written to the `silver` container.
- **Key Files:**  
  - `function_app.py`  
  - `requirements.txt`  
  - `host.json`  

### 2. Database Loading Functions App

- **Purpose:** Loads cleaned data from the `silver` container into the SQL database, mapping payers, plans, and codes to dimension tables and preventing duplicates.
- **Output:** Populated `Price` table and related dimensions in the SQL database.
- **Key Files:**  
  - `function_app.py`  
  - `requirements.txt`  
  - `host.json`  

### 3. Webpage Frontend

- **Purpose:** Provides a user interface to view, search, and analyze the processed healthcare pricing data from the SQL database.
- **Key Files:**  
  - `init.py` or `app.py` (entry point for the web app)  
  - Additional frontend assets (templates, static files, etc.)

---

## Folder Structure

/bronze-to-silver/
├── function_app.py
├── requirements.txt
└── host.json

/silver-to-gold/
├── function_app.py
├── requirements.txt
└── host.json

/webpage/
├── init.py (or app.py)
├── requirements.txt
├── templates/
└── static/


---

## Setup & Deployment

1. **Azure Functions Apps**
   - Deploy the `Data Processing` and `Database Loading` function apps to Azure.
   - Configure Blob Storage triggers and environment variables as required.

2. **SQL Database**
   - Ensure the SQL schema is created with the necessary tables (`Price`, `Payer`, `Plan_`, `CodeDescription`, `Hospital`).

3. **Webpage Frontend**
   - Install dependencies and run the web server locally or deploy to Azure App Service.

4. **Blob Storage**
   - Set up `bronze` and `silver` containers for file ingestion and processing.

---

## Technologies Used

- Azure Functions (Python)
- Azure Blob Storage
- Azure SQL Database
- Python (pandas, pyodbc, azure-functions, etc.)
- Web framework (Flask or FastAPI recommended)
- HTML/CSS/JavaScript for frontend
- Power BI for Visualizations

---

## License

MIT License.

---

_For questions or contributions, please open an issue or pull request._
