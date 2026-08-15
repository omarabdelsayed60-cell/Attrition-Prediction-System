from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from src.database.repository import AttritionRepository
from src.utils.logger import logger

class DashboardService:
    """
    Analytics & Dashboard Service encapsulating executive metric aggregations,
    employee lists, historical trajectories, and audit logs fetching.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = AttritionRepository(db)

    def get_dashboard_metrics(
        self,
        department_filter: Optional[str] = None,
        job_role_filter: Optional[str] = None,
        risk_level_filter: Optional[str] = None,
        employee_id_filter: Optional[str] = None,
        overtime_filter: Optional[str] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Fetches high-level executive dashboard stats with multi-dimensional filters."""
        logger.info(f"Fetching executive dashboard metrics summary (dept={department_filter}, role={job_role_filter}, risk={risk_level_filter}, emp={employee_id_filter}, ot={overtime_filter})...")
        return self.repo.get_dashboard_summary(
            department_filter=department_filter,
            job_role_filter=job_role_filter,
            risk_level_filter=risk_level_filter,
            employee_id_filter=employee_id_filter,
            overtime_filter=overtime_filter,
            start_date=start_date,
            end_date=end_date
        )

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
        return self.repo.get_filtered_employee_roster(
            department_filter=department_filter,
            job_role_filter=job_role_filter,
            risk_level_filter=risk_level_filter,
            employee_id_filter=employee_id_filter,
            overtime_filter=overtime_filter,
            limit=limit
        )

    def get_prediction_history(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Fetches prediction history logs with SHAP factors and HR recommendations."""
        return self.repo.get_prediction_history(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date
        )

    def get_employee_history_timeline(self, employee_id: str) -> List[Dict[str, Any]]:
        """Fetches historical prediction trajectory for a specific employee."""
        return self.repo.get_employee_history_timeline(employee_id)

    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Fetches full employee record by ID."""
        e = self.repo.get_employee_by_id(employee_id)
        if not e:
            return None
        return {
            "employee_id": e.employee_id,
            "full_name": e.full_name or "",
            "age": e.age or 30,
            "gender": e.gender or "Male",
            "department": e.department or "Research & Development",
            "job_role": e.job_role or "Research Scientist",
            "education_field": e.education_field or "Life Sciences",
            "monthly_income": float(e.monthly_income or 3000.0),
            "distance_from_home": e.distance_from_home or 10,
            "total_working_years": e.total_working_years or 5,
            "years_at_company": e.years_at_company or 2,
            "years_in_current_role": e.years_in_current_role or 1,
            "years_since_last_promotion": e.years_since_last_promotion or 1,
            "years_with_curr_manager": e.years_with_curr_manager or 1,
            "num_companies_worked": e.num_companies_worked or 1,
            "job_satisfaction": e.job_satisfaction or 3,
            "overtime": e.overtime or "No"
        }

    def get_employees(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetches employee master database list."""
        employees = self.repo.get_all_employees(limit=limit, offset=offset)
        return [
            {
                "employee_id": e.employee_id,
                "full_name": e.full_name,
                "age": e.age,
                "gender": e.gender,
                "department": e.department,
                "job_role": e.job_role,
                "education_field": e.education_field,
                "monthly_income": float(e.monthly_income),
                "distance_from_home": e.distance_from_home,
                "total_working_years": e.total_working_years,
                "years_at_company": e.years_at_company,
                "job_satisfaction": e.job_satisfaction,
                "overtime": e.overtime
            }
            for e in employees
        ]
