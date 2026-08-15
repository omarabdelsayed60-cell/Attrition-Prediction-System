from typing import Dict, Any, List, Optional
import joblib
import pandas as pd
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.domain.entities import PredictionOutput, RiskLevel, AttritionFactor, HRRecommendation
from src.domain.exceptions import ModelNotFoundError, ModelInferenceError, InvalidEmployeeDataError
from src.ml.explainer import SHAPExplainer
from src.ml.preprocessor import AttritionDataPreprocessor
from src.ml.recommender import HRRecommender
from src.database.repository import AttritionRepository
from src.utils.logger import logger

class PredictionService:
    """
    Core Service Orchestrator linking ML Model, Preprocessor, SHAP Explainer,
    HR Recommender, and Database Repository.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.repository = AttritionRepository(db) if db else None
        self.model = None
        self.preprocessor = None
        self.explainer = None
        self.recommender = HRRecommender()
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads trained model and preprocessor binaries from disk."""
        model_path = settings.model_path
        prep_path = settings.preprocessor_path

        if not model_path.exists() or not prep_path.exists():
            logger.warning("Model or preprocessor binary missing. Training fresh model...")
            from src.ml.trainer import train_and_evaluate_model
            train_and_evaluate_model()

        try:
            logger.info("Loading ML model and preprocessor artifacts into memory...")
            self.model = joblib.load(model_path)
            self.preprocessor = joblib.load(prep_path)
            self.explainer = SHAPExplainer(self.model, self.preprocessor)
            logger.info("Successfully loaded ML prediction pipeline and SHAP engine.")
        except Exception as e:
            logger.error(f"Error loading model artifacts: {str(e)}")
            raise ModelNotFoundError(
                message="Failed to load trained machine learning model artifacts.",
                details=str(e)
            )

    def predict_single(
        self,
        employee_data: Dict[str, Any],
        save_to_db: bool = True
    ) -> PredictionOutput:
        """
        Executes end-to-end prediction pipeline for a single employee record.
        Validates mandatory feature columns strictly.
        """
        try:
            df = pd.DataFrame([employee_data])

            # 1. Transform raw input with strict mandatory validation
            transformed = self.preprocessor.transform(df, strict_mandatory=True)

            # 2. Predict Attrition Probability
            probs = self.model.predict_proba(transformed)[:, 1]
            prob = float(probs[0])
            pred_class = int(prob >= 0.5)

            # 3. Risk Level Classification
            risk_level = self.recommender.classify_risk_level(prob)

            # 4. Explainable AI (SHAP factors)
            top_factors = self.explainer.explain_instance(df, top_k=5)

            # 5. Generate HR Recommendations
            recommendations = self.recommender.generate_recommendations(prob, top_factors)

            emp_id = str(employee_data.get("employee_id") or employee_data.get("EmployeeID") or "EMP-RAW")

            output = PredictionOutput(
                employee_id=emp_id,
                attrition_probability=round(prob, 4),
                attrition_prediction=pred_class,
                risk_level=risk_level,
                top_factors=top_factors,
                recommendations=recommendations
            )

            # 6. Save to Database if Session Available
            if save_to_db and self.repository:
                self.repository.save_prediction(output, employee_data)

            return output

        except InvalidEmployeeDataError:
            raise
        except Exception as e:
            logger.error(f"Error during single employee prediction execution: {str(e)}")
            raise ModelInferenceError("Prediction calculation failed", details=str(e))

    def predict_batch(
        self,
        df: pd.DataFrame,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Executes batch prediction with strict mandatory column validation.
        Valid records are predicted, while records missing mandatory fields are skipped and returned in audit report.
        """
        logger.info(f"Processing batch prediction request for {len(df)} total rows...")
        
        # 1. Scan for valid vs skipped rows
        valid_indices, skipped_records = self.preprocessor.check_mandatory_features(df)
        
        results: List[PredictionOutput] = []
        if valid_indices:
            valid_df = df.iloc[valid_indices]
            records = valid_df.to_dict(orient="records")
            
            for record in records:
                try:
                    output = self.predict_single(record, save_to_db=save_to_db)
                    results.append(output)
                except Exception as ex:
                    if self.db:
                        self.db.rollback()
                    logger.warning(f"Error processing record {record.get('employee_id')}: {str(ex)}")

        logger.info(f"Batch prediction complete. Processed: {len(results)}, Skipped: {len(skipped_records)}")
        
        return {
            "total_processed": len(results),
            "total_skipped": len(skipped_records),
            "predictions": results,
            "skipped_records": skipped_records
        }
