# app/routes/excel_market.py

import os
import shutil
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.market import MarketData
from app.config import settings

router = APIRouter(prefix="/excel-market", tags=["Excel Market Upload"])


@router.post("/upload")
async def upload_market_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload Excel file and replace entire market_data table
    """

    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files allowed")

    # ================= SAVE FILE =================

    filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ================= READ EXCEL =================

    try:
        df = pd.read_excel(filepath, sheet_name=0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel read failed: {str(e)}")

    # Replace NaN with 0
    df = df.fillna(0)

    # ================= NORMALIZE COLUMNS =================
    # Remove spaces, commas, brackets and convert to lowercase

    df.columns = (
        df.columns
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.lower()
    )

    print("Normalized Columns:", df.columns.tolist())
    print("Total Rows Found:", len(df))

    # ================= CLEAR OLD DATA =================

    db.query(MarketData).delete()
    db.commit()

    # ================= INSERT ALL ROWS =================

    inserted_count = 0

    for _, row in df.iterrows():

        market = MarketData(
            stock=row.get("stock", ""),
            open_price=row.get("openpricer2", 0),

            square=row.get("square", 0),
            base=row.get("base", 0),

            dig1=row.get("dig1", 0),
            dig2=row.get("dig2", 0),
            dig3=row.get("dig3", 0),

            r1_d=row.get("r1d", 0),
            r2_d=row.get("r2d", 0),
            r3_d=row.get("r3d", 0),

            r1_f=row.get("r1f", 0),
            r2_f=row.get("r2f", 0),

            buy=row.get("buy", 0),
            s1_f=row.get("s1f", 0),
            s2=row.get("s2", 0),
            sell=row.get("sell", 0),

            quantity=int(row.get("quantity", 0)),
            sl_buffer=row.get("sl_buffer", 0),
        )

        db.add(market)
        inserted_count += 1

    db.commit()

    return {
        "success": True,
        "message": "Market data uploaded successfully",
        "rows_inserted": inserted_count
    }
