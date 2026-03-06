import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models.market import MarketData
from app.services.market_calculator import MarketCalculator
from app.utils.instrument_mapper import instrument_mapper
from app.config import settings
from app.services.smart_api_service import SmartAPIService


logger = logging.getLogger("open_price_scheduler")


class OpenPriceUpdater:

    def __init__(self):
        self.smart_service = SmartAPIService.get_instance()

    # ============================================
    # MAIN UPDATE METHOD (BULK SAFE VERSION)
    # ============================================
    def update_all_markets(self):

        db: Session = SessionLocal()

        try:
            logger.info("🚀 Starting open price update job")

            rows = db.query(MarketData).all()

            if not rows:
                logger.warning("⚠ No markets found in DB")
                return

            # --------------------------------------
            # STEP 1: Collect Tokens
            # --------------------------------------
            token_row_map = {}
            tokens = []

            for row in rows:

                symbol = (row.stock or "").strip().upper()

                if not symbol:
                    continue

                token = instrument_mapper.get_token("NSE", symbol)

                if not token:
                    logger.warning(f"⚠ Token not found: {symbol}")
                    continue

                token_row_map[token] = row
                tokens.append(token)

            if not tokens:
                logger.warning("⚠ No valid tokens found")
                return

            # --------------------------------------
            # STEP 2: Fetch LTP in Batch
            # --------------------------------------
            if settings.DRY_RUN:

                ltp_map = {
                    instrument_mapper.get_token("NSE", row.stock.upper()):
                        float(row.open_price or 100)
                    for row in rows
                }

            else:

                ltp_data = self.smart_service.get_batch_ltp(tokens)

                ltp_map = {}

                for token, data in ltp_data.items():
                    try:
                        # ⚠ Some brokers don't return 'open' in LTP mode
                        # So we fallback to LTP if open missing
                        open_price = float(data.get("open") or data.get("ltp") or 0)
                        ltp_map[token] = open_price
                    except:
                        continue

            # --------------------------------------
            # STEP 3: Update DB
            # --------------------------------------
            updated_count = 0

            for token, open_price in ltp_map.items():

                row = token_row_map.get(token)

                if not row:
                    continue

                if open_price <= 0:
                    continue

                levels = MarketCalculator.calculate(open_price)

                row.open_price = open_price
                row.square = levels["square"]
                row.base = levels["base"]
                row.dig1 = levels["dig1"]
                row.dig2 = levels["dig2"]
                row.dig3 = levels["dig3"]
                row.r1_d = levels["r1_d"]
                row.r2_d = levels["r2_d"]
                row.r3_d = levels["r3_d"]
                row.r1_f = levels["r1_f"]
                row.r2_f = levels["r2_f"]
                row.buy = levels["buy"]
                row.s1_f = levels["s1_f"]
                row.s2 = levels["s2"]
                row.sell = levels["sell"]

                updated_count += 1

            db.commit()

            logger.info(f"✅ Open price update completed. Updated: {updated_count}")

        except SQLAlchemyError:
            db.rollback()
            logger.exception("❌ Database error")

        except Exception:
            db.rollback()
            logger.exception("❌ Unexpected error in open price update")

        finally:
            db.close()


#======================>>>> FOR TESTING ===========================================#
# from sqlalchemy.orm import Session
# from app.database import SessionLocal
# from app.models.market import MarketData
# from app.services.market_calculator import MarketCalculator
# import logging

# logger = logging.getLogger("open_price_scheduler")


# class OpenPriceUpdater:

#     @staticmethod
#     def update_all_open_prices():

#         db: Session = SessionLocal()

#         try:
#             markets = db.query(MarketData).all()

#             if not markets:
#                 print("⚠ No markets found")
#                 return

#             print("🔥 Running Open Price Update Job")

#             for market in markets:

#                 # 🔥 TEST MODE VALUE
#                 new_open_price = 1445.50

#                 levels = MarketCalculator.calculate(new_open_price)

#                 market.open_price = new_open_price
#                 market.square = levels["square"]
#                 market.base = levels["base"]
#                 market.dig1 = levels["dig1"]
#                 market.dig2 = levels["dig2"]
#                 market.dig3 = levels["dig3"]
#                 market.r1_d = levels["r1_d"]
#                 market.r2_d = levels["r2_d"]
#                 market.r3_d = levels["r3_d"]
#                 market.r1_f = levels["r1_f"]
#                 market.r2_f = levels["r2_f"]
#                 market.buy = levels["buy"]
#                 market.s1_f = levels["s1_f"]
#                 market.s2 = levels["s2"]
#                 market.sell = levels["sell"]

#             db.commit()

#             print("✅ Open prices updated successfully")

#         except Exception as e:
#             print("❌ Scheduler Error:", e)

#         finally:
#             db.close()
