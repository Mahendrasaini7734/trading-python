from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database import engine, Base
from app.scheduler import start_scheduler

from app.models.excel_trade_model import ExcelTrade
from app.models.market_symbol_model import MarketSymbol
from app.models.market import MarketData

from app.routes import markets
from app.routes.excel_trade import router as excel_trade_router
from app.routes.settings_routes import router as settings_router
from app.routes import excel_market


# ==========================================
# LOGGING CONFIGURATION (🔥 REQUIRED)
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)


# ==========================================
# LIFESPAN
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🚀 Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("🚀 Starting Scheduler...")
    start_scheduler()

    yield

    print("🛑 Application shutting down...")


app = FastAPI(
    title="StackEarn Excel Trading API",
    lifespan=lifespan,
    root_path="/trading/pyapi"
)


@app.get("/")
def root():
    return {
        "status": "running",
        "app": "StackEarn Excel Trading API",
        "auto_trading": "ready"
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://shivayconstructions.com/trading/pyapi"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(excel_trade_router)
app.include_router(settings_router)
app.include_router(markets.router)
app.include_router(excel_market.router)
