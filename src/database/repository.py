import json
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.database.models import Employee, Prediction, PredictionHistory, User
from src.domain.entities import PredictionOutput, RiskLevel
from src.utils.logger import logger

class AttritionRepository:
    """
    Data Access Layer / Repository Pattern handling all SQL operations for Employees,
    Predictions, and Dashboard aggregation metrics.
    """

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # EMPLOYEE OPERATIONS
    # -------------------------------------------------------------------------
    def upsert_employee(self, employee_data: Dict[str, Any]) -> Employee:
        """Creates or updates an employee record in the database."""
        column_mapping = {
            "EmployeeID": "employee_id",
            "FullName": "full_name",
            "Age": "age",
            "Gender": "gender",
            "Department": "department",
            "JobRole": "job_role",
            "EducationField": "education_field",
            "MonthlyIncome": "monthly_income",
            "DistanceFromHome": "distance_from_home",
            "NumCompaniesWorked": "num_companies_worked",
            "TotalWorkingYears": "total_working_years",
            "YearsAtCompany": "years_at_company",
            "YearsInCurrentRole": "years_in_current_role",
            "YearsSinceLastPromotion": "years_since_last_promotion",
            "YearsWithCurrManager": "years_with_curr_manager",
            "JobSatisfaction": "job_satisfaction",
            "EnvironmentSatisfaction": "environment_satisfaction",
            "WorkLifeBalance": "work_life_balance",
            "JobInvolvement": "job_involvement",
            "PerformanceRating": "performance_rating",
            "OverTime": "overtime",
            "BusinessTravel": "business_travel"
        }

        # Normalize incoming dictionary keys to DB model column names
        normalized_data = {}
        for k, v in employee_data.items():
            db_key = column_mapping.get(k, k)
            normalized_data[db_key] = v

        # Sanitize pandas/numpy NaN to Python None for SQL Server compatibility
        cleaned_data = {}
        for k, v in normalized_data.items():
            if pd.isna(v) or str(v).lower() == "nan":
                cleaned_data[k] = None
            else:
                cleaned_data[k] = v

        # Set safe default fallbacks for optional SQL columns
        defaults = {
            "distance_from_home": 10,
            "num_companies_worked": 2,
            "years_in_current_role": 2,
            "years_since_last_promotion": 1,
            "years_with_curr_manager": 2,
            "environment_satisfaction": 3,
            "work_life_balance": 3,
            "job_involvement": 3,
            "performance_rating": 3
        }
        for k, v in defaults.items():
            if cleaned_data.get(k) is None:
                cleaned_data[k] = v

        emp_id = str(cleaned_data.get("employee_id") or cleaned_data.get("EmployeeID"))
        cleaned_data["employee_id"] = emp_id

        existing_emp = self.db.query(Employee).filter(Employee.employee_id == emp_id).first()

        if existing_emp:
            for key, value in cleaned_data.items():
                if hasattr(existing_emp, key):
                    setattr(existing_emp, key, value)
            employee = existing_emp
            logger.info(f"Updated existing employee record: {emp_id}")
        else:
            # Filter keys to match model attributes
            model_keys = {c.name for c in Employee.__table__.columns}
            filtered_data = {k: v for k, v in cleaned_data.items() if k in model_keys}
            employee = Employee(**filtered_data)
            self.db.add(employee)
            logger.info(f"Inserted new employee record: {emp_id}")

        self.db.commit()
        self.db.refresh(employee)
        return employee

    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Fetches employee by primary key ID."""
        return self.db.query(Employee).filter(Employee.employee_id == str(employee_id)).first()

    def get_all_employees(self, limit: int = 1000, offset: int = 0) -> List[Employee]:
        """Fetches list of employees with pagination support."""
        return self.db.query(Employee).order_by(Employee.created_at.desc()).offset(offset).limit(limit).all()

    def get_unpredicted_employees(self) -> List[Employee]:
        """Fetches all employees from database with no existing prediction record."""
        return (
            self.db.query(Employee)
            .outerjoin(Prediction, Employee.employee_id == Prediction.employee_id)
            .filter(Prediction.prediction_id == None)
            .order_by(Employee.employee_id.asc())
            .all()
        )

    def count_total_employees(self) -> int:
        """Returns total count of registered employees."""
        return self.db.query(func.count(Employee.employee_id)).scalar() or 0

    def get_filtered_employee_roster(
        self,
        department_filter: Optional[str] = None,
        job_role_filter: Optional[str] = None,
        risk_level_filter: Optional[str] = None,
        employee_id_filter: Optional[str] = None,
        overtime_filter: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Fetches detailed employee roster matching active filters."""
        query = self.db.query(Employee, Prediction).outerjoin(Prediction, Employee.employee_id == Prediction.employee_id)

        if department_filter and department_filter != "All":
            query = query.filter(Employee.department == department_filter)
        if job_role_filter and job_role_filter != "All":
            query = query.filter(Employee.job_role == job_role_filter)
        if employee_id_filter and employee_id_filter != "All":
            query = query.filter(Employee.employee_id == employee_id_filter)
        if overtime_filter and overtime_filter != "All":
            query = query.filter(Employee.overtime == overtime_filter)
        if risk_level_filter and risk_level_filter != "All":
            query = query.filter(Prediction.risk_level == risk_level_filter)

        records = query.order_by(Employee.employee_id.asc()).limit(limit).all()

        roster = []
        seen_ids = set()
        for emp, pred in records:
            if emp.employee_id in seen_ids:
                continue
            seen_ids.add(emp.employee_id)

            risk_prob_str = f"{float(pred.attrition_probability)*100:.1f}%" if pred else "N/A (Not Calculated Yet)"
            risk_tier = pred.risk_level if pred else "Unrated"

            roster.append({
                "Employee ID": emp.employee_id,
                "Employee Name": emp.full_name or "N/A",
                "Department / Account": emp.department or "N/A",
                "Job Role": emp.job_role or "N/A",
                "Monthly Income ($)": f"${float(emp.monthly_income or 0):,.2f}",
                "Years at Company": emp.years_at_company,
                "Overtime Status": emp.overtime or "No",
                "Attrition Risk Probability (%)": risk_prob_str,
                "Risk Tier": risk_tier
            })

        return roster

    # -------------------------------------------------------------------------
    # PREDICTION & HISTORY OPERATIONS
    # -------------------------------------------------------------------------
    def save_prediction(
        self,
        output: PredictionOutput,
        employee_data: Optional[Dict[str, Any]] = None
    ) -> Prediction:
        """
        Saves prediction result and detailed SHAP factor/recommendation audit log into database.
        """
        # Ensure employee exists if ID provided
        emp_id = output.employee_id
        if emp_id and employee_data:
            self.upsert_employee(employee_data)

        # 1. Create Prediction Record
        prediction = Prediction(
            employee_id=emp_id,
            attrition_probability=round(output.attrition_probability, 4),
            attrition_prediction=output.attrition_prediction,
            risk_level=output.risk_level.value if isinstance(output.risk_level, RiskLevel) else str(output.risk_level),
            model_version="v1.0.0"
        )
        self.db.add(prediction)
        self.db.flush()  # Generates prediction_id

        # 2. Serialize SHAP factors and recommendations to JSON
        factors_json = json.dumps([
            {
                "feature_name": f.feature_name,
                "feature_value": str(f.feature_value),
                "shap_value": round(f.shap_value, 4),
                "impact": f.impact,
                "description": f.description
            } for f in output.top_factors
        ])

        recs_json = json.dumps([
            {
                "category": r.category,
                "title": r.title,
                "action": r.action,
                "priority": r.priority
            } for r in output.recommendations
        ])

        # 3. Create History Record
        history = PredictionHistory(
            prediction_id=prediction.prediction_id,
            top_risk_factors_json=factors_json,
            hr_recommendations_json=recs_json
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(prediction)

        logger.info(f"Successfully saved prediction #{prediction.prediction_id} (Risk: {prediction.risk_level})")
        return prediction

    def get_prediction_history(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches prediction logs joined with employee information and detailed history.
        """
        query = (
            self.db.query(Prediction, PredictionHistory, Employee)
            .outerjoin(PredictionHistory, Prediction.prediction_id == PredictionHistory.prediction_id)
            .outerjoin(Employee, Prediction.employee_id == Employee.employee_id)
        )

        if start_date:
            query = query.filter(Prediction.created_at >= start_date)
        if end_date:
            query = query.filter(Prediction.created_at <= end_date)

        records = query.order_by(desc(Prediction.created_at)).offset(offset).limit(limit).all()

        results = []
        for pred, hist, emp in records:
            factors = json.loads(hist.top_risk_factors_json) if hist and hist.top_risk_factors_json else []
            recs = json.loads(hist.hr_recommendations_json) if hist and hist.hr_recommendations_json else []
            
            results.append({
                "prediction_id": pred.prediction_id,
                "employee_id": pred.employee_id,
                "employee_name": emp.full_name if emp else "N/A",
                "department": emp.department if emp else "N/A",
                "job_role": emp.job_role if emp else "N/A",
                "attrition_probability": float(pred.attrition_probability),
                "attrition_prediction": pred.attrition_prediction,
                "risk_level": pred.risk_level,
                "top_factors": factors,
                "recommendations": recs,
                "created_at": pred.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return results

    # -------------------------------------------------------------------------
    # DASHBOARD AGGREGATIONS & MULTI-DIMENSIONAL FILTERS
    # -------------------------------------------------------------------------
    def get_dashboard_summary(
        self,
        department_filter: Optional[str] = None,
        job_role_filter: Optional[str] = None,
        risk_level_filter: Optional[str] = None,
        employee_id_filter: Optional[str] = None,
        overtime_filter: Optional[str] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Calculates aggregate HR metrics with multi-dimensional filters:
        Department/Account, Job Role, Risk Tier, Employee ID, Overtime Status, Analysis Date Range.
        """
        # Base employee query with demographic filters
        emp_query = self.db.query(Employee)
        if department_filter and department_filter != "All":
            emp_query = emp_query.filter(Employee.department == department_filter)
        if job_role_filter and job_role_filter != "All":
            emp_query = emp_query.filter(Employee.job_role == job_role_filter)
        if employee_id_filter and employee_id_filter != "All":
            emp_query = emp_query.filter(Employee.employee_id == employee_id_filter)
        if overtime_filter and overtime_filter != "All":
            emp_query = emp_query.filter(Employee.overtime == overtime_filter)

        # Base prediction query joined with employee filters
        base_pred_query = self.db.query(Prediction).join(Employee, Prediction.employee_id == Employee.employee_id)
        if department_filter and department_filter != "All":
            base_pred_query = base_pred_query.filter(Employee.department == department_filter)
        if job_role_filter and job_role_filter != "All":
            base_pred_query = base_pred_query.filter(Employee.job_role == job_role_filter)
        if employee_id_filter and employee_id_filter != "All":
            base_pred_query = base_pred_query.filter(Prediction.employee_id == employee_id_filter)
        if overtime_filter and overtime_filter != "All":
            base_pred_query = base_pred_query.filter(Employee.overtime == overtime_filter)
        if start_date:
            base_pred_query = base_pred_query.filter(Prediction.created_at >= start_date)
        if end_date:
            base_pred_query = base_pred_query.filter(Prediction.created_at <= end_date)

        # Calculate breakdown risk counts BEFORE applying risk tier filter
        high_risk_count = base_pred_query.filter(Prediction.risk_level == "High").count()
        medium_risk_count = base_pred_query.filter(Prediction.risk_level == "Medium").count()
        low_risk_count = base_pred_query.filter(Prediction.risk_level == "Low").count()

        # Apply risk tier filter to prediction and employee queries if selected
        final_pred_query = base_pred_query
        if risk_level_filter and risk_level_filter != "All":
            final_pred_query = final_pred_query.filter(Prediction.risk_level == risk_level_filter)
            matching_ids = [p.employee_id for p in final_pred_query.all()]
            if matching_ids:
                emp_query = emp_query.filter(Employee.employee_id.in_(matching_ids))
            else:
                emp_query = emp_query.filter(Employee.employee_id == "__NONE__")

        total_employees = emp_query.count()
        total_predictions = final_pred_query.count()

        avg_prob = final_pred_query.with_entities(func.avg(Prediction.attrition_probability)).scalar()
        avg_attrition_rate = round(float(avg_prob), 4) if avg_prob is not None else 0.0

        # Department breakdown query
        dept_stats_query = (
            self.db.query(
                Employee.department,
                func.count(Employee.employee_id).label("total"),
                func.avg(Prediction.attrition_probability).label("avg_risk")
            )
            .outerjoin(Prediction, Employee.employee_id == Prediction.employee_id)
            .group_by(Employee.department)
        )
        if department_filter and department_filter != "All":
            dept_stats_query = dept_stats_query.filter(Employee.department == department_filter)
        if job_role_filter and job_role_filter != "All":
            dept_stats_query = dept_stats_query.filter(Employee.job_role == job_role_filter)
        if employee_id_filter and employee_id_filter != "All":
            dept_stats_query = dept_stats_query.filter(Employee.employee_id == employee_id_filter)
        if overtime_filter and overtime_filter != "All":
            dept_stats_query = dept_stats_query.filter(Employee.overtime == overtime_filter)
        if risk_level_filter and risk_level_filter != "All":
            dept_stats_query = dept_stats_query.filter(Prediction.risk_level == risk_level_filter)

        dept_stats = []
        for dept, count, avg_r in dept_stats_query.all():
            dept_stats.append({
                "department": dept or "Unspecified",
                "total_employees": count,
                "average_risk_probability": round(float(avg_r or 0.0), 4)
            })

        # Calculate unique count of employees with at least one prediction
        pred_emp_query = (
            self.db.query(func.count(func.distinct(Prediction.employee_id)))
            .join(Employee, Prediction.employee_id == Employee.employee_id)
        )
        if department_filter and department_filter != "All":
            pred_emp_query = pred_emp_query.filter(Employee.department == department_filter)
        if job_role_filter and job_role_filter != "All":
            pred_emp_query = pred_emp_query.filter(Employee.job_role == job_role_filter)
        if employee_id_filter and employee_id_filter != "All":
            pred_emp_query = pred_emp_query.filter(Prediction.employee_id == employee_id_filter)
        if overtime_filter and overtime_filter != "All":
            pred_emp_query = pred_emp_query.filter(Employee.overtime == overtime_filter)
        if start_date:
            pred_emp_query = pred_emp_query.filter(Prediction.created_at >= start_date)
        if end_date:
            pred_emp_query = pred_emp_query.filter(Prediction.created_at <= end_date)

        predicted_employees_count = pred_emp_query.scalar() or 0
        missing_predictions_count = max(0, total_employees - predicted_employees_count)

        return {
            "total_employees": total_employees,
            "predicted_employees_count": predicted_employees_count,
            "missing_predictions_count": missing_predictions_count,
            "total_predictions": total_predictions,
            "overall_attrition_rate": avg_attrition_rate,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "department_statistics": dept_stats
        }

    def get_employee_history_timeline(self, employee_id: str) -> List[Dict[str, Any]]:
        """Fetches historical prediction trajectory timeline for a specific employee."""
        records = (
            self.db.query(Prediction, PredictionHistory)
            .join(PredictionHistory, Prediction.prediction_id == PredictionHistory.prediction_id)
            .filter(Prediction.employee_id == str(employee_id))
            .order_by(Prediction.created_at.asc())
            .all()
        )
        timeline = []
        for pred, hist in records:
            timeline.append({
                "prediction_id": pred.prediction_id,
                "employee_id": pred.employee_id,
                "attrition_probability": float(pred.attrition_probability),
                "risk_level": pred.risk_level,
                "top_factors": json.loads(hist.top_risk_factors_json) if hist.top_risk_factors_json else [],
                "recommendations": json.loads(hist.hr_recommendations_json) if hist.hr_recommendations_json else [],
                "created_at": pred.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        return timeline
