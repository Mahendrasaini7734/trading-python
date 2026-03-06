import logging
import threading
import time
from datetime import datetime, time as dt_time

from app.services.excel_trade_executor import ExcelTradeExecutor

logger = logging.getLogger("auto_trading")


class AutoTradingService:

    def __init__(self):
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.is_running: bool = False
        self.executor = ExcelTradeExecutor()

        # Market timings (IST)
        self.market_start = dt_time(9, 15)
        self.market_stop = dt_time(15, 15)

        # Poll interval
        self.poll_interval = 10

    # ======================================
    # MARKET TIME CHECK
    # ======================================
    def _is_market_time(self):

        now = datetime.now()

        if now.weekday() >= 5:
            logger.info("🛑 Weekend - Market Closed")
            return False

        if not (self.market_start <= now.time() <= self.market_stop):
            logger.info(f"🛑 Outside Market Time ({now.time()})")
            return False

        return True

    # ======================================
    # INTERNAL LOOP
    # ======================================
    def _trading_loop(self):

        logger.info("🔄 Trading loop started")

        try:
            while not self._stop_event.is_set():

                # Market time check inside loop
                if not self._is_market_time():
                    logger.info("🛑 Market time over. Exiting loop.")
                    break

                try:
                    logger.info("🔥 Calling execute_from_db()")
                    self.executor.execute_from_db()
                except Exception:
                    logger.exception("❌ Trading execution error")

                # Safe sleep
                for _ in range(self.poll_interval):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)

        finally:
            self.is_running = False
            self._stop_event.clear()
            logger.info("🛑 Trading loop stopped")

    # ======================================
    # START TRADING
    # ======================================
    def start_trading(self):

        with self._lock:

            if self.is_running:
                logger.info("⚠ Trading already running")
                return

            logger.info("🚀 Starting Auto Trading...")

            self.is_running = True
            self._stop_event.clear()

            self._thread = threading.Thread(
                target=self._trading_loop,
                daemon=True
            )

            self._thread.start()

            logger.info("✅ Auto Trading STARTED")

    # ======================================
    # STOP TRADING
    # ======================================
    def stop_trading(self):

        with self._lock:

            if not self.is_running:
                logger.info("⚠ Trading already stopped")
                return

            logger.info("🛑 Stopping Auto Trading...")
            self._stop_event.set()

        if self._thread and self._thread.is_alive():
            logger.info("⏳ Waiting for trading thread to finish...")
            self._thread.join(timeout=10)

        self.is_running = False
        logger.info("✅ Auto Trading STOPPED")

    # ======================================
    # STATUS
    # ======================================
    def status(self):

        return {
            "running": self.is_running,
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "market_time": self._is_market_time(),
            "poll_interval": self.poll_interval
        }








# import logging
# import threading
# import time
# from datetime import datetime, time as dt_time

# from app.services.excel_trade_executor import ExcelTradeExecutor

# logger = logging.getLogger("auto_trading")


# class AutoTradingService:

#     def __init__(self):
#         self._lock = threading.Lock()
#         self._thread: threading.Thread | None = None
#         self.is_running: bool = False
#         self.executor = ExcelTradeExecutor()

#     # ======================================
#     # INTERNAL LOOP
#     # ======================================
#     def _trading_loop(self):

#         logger.info("🔄 Trading loop started")

#         try:
#             while self.is_running:

#                 # 🕒 Auto Stop After Market Close (3:30 PM)
#                 now = datetime.now().time()
#                 if now >= dt_time(15, 30):
#                     logger.info("🛑 Market closed. Auto stopping trading.")
#                     self.is_running = False
#                     break

#                 try:
#                     self.executor.execute_from_db()
#                 except Exception:
#                     logger.exception("❌ Trading execution error")

#                 # ⏱ Poll interval (10 sec)
#                 for _ in range(10):
#                     if not self.is_running:
#                         break
#                     time.sleep(1)

#         finally:
#             self.is_running = False
#             logger.info("🛑 Trading loop stopped")

#     # ======================================
#     # START TRADING
#     # ======================================
#     def start_trading(self):

#         with self._lock:

#             if self.is_running:
#                 logger.info("⚠ Trading already running")
#                 return

#             logger.info("🚀 Starting Auto Trading...")

#             self.is_running = True

#             self._thread = threading.Thread(
#                 target=self._trading_loop,
#                 daemon=True
#             )

#             self._thread.start()

#             logger.info("✅ Auto Trading STARTED")

#     # ======================================
#     # STOP TRADING
#     # ======================================
#     def stop_trading(self):

#         with self._lock:

#             if not self.is_running:
#                 logger.info("⚠ Trading already stopped")
#                 return

#             logger.info("🛑 Stopping Auto Trading...")

#             self.is_running = False

#         # Wait for thread to close cleanly
#         if self._thread and self._thread.is_alive():
#          logger.info("Waiting for trading thread to finish...")
#         self._thread.join(timeout=5)

#         logger.info("✅ Auto Trading STOPPED")

#     # ======================================
#     # STATUS
#     # ======================================
#     def status(self):

#         return {
#             "running": self.is_running,
#             "thread_alive": self._thread.is_alive() if self._thread else False
#         }
