import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from src.database.connection import SessionLocal
from src.services.prediction_service import PredictionService

def test_batch():
    excel_path = ROOT_DIR / "data" / "test_samples" / "omar_test_v2.xlsx"
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} rows from {excel_path.name}")

    db = SessionLocal()
    try:
        service = PredictionService(db=db)
        out = service.predict_batch(df, save_to_db=False)
        print("Batch Output Keys:", out.keys())
        print("Total Processed:", out.get("total_processed"))
        print("Total Skipped:", out.get("total_skipped"))
        print("Predictions length:", len(out.get("predictions", [])))
        print("Skipped records length:", len(out.get("skipped_records", [])))
    except Exception as e:
        print("EXCEPTIONS CAUGHT DURING BATCH:", str(e))
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_batch()
