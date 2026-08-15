from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

class RiskLevel(str, Enum):
    """Enumeration representing employee attrition risk tier."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

@dataclass
class AttritionFactor:
    """
    Represents a specific feature's contribution to the attrition prediction (via Explainable AI / SHAP).
    """
    feature_name: str
    feature_value: Any
    shap_value: float
    impact: str  # "Increases Risk" or "Decreases Risk"
    description: str

@dataclass
class HRRecommendation:
    """
    Represents a targeted action recommended by the AI engine for HR personnel.
    """
    category: str
    title: str
    action: str
    priority: str  # "High", "Medium", "Low"

@dataclass
class PredictionOutput:
    """
    Complete output package produced by the AI prediction pipeline for a single employee.
    """
    employee_id: Optional[str]
    attrition_probability: float
    attrition_prediction: int  # 0: Stay, 1: Leave
    risk_level: RiskLevel
    top_factors: List[AttritionFactor] = field(default_factory=list)
    recommendations: List[HRRecommendation] = field(default_factory=list)
    prediction_timestamp: Optional[str] = None
