# app/routes/excel_trade.py
import logging
import os
import shutil
import asyncio
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException

from app.config import settings
from app.services.excel_trade_executor import ExcelTradeExecutor
from app.database import SessionLocal
from app.services.excel_trade_history import ExcelTradeHistoryService

router = APIRouter(prefix="/excel", tags=["Excel Upload Trading"])
logger = logging.getLogger("excel_trade")

_auto_task: asyncio.Task | None = None
_auto_running: bool = False
_last_auto_summary = {}

# ================= LOGGER =================

def setup_logger():
    if logger.handlers:
        return
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(settings.EXCEL_TRADE_LOG_PATH)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

# =====================================================
# 🔥 1️⃣ Upload + Preview Excel (NEW FEATURE)
# =====================================================

@router.post("/upload-preview")
async def upload_preview(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files allowed")

    filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 📊 Read Excel for preview
    df = pd.read_excel(filepath)
    df = df.fillna("")

    return {
        "success": True,
        "file_path": filepath,
        "columns": df.columns.tolist(),
        "rows": df.to_dict(orient="records")
    }

# =====================================================
# 2️⃣ Normal Upload (for trading)
# =====================================================

@router.post("/upload-trade")
async def upload_trade(file: UploadFile = File(...)):
    setup_logger()

    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed")

    filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"success": True, "file_saved_as": filepath}


# =====================================================
# 3️⃣ AUTO LOOP (DB BASED)
# =====================================================
async def _auto_loop():
    global _auto_running, _last_auto_summary

    executor = ExcelTradeExecutor()

    while _auto_running:
        try:
            executor.execute_from_db()   

            _last_auto_summary = {
                "time": datetime.utcnow().isoformat(),
                "success": True,
                "message": "Execution cycle completed"
            }

        except Exception as e:
            logger.exception("Auto loop error")
            _last_auto_summary = {
                "success": False,
                "message": str(e)
            }

        await asyncio.sleep(settings.AUTO_POLL_INTERVAL_SEC)

# =====================================================
# 4️⃣ START AUTO
# =====================================================
# =====================================================
# 4️⃣ START AUTO (DB MODE)
# =====================================================

@router.post("/start-auto")
async def start_auto():
    global _auto_task, _auto_running

    if _auto_task and not _auto_task.done():
        return {"success": True, "message": "Auto mode already running"}

    _auto_running = True
    _auto_task = asyncio.create_task(_auto_loop())

    return {"success": True, "message": "Auto mode started (DB Mode)"}


# =====================================================
# 5️⃣ STOP AUTO
# =====================================================

@router.post("/stop-auto")
async def stop_auto():
    global _auto_task, _auto_running
    _auto_running = False

    if _auto_task and not _auto_task.done():
        _auto_task.cancel()

    return {"success": True, "message": "Auto mode stopped"}

# =====================================================
# 6️⃣ AUTO STATUS
# =====================================================

@router.get("/auto-status")
async def auto_status():
    return {
        "auto_running": _auto_running,
        "poll_interval_sec": settings.AUTO_POLL_INTERVAL_SEC,
        "last_summary": _last_auto_summary
    }

# =====================================================
# 7️⃣ TRADES HISTORY
# =====================================================

@router.get("/trades")
async def list_trades(
    status: str | None = None,
    symbol: str | None = None,
    limit: int = 100,
    offset: int = 0,
):

    if limit > 500:
        limit = 500

    db = SessionLocal()
    try:
        service = ExcelTradeHistoryService()
        result = service.list_trades(
            db=db,
            status=status,
            symbol=symbol,
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            **result
        }

    finally:
        db.close()




# import logging
# import os
# import shutil
# from datetime import datetime

# from fastapi import APIRouter, File, UploadFile, HTTPException

# from app.config import settings
# from app.services.excel_parser import ExcelParser
# from app.services.excel_trade_executor import ExcelTradeExecutor

# router = APIRouter(prefix="/excel", tags=["Excel Upload Trading"])
# logger = logging.getLogger("excel_trade")

# def setup_logger():
#     if logger.handlers:
#         return
#     logger.setLevel(logging.INFO)
#     fh = logging.FileHandler(settings.EXCEL_TRADE_LOG_PATH)
#     formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
#     fh.setFormatter(formatter)
#     logger.addHandler(fh)

# @router.post("/upload-trade")
# async def upload_trade(file: UploadFile = File(...)):
#     setup_logger()

#     if not file.filename.lower().endswith(".xlsx"):
#         raise HTTPException(status_code=400, detail="Only .xlsx files are allowed")

#     filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
#     filepath = os.path.join(settings.UPLOAD_DIR, filename)

#     with open(filepath, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     parser = ExcelParser()
#     try:
#         valid_rows, invalid_rows = parser.parse(filepath)
#     except Exception as e:
#         logger.exception("Excel parsing failed")
#         raise HTTPException(status_code=400, detail=str(e))

#     total_rows = len(valid_rows) + len(invalid_rows)

#     if total_rows > settings.MAX_ORDERS_PER_UPLOAD:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Upload rejected: rows={total_rows} exceeds MAX_ORDERS_PER_UPLOAD={settings.MAX_ORDERS_PER_UPLOAD}",
#         )

#     executor = ExcelTradeExecutor()

#     details = []
#     executed_count = 0
#     failed_count = 0
#     skipped_count = 0

#     for inv in invalid_rows:
#         failed_count += 1
#         details.append(inv)

#     for row in valid_rows:
#         result = executor.execute_one(row)
#         details.append(result)

#         if result["status"] == "EXECUTED":
#             executed_count += 1
#         elif result["status"] == "FAILED":
#             failed_count += 1
#         elif result["status"] == "SKIPPED":
#             skipped_count += 1

#     return {
#         "total_rows": total_rows,
#         "executed_count": executed_count,
#         "failed_count": failed_count,
#         "skipped_count": skipped_count,
#         "dry_run": settings.DRY_RUN,
#         "file_saved_as": filepath,
#         "details": details,
#     }
