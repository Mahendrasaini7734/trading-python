from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base   # ✅ IMPORTANT CHANGE

class ExcelTrade(Base):
    __tablename__ = "excel_trades"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String, index=True)
    stage = Column(String, index=True)   # ✅ REQUIRED

    action = Column(String)
    quantity = Column(Integer)

    trigger_price = Column(Float)
    sl_price = Column(Float)

    order_id = Column(String, nullable=True)
    status = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
