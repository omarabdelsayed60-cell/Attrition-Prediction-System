import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from src.utils.logger import logger
from src.domain.exceptions import InvalidEmployeeDataError

# Mandatory Features List (Strict validation: Must NOT be missing or null)
MANDATORY_FEATURES = [
    "Age",
    "Department",
    "JobRole",
    "MonthlyIncome",
    "OverTime",
    "JobSatisfaction",
    "YearsAtCompany",
    "TotalWorkingYears"
]

# Feature Lists Definitions
NUMERICAL_FEATURES = [
    "Age",
    "MonthlyIncome",
    "DistanceFromHome",
    "NumCompaniesWorked",
    "TotalWorkingYears",
    "YearsAtCompany",
    "YearsInCurrentRole",
    "YearsSinceLastPromotion",
    "YearsWithCurrManager",
    "EnvironmentSatisfaction",
    "JobSatisfaction",
    "WorkLifeBalance",
    "JobInvolvement",
    "PerformanceRating"
]

ENGINEERED_FEATURES = [
    "IncomePerWorkingYear",
    "TenureRatio",
    "PromotionLagRatio",
    "SatisfactionIndex",
    "ManagerTenureRatio"
]

CATEGORICAL_FEATURES = [
    "Gender",
    "Department",
    "JobRole",
    "EducationField",
    "OverTime",
    "BusinessTravel"
]

# Column renaming map to accept lower_snake_case or PascalCase headers
COLUMN_MAPPING = {
    "employee_id": "EmployeeID",
    "full_name": "FullName",
    "age": "Age",
    "gender": "Gender",
    "department": "Department",
    "job_role": "JobRole",
    "education_field": "EducationField",
    "monthly_income": "MonthlyIncome",
    "distance_from_home": "DistanceFromHome",
    "num_companies_worked": "NumCompaniesWorked",
    "total_working_years": "TotalWorkingYears",
    "years_at_company": "YearsAtCompany",
    "years_in_current_role": "YearsInCurrentRole",
    "years_since_last_promotion": "YearsSinceLastPromotion",
    "years_with_curr_manager": "YearsWithCurrManager",
    "environment_satisfaction": "EnvironmentSatisfaction",
    "job_satisfaction": "JobSatisfaction",
    "work_life_balance": "WorkLifeBalance",
    "job_involvement": "JobInvolvement",
    "performance_rating": "PerformanceRating",
    "overtime": "OverTime",
    "business_travel": "BusinessTravel"
}

class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Custom Scikit-Learn transformer that creates domain-specific HR features.
    Derived features help tree-based models capture tenure ratios, salary progression,
    and aggregate satisfaction indexes.
    """
    def __init__(self):
        pass

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        
        # 1. Income per total working year
        working_years = df["TotalWorkingYears"].astype(float) + 1.0
        df["IncomePerWorkingYear"] = df["MonthlyIncome"].astype(float) / working_years

        # 2. Tenure ratio
        company_years = df["YearsAtCompany"].astype(float)
        df["TenureRatio"] = company_years / working_years

        # 3. Promotion lag ratio
        df["PromotionLagRatio"] = df["YearsSinceLastPromotion"].astype(float) / (company_years + 1.0)

        # 4. Satisfaction Index
        satisfaction_sum = (
            df["EnvironmentSatisfaction"].astype(float) +
            df["JobSatisfaction"].astype(float) +
            df["WorkLifeBalance"].astype(float) +
            df["JobInvolvement"].astype(float)
        )
        df["SatisfactionIndex"] = satisfaction_sum / 4.0

        # 5. Manager Tenure Ratio
        df["ManagerTenureRatio"] = df["YearsWithCurrManager"].astype(float) / (company_years + 1.0)

        return df

class AttritionDataPreprocessor:
    """
    Main Preprocessing & Feature Transformation Orchestrator.
    Handles strict mandatory data validation, optional feature defaults, feature engineering, encoding, and scaling.
    """

    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.column_transformer = None
        self.feature_names_out: List[str] = []
        self.is_fitted: bool = False

    def check_mandatory_features(self, df: pd.DataFrame) -> Tuple[List[int], List[Dict[str, Any]]]:
        """
        Scans DataFrame for missing mandatory columns or empty mandatory cells.
        Returns:
            Tuple[valid_row_indices, skipped_records_info]
        """
        df_renamed = df.rename(columns=COLUMN_MAPPING)
        valid_indices = []
        skipped_records = []

        for idx, row in df_renamed.iterrows():
            emp_id = str(row.get("EmployeeID") or f"ROW-{idx+1}")
            missing = []

            for col in MANDATORY_FEATURES:
                if col not in df_renamed.columns or pd.isnull(row[col]) or str(row[col]).strip() == "":
                    missing.append(col)

            if missing:
                skipped_records.append({
                    "row_index": idx + 1,
                    "employee_id": emp_id,
                    "missing_mandatory_columns": missing
                })
            else:
                valid_indices.append(idx)

        return valid_indices, skipped_records

    def validate_input(self, df: pd.DataFrame, strict_mandatory: bool = True) -> pd.DataFrame:
        """
        Ensures input dataframe contains mandatory columns and populates non-mandatory optional defaults.
        """
        df_copy = df.copy()
        df_copy = df_copy.rename(columns=COLUMN_MAPPING)

        # 1. Strict Mandatory Validation Check
        if strict_mandatory:
            missing_mandatory = [col for col in MANDATORY_FEATURES if col not in df_copy.columns]
            if missing_mandatory:
                raise InvalidEmployeeDataError(
                    message="Missing mandatory feature columns in input payload.",
                    details=f"The following mandatory columns are required: {missing_mandatory}"
                )

            # Check for null values in mandatory columns
            null_mandatory_mask = df_copy[MANDATORY_FEATURES].isnull().any(axis=1)
            if null_mandatory_mask.any():
                invalid_ids = df_copy.loc[null_mandatory_mask, "EmployeeID"].tolist() if "EmployeeID" in df_copy.columns else list(df_copy.index[null_mandatory_mask])
                raise InvalidEmployeeDataError(
                    message="Input data contains empty/null values in mandatory columns.",
                    details=f"Mandatory columns missing for record IDs: {invalid_ids}"
                )

        # 2. Fill optional non-mandatory defaults (e.g. DistanceFromHome, PerformanceRating) if omitted
        optional_defaults = {
            "Gender": "Male",
            "EducationField": "Other",
            "BusinessTravel": "Travel_Rarely",
            "DistanceFromHome": 10,
            "NumCompaniesWorked": 2,
            "YearsInCurrentRole": 2,
            "YearsSinceLastPromotion": 1,
            "YearsWithCurrManager": 2,
            "EnvironmentSatisfaction": 3,
            "WorkLifeBalance": 3,
            "JobInvolvement": 3,
            "PerformanceRating": 3
        }

        for col, default_val in optional_defaults.items():
            if col not in df_copy.columns:
                df_copy[col] = default_val
            else:
                df_copy[col] = df_copy[col].fillna(default_val)

        return df_copy

    def fit(self, df: pd.DataFrame, y=None):
        """Fits the FeatureEngineer, OneHotEncoder, and StandardScaler transformers."""
        logger.info("Fitting ML Preprocessor pipeline on training dataset...")
        clean_df = self.validate_input(df, strict_mandatory=False)
        engineered_df = self.feature_engineer.transform(clean_df)

        all_numerical = NUMERICAL_FEATURES + ENGINEERED_FEATURES

        numeric_pipeline = Pipeline([
            ("scaler", StandardScaler())
        ])

        categorical_pipeline = Pipeline([
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])

        self.column_transformer = ColumnTransformer(
            transformers=[
                ("num", numeric_pipeline, all_numerical),
                ("cat", categorical_pipeline, CATEGORICAL_FEATURES)
            ]
        )

        self.column_transformer.fit(engineered_df)

        cat_encoder = self.column_transformer.named_transformers_["cat"].named_steps["onehot"]
        encoded_cat_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
        self.feature_names_out = all_numerical + encoded_cat_names
        
        self.is_fitted = True
        logger.info(f"Preprocessor fit complete. Total transformed features: {len(self.feature_names_out)}")
        return self

    def transform(self, df: pd.DataFrame, strict_mandatory: bool = True) -> np.ndarray:
        """Transforms raw employee data into model-ready numerical feature matrix."""
        if not self.is_fitted or self.column_transformer is None:
            raise InvalidEmployeeDataError("Preprocessor must be fitted before transforming data.")
        
        clean_df = self.validate_input(df, strict_mandatory=strict_mandatory)
        engineered_df = self.feature_engineer.transform(clean_df)
        transformed_matrix = self.column_transformer.transform(engineered_df)
        return transformed_matrix

    def fit_transform(self, df: pd.DataFrame, y=None) -> np.ndarray:
        """Fits and transforms input dataframe in a single call."""
        self.fit(df, y)
        return self.transform(df, strict_mandatory=False)
