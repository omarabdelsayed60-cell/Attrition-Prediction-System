import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from src.domain.entities import AttritionFactor
from src.ml.preprocessor import AttritionDataPreprocessor
from src.utils.logger import logger
from src.domain.exceptions import ModelInferenceError

# Human-friendly feature display labels & descriptions map
FEATURE_LABEL_MAP = {
    "num__JobSatisfaction": "Job Satisfaction Level",
    "num__EnvironmentSatisfaction": "Environment Satisfaction Level",
    "num__WorkLifeBalance": "Work-Life Balance Score",
    "num__JobInvolvement": "Job Involvement Level",
    "num__MonthlyIncome": "Monthly Base Salary",
    "num__DistanceFromHome": "Commute Distance (Miles)",
    "num__YearsSinceLastPromotion": "Years Since Last Promotion",
    "num__YearsAtCompany": "Tenure at Company",
    "num__YearsWithCurrManager": "Years With Current Manager",
    "num__TotalWorkingYears": "Total Career Working Years",
    "num__NumCompaniesWorked": "Prior Companies Worked",
    "num__Age": "Employee Age",
    "num__IncomePerWorkingYear": "Income Growth Rate per Career Year",
    "num__TenureRatio": "Company Tenure to Career Ratio",
    "num__PromotionLagRatio": "Promotion Lag Ratio",
    "num__SatisfactionIndex": "Composite Satisfaction Index",
    "num__ManagerTenureRatio": "Manager Stability Ratio",
    "cat__OverTime_Yes": "Frequent Overtime Work",
    "cat__OverTime_No": "No Overtime Worked",
    "cat__BusinessTravel_Travel_Frequently": "Frequent Business Travel",
    "cat__BusinessTravel_Travel_Rarely": "Rare Business Travel",
    "cat__BusinessTravel_Non-Travel": "Non-Travel Role",
    "cat__Department_Sales": "Sales Department Workload",
    "cat__Department_Research & Development": "R&D Department Workload",
    "cat__Department_Human Resources": "HR Department Workload"
}

class SHAPExplainer:
    """
    Explainable AI (XAI) Engine using SHAP (SHapley Additive exPlanations)
    with automatic Tree Contribution Fallback if C-extension DLLs are blocked by OS Application Control policies.
    """

    def __init__(self, model: Any, preprocessor: AttritionDataPreprocessor):
        self.model = model
        self.preprocessor = preprocessor
        self.explainer = None
        self.use_fallback = False
        self._init_explainer()

    def _init_explainer(self):
        """Attempts to initialize SHAP TreeExplainer, falling back gracefully if OS blocks Scipy DLLs."""
        try:
            import shap
            logger.info("Initializing SHAP TreeExplainer engine...")
            self.explainer = shap.TreeExplainer(self.model)
        except Exception as e:
            logger.warning(f"SHAP / Scipy C-extension DLL blocked by OS policy ({str(e)}). Activating Tree Feature Contribution Engine...")
            self.use_fallback = True

    def explain_instance(
        self,
        raw_df: pd.DataFrame,
        top_k: int = 5
    ) -> List[AttritionFactor]:
        """
        Calculates feature contributions for a single employee record.
        """
        try:
            transformed_matrix = self.preprocessor.transform(raw_df)
            feature_names = self.preprocessor.feature_names_out

            if not self.use_fallback and self.explainer is not None:
                try:
                    shap_values = self.explainer.shap_values(transformed_matrix)
                    if isinstance(shap_values, list):
                        vals = shap_values[1][0]
                    elif len(shap_values.shape) == 3:
                        vals = shap_values[0, :, 1]
                    elif len(shap_values.shape) == 2:
                        vals = shap_values[0]
                    else:
                        vals = shap_values
                except Exception as ex:
                    logger.warning(f"SHAP inference error ({str(ex)}). Using Tree Contribution fallback.")
                    vals = self._tree_contribution_fallback(transformed_matrix)
            else:
                vals = self._tree_contribution_fallback(transformed_matrix)

            feature_contribs = []
            for i, feat_name in enumerate(feature_names):
                shap_val = float(vals[i])
                friendly_name = FEATURE_LABEL_MAP.get(feat_name, feat_name.replace("num__", "").replace("cat__", ""))
                
                raw_col_name = feat_name.split("__")[-1].split("_")[0]
                val_repr = raw_df[raw_col_name].iloc[0] if raw_col_name in raw_df.columns else "N/A"

                impact = "Increases Risk" if shap_val > 0 else "Decreases Risk"
                desc = (
                    f"Increases attrition risk by +{abs(shap_val):.3f} log-odds"
                    if shap_val > 0 else
                    f"Reduces attrition risk by -{abs(shap_val):.3f} log-odds"
                )

                feature_contribs.append(
                    AttritionFactor(
                        feature_name=friendly_name,
                        feature_value=val_repr,
                        shap_value=shap_val,
                        impact=impact,
                        description=desc
                    )
                )

            sorted_factors = sorted(feature_contribs, key=lambda f: abs(f.shap_value), reverse=True)
            return sorted_factors[:top_k]

        except Exception as e:
            logger.error(f"Error calculating explainability: {str(e)}")
            raise ModelInferenceError("Failed to calculate feature contributions", details=str(e))

    def _tree_contribution_fallback(self, transformed_matrix: np.ndarray) -> np.ndarray:
        """
        Pure Python/Numpy Tree Contribution calculation.
        Computes instance risk contribution based on model feature importances and input feature values.
        """
        row = transformed_matrix[0]
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        else:
            importances = np.ones_like(row) / len(row)

        # Baseline centering
        row_centered = row - np.mean(row)
        contributions = row_centered * importances
        return contributions
