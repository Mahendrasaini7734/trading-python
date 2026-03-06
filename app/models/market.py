from sqlalchemy import Column, Integer, String, Float, Date
from app.database import Base

class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)

    stock = Column(String, index=True)
    open_price = Column(Float)
    square = Column(Float)
    base = Column(Float)

    dig1 = Column(Float)
    dig2 = Column(Float)
    dig3 = Column(Float)

    r1_d = Column(Float)
    r2_d = Column(Float)
    r3_d = Column(Float)

    r1_f = Column(Float)
    r2_f = Column(Float)

    buy = Column(Float)
    s1_f = Column(Float)
    s2 = Column(Float)
    sell = Column(Float)

    quantity = Column(Integer)
    sl_buffer = Column(Float)

    # 🔥 TRADE CONTROL FIELDS
    current_stage = Column(String, default="WAITING")
    position = Column(String, default="NONE")  # NONE / LONG / SHORT
    last_trade_date = Column(Date, nullable=True)
