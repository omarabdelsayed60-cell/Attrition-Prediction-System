import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from src.database.connection import SessionLocal, init_db
from src.services.prediction_service import PredictionService
from src.utils.logger import logger

def seed_omar_dataset_to_sql():
    init_db()
    excel_path = Path(__file__).resolve().parent / "omar.xlsx"
    if not excel_path.exists():
        logger.error(f"File {excel_path} not found!")
        return

    df = pd.read_excel(excel_path)
    db = SessionLocal()
    try:
        service = PredictionService(db=db)
        logger.info(f"Seeding Call Center test records from {excel_path.name} into Microsoft SQL Server...")
        result = service.predict_batch(df, save_to_db=True)
        logger.info(f"Seeding finished. Successfully processed {result['total_processed']} valid predictions, skipped {result['total_skipped']} records.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_omar_dataset_to_sql()
