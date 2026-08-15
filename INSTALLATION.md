# Installation & Setup Guide

This guide provides step-by-step instructions for setting up the **Enterprise Employee Attrition Prediction System** on a local development machine or production environment.

---

## 1. Prerequisites

- **Python**: Version 3.10 or higher
- **Git**: For version control
- **Database**: Microsoft SQL Server 2016+ (Optional: System includes automatic SQLite fallback if SQL Server is not installed locally)
- **ODBC Driver**: `ODBC Driver 17 for SQL Server` or `ODBC Driver 18 for SQL Server`

---

## 2. Environment Setup

### Step 2.1: Clone & Navigate to Repository
```bash
cd "c:\Work\Python Projects\Attrition Prediction System"
```

### Step 2.2: Create and Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2.3: Install Python Packages
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Database Setup (Microsoft SQL Server)

### Option A: Using Microsoft SQL Server (Recommended for Production)
1. Open **SQL Server Management Studio (SSMS)** or `sqlcmd`.
2. Execute the provided schema script:
   ```sql
   -- Run schema.sql script inside SQL Server
   ```
3. Update `.env` with your SQL Server connection credentials:
   ```env
   DB_ENGINE="sqlserver"
   DB_SERVER="localhost"      # Or localhost\SQLEXPRESS
   DB_NAME="EmployeeAttritionDB"
   DB_USER="sa"
   DB_PASSWORD="YourPassword123!"
   DB_DRIVER="ODBC Driver 17 for SQL Server"
   ```

### Option B: Automatic SQLite Fallback (Zero Config Local Setup)
If SQL Server is not installed on your machine, simply update `.env`:
```env
DB_ENGINE="sqlite"
```
The application will automatically initialize a lightweight SQLite database file at `data/attrition_system.db`.

---

## 4. Seeding Data & Training the Model

Execute the database seeder and machine learning training pipeline:

```bash
# 1. Seed database with employee records & generate sample test files
python -m src.database.seed_data

# 2. Train ML model, compute evaluation metrics, and save binaries to artifacts/
python -m src.ml.trainer
```

---

## 5. Running the System

### Launch FastAPI Backend
```bash
python -m src.api.app
```
Access the interactive REST API Swagger docs at: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### Launch Streamlit Executive Dashboard
In a separate terminal window:
```bash
streamlit run dashboard/app.py
```
Access the dashboard at: **[http://localhost:8501](http://localhost:8501)**

---

## 6. Sample Test Payloads

Sample test payload files are automatically generated in `data/test_samples/`:
- `sample_single_employee.json`: Payload for testing `POST /api/v1/predict`
- `sample_batch_employees.csv`: CSV file for testing batch file uploads
- `sample_batch_employees.xlsx`: Excel file for testing batch file uploads
