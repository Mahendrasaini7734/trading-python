# app/models/system_settings_model.py

from sqlalchemy import Column, Integer, Boolean
from app.database import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    auto_trading_enabled = Column(Boolean, default=False)
