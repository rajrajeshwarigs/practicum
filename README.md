your # Hospital Price Transparency API

This Flask application provides an API for accessing hospital price transparency data. It connects to an Azure SQL database and exposes endpoints to retrieve information about hospitals, regions, and pricing data.

## Prerequisites

- Python 3.x
- ODBC Driver for SQL Server
- Required Python packages (see `requirements.txt`)

## Setup Instructions

1. Install ODBC Driver for SQL Server:

   **For macOS:**
   ```bash
   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
   brew update
   HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18 mssql-tools18
   ```
   
   **For Windows and Linux:**
   Download and install the appropriate driver from the [Microsoft SQL Server documentation](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

2. Extract the zip file to your desired location

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

To start the application:

```bash
python app.py
```

Once running, open your web browser and navigate to:
```
http://localhost:5000
```

## Database Schema

The application uses the following main tables:
- Hospital: Contains hospital information including name, region, and location
- Price: Stores pricing data for different procedures
- Plan_: Contains insurance plan information
- Payer: Stores insurance payer details
- CodeDescription: Contains procedure code information

## Development

The application includes logging for debugging purposes. When running in debug mode, detailed logs will be printed to the console.

## Troubleshooting

Common issues and solutions:

1. **ODBC Driver Error**: If you get an error about missing ODBC drivers, make sure you've installed the correct version of the Microsoft ODBC Driver for SQL Server as described in the setup instructions.

2. **Connection Issues**: Ensure you have network access to the Azure SQL Database and that your firewall rules allow the connection.

3. **Package Installation Errors**: If you encounter issues installing packages, try upgrading pip:
   ```bash
   python -m pip install --upgrade pip
   ```

## Security Notes

- The application uses CORS to allow cross-origin requests
- Ensure proper security measures are in place when deploying to production 
