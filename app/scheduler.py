import logging
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.open_price_scheduler import OpenPriceUpdater
from app.services.auto_trading_service import AutoTradingService
from app.utils.instrument_mapper import instrument_mapper

logger = logging.getLogger("scheduler")

# -----------------------------------------
# IST Timezone
# -----------------------------------------
IST = pytz.timezone("Asia/Kolkata")

# -----------------------------------------
# Scheduler Instance
# -----------------------------------------
scheduler = BackgroundScheduler(
    timezone=IST,
    job_defaults={
        "coalesce": True,          # Merge missed runs
        "max_instances": 1,        # Prevent parallel runs
        "misfire_grace_time": 300  # 5 min grace
    }
)

trading_service = AutoTradingService()


def start_scheduler():

    if scheduler.running:
        logger.warning("⚠ Scheduler already running")
        return

    logger.info("🚀 Scheduler Starting...")

    updater = OpenPriceUpdater()

    # ==========================================
    # WEEKDAYS ONLY (MON-FRI)
    # ==========================================
    weekdays = "mon-fri"

    # ==========================================
    # 8:35 AM → Instrument Master Refresh
    # ==========================================
    scheduler.add_job(
        instrument_mapper._load,
        CronTrigger(day_of_week=weekdays, hour=8, minute=35),
        id="instrument_refresh_job",
        replace_existing=True
    )

    # ==========================================
    # 9:10 AM → Open Price Update
    # ==========================================
    scheduler.add_job(
        updater.update_all_markets,
        CronTrigger(day_of_week=weekdays, hour=16, minute=23),
        id="daily_open_price_job",
        replace_existing=True
    )

    # ==========================================
    # 9:16 AM → Start Trading
    # ==========================================
    scheduler.add_job(
        trading_service.start_trading,
        CronTrigger(day_of_week=weekdays, hour=9, minute=37),
        id="start_trading_job",
        replace_existing=True
    )

    # ==========================================
    # 3:15 PM → Stop Trading (Auto Stop Before Close)
    # ==========================================
    scheduler.add_job(
        trading_service.stop_trading,
        CronTrigger(day_of_week=weekdays, hour=15, minute=30),
        id="stop_trading_job",
        replace_existing=True
    )

    scheduler.start()

    logger.info("✅ Scheduler Started Successfully (IST)")





# from apscheduler.schedulers.background import BackgroundScheduler
# from app.services.open_price_scheduler import OpenPriceUpdater
# from app.services.auto_trading_service import AutoTradingService
# from app.utils.instrument_mapper import instrument_mapper
# import logging
# import pytz

# logger = logging.getLogger("scheduler")

# scheduler = BackgroundScheduler(
#     timezone=pytz.timezone("Asia/Kolkata")
# )

# trading_service = AutoTradingService()


# def start_scheduler():

#     logger.info("🚀 Scheduler Starting...")

#     updater = OpenPriceUpdater()

#     # ==========================================
#     # 8:30 AM → Instrument Master Refresh
#     # ==========================================
#     scheduler.add_job(
#         instrument_mapper._load,
#         trigger="cron",
#         hour=8,
#         minute=35,
#         id="instrument_refresh_job",
#         replace_existing=True
#     )

#     # ==========================================
#     # 9:10 AM → Open Price Update
#     # ==========================================
#     scheduler.add_job(
#         updater.update_all_markets,
#         trigger="cron",
#         hour=9,
#         minute=10,
#         id="daily_open_price_job",
#         replace_existing=True
#     )

#     # ==========================================
#     # 9:16 AM → Start Trading
#     # ==========================================
#     scheduler.add_job(
#         trading_service.start_trading,
#         trigger="cron",
#         hour=9,
#         minute=16,
#         id="start_trading_job",
#         replace_existing=True
#     )

#     scheduler.add_job(
#         trading_service.stop_trading,
#         trigger="cron",
#         hour=15,
#         minute=15,
#         id="stop_trading_job",
#         replace_existing=True
#     )


#     scheduler.start()


#     logger.info("🚀 Scheduler Started (IST Timezone)")
