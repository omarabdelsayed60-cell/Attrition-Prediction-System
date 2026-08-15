import pandas as pd
import random
from pathlib import Path

def generate_new_test_dataset():
    random.seed(42) # Consistent reproducible generation

    accounts = [
        "CallCenter - Tech Support",
        "CallCenter - Customer Care",
        "CallCenter - Billing & Sales",
        "CallCenter - VIP Services",
        "CallCenter - Financial Support",
        "Sales",
        "Research & Development"
    ]

    roles = [
        "Call Center Agent",
        "Technical Support Representative",
        "Customer Service Specialist",
        "Sales Representative",
        "Research Scientist"
    ]

    first_names = ["Omar", "Sarah", "Khaled", "Layla", "Youssef", "Nour", "Tariq", "Hana", "Ziad", "Maya", "Amr", "Dina", "Faris", "Lina", "Rami", "Yasmin", "Hassan", "Mariam", "Kareem", "Reem"]
    last_names = ["Al-Mansoor", "El-Sayed", "Farouk", "Hassan", "Nasser", "Ibrahim", "Zaki", "Salem", "Mahmoud", "Suleiman", "Khoury", "Abadi", "Ghanem", "Darwish"]

    records = []

    # Generate 50 unique test records (CC-AGENT-101 to CC-AGENT-150)
    for i in range(101, 151):
        emp_id = f"CC-AGENT-{i:03d}"
        full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = random.randint(20, 58)
        gender = random.choice(["Male", "Female"])
        dept = random.choice(accounts)
        role = random.choice(roles)
        edu = random.choice(["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources", "Other"])
        
        income = round(random.uniform(2200.0, 14000.0), 2)
        dist = random.randint(1, 29)
        num_comp = random.randint(1, 8)
        tot_work_years = random.randint(1, 25)
        years_comp = random.randint(0, min(15, tot_work_years))
        years_role = random.randint(0, min(10, years_comp))
        years_promo = random.randint(0, min(8, years_comp))
        years_mgr = random.randint(0, min(8, years_comp))
        
        job_sat = random.choice([1, 2, 3, 4])
        env_sat = random.choice([1, 2, 3, 4])
        work_life = random.choice([1, 2, 3, 4])
        job_inv = random.choice([1, 2, 3, 4])
        
        overtime = random.choice(["Yes", "No"])
        travel = random.choice(["Non-Travel", "Travel_Rarely", "Travel_Frequently"])

        rec = {
            "EmployeeID": emp_id,
            "FullName": full_name,
            "Age": age,
            "Gender": gender,
            "Department": dept,
            "JobRole": role,
            "EducationField": edu,
            "MonthlyIncome": income,
            "DistanceFromHome": dist,
            "NumCompaniesWorked": num_comp,
            "TotalWorkingYears": tot_work_years,
            "YearsAtCompany": years_comp,
            "YearsInCurrentRole": years_role,
            "YearsSinceLastPromotion": years_promo,
            "YearsWithCurrManager": years_mgr,
            "JobSatisfaction": job_sat,
            "EnvironmentSatisfaction": env_sat,
            "WorkLifeBalance": work_life,
            "JobInvolvement": job_inv,
            "OverTime": overtime,
            "BusinessTravel": travel
        }

        # Intentionally introduce missing mandatory fields for 5 specific rows (for testing validation/skipped tables)
        if i in [110, 122, 135, 141, 148]:
            if i == 110:
                rec["MonthlyIncome"] = None
            elif i == 122:
                rec["JobRole"] = None
            elif i == 135:
                rec["Age"] = None
            elif i == 141:
                rec["OverTime"] = None
            elif i == 148:
                rec["TotalWorkingYears"] = None

        records.append(rec)

    df = pd.DataFrame(records)

    target_dir = Path(__file__).resolve().parent
    excel_path = target_dir / "omar_test_v2.xlsx"
    csv_path = target_dir / "omar_test_v2.csv"

    df.to_excel(excel_path, index=False)
    df.to_csv(csv_path, index=False)

    print(f"Successfully generated new test sheet: {excel_path} (Total Rows: {len(df)})")

if __name__ == "__main__":
    generate_new_test_dataset()
