# Hospital Price Transparency

This Flask application provides an API for accessing hospital price transparency data. It connects to an Azure SQL database and exposes endpoints to retrieve information about hospitals, regions, and pricing data.

## Production Environment

The application is deployed and accessible at:
```
https://practicum-cgfhfxf0axdteuer.centralus-01.azurewebsites.net
```

## Local Development Setup

### Prerequisites

- Python 3.x
- ODBC Driver for SQL Server
- Git
- Required Python packages (see `requirements.txt`)

### Setup Instructions

1. Install ODBC Driver for SQL Server:

   **For macOS:**
   ```bash
   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
   brew update
   HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18 mssql-tools18
   ```
   
   **For Windows and Linux:**
   Download and install the appropriate driver from the [Microsoft SQL Server documentation](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

2. Clone the repository:
   ```bash
   git clone https://github.com/rajrajeshwarigs/practicum.git
   cd practicum
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally

To start the application on your local machine:

```bash
python app.py
```

Once running, open your web browser and navigate to:
```
http://localhost:5000
```

## Deployment

The application is hosted on Azure Web App Service with automated continuous integration (CI) setup. The deployment process is as follows:

1. The main branch is connected to Azure Web App Service
2. When changes are pushed to the main branch, it automatically triggers a deployment
3. Azure's built-in CI system will:
   - Pull the latest code
   - Install dependencies from requirements.txt
   - Deploy the updated application
   - Restart the web service

To deploy changes:
```bash
git push origin main
```

The deployment status and logs can be monitored in the GitHub Actions tab of the repository. Each push to main will trigger a new workflow run that you can track in real-time.

### Frontend Development

For frontend development, you can work directly with the `practicum.html` file without running the Flask server locally:

1. Simply open `practicum.html` directly in your browser (file:// mode)
2. The frontend automatically detects it's running in file mode and will direct API calls to the production server
3. This allows you to make and test frontend changes without setting up the local Python environment

## Database Schema

The application uses the following main tables:
- Hospital: Contains hospital information including name, region, and location
- Price: Stores pricing data for different procedures
- Plan_: Contains insurance plan information
- Payer: Stores insurance payer details
- CodeDescription: Contains procedure code information

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
