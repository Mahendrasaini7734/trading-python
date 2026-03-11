import logging
import threading
import time
from typing import Optional, List, Dict
from SmartApi import SmartConnect
import pyotp
from app.config import settings

logger = logging.getLogger("smart_api")


class SmartAPIService:

    _instance = None
    _lock = threading.Lock()

    # ==========================================
    # INIT
    # ==========================================
    def __init__(self):
        self.smart: Optional[SmartConnect] = None
        self.logged_in = False
        self.last_order_time = 0
        self.rate_limit_cooldown = 5   # seconds cooldown after rate limit

    # ==========================================
    # SINGLETON
    # ==========================================
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = SmartAPIService()
        return cls._instance

    # ==========================================
    # LOGIN
    # ==========================================
    def login(self):

        with self._lock:

            if self.logged_in and self.smart:
                return

            logger.info("🔐 Logging into Angel SmartAPI")

            smart = SmartConnect(settings.API_KEY)
            totp = pyotp.TOTP(settings.TOTP_SECRET).now()

            data = smart.generateSession(
                settings.CLIENT_CODE,
                settings.MPIN,
                totp
            )

            if not data or not data.get("status"):
                raise Exception("Angel login failed")

            self.smart = smart
            self.logged_in = True

            logger.info("✅ Angel login successful")

    # ==========================================
    # GET CLIENT (Auto re-login)
    # ==========================================
    def get_client(self):

        if not self.logged_in or not self.smart:
            self.login()

        return self.smart

    # ==========================================
    # BATCH LTP (SAFE MODE - LTP ONLY)
    # ==========================================
    def get_batch_ltp(self, tokens: List[str], exchange: str = "NSE") -> Dict:

        try:
            smart = self.get_client()

            exchange_tokens = {
                exchange: tokens
            }

            # 🔥 Light mode instead of FULL
            response = smart.getMarketData("FULL", exchange_tokens)

            if not response or not response.get("status"):
                logger.error("❌ Batch LTP API invalid response")
                return {}

            fetched = response.get("data", {}).get("fetched", [])

            result = {}
            for item in fetched:
                result[item["symbolToken"]] = item

            return result

        except Exception:
            logger.exception("❌ Batch LTP Error")
            return {}

    # ==========================================
    # ORDER THROTTLE
    # ==========================================
    def _apply_order_throttle(self):

        current_time = time.time()

        # Minimum 1 second gap between orders
        if current_time - self.last_order_time < 1:
            sleep_time = 1 - (current_time - self.last_order_time)
            time.sleep(sleep_time)

        self.last_order_time = time.time()

    # ==========================================
    # PLACE ORDER (SAFE VERSION)
    # ==========================================
    def place_order(self, orderparams):

        try:
            smart = self.get_client()

            # 🔥 Throttle to avoid rate limit
            self._apply_order_throttle()

            response = smart.placeOrder(orderparams)

            # If order ID returned as string
            if isinstance(response, str):
                return {
                    "status": True,
                    "data": {"orderid": response}
                }

            if isinstance(response, dict):

                # 🔥 Restricted stock handling (ASM/GSM)
                if response.get("errorcode") == "AB4036":
                    return {
                        "status": False,
                        "restricted": True,
                        "message": response.get("message")
                    }

                return response

            return {
                "status": False,
                "message": "Unknown response format"
            }

        except Exception as e:

            error_text = str(e).lower()

            # 🔥 Rate limit detected
            if "exceeding access rate" in error_text:
                logger.warning("⚠ Rate limit hit. Cooling down...")
                time.sleep(self.rate_limit_cooldown)

                return {
                    "status": False,
                    "rate_limited": True,
                    "message": "Rate limit exceeded"
                }

            # 🔥 Token expired
            if "invalid token" in error_text:
                logger.warning("⚠ Token expired. Re-login triggered.")
                self.logged_in = False
                self.login()

                return {
                    "status": False,
                    "retry": True,
                    "message": "Session refreshed, retry order"
                }

            logger.exception("❌ Order Error")
            return {
                "status": False,
                "message": str(e)
            }





# # import logging
# # import threading
# # from typing import Optional
# # from SmartApi import SmartConnect
# # import pyotp
# # from app.config import settings

# # logger = logging.getLogger("smart_api")


# # class SmartAPIService:

# #     _instance = None
# #     _lock = threading.Lock()

# #     def __init__(self):
# #         self.smart: Optional[SmartConnect] = None
# #         self.logged_in = False

# #     # ==================================
# #     # SINGLETON
# #     # ==================================
# #     @classmethod
# #     def get_instance(cls):
# #         if not cls._instance:
# #             cls._instance = SmartAPIService()
# #         return cls._instance

# #     # ==================================
# #     # LOGIN
# #     # ==================================
# #     def login(self):
# #         with self._lock:

# #             if self.logged_in and self.smart:
# #                 return

# #             logger.info("🔐 Logging into Angel SmartAPI")

# #             smart = SmartConnect(settings.API_KEY)
# #             totp = pyotp.TOTP(settings.TOTP_SECRET).now()

# #             data = smart.generateSession(
# #                 settings.CLIENT_CODE,
# #                 settings.MPIN,
# #                 totp
# #             )

# #             if not data or not data.get("status"):
# #                 raise Exception("Angel login failed")

# #             self.smart = smart
# #             self.logged_in = True

# #             logger.info("✅ Angel login successful")

# #     # ==================================
# #     # GET CLIENT
# #     # ==================================
# #     def get_client(self):
# #         if not self.logged_in or not self.smart:
# #             self.login()
# #         return self.smart

# #     # ==================================
# #     # PLACE ORDER (WITH RESTRICTION HANDLE)
# #     # ==================================
# #     def place_order(self, orderparams):

# #         try:
# #             smart = self.get_client()

# #             response = smart.placeOrder(orderparams)

# #             # If Angel returns order id string
# #             if isinstance(response, str):
# #                 return {
# #                     "status": True,
# #                     "data": {"orderid": response}
# #                 }

# #             if isinstance(response, dict):

# #                 # 🔥 Handle Restricted Script (AB4036)
# #                 if response.get("errorcode") == "AB4036":
# #                     return {
# #                         "status": False,
# #                         "restricted": True,
# #                         "message": response.get("message")
# #                     }

# #                 return response

# #             return None

# #         except Exception:
# #             logger.exception("❌ Order Error")
# #             return None

# #     # ==================================
# #     # LTP
# #     # ==================================
# #     def get_ltp_data(self, exchange, tradingsymbol, symboltoken):

# #         try:
# #             smart = self.get_client()

# #             return smart.ltpData(
# #                 exchange=exchange,
# #                 tradingsymbol=tradingsymbol,
# #                 symboltoken=symboltoken
# #             )

# #         except Exception:
# #             logger.exception("❌ LTP Error")
# #             return None





# import logging
# import threading
# from typing import Optional, List
# from SmartApi import SmartConnect
# import pyotp
# from app.config import settings

# logger = logging.getLogger("smart_api")


# class SmartAPIService:

#     _instance = None
#     _lock = threading.Lock()

#     def __init__(self):
#         self.smart: Optional[SmartConnect] = None
#         self.logged_in = False

#     # ==========================================
#     # SINGLETON
#     # ==========================================
#     @classmethod
#     def get_instance(cls):
#         if not cls._instance:
#             cls._instance = SmartAPIService()
#         return cls._instance

#     # ==========================================
#     # LOGIN
#     # ==========================================
#     def login(self):

#         with self._lock:

#             if self.logged_in and self.smart:
#                 return

#             logger.info("🔐 Logging into Angel SmartAPI")

#             smart = SmartConnect(settings.API_KEY)
#             totp = pyotp.TOTP(settings.TOTP_SECRET).now()

#             data = smart.generateSession(
#                 settings.CLIENT_CODE,
#                 settings.MPIN,
#                 totp
#             )

#             if not data or not data.get("status"):
#                 raise Exception("Angel login failed")

#             self.smart = smart
#             self.logged_in = True

#             logger.info("✅ Angel login successful")

#     # ==========================================
#     # GET CLIENT
#     # ==========================================
#     def get_client(self):

#         if not self.logged_in or not self.smart:
#             self.login()

#         return self.smart

#     # ==========================================
#     # ==========================================
# # SINGLE LTP (Required for Open Price)
# # ==========================================
#     def get_ltp_data(self, exchange, tradingsymbol, symboltoken):

#         try:
#             smart = self.get_client()

#             response = smart.ltpData(
#                 exchange=exchange,
#                 tradingsymbol=tradingsymbol,
#                 symboltoken=symboltoken
#             )

#             if response and not response.get("status"):

#                 message = str(response.get("message", "")).lower()

#                 if "invalid token" in message:
#                     logger.warning("⚠ Token expired. Re-login once.")
#                     self.logged_in = False
#                     self.login()

#                     smart = self.get_client()

#                     return smart.ltpData(
#                         exchange=exchange,
#                         tradingsymbol=tradingsymbol,
#                         symboltoken=symboltoken
#                     )

#             return response

#         except Exception:
#             logger.exception("❌ LTP Error")
#             return None
#     # BULK LTP (AUTO CHUNKED)
#     # ==========================================
#     def get_bulk_ltp(self, exchange: str, tokens: List[str]):

#         try:
#             smart = self.get_client()

#             all_data = []

#             # Angel safe chunk size
#             chunk_size = 50

#             for i in range(0, len(tokens), chunk_size):

#                 chunk = tokens[i:i + chunk_size]

#                 response = smart.getMarketData(
#                     mode="LTP",
#                     exchangeTokens={
#                         exchange: chunk
#                     }
#                 )

#                 if response and response.get("status"):

#                     fetched = response.get("data", {}).get("fetched", [])
#                     all_data.extend(fetched)

#                 else:
#                     logger.warning(f"⚠ Bulk LTP failed for chunk: {chunk}")

#             return all_data

#         except Exception:
#             logger.exception("❌ Bulk LTP Error")
#             return []

#     # ==========================================
#     # PLACE ORDER
#     # ==========================================
#     def place_order(self, orderparams):

#         try:
#             smart = self.get_client()

#             response = smart.placeOrder(orderparams)

#             if isinstance(response, str):
#                 return {
#                     "status": True,
#                     "data": {"orderid": response}
#                 }

#             if isinstance(response, dict):
#                 return response

#             return None

#         except Exception:
#             logger.exception("❌ Order Error")
#             return None