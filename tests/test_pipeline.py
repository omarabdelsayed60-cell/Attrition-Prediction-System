import unittest
import os
import json
import pandas as pd
from fastapi.testclient import TestClient

from src.config.settings import settings
from src.database.connection import init_db, SessionLocal
from src.database.repository import AttritionRepository
from src.ml.trainer import train_and_evaluate_model
from src.services.prediction_service import PredictionService
from src.domain.exceptions import InvalidEmployeeDataError
from src.api.app import app

class TestAttritionSystemPipeline(unittest.TestCase):
    """
    Integration & End-to-End System Tests verifying ML pipeline,
    database persistence, SHAP explainability, and REST API endpoints.
    """

    @classmethod
    def setUpClass(cls):
        """Initializes database schema and ensures model artifacts exist."""
        init_db()
        if not settings.model_path.exists():
            train_and_evaluate_model()

    def setUp(self):
        self.db = SessionLocal()
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()

    def test_01_database_connection_and_seeding(self):
        """Verifies database session initialization and employee repository query."""
        repo = AttritionRepository(self.db)
        emp_count = repo.count_total_employees()
        self.assertGreaterEqual(emp_count, 0, "Database should return non-negative employee count.")

    def test_02_single_prediction_service(self):
        """Verifies single employee ML inference, SHAP generation, and DB saving."""
        sample_payload = {
            "employee_id": "EMP-TEST-UNIT",
            "full_name": "Unit Test User",
            "age": 30,
            "gender": "Female",
            "department": "Research & Development",
            "job_role": "Research Scientist",
            "education_field": "Life Sciences",
            "monthly_income": 3500.0,
            "distance_from_home": 15,
            "num_companies_worked": 2,
            "total_working_years": 6,
            "years_at_company": 2,
            "years_in_current_role": 1,
            "years_since_last_promotion": 2,
            "years_with_curr_manager": 1,
            "environment_satisfaction": 1,
            "job_satisfaction": 1,
            "work_life_balance": 1,
            "job_involvement": 2,
            "performance_rating": 3,
            "overtime": "Yes",
            "business_travel": "Travel_Frequently"
        }

        service = PredictionService(db=self.db)
        result = service.predict_single(sample_payload, save_to_db=True)

        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.attrition_probability, 0.0)
        self.assertLessEqual(result.attrition_probability, 1.0)
        self.assertIn(result.risk_level.value, ["Low", "Medium", "High"])
        self.assertGreater(len(result.top_factors), 0, "SHAP explainer should return top factors.")
        self.assertGreater(len(result.recommendations), 0, "HR Recommender should generate recommendations.")

    def test_03_fastapi_predict_endpoint(self):
        """Verifies POST /api/v1/predict REST API endpoint."""
        sample_payload = {
            "employee_id": "EMP-API-TEST",
            "full_name": "API Test User",
            "age": 42,
            "gender": "Male",
            "department": "Sales",
            "job_role": "Sales Executive",
            "education_field": "Marketing",
            "monthly_income": 9500.0,
            "distance_from_home": 5,
            "num_companies_worked": 1,
            "total_working_years": 15,
            "years_at_company": 8,
            "years_in_current_role": 5,
            "years_since_last_promotion": 1,
            "years_with_curr_manager": 5,
            "environment_satisfaction": 4,
            "job_satisfaction": 4,
            "work_life_balance": 3,
            "job_involvement": 3,
            "performance_rating": 4,
            "overtime": "No",
            "business_travel": "Travel_Rarely"
        }

        response = self.client.post("/api/v1/predict", json=sample_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["employee_id"], "EMP-API-TEST")
        self.assertIn("attrition_probability", data)
        self.assertIn("risk_level", data)

    def test_04_fastapi_dashboard_endpoint(self):
        """Verifies GET /api/v1/dashboard REST API endpoint."""
        response = self.client.get("/api/v1/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_employees", data)
        self.assertIn("overall_attrition_rate", data)
        self.assertIn("high_risk_count", data)

    def test_05_strict_validation_and_batch_skip(self):
        """Verifies that missing mandatory data raises errors in single prediction and skips incomplete rows in batch prediction."""
        service = PredictionService(db=self.db)
        
        # Incomplete single payload (missing MonthlyIncome and JobRole)
        incomplete_payload = {
            "employee_id": "EMP-BAD",
            "age": 29,
            "department": "Sales"
        }
        with self.assertRaises(InvalidEmployeeDataError):
            service.predict_single(incomplete_payload, save_to_db=False)

        # Batch DataFrame with 1 complete row and 1 incomplete row
        batch_df = pd.DataFrame([
            {
                "employee_id": "EMP-GOOD-1",
                "age": 35,
                "department": "Sales",
                "job_role": "Sales Executive",
                "monthly_income": 6000,
                "overtime": "No",
                "job_satisfaction": 3,
                "years_at_company": 4,
                "total_working_years": 8
            },
            {
                "employee_id": "EMP-BAD-2",
                "age": 28,
                "department": "Sales"
                # Missing mandatory fields
            }
        ])

        batch_result = service.predict_batch(batch_df, save_to_db=False)
        self.assertEqual(batch_result["total_processed"], 1)
        self.assertEqual(batch_result["total_skipped"], 1)
        self.assertEqual(batch_result["skipped_records"][0]["employee_id"], "EMP-BAD-2")

if __name__ == "__main__":
    unittest.main()
