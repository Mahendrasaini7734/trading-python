from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.system_settings_model import SystemSettings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    setting = db.query(SystemSettings).first()
    return setting


@router.put("/auto")
def toggle_auto(data: dict, db: Session = Depends(get_db)):
    setting = db.query(SystemSettings).first()
    setting.auto_trading_enabled = data.get("auto_trading_enabled")
    db.commit()
    return setting
