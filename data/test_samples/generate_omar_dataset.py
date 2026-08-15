import random
import pandas as pd
from pathlib import Path

def generate_omar_callcenter_dataset():
    random.seed(42)
    
    first_names = [
        "Omar", "Ahmad", "Fatima", "Youssef", "Mariam", "Khaled", "Nour", "Ziad", "Hoda", "Tarek",
        "Layla", "Mostafa", "Salma", "Karim", "Dalia", "Hassan", "Rania", "Mahmoud", "Dina", "Amr",
        "Sara", "Sherif", "Mona", "Ali", "Nada", "Wael", "Yasmine", "Samy", "Noha", "Ibrahim"
    ]
    last_names = [
        "El-Sayed", "Hassan", "Fahmy", "Kamel", "Mansour", "Nassar", "Soliman", "Radwan", "Tawfik", "Abdel-Aziz",
        "Hamdy", "Farag", "Zaghloul", "Badawi", "Osman", "Salem", "Ghanem", "Hafez", "Kassem", "Ezzat"
    ]
    
    accounts = [
        "CallCenter - Tech Support",
        "CallCenter - Customer Care",
        "CallCenter - Billing & Sales",
        "CallCenter - VIP Services",
        "CallCenter - Financial Support"
    ]
    
    roles = [
        "Call Center Agent",
        "Customer Service Specialist",
        "Technical Support Representative",
        "Sales Representative",
        "Team Leader"
    ]

    records = []

    for i in range(1, 51):
        emp_id = f"CC-AGENT-{i:03d}"
        full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        account = random.choice(accounts)
        role = random.choice(roles)
        
        # Base realistic call center agent metrics
        age = random.randint(20, 42)
        income = round(random.uniform(2200.0, 5800.0), 2)
        working_years = random.randint(1, 12)
        company_years = min(working_years, random.randint(1, 6))
        job_sat = random.choice([1, 1, 2, 3, 4])  # Weight towards lower satisfaction for Call Center benchmark
        overtime = random.choice(["Yes", "Yes", "No"])
        distance = random.randint(2, 30)
        
        # Test Cases:
        # Rows 1-35: 100% Complete Rows
        # Rows 36-44: Missing Mandatory Fields (tests skipped audit report)
        # Rows 45-50: Missing Optional Fields (tests optional baseline handling)
        
        rec = {
            "employee_id": emp_id,
            "full_name": full_name,
            "age": age,
            "gender": random.choice(["Male", "Female"]),
            "department": account,
            "job_role": role,
            "education_field": random.choice(["Technical Degree", "Marketing", "Life Sciences", "Other"]),
            "monthly_income": income,
            "distance_from_home": distance,
            "num_companies_worked": random.randint(1, 5),
            "total_working_years": working_years,
            "years_at_company": company_years,
            "years_in_current_role": random.randint(1, max(1, company_years)),
            "years_since_last_promotion": random.randint(0, 3),
            "years_with_curr_manager": random.randint(1, max(1, company_years)),
            "environment_satisfaction": random.choice([1, 2, 3, 4]),
            "job_satisfaction": job_sat,
            "work_life_balance": random.choice([1, 2, 3, 4]),
            "job_involvement": random.choice([1, 2, 3, 4]),
            "performance_rating": random.choice([3, 4]),
            "overtime": overtime,
            "business_travel": random.choice(["Travel_Rarely", "Travel_Frequently", "Non-Travel"])
        }

        if 36 <= i <= 44:
            # Intentionally omit mandatory fields for testing
            missing_choice = i % 3
            if missing_choice == 0:
                rec["monthly_income"] = None
            elif missing_choice == 1:
                rec["job_role"] = None
            else:
                rec["overtime"] = None
                rec["age"] = None

        elif 45 <= i <= 50:
            # Intentionally omit optional fields for testing
            rec["work_life_balance"] = None
            rec["environment_satisfaction"] = None
            rec["distance_from_home"] = None

        records.append(rec)

    df = pd.DataFrame(records)
    
    out_dir = Path(__file__).resolve().parent
    file_omar = out_dir / "omar.xlsx"
    file_full = out_dir / "omar_callcenter_test.xlsx"
    
    df.to_excel(file_omar, index=False)
    df.to_excel(file_full, index=False)
    print(f"Successfully generated 50-agent Call Center test sheets:\n - {file_omar}\n - {file_full}")

if __name__ == "__main__":
    generate_omar_callcenter_dataset()
