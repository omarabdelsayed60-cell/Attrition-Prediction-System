import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.database.models import Employee, Prediction
from src.utils.logger import logger

def export_unpredicted_to_downloads():
    db: Session = SessionLocal()
    try:
        # Query employees with NO existing prediction record
        unpredicted_query = (
            db.query(Employee)
            .outerjoin(Prediction, Employee.employee_id == Prediction.employee_id)
            .filter(Prediction.prediction_id == None)
            .order_by(Employee.employee_id.asc())
        )

        unpredicted_emps = unpredicted_query.all()
        logger.info(f"Found {len(unpredicted_emps)} employees in SQL with no prediction records.")

        if not unpredicted_emps:
            print("All employees in SQL database already have predictions!")
            return None

        # Build clean dataframe matching batch predictor expected columns
        records = []
        for e in unpredicted_emps:
            records.append({
                "EmployeeID": e.employee_id,
                "FullName": e.full_name or "Employee",
                "Age": e.age or 30,
                "Gender": e.gender or "Male",
                "Department": e.department or "Research & Development",
                "JobRole": e.job_role or "Research Scientist",
                "EducationField": e.education_field or "Life Sciences",
                "MonthlyIncome": float(e.monthly_income) if e.monthly_income else 3500.0,
                "DistanceFromHome": e.distance_from_home or 10,
                "NumCompaniesWorked": e.num_companies_worked or 2,
                "TotalWorkingYears": e.total_working_years or 5,
                "YearsAtCompany": e.years_at_company or 2,
                "YearsInCurrentRole": e.years_in_current_role or 1,
                "YearsSinceLastPromotion": e.years_since_last_promotion or 1,
                "YearsWithCurrManager": e.years_with_curr_manager or 1,
                "JobSatisfaction": e.job_satisfaction or 3,
                "EnvironmentSatisfaction": e.environment_satisfaction or 3,
                "WorkLifeBalance": e.work_life_balance or 3,
                "JobInvolvement": e.job_involvement or 3,
                "OverTime": e.overtime or "No",
                "BusinessTravel": e.business_travel or "Travel_Rarely"
            })

        df = pd.DataFrame(records)

        # Locate Windows Downloads Folder
        downloads_dir = Path(os.path.expanduser("~")) / "Downloads"
        if not downloads_dir.exists():
            downloads_dir.mkdir(parents=True, exist_ok=True)

        excel_path = downloads_dir / "unpredicted_employees.xlsx"
        csv_path = downloads_dir / "unpredicted_employees.csv"

        df.to_excel(excel_path, index=False)
        df.to_csv(csv_path, index=False)

        print(f"Successfully exported {len(df)} unpredicted employees to:")
        print(f"  Excel: {excel_path}")
        print(f"  CSV:   {csv_path}")

        return excel_path

    finally:
        db.close()

if __name__ == "__main__":
    export_unpredicted_to_downloads()
