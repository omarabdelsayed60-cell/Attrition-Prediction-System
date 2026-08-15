-- ============================================================================
-- Enterprise Employee Attrition Prediction System - SQL Server Schema Script
-- Target RDBMS: Microsoft SQL Server 2016+ / Azure SQL Database
-- ============================================================================

-- Create Database (Run separately if database does not exist)
-- CREATE DATABASE EmployeeAttritionDB;
-- GO

-- USE EmployeeAttritionDB;
-- GO

-- 1. Table: Users (HR Managers & System Administrators)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Users]') AND type in (N'U'))
BEGIN
    CREATE TABLE dbo.Users (
        user_id INT IDENTITY(1,1) PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'HR_Manager', -- 'Admin', 'HR_Manager', 'Analyst'
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;
GO

-- 2. Table: Employees (Master Employee Records)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Employees]') AND type in (N'U'))
BEGIN
    CREATE TABLE dbo.Employees (
        employee_id VARCHAR(50) PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        age INT NOT NULL,
        gender VARCHAR(20) NOT NULL,
        department VARCHAR(50) NOT NULL,
        job_role VARCHAR(50) NOT NULL,
        education_field VARCHAR(50) NOT NULL,
        monthly_income DECIMAL(12,2) NOT NULL,
        distance_from_home INT NOT NULL,
        num_companies_worked INT NOT NULL,
        total_working_years INT NOT NULL,
        years_at_company INT NOT NULL,
        years_in_current_role INT NOT NULL,
        years_since_last_promotion INT NOT NULL,
        years_with_curr_manager INT NOT NULL,
        environment_satisfaction INT NOT NULL,  -- 1: Low, 4: Very High
        job_satisfaction INT NOT NULL,          -- 1: Low, 4: Very High
        work_life_balance INT NOT NULL,         -- 1: Bad, 4: Best
        job_involvement INT NOT NULL,           -- 1: Low, 4: Very High
        performance_rating INT NOT NULL,        -- 1: Low, 4: Outstanding
        overtime VARCHAR(5) NOT NULL,           -- 'Yes', 'No'
        business_travel VARCHAR(30) NOT NULL,   -- 'Non-Travel', 'Travel_Rarely', 'Travel_Frequently'
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;
GO

-- 3. Table: Predictions (Real-time Prediction Logs)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Predictions]') AND type in (N'U'))
BEGIN
    CREATE TABLE dbo.Predictions (
        prediction_id INT IDENTITY(1,1) PRIMARY KEY,
        employee_id VARCHAR(50) NULL,
        attrition_probability DECIMAL(5,4) NOT NULL, -- e.g. 0.8542
        attrition_prediction INT NOT NULL,          -- 0: Stay, 1: Leave
        risk_level VARCHAR(20) NOT NULL,             -- 'Low', 'Medium', 'High'
        model_version VARCHAR(50) NOT NULL DEFAULT 'v1.0.0',
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT FK_Predictions_Employees FOREIGN KEY (employee_id) 
            REFERENCES dbo.Employees (employee_id) ON DELETE SET NULL
    );
END;
GO

-- 4. Table: PredictionHistory (Detailed Audit Trail: SHAP Factors & HR Recommendations)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PredictionHistory]') AND type in (N'U'))
BEGIN
    CREATE TABLE dbo.PredictionHistory (
        history_id INT IDENTITY(1,1) PRIMARY KEY,
        prediction_id INT NOT NULL,
        top_risk_factors_json NVARCHAR(MAX) NOT NULL, -- Store serialized SHAP factors
        hr_recommendations_json NVARCHAR(MAX) NOT NULL, -- Store serialized recommendations
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT FK_PredictionHistory_Predictions FOREIGN KEY (prediction_id) 
            REFERENCES dbo.Predictions (prediction_id) ON DELETE CASCADE
    );
END;
GO

-- Create Indexes for Query Optimization
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Predictions_EmployeeID' AND object_id = OBJECT_ID('dbo.Predictions'))
    CREATE INDEX IX_Predictions_EmployeeID ON dbo.Predictions(employee_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Predictions_RiskLevel' AND object_id = OBJECT_ID('dbo.Predictions'))
    CREATE INDEX IX_Predictions_RiskLevel ON dbo.Predictions(risk_level);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Employees_Department' AND object_id = OBJECT_ID('dbo.Employees'))
    CREATE INDEX IX_Employees_Department ON dbo.Employees(department);
GO
