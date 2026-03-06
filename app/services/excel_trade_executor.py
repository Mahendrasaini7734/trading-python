import logging
from datetime import date, datetime, time
from app.models.market import MarketData
from app.models.excel_trade_model import ExcelTrade
from app.database import SessionLocal
from app.config import settings
from app.utils.instrument_mapper import instrument_mapper
from app.services.smart_api_service import SmartAPIService

logger = logging.getLogger("excel_trade_executor")


class ExcelTradeExecutor:

    def __init__(self):
        self.smart_service = SmartAPIService.get_instance()

    # ==========================================
    # MARKET TIME CHECK
    # ==========================================
    def is_market_open(self):
        now = datetime.now()

        if now.weekday() >= 5:
            logger.info("🛑 Weekend")
            return False

        if not (time(9, 15) <= now.time() <= time(15, 30)):
            logger.info("🛑 Outside market time")
            return False

        return True

    # ==========================================
    # CHECK COMPLETED TODAY
    # ==========================================
    def is_completed_today(self, db, symbol):

        today = date.today()

        trade = db.query(ExcelTrade).filter(
            ExcelTrade.symbol == symbol,
            ExcelTrade.stage == "COMPLETED",
            ExcelTrade.created_at >= today
        ).first()

        return bool(trade)

    # ==========================================
    # PLACE TRADE
    # ==========================================
    def place_trade(self, db, row, action, trigger_price, stage):

        symbol = row.stock.upper()
        qty = int(row.quantity or 0)

        if qty <= 0:
            logger.warning(f"{symbol} quantity invalid")
            return

        order_id = "DRY_RUN"

        if not settings.DRY_RUN:

            token = instrument_mapper.get_token("NSE", symbol)
            if not token:
                logger.warning(f"{symbol} token not found")
                return

            response = self.smart_service.place_order({
                "variety": "NORMAL",
                "tradingsymbol": f"{symbol}-EQ",
                "symboltoken": token,
                "transactiontype": action,
                "exchange": "NSE",
                "ordertype": "MARKET",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "quantity": qty
            })

            if not response or not response.get("status"):
                logger.warning(f"❌ Order failed: {symbol}")
                return

            order_id = response["data"]["orderid"]

        trade = ExcelTrade(
            symbol=symbol,
            action=action,
            quantity=qty,
            trigger_price=trigger_price,
            sl_price=row.open_price,   # 🔥 ALWAYS OPEN PRICE
            order_id=order_id,
            status="EXECUTED",
            stage=stage
        )

        db.add(trade)
        row.current_stage = stage
        db.commit()

        logger.info(f"✅ {symbol} {action} @ {trigger_price} | Stage={stage}")

    # ==========================================
    # MAIN ENGINE
    # ==========================================
    def execute_from_db(self):

        db = SessionLocal()

        try:

            if not self.is_market_open():
                return

            rows = db.query(MarketData).all()

            if not rows:
                logger.info("⚠ No market data")
                return

            tokens = []
            token_map = {}

            for row in rows:
                symbol = row.stock.upper()
                token = instrument_mapper.get_token("NSE", symbol)
                if token:
                    tokens.append(token)
                    token_map[token] = row

            if not tokens:
                logger.warning("⚠ No tokens found")
                return

            # =====================================
            # FETCH BATCH LTP (🔥 FIXED PARSING)
            # =====================================
            ltp_map = {}

            if settings.DRY_RUN:

                for row in rows:
                    token = instrument_mapper.get_token("NSE", row.stock.upper())
                    ltp_map[token] = float(row.open_price or 0)

            else:

                ltp_data = self.smart_service.get_batch_ltp(tokens)

                logger.info(f"Raw LTP Data Count: {len(ltp_data)}")

                for token, data in ltp_data.items():
                    try:
                        ltp_map[str(token)] = float(data.get("ltp", 0))
                    except Exception:
                        continue

            # =====================================
            # STRICT 4 CASE LOGIC
            # =====================================
            for token, ltp in ltp_map.items():

                row = token_map.get(token)
                if not row:
                    continue

                symbol = row.stock.upper()
                open_price = float(row.open_price or 0)
                stage = row.current_stage or "WAITING"

                if self.is_completed_today(db, symbol):
                    continue

                logger.info(f"{symbol} | Stage={stage} | LTP={ltp}")

                # =============================
                # CASE 1 & 2 (UP SIDE FIRST)
                # =============================
                if stage == "WAITING":

                    # R1 BUY
                    if ltp >= row.r1_f:
                        self.place_trade(db, row, "BUY", row.r1_f, "BOUGHT_R1")

                    # S1 SELL
                    elif ltp <= row.s1_f:
                        self.place_trade(db, row, "SELL", row.s1_f, "SOLD_S1")

                # =============================
                # AFTER R1 BUY
                # =============================
                elif stage == "BOUGHT_R1":

                    # R2 SELL → COMPLETE
                    if ltp >= row.r2_f:
                        self.place_trade(db, row, "SELL", row.r2_f, "COMPLETED")

                    # STOPLOSS @ OPEN → COMPLETE
                    elif ltp <= open_price:
                        self.place_trade(db, row, "SELL", open_price, "COMPLETED")

                # =============================
                # AFTER S1 SELL
                # =============================
                elif stage == "SOLD_S1":

                    # S2 BUY → COMPLETE
                    if ltp <= row.s2:
                        self.place_trade(db, row, "BUY", row.s2, "COMPLETED")

                    # STOPLOSS @ OPEN → COMPLETE
                    elif ltp >= open_price:
                        self.place_trade(db, row, "BUY", open_price, "COMPLETED")

        except Exception:
            logger.exception("❌ Execution error")

        finally:
            db.close()






# import logging
# from datetime import date, datetime, time
# from app.models.market import MarketData
# from app.models.excel_trade_model import ExcelTrade
# from app.database import SessionLocal
# from app.config import settings
# from app.utils.instrument_mapper import instrument_mapper
# from app.services.smart_api_service import SmartAPIService

# logger = logging.getLogger("excel_trade_executor")


# class ExcelTradeExecutor:

#     def __init__(self):
#         self.smart_service = SmartAPIService.get_instance()

#     # ==========================================
#     # MARKET TIME CHECK
#     # ==========================================
#     def is_market_open(self):

#         now = datetime.now()

#         if now.weekday() >= 5:
#             logger.info("🛑 Weekend - Market Closed")
#             return False

#         market_start = time(9, 15)
#         market_end = time(15, 30)

#         if not (market_start <= now.time() <= market_end):
#             logger.info("🛑 Market Closed (Time Check)")
#             return False

#         return True

#     # ==========================================
#     # DUPLICATE CHECK
#     # ==========================================
#     def already_executed_today(self, db, symbol, level_name):

#         today = date.today()

#         trade = db.query(ExcelTrade).filter(
#             ExcelTrade.symbol == symbol,
#             ExcelTrade.stage == level_name,
#             ExcelTrade.status == "EXECUTED",
#             ExcelTrade.created_at >= today
#         ).first()

#         return bool(trade)

#     # ==========================================
#     # PLACE TRADE
#     # ==========================================
#     def place_trade(self, db, row, action, trigger_price, level_name):

#         symbol = row.stock.upper()
#         qty = int(row.quantity or 0)

#         if qty <= 0:
#             return

#         sl_price = float(row.open_price)   # 🔥 SL ALWAYS OPEN PRICE

#         order_id = None
#         status = "FAILED"

#         if settings.DRY_RUN:
#             logger.info(f"🧪 DRY RUN: {symbol} {action}")
#             order_id = "DRY_RUN"
#             status = "EXECUTED"

#         else:
#             token = instrument_mapper.get_token("NSE", symbol)
#             if not token:
#                 return

#             response = self.smart_service.place_order({
#                 "variety": "NORMAL",
#                 "tradingsymbol": f"{symbol}-EQ",
#                 "symboltoken": token,
#                 "transactiontype": action,
#                 "exchange": "NSE",
#                 "ordertype": "MARKET",
#                 "producttype": "INTRADAY",
#                 "duration": "DAY",
#                 "quantity": qty
#             })

#             if response and response.get("status"):
#                 order_id = response["data"]["orderid"]
#                 status = "EXECUTED"
#             else:
#                 logger.warning(f"❌ Order failed: {symbol}")
#                 return

#         # SAVE SUCCESS ONLY
#         trade = ExcelTrade(
#             symbol=symbol,
#             action=action,
#             quantity=qty,
#             trigger_price=trigger_price,
#             sl_price=sl_price,     # 🔥 OPEN PRICE
#             order_id=order_id,
#             status="EXECUTED",
#             stage=level_name
#         )

#         db.add(trade)
#         db.commit()

#         logger.info(f"✅ {symbol} {action} @ {trigger_price} SL={sl_price}")

#     # ==========================================
#     # MAIN EXECUTION ENGINE
#     # ==========================================
#     def execute_from_db(self):

#         db = SessionLocal()

#         try:

#             if not self.is_market_open():
#                 return

#             rows = db.query(MarketData).all()

#             if not rows:
#                 logger.info("⚠ No market data")
#                 return

#             # Collect tokens
#             tokens = []
#             token_map = {}

#             for row in rows:
#                 symbol = (row.stock or "").strip().upper()
#                 token = instrument_mapper.get_token("NSE", symbol)

#                 if token:
#                     tokens.append(token)
#                     token_map[token] = row

#             if not tokens:
#                 return

#             # Get Batch LTP
#             if settings.DRY_RUN:
#                 ltp_map = {
#                     instrument_mapper.get_token("NSE", row.stock.upper()):
#                         float(row.open_price or 0)
#                     for row in rows
#                 }
#             else:
#                 ltp_data = self.smart_service.get_batch_ltp(tokens)
#                 ltp_map = {}

#                 fetched = ltp_data.get("fetched", [])

#                 for item in fetched:
#                     token = str(item.get("symbolToken"))
#                     ltp_map[token] = float(item.get("ltp") or 0)

#             # ======================================
#             # LEVEL BASED LOGIC (NO STAGE DEPENDENCY)
#             # ======================================
#             for token, ltp in ltp_map.items():

#                 row = token_map.get(token)
#                 if not row:
#                     continue

#                 symbol = row.stock.upper()

#                 logger.info(f"📈 {symbol} LTP = {ltp}")

#                 # ---------- R1 BUY ----------
#                 if ltp >= row.r1_f and not self.already_executed_today(db, symbol, "R1_BUY"):

#                     self.place_trade(
#                         db=db,
#                         row=row,
#                         action="BUY",
#                         trigger_price=row.r1_f,
#                         level_name="R1_BUY"
#                     )

#                 # ---------- R2 SELL ----------
#                 elif ltp >= row.r2_f and not self.already_executed_today(db, symbol, "R2_SELL"):

#                     self.place_trade(
#                         db=db,
#                         row=row,
#                         action="SELL",
#                         trigger_price=row.r2_f,
#                         level_name="R2_SELL"
#                     )

#                 # ---------- S1 SELL ----------
#                 elif ltp <= row.s1_f and not self.already_executed_today(db, symbol, "S1_SELL"):

#                     self.place_trade(
#                         db=db,
#                         row=row,
#                         action="SELL",
#                         trigger_price=row.s1_f,
#                         level_name="S1_SELL"
#                     )

#                 # ---------- S2 BUY ----------
#                 elif ltp <= row.s2 and not self.already_executed_today(db, symbol, "S2_BUY"):

#                     self.place_trade(
#                         db=db,
#                         row=row,
#                         action="BUY",
#                         trigger_price=row.s2,
#                         level_name="S2_BUY"
#                     )

#         finally:
#             db.close()

#     def __init__(self):
#         self.smart_service = SmartAPIService.get_instance()

#     # ==========================================
#     # MARKET TIME CHECK
#     # ==========================================
#     def is_market_open(self):

#         now = datetime.now()

#         if now.weekday() >= 5:
#             return False

#         market_start = time(9, 15)
#         market_end = time(15, 30)

#         return market_start <= now.time() <= market_end

#     # ==========================================
#     # DUPLICATE CHECK
#     # ==========================================
#     def already_executed_today(self, db, symbol, stage_name):

#         today = date.today()

#         trade = db.query(ExcelTrade).filter(
#             ExcelTrade.symbol == symbol,
#             ExcelTrade.stage == stage_name,
#             ExcelTrade.status == "EXECUTED",
#             ExcelTrade.created_at >= today
#         ).first()

#         return bool(trade)

#     # ==========================================
#     # PLACE TRADE (PRODUCTION SAFE)
#     # ==========================================
#     def place_trade(self, db, row, action, trigger_price, sl_price, stage_name):

#         symbol = row.stock.upper()
#         qty = int(row.quantity)

#         # --------------------------------------
#         # DRY RUN
#         # --------------------------------------
#         if settings.DRY_RUN:

#             order_id = "DRY_RUN"
#             status = "EXECUTED"

#         else:

#             token = instrument_mapper.get_token("NSE", symbol)
#             if not token:
#                 return

#             orderparams = {
#                 "variety": "NORMAL",
#                 "tradingsymbol": f"{symbol}-EQ",
#                 "symboltoken": token,
#                 "transactiontype": action,
#                 "exchange": "NSE",
#                 "ordertype": "MARKET",
#                 "producttype": "INTRADAY",
#                 "duration": "DAY",
#                 "quantity": qty
#             }

#             response = self.smart_service.place_order(orderparams)

#             # --------------------------------------
#             # SUCCESS
#             # --------------------------------------
#             if response and response.get("status"):

#                 order_id = response["data"]["orderid"]
#                 status = "EXECUTED"

#             # --------------------------------------
#             # RESTRICTED STOCK
#             # --------------------------------------
#             elif response and response.get("restricted"):

#                 print(f"🚫 {symbol} Restricted by exchange.")
#                 row.current_stage = "BLOCKED"
#                 db.commit()
#                 return

#             # --------------------------------------
#             # RATE LIMIT
#             # --------------------------------------
#             elif response and response.get("rate_limited"):

#                 print("⚠ Rate limited. Skipping this cycle.")
#                 return

#             # --------------------------------------
#             # OTHER FAILURE
#             # --------------------------------------
#             else:

#                 print(f"❌ {symbol} Order Failed — Not Saved")
#                 return

#         # --------------------------------------
#         # SAVE ONLY SUCCESS
#         # --------------------------------------
#         trade = ExcelTrade(
#             symbol=symbol,
#             action=action,
#             quantity=qty,
#             trigger_price=trigger_price,
#             sl_price=sl_price,
#             order_id=order_id,
#             status="EXECUTED",
#             stage=stage_name
#         )

#         db.add(trade)

#         # Move stage forward
#         row.current_stage = stage_name

#         db.commit()

#         print(f"✅ {symbol} {action} {stage_name} -> EXECUTED")

#     # ==========================================
#     # MAIN ENGINE (BULK LTP SAFE VERSION)
#     # ==========================================
#     def execute_from_db(self):

#         db = SessionLocal()

#         try:

#             rows = db.query(MarketData).all()

#             if not rows:
#                 print("⚠ No market data found")
#                 return

#             if not self.is_market_open():
#                 print("🛑 Market Closed")
#                 return

#             # --------------------------------------
#             # STEP 1: Collect Tokens
#             # --------------------------------------
#             symbol_token_map = {}
#             tokens = []

#             for row in rows:

#                 symbol = (row.stock or "").strip().upper()
#                 token = instrument_mapper.get_token("NSE", symbol)

#                 if token:
#                     symbol_token_map[token] = symbol
#                     tokens.append(token)

#             if not tokens:
#                 return

#             # --------------------------------------
#             # STEP 2: Fetch Bulk LTP
#             # --------------------------------------
#             if settings.DRY_RUN:

#                 ltp_map = {
#                     instrument_mapper.get_token("NSE", row.stock.upper()):
#                         float(row.open_price or 0)
#                     for row in rows
#                 }

#             else:

#                 ltp_data = self.smart_service.get_batch_ltp(tokens)

#                 ltp_map = {}

#                 for token, data in ltp_data.items():
#                     try:
#                         ltp_map[token] = float(data.get("ltp", 0))
#                     except:
#                         continue

#             # --------------------------------------
#             # STEP 3: Trading Logic
#             # --------------------------------------
#             for row in rows:

#                 symbol = (row.stock or "").strip().upper()
#                 qty = int(row.quantity or 0)
#                 open_price = float(row.open_price or 0)

#                 if qty <= 0:
#                     continue

#                 token = instrument_mapper.get_token("NSE", symbol)
#                 if not token:
#                     continue

#                 ltp = ltp_map.get(token)

#                 if not ltp:
#                     continue

#                 stage = row.current_stage or "WAITING"

#                 action = None
#                 trigger_price = None
#                 sl_price = None
#                 next_stage = None

#                 # -------------------------------
#                 # STAGE FLOW
#                 # -------------------------------
#                 if stage == "WAITING":

#                     if ltp >= row.r1_f:
#                         action = "BUY"
#                         trigger_price = row.r1_f
#                         sl_price = open_price 
#                         next_stage = "R1_DONE"

#                 elif stage == "R1_DONE":

#                     if ltp <= open_price:
#                         action = "SELL"
#                         trigger_price = open_price
#                         sl_price = row.r1_f 
#                         next_stage = "COMPLETED"

#                     elif ltp >= row.r2_f:
#                         action = "SELL"
#                         trigger_price = row.r2_f
#                         sl_price = row.r1_f
#                         next_stage = "R2_DONE"

#                 elif stage == "R2_DONE":

#                     if ltp <= row.s1_f:
#                         action = "SELL"
#                         trigger_price = row.s1_f
#                         sl_price = row.r2_f 
#                         next_stage = "S1_DONE"

#                 elif stage == "S1_DONE":

#                     if ltp <= row.s2:
#                         action = "BUY"
#                         trigger_price = row.s2
#                         sl_price = row.s1_f
#                         next_stage = "COMPLETED"

#                 # -------------------------------
#                 # Skip completed or blocked
#                 # -------------------------------
#                 if stage in ["COMPLETED", "BLOCKED"]:
#                     continue

#                 if not action:
#                     continue

#                 if self.already_executed_today(db, symbol, next_stage):
#                     continue

#                 # -------------------------------
#                 # EXECUTE
#                 # -------------------------------
#                 self.place_trade(
#                     db=db,
#                     row=row,
#                     action=action,
#                     trigger_price=trigger_price,
#                     sl_price=sl_price,
#                     stage_name=next_stage
#                 )

#         finally:
#             db.close()