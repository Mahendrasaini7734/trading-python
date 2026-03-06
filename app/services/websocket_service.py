# import threading
# import logging
# from typing import Dict

# from SmartApi.smartWebSocketV2 import SmartWebSocketV2
# from app.services.smart_api_service import SmartAPIService
# from app.utils.instrument_mapper import instrument_mapper
# from app.config import settings

# logger = logging.getLogger("websocket")

# # 🔥 Global LTP Store
# ltp_cache: Dict[str, float] = {}


# class AngelWebSocket:

#     def __init__(self):
#         self.ws = None
#         self.thread = None
#         self.running = False

#     # ==========================================
#     # ON DATA (LTP RECEIVE)
#     # ==========================================
#     def on_data(self, wsapp, message):

#         try:
#             token = message.get("token")
#             ltp = message.get("last_traded_price")

#             if token and ltp:
#                 # Angel sends price ×100
#                 ltp_cache[str(token)] = float(ltp) / 100

#         except Exception:
#             logger.exception("❌ WebSocket data error")

#     # ==========================================
#     # ON OPEN
#     # ==========================================
#     def on_open(self, wsapp):
#         logger.info("✅ WebSocket Connected")

#         tokens = instrument_mapper.get_all_tokens()

#         if not tokens:
#             logger.warning("⚠ No tokens to subscribe")
#             return

#         try:
#             wsapp.subscribe(
#                 correlation_id="1",
#                 mode=1,  # LTP mode
#                 token_list=[
#                     {
#                         "exchangeType": 1,  # NSE
#                         "tokens": tokens
#                     }
#                 ]
#             )

#             logger.info(f"📡 Subscribed {len(tokens)} tokens")

#         except Exception:
#             logger.exception("❌ Subscription failed")

#     # ==========================================
#     # ON ERROR
#     # ==========================================
#     def on_error(self, wsapp, error):
#         logger.error(f"❌ WebSocket Error: {error}")

#     # ==========================================
#     # ON CLOSE
#     # ==========================================
#     def on_close(self, wsapp):
#         logger.warning("⚠ WebSocket Closed")

#     # ==========================================
#     # CONNECT
#     # ==========================================
#     def connect(self):

#         smart_service = SmartAPIService.get_instance()
#         smart_service.login()

#         smart = smart_service.get_client()

#         auth_token = smart.access_token
#         feed_token = smart.getfeedToken()

#         self.ws = SmartWebSocketV2(
#             auth_token,
#             settings.API_KEY,
#             settings.CLIENT_CODE,
#             feed_token
#         )

#         self.ws.on_open = self.on_open
#         self.ws.on_data = self.on_data
#         self.ws.on_error = self.on_error
#         self.ws.on_close = self.on_close

#         self.running = True
#         self.ws.connect()

#     # ==========================================
#     # START THREAD
#     # ==========================================
#     def start(self):
#         if self.thread and self.thread.is_alive():
#             return

#         self.thread = threading.Thread(target=self.connect, daemon=True)
#         self.thread.start()

#     # ==========================================
#     # STOP
#     # ==========================================
#     def stop(self):
#         self.running = False
#         if self.ws:
#             self.ws.close()


# # 🔥 Singleton Instance
# angel_ws = AngelWebSocket()


# # ==========================================
# # START FUNCTION FOR main.py
# # ==========================================
# def start_websocket():
#     angel_ws.start()
