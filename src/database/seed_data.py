import os
import json
from pathlib import Path
import pandas as pd
from src.config.settings import settings
from src.database.connection import init_db, SessionLocal
from src.database.repository import AttritionRepository
from src.ml.data_generator import generate_hr_attrition_dataset
from src.utils.logger import logger

def seed_database_and_samples():
    """
    Initializes database tables, seeds initial employee database records from dataset,
    and generates sample test payloads (JSON, CSV, Excel) for user testing.
    """
    logger.info("Starting database seeding process...")
    init_db()

    csv_path = settings.BASE_DIR / "data" / "hr_attrition.csv"
    if not csv_path.exists():
        df = generate_hr_attrition_dataset(n_samples=1500, output_path=str(csv_path))
    else:
        df = pd.read_csv(csv_path)

    # 1. Seed SQL Database
    db = SessionLocal()
    try:
        repo = AttritionRepository(db)
        existing_count = repo.count_total_employees()
        
        if existing_count == 0:
            logger.info(f"Seeding {min(500, len(df))} employee records into database...")
            sample_records = df.head(500).to_dict(orient="records")
            
            for row in sample_records:
                emp_data = {
                    "employee_id": str(row["EmployeeID"]),
                    "full_name": str(row.get("FullName", f"Employee {row['EmployeeID']}")),
                    "age": int(row["Age"]),
                    "gender": str(row["Gender"]),
                    "department": str(row["Department"]),
                    "job_role": str(row["JobRole"]),
                    "education_field": str(row["EducationField"]),
                    "monthly_income": float(row["MonthlyIncome"]),
                    "distance_from_home": int(row["DistanceFromHome"]),
                    "num_companies_worked": int(row["NumCompaniesWorked"]),
                    "total_working_years": int(row["TotalWorkingYears"]),
                    "years_at_company": int(row["YearsAtCompany"]),
                    "years_in_current_role": int(row["YearsInCurrentRole"]),
                    "years_since_last_promotion": int(row["YearsSinceLastPromotion"]),
                    "years_with_curr_manager": int(row["YearsWithCurrManager"]),
                    "environment_satisfaction": int(row["EnvironmentSatisfaction"]),
                    "job_satisfaction": int(row["JobSatisfaction"]),
                    "work_life_balance": int(row["WorkLifeBalance"]),
                    "job_involvement": int(row["JobInvolvement"]),
                    "performance_rating": int(row["PerformanceRating"]),
                    "overtime": str(row["OverTime"]),
                    "business_travel": str(row["BusinessTravel"])
                }
                repo.upsert_employee(emp_data)
            logger.info("Successfully seeded employee master data into database.")
        else:
            logger.info(f"Database already contains {existing_count} employees. Skipping duplicate seed.")

    finally:
        db.close()

    # 2. Generate Test Samples for User Testing
    samples_dir = settings.BASE_DIR / "data" / "test_samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    # A) Single Employee Test Payload (JSON)
    sample_single = {
        "employee_id": "EMP-TEST-9999",
        "full_name": "Alexander Wright",
        "age": 34,
        "gender": "Male",
        "department": "Research & Development",
        "job_role": "Research Scientist",
        "education_field": "Life Sciences",
        "monthly_income": 3800.00,
        "distance_from_home": 22,
        "num_companies_worked": 4,
        "total_working_years": 8,
        "years_at_company": 3,
        "years_in_current_role": 2,
        "years_since_last_promotion": 3,
        "years_with_curr_manager": 1,
        "environment_satisfaction": 1,
        "job_satisfaction": 1,
        "work_life_balance": 1,
        "job_involvement": 2,
        "performance_rating": 3,
        "overtime": "Yes",
        "business_travel": "Travel_Frequently"
    }

    json_sample_path = samples_dir / "sample_single_employee.json"
    with open(json_sample_path, "w", encoding="utf-8") as f:
        json.dump(sample_single, f, indent=2)
    logger.info(f"Created sample single prediction JSON payload: {json_sample_path}")

    # B) Batch Test Payload (CSV & Excel)
    batch_records = [
        sample_single,
        {
            "employee_id": "EMP-TEST-8888",
            "full_name": "Sophia Martinez",
            "age": 45,
            "gender": "Female",
            "department": "Sales",
            "job_role": "Sales Executive",
            "education_field": "Marketing",
            "monthly_income": 12500.00,
            "distance_from_home": 4,
            "num_companies_worked": 2,
            "total_working_years": 18,
            "years_at_company": 10,
            "years_in_current_role": 7,
            "years_since_last_promotion": 1,
            "years_with_curr_manager": 6,
            "environment_satisfaction": 4,
            "job_satisfaction": 4,
            "work_life_balance": 3,
            "job_involvement": 4,
            "performance_rating": 4,
            "overtime": "No",
            "business_travel": "Travel_Rarely"
        },
        {
            "employee_id": "EMP-TEST-7777",
            "full_name": "Marcus Vance",
            "age": 29,
            "gender": "Male",
            "department": "Human Resources",
            "job_role": "Human Resources",
            "education_field": "Human Resources",
            "monthly_income": 4200.00,
            "distance_from_home": 18,
            "num_companies_worked": 3,
            "total_working_years": 5,
            "years_at_company": 2,
            "years_in_current_role": 1,
            "years_since_last_promotion": 2,
            "years_with_curr_manager": 1,
            "environment_satisfaction": 2,
            "job_satisfaction": 2,
            "work_life_balance": 2,
            "job_involvement": 2,
            "performance_rating": 3,
            "overtime": "Yes",
            "business_travel": "Travel_Frequently"
        }
    ]

    batch_df = pd.DataFrame(batch_records)
    csv_batch_path = samples_dir / "sample_batch_employees.csv"
    excel_batch_path = samples_dir / "sample_batch_employees.xlsx"

    batch_df.to_csv(csv_batch_path, index=False)
    batch_df.to_excel(excel_batch_path, index=False)
    logger.info(f"Created sample batch test files: CSV ({csv_batch_path}) and Excel ({excel_batch_path})")

if __name__ == "__main__":
    seed_database_and_samples()
