import os
from pathlib import Path
import numpy as np
import pandas as pd
from src.config.settings import settings
from src.utils.logger import logger

def generate_hr_attrition_dataset(
    n_samples: int = 1500,
    seed: int = 42,
    output_path: str = "data/hr_attrition.csv"
) -> pd.DataFrame:
    """
    Generates a realistic enterprise HR attrition dataset modeled after the IBM HR Analytics benchmark.
    Incorporate key domain patterns: higher attrition for low satisfaction, frequent overtime,
    long commute, low pay relative to tenure, and lack of recent promotion.

    Args:
        n_samples (int): Number of synthetic employee records to generate.
        seed (int): Random seed for reproducibility.
        output_path (str): File destination path for CSV export.

    Returns:
        pd.DataFrame: Generated dataset containing employee demographics, job details, and Attrition label.
    """
    np.random.seed(seed)
    logger.info(f"Generating synthetic HR dataset with {n_samples} employee records...")

    # Departments & Roles mapping
    dept_roles = {
        "Research & Development": [
            "Research Scientist", "Laboratory Technician", "Manufacturing Director",
            "Healthcare Representative", "Research Director", "Manager"
        ],
        "Sales": ["Sales Executive", "Sales Representative", "Manager"],
        "Human Resources": ["Human Resources", "Manager"]
    }
    
    education_fields = ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources", "Other"]
    business_travels = ["Non-Travel", "Travel_Rarely", "Travel_Frequently"]

    records = []

    for i in range(1, n_samples + 1):
        emp_id = f"EMP-{i:04d}"
        
        # Demographics
        age = int(np.random.normal(loc=37, scale=9))
        age = max(18, min(65, age))
        gender = np.random.choice(["Male", "Female"], p=[0.6, 0.4])
        
        # Department & Role
        dept = np.random.choice(list(dept_roles.keys()), p=[0.65, 0.28, 0.07])
        job_role = np.random.choice(dept_roles[dept])
        education_field = np.random.choice(education_fields)
        
        # Tenure & History
        total_working_years = int(max(0, min(age - 18, np.random.normal(loc=11, scale=7))))
        years_at_company = int(max(0, min(total_working_years, np.random.normal(loc=7, scale=5))))
        years_in_current_role = int(max(0, min(years_at_company, np.random.normal(loc=4, scale=3))))
        years_since_last_promotion = int(max(0, min(years_at_company, np.random.normal(loc=2, scale=2))))
        years_with_curr_manager = int(max(0, min(years_at_company, np.random.normal(loc=4, scale=3))))
        num_companies_worked = int(np.random.poisson(lam=2.5))
        
        # Income calculation linked to role and working years
        base_salary = 2500 + (total_working_years * 350) + np.random.normal(0, 1000)
        if "Director" in job_role or "Manager" in job_role:
            base_salary += 6000
        monthly_income = float(max(2000.0, round(base_salary, 2)))
        
        # Distance & Overtime
        distance_from_home = int(max(1, min(30, np.random.exponential(scale=9))))
        overtime = np.random.choice(["Yes", "No"], p=[0.28, 0.72])
        business_travel = np.random.choice(business_travels, p=[0.10, 0.70, 0.20])

        # Satisfaction Ratings (1: Low -> 4: High)
        env_sat = int(np.random.choice([1, 2, 3, 4], p=[0.18, 0.20, 0.32, 0.30]))
        job_sat = int(np.random.choice([1, 2, 3, 4], p=[0.19, 0.19, 0.31, 0.31]))
        work_life = int(np.random.choice([1, 2, 3, 4], p=[0.10, 0.23, 0.50, 0.17]))
        job_inv = int(np.random.choice([1, 2, 3, 4], p=[0.06, 0.25, 0.53, 0.16]))
        perf_rating = int(np.random.choice([3, 4], p=[0.84, 0.16]))

        # Calculate Realistic Attrition Risk Logits (Domain Knowledge Drivers)
        risk_score = 0.0
        
        # Overtime driver
        if overtime == "Yes":
            risk_score += 1.2
        # Frequent travel driver
        if business_travel == "Travel_Frequently":
            risk_score += 0.8
        # Low satisfaction drivers
        if job_sat <= 2:
            risk_score += 1.1
        if env_sat <= 2:
            risk_score += 0.7
        if work_life <= 2:
            risk_score += 0.9
        # Distance driver
        if distance_from_home > 15:
            risk_score += 0.6
        # Low salary ratio driver
        expected_income = 3000 + (total_working_years * 400)
        if monthly_income < expected_income * 0.8:
            risk_score += 0.9
        # Promotion lag driver
        if years_since_last_promotion >= 5:
            risk_score += 0.8
        # Young / low tenure higher mobility
        if age < 28 and years_at_company < 3:
            risk_score += 0.7

        # Base attrition probability calculation using sigmoid transform
        logits = -3.2 + risk_score
        prob = 1.0 / (1.0 + np.exp(-logits))
        
        # Binary target: 1 = Attrition (Yes), 0 = Stay (No)
        attrition = 1 if np.random.rand() < prob else 0

        record = {
            "EmployeeID": emp_id,
            "FullName": f"Employee {i}",
            "Age": age,
            "Gender": gender,
            "Department": dept,
            "JobRole": job_role,
            "EducationField": education_field,
            "MonthlyIncome": monthly_income,
            "DistanceFromHome": distance_from_home,
            "NumCompaniesWorked": num_companies_worked,
            "TotalWorkingYears": total_working_years,
            "YearsAtCompany": years_at_company,
            "YearsInCurrentRole": years_in_current_role,
            "YearsSinceLastPromotion": years_since_last_promotion,
            "YearsWithCurrManager": years_with_curr_manager,
            "EnvironmentSatisfaction": env_sat,
            "JobSatisfaction": job_sat,
            "WorkLifeBalance": work_life,
            "JobInvolvement": job_inv,
            "PerformanceRating": perf_rating,
            "OverTime": overtime,
            "BusinessTravel": business_travel,
            "Attrition": attrition
        }
        records.append(record)

    df = pd.DataFrame(records)
    
    # Save dataset to disk
    full_output_path = Path(output_path)
    full_output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(full_output_path, index=False)
    
    attrition_rate = (df["Attrition"].sum() / len(df)) * 100
    logger.info(f"Dataset generated and saved to {full_output_path}. Total records: {len(df)}, Attrition Rate: {attrition_rate:.2f}%")
    
    return df

if __name__ == "__main__":
    generate_hr_attrition_dataset()
