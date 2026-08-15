import json
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

from src.config.settings import settings
from src.ml.data_generator import generate_hr_attrition_dataset
from src.ml.preprocessor import AttritionDataPreprocessor
from src.utils.logger import logger

def train_and_evaluate_model(
    data_path: str = "data/hr_attrition.csv",
    test_size: float = 0.2,
    seed: int = 42
):
    """
    Complete ML Training Pipeline:
    1. Loads / Generates benchmark dataset
    2. Runs feature engineering & preprocessing
    3. Train / Test split
    4. Random Forest Classifier model fitting
    5. Comprehensive metrics evaluation (Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix)
    6. Binary artifact persistence (model, preprocessor, metrics)
    """
    logger.info("Initializing Machine Learning Pipeline Execution...")

    csv_file = settings.BASE_DIR / data_path
    if not csv_file.exists():
        logger.info("Dataset file not found. Triggering synthetic data generator...")
        df = generate_hr_attrition_dataset(n_samples=1500, seed=seed, output_path=str(csv_file))
    else:
        logger.info(f"Loading training dataset from {csv_file}")
        df = pd.read_csv(csv_file)

    if "Attrition" not in df.columns:
        raise ValueError("Target column 'Attrition' not found in dataset.")

    X = df.drop(columns=["Attrition"])
    y = df["Attrition"].values

    # Stratified Train/Test Split
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    logger.info(f"Split dataset into {len(X_train_raw)} training samples and {len(X_test_raw)} testing samples.")

    # Fit ML Preprocessor
    preprocessor = AttritionDataPreprocessor()
    X_train_transformed = preprocessor.fit_transform(X_train_raw)
    X_test_transformed = preprocessor.transform(X_test_raw)

    # Train Classifier (Random Forest Ensemble)
    try:
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=4,
            random_state=seed,
            class_weight="balanced"
        )
        logger.info("Fitting Random Forest Ensemble Classifier...")
        model.fit(X_train_transformed, y_train)
    except Exception as e:
        logger.warning(f"Random Forest fit error ({str(e)}). Using DecisionTree fallback...")
        model = DecisionTreeClassifier(max_depth=8, random_state=seed, class_weight="balanced")
        model.fit(X_train_transformed, y_train)

    # Model Evaluation on Hold-out Test Set
    y_pred = model.predict(X_test_transformed)
    y_prob = model.predict_proba(X_test_transformed)[:, 1]

    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": {
            "tn": cm[0][0],
            "fp": cm[0][1],
            "fn": cm[1][0],
            "tp": cm[1][1]
        },
        "total_test_samples": len(y_test),
        "model_type": model.__class__.__name__
    }

    logger.info("=== Model Performance Evaluation Metrics ===")
    logger.info(f"Model Type:      {model.__class__.__name__}")
    logger.info(f"Accuracy:        {accuracy:.4f}")
    logger.info(f"Precision:       {precision:.4f}")
    logger.info(f"Recall:          {recall:.4f}")
    logger.info(f"F1-Score:        {f1:.4f}")
    logger.info(f"ROC-AUC:         {roc_auc:.4f}")
    logger.info(f"Confusion Matrix: TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")

    # Persist Artifacts to Disk
    artifacts_dir = settings.BASE_DIR / settings.ARTIFACTS_DIR
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, settings.model_path)
    joblib.dump(preprocessor, settings.preprocessor_path)
    
    with open(settings.metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Successfully saved model artifact to: {settings.model_path}")
    logger.info(f"Successfully saved preprocessor to:     {settings.preprocessor_path}")
    logger.info(f"Successfully saved metrics report to:   {settings.metrics_path}")

    return model, preprocessor, metrics

if __name__ == "__main__":
    train_and_evaluate_model()
