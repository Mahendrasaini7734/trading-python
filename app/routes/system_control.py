# app/routes/system_control.py

from fastapi import APIRouter
from app.database import SessionLocal
from app.models.system_settings_model import SystemSettings

router = APIRouter()


@router.post("/admin/auto-enable")
def enable_auto():
    db = SessionLocal()

    setting = db.query(SystemSettings).first()

    if not setting:
        setting = SystemSettings(auto_trading_enabled=True)
        db.add(setting)
    else:
        setting.auto_trading_enabled = True

    db.commit()
    db.close()

    return {"status": "Auto trading enabled"}


@router.post("/admin/auto-disable")
def disable_auto():
    db = SessionLocal()

    setting = db.query(SystemSettings).first()

    if setting:
        setting.auto_trading_enabled = False

    db.commit()
    db.close()

    return {"status": "Auto trading disabled"}
