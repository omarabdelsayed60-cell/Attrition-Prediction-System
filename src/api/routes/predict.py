import io
from typing import List
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from src.api.schemas import EmployeeBaseSchema, SinglePredictionResponse, BatchPredictionResponse
from src.database.connection import get_db
from src.domain.exceptions import InvalidEmployeeDataError, BatchProcessingError
from src.services.prediction_service import PredictionService
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["Prediction Engine"])

@router.post(
    "/predict",
    response_model=SinglePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Attrition for Single Employee",
    description="Calculates attrition probability, risk classification (Low/Medium/High), top SHAP factors, and HR recommendations for a single employee record."
)
def predict_single_employee(
    payload: EmployeeBaseSchema,
    db: Session = Depends(get_db)
):
    """Handles manual/single employee REST prediction request with strict mandatory validation."""
    try:
        service = PredictionService(db=db)
        input_dict = payload.model_dump()
        result = service.predict_single(input_dict, save_to_db=True)
        return result
    except InvalidEmployeeDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error in /predict endpoint: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post(
    "/batch-predict",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Predict Employee Attrition",
    description="Upload a CSV or Excel file. Rows missing mandatory columns are skipped and reported in the response audit log."
)
async def batch_predict_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Handles bulk CSV/Excel upload prediction request with skipped record reporting."""
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file extension. Only .csv and .xlsx files are accepted."
        )

    try:
        contents = await file.read()
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        service = PredictionService(db=db)
        batch_output = service.predict_batch(df, save_to_db=True)

        return batch_output
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch prediction file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process batch file: {str(e)}"
        )
