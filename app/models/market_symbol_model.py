from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base


class MarketSymbol(Base):
    __tablename__ = "market_symbols"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String, unique=True, index=True)

    r1f = Column(Float, nullable=True)
    r2f = Column(Float, nullable=True)
    s1f = Column(Float, nullable=True)
    s2 = Column(Float, nullable=True)

    quantity = Column(Integer, default=1)
    sl_buffer = Column(Float, default=0)

    open_price = Column(Float, nullable=True)

    is_active = Column(Boolean, default=True)
