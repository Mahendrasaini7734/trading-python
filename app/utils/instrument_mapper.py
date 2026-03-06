import json
import logging
import os
import time
from typing import Dict, Optional, Tuple, List

import requests
from app.config import settings

logger = logging.getLogger("instrument_mapper")


class InstrumentMapper:

    CACHE_DIR = "cache"
    CACHE_FILE = os.path.join(CACHE_DIR, "instrument_master.json")
    CACHE_EXPIRY = 86400  # 24 hours

    def __init__(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        self._mapping: Dict[Tuple[str, str], str] = {}
        self._loaded_at: float = 0.0

    # ==========================================
    # DOWNLOAD MASTER FILE
    # ==========================================
    def _download_master(self) -> list:
        logger.info("⬇ Downloading instrument master...")

        response = requests.get(settings.INSTRUMENTS_URL, timeout=30)
        response.raise_for_status()

        data = response.json()

        with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)

        logger.info("✅ Instrument master downloaded")

        return data

    # ==========================================
    # LOAD MASTER (With Cache Support)
    # ==========================================
    def _load(self) -> None:
        now = time.time()

        # If already loaded and cache valid → skip
        if self._mapping and (now - self._loaded_at) < self.CACHE_EXPIRY:
            return

        data = None

        # Try loading from cache
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info("📁 Loaded instrument master from cache")
            except Exception as e:
                logger.warning("⚠ Cache load failed: %s", e)
                data = None

        # If no cache → download
        if not data:
            data = self._download_master()

        mapping: Dict[Tuple[str, str], str] = {}

        for item in data:
            exch = (item.get("exch_seg") or "").strip().upper()
            sym = (item.get("symbol") or "").strip().upper()
            token = str(item.get("token") or "").strip()

            # Only NSE Cash Equity
            if exch == "NSE" and sym.endswith("-EQ") and token:

                clean_symbol = sym.replace("-EQ", "")
                mapping[(exch, clean_symbol)] = token

        self._mapping = mapping
        self._loaded_at = now

        logger.info("✅ Instrument master loaded. NSE EQ count=%s", len(mapping))

    # ==========================================
    # GET TOKEN FOR SYMBOL
    # ==========================================
    def get_token(self, exchange: str, symbol: str) -> Optional[str]:

        self._load()

        exchange = exchange.strip().upper()
        symbol = symbol.strip().upper()

        token = self._mapping.get((exchange, symbol))

        if not token:
            logger.warning("❌ Token not found for %s %s", exchange, symbol)

        return token

    # ==========================================
    # GET ALL TOKENS (For WebSocket Subscribe)
    # ==========================================
    def get_all_tokens(self):
        self._load()
        return list(self._mapping.values())


    # ==========================================
    # FORCE REFRESH MASTER
    # ==========================================
    def refresh(self):

        logger.info("🔄 Force refreshing instrument master...")

        if os.path.exists(self.CACHE_FILE):
            os.remove(self.CACHE_FILE)

        self._mapping = {}
        self._loaded_at = 0.0

        self._load()

        logger.info("✅ Instrument master refreshed successfully")


# Singleton Instance
instrument_mapper = InstrumentMapper()





# import json
# import logging
# import os
# import time
# from typing import Dict, Optional, Tuple

# import requests
# from app.config import settings

# logger = logging.getLogger("excel_trade")


# class InstrumentMapper:

#     CACHE_DIR = "cache"
#     CACHE_FILE = os.path.join(CACHE_DIR, "instrument_master.json")
#     CACHE_EXPIRY = 86400  # 24 hours

#     def __init__(self):
#         os.makedirs(self.CACHE_DIR, exist_ok=True)
#         self._mapping: Dict[Tuple[str, str], str] = {}
#         self._loaded_at: float = 0.0

#     # ==========================================
#     # DOWNLOAD MASTER
#     # ==========================================
#     def _download_master(self) -> list:
#         logger.info("Downloading instrument master from %s", settings.INSTRUMENTS_URL)

#         response = requests.get(settings.INSTRUMENTS_URL, timeout=30)
#         response.raise_for_status()

#         data = response.json()

#         with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
#             json.dump(data, f)

#         logger.info("Instrument master downloaded")

#         return data

#     # ==========================================
#     # LOAD MASTER (WITH CACHE)
#     # ==========================================
#     def _load(self) -> None:
#         now = time.time()

#         if self._mapping and (now - self._loaded_at) < self.CACHE_EXPIRY:
#             return

#         data = None

#         if os.path.exists(self.CACHE_FILE):
#             try:
#                 with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
#                     data = json.load(f)
#             except Exception as e:
#                 logger.warning("Cache load failed: %s", e)
#                 data = None

#         if not data:
#             data = self._download_master()

#         mapping: Dict[Tuple[str, str], str] = {}

#         for item in data:
#             exch = (item.get("exch_seg") or "").strip().upper()
#             sym = (item.get("symbol") or "").strip().upper()
#             token = str(item.get("token") or "").strip()

#             # 🔥 Correct filter for NSE Cash Equity
#             if exch == "NSE" and sym.endswith("-EQ") and token:

#                 # Store without -EQ so Excel can use plain symbol
#                 clean_symbol = sym.replace("-EQ", "")

#                 mapping[(exch, clean_symbol)] = token

#         self._mapping = mapping
#         self._loaded_at = now

#         logger.info("Instrument master loaded. NSE EQ count=%s", len(mapping))

#     # ==========================================
#     # GET TOKEN
#     # ==========================================
#     def get_token(self, exchange: str, symbol: str) -> Optional[str]:

#         self._load()

#         exchange = exchange.strip().upper()
#         symbol = symbol.strip().upper()

#         logger.info("Fetching token for %s %s", exchange, symbol)

#         token = self._mapping.get((exchange, symbol))
#         if token:
#             return token

#         logger.warning("Token not found for %s %s", exchange, symbol)
#         return None

#     # ==========================================
#     # FORCE REFRESH
#     # ==========================================
#     def refresh(self):
#         if os.path.exists(self.CACHE_FILE):
#             os.remove(self.CACHE_FILE)

#         self._mapping = {}
#         self._loaded_at = 0.0
#         self._load()


# instrument_mapper = InstrumentMapper()







