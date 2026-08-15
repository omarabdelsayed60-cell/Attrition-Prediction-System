from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from src.domain.entities import RiskLevel

class EmployeeBaseSchema(BaseModel):
    """Base Employee Input Schema for manual single prediction and API calls."""
    model_config = ConfigDict(populate_by_name=True)

    employee_id: Optional[str] = Field(default="EMP-9999", description="Unique Employee ID")
    full_name: Optional[str] = Field(default="John Doe", description="Employee Full Name")
    age: int = Field(..., ge=18, le=70, description="Mandatory: Employee Age in years")
    gender: Optional[str] = Field(default="Male", description="Gender: 'Male' or 'Female'")
    department: str = Field(..., description="Mandatory: Department: 'Research & Development', 'Sales', 'Human Resources'")
    job_role: str = Field(..., description="Mandatory: Job Title / Role")
    education_field: Optional[str] = Field(default="Other", description="Education Specialization")
    monthly_income: float = Field(..., gt=0, description="Mandatory: Monthly Base Salary")
    distance_from_home: Optional[int] = Field(default=10, ge=0, description="Commute distance in miles")
    num_companies_worked: Optional[int] = Field(default=2, ge=0, description="Number of prior employers")
    total_working_years: int = Field(..., ge=0, description="Mandatory: Total working experience years")
    years_at_company: int = Field(..., ge=0, description="Mandatory: Tenure at current company")
    years_in_current_role: Optional[int] = Field(default=2, ge=0, description="Years in current role")
    years_since_last_promotion: Optional[int] = Field(default=1, ge=0, description="Years since last promotion")
    years_with_curr_manager: Optional[int] = Field(default=2, ge=0, description="Years under current manager")
    environment_satisfaction: Optional[int] = Field(default=3, ge=1, le=4, description="Environment Satisfaction (1-4)")
    job_satisfaction: int = Field(..., ge=1, le=4, description="Mandatory: Job Satisfaction Rating (1-4)")
    work_life_balance: Optional[int] = Field(default=3, ge=1, le=4, description="Work-Life Balance Score (1-4)")
    job_involvement: Optional[int] = Field(default=3, ge=1, le=4, description="Job Involvement Score (1-4)")
    performance_rating: Optional[int] = Field(default=3, ge=3, le=4, description="Performance Rating (3-4)")
    overtime: str = Field(..., description="Mandatory: Overtime status: 'Yes' or 'No'")
    business_travel: Optional[str] = Field(default="Travel_Rarely", description="Travel frequency")

class FactorSchema(BaseModel):
    """API DTO for SHAP Explainability factor."""
    feature_name: str
    feature_value: Any
    shap_value: float
    impact: str
    description: str

class HRRecommendationSchema(BaseModel):
    """API DTO for HR Recommendation."""
    category: str
    title: str
    action: str
    priority: str

class SinglePredictionResponse(BaseModel):
    """Response DTO for Single Employee Prediction."""
    employee_id: Optional[str]
    attrition_probability: float
    attrition_prediction: int
    risk_level: RiskLevel
    top_factors: List[FactorSchema]
    recommendations: List[HRRecommendationSchema]

class SkippedRecordSchema(BaseModel):
    """API DTO for skipped batch records missing mandatory data."""
    row_index: int
    employee_id: str
    missing_mandatory_columns: List[str]

class BatchPredictionResponse(BaseModel):
    """Response DTO for Batch Employees Prediction."""
    total_processed: int
    total_skipped: int
    predictions: List[SinglePredictionResponse]
    skipped_records: List[SkippedRecordSchema]

class DepartmentStatSchema(BaseModel):
    department: str
    total_employees: int
    average_risk_probability: float

class DashboardSummaryResponse(BaseModel):
    """Response DTO for Executive Dashboard Summary."""
    total_employees: int
    predicted_employees_count: Optional[int] = None
    missing_predictions_count: Optional[int] = None
    total_predictions: int
    overall_attrition_rate: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    department_statistics: List[DepartmentStatSchema]
