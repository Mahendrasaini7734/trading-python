from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.market import MarketData
from app.services.market_calculator import MarketCalculator
from app.services.open_price_scheduler import OpenPriceUpdater


router = APIRouter(prefix="/markets", tags=["Markets"])

# ===============================
# 📦 Pydantic Schemas
# ===============================

class MarketCreate(BaseModel):
    stock: str
    open_price: float
    quantity: int
    sl_buffer: float


class MarketUpdate(BaseModel):
    stock: str | None = None
    open_price: float | None = None
    quantity: int | None = None
    sl_buffer: float | None = None


# ===============================
# GET ALL MARKETS
# ===============================

@router.get("/market-data")
def get_market_data(db: Session = Depends(get_db)):
    markets = db.query(MarketData).order_by(MarketData.id.asc()).all()
    return markets


# ===============================
# ADD MARKET
# ===============================

@router.post("/")
def add_market(data: MarketCreate, db: Session = Depends(get_db)):

    levels = MarketCalculator.calculate(data.open_price)

    market = MarketData(
        stock=data.stock,
        open_price=data.open_price,
        quantity=data.quantity,
        sl_buffer=data.sl_buffer,

        square=levels["square"],
        base=levels["base"],
        dig1=levels["dig1"],
        dig2=levels["dig2"],
        dig3=levels["dig3"],

        r1_d=levels["r1_d"],
        r2_d=levels["r2_d"],
        r3_d=levels["r3_d"],
        r1_f=levels["r1_f"],
        r2_f=levels["r2_f"],
        buy=levels["buy"],
        s1_f=levels["s1_f"],
        s2=levels["s2"],
        sell=levels["sell"],
    )

    db.add(market)
    db.commit()
    db.refresh(market)

    return {
        "success": True,
        "data": market
    }


# ===============================
# UPDATE MARKET
# ===============================

@router.put("/{id}")
def update_market(id: int, data: MarketUpdate, db: Session = Depends(get_db)):

    market = db.query(MarketData).filter(MarketData.id == id).first()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    if data.stock is not None:
        market.stock = data.stock

    if data.open_price is not None:
        market.open_price = data.open_price

        # 🔥 Auto Recalculate Levels
        levels = MarketCalculator.calculate(data.open_price)

        market.square = levels["square"]
        market.base = levels["base"]
        market.dig1 = levels["dig1"]
        market.dig2 = levels["dig2"]
        market.dig3 = levels["dig3"]
        market.r1_d = levels["r1_d"]
        market.r2_d = levels["r2_d"]
        market.r3_d = levels["r3_d"]
        market.r1_f = levels["r1_f"]
        market.r2_f = levels["r2_f"]
        market.buy = levels["buy"]
        market.s1_f = levels["s1_f"]
        market.s2 = levels["s2"]
        market.sell = levels["sell"]

    if data.quantity is not None:
        market.quantity = data.quantity

    if data.sl_buffer is not None:
        market.sl_buffer = data.sl_buffer

    db.commit()
    db.refresh(market)

    return {
        "success": True,
        "data": market
    }


# ===============================
# DELETE MARKET
# ===============================

@router.delete("/{id}")
def delete_market(id: int, db: Session = Depends(get_db)):

    market = db.query(MarketData).filter(MarketData.id == id).first()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    db.delete(market)
    db.commit()

    return {
        "success": True,
        "message": "Market deleted"
    }


# ===============================
# TOGGLE ACTIVE
# ===============================

@router.put("/toggle/{id}")
def toggle_market(id: int, db: Session = Depends(get_db)):

    market = db.query(MarketData).filter(MarketData.id == id).first()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market.is_active = not market.is_active
    db.commit()

    return {
        "success": True,
        "is_active": market.is_active
    }


@router.post("/update-open-price-now")
def update_open_price_now():

    updater = OpenPriceUpdater()
    updater.update_all_markets()

    return {
        "success": True,
        "message": "All market open prices updated manually"
    }
