import os
from pydantic_settings import BaseSettings
from pydantic import Field
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    # ================= API Credentials =================
    API_KEY: str = Field(default="")
    CLIENT_CODE: str = Field(default="")
    MPIN: str = Field(default="")
    TOTP_SECRET: str = Field(default="")

    # ================= Database ================

    DATABASE_URL: str = Field(
        default=f"sqlite:///{BASE_DIR}/excel_trades.db"
    )
    # ================= Trading Settings =================
    MAX_ORDERS_PER_UPLOAD: int = Field(default=50)
    DRY_RUN: bool = Field(default=False)

    # ================= Angel Instruments =================
    INSTRUMENTS_URL: str = Field(
        default="https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    )

    # ================= File System =================
    UPLOAD_DIR: str = Field(default="uploads")
    EXCEL_TRADE_LOG_PATH: str = Field(default="logs/excel_trade.log")

    # ================= Auto Mode =================
    AUTO_POLL_INTERVAL_SEC: int = Field(default=10)

    # ================= Default Order Config =================
    DEFAULT_EXCHANGE: str = Field(default="NSE")
    DEFAULT_QTY: int = Field(default=1)
    DEFAULT_PRODUCT_TYPE: str = Field(default="INTRADAY")
    DEFAULT_VALIDITY: str = Field(default="DAY")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# ================= Ensure directories exist =================
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

log_dir = os.path.dirname(settings.EXCEL_TRADE_LOG_PATH)
if log_dir:
    os.makedirs(log_dir, exist_ok=True)



# import os
# from pydantic_settings import BaseSettings
# from pydantic import Field


# class Settings(BaseSettings):
#     API_KEY: str = Field(default="")
#     CLIENT_CODE: str = Field(default="")
#     MPIN: str = Field(default="")
#     TOTP_SECRET: str = Field(default="")

#     DATABASE_URL: str = Field(default="sqlite:///./excel_trades.db")

#     MAX_ORDERS_PER_UPLOAD: int = Field(default=50)
#     DRY_RUN: bool = Field(default=False)

#     INSTRUMENTS_URL: str = Field(
#         default="https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
#     )

#     UPLOAD_DIR: str = Field(default="uploads")
#     EXCEL_TRADE_LOG_PATH: str = Field(default="logs/excel_trade.log")

#     # ✅ AUTO MODE SETTINGS (must be inside class)
#     AUTO_POLL_INTERVAL_SEC: int = Field(default=10)

#     DEFAULT_EXCHANGE: str = Field(default="NSE")
#     DEFAULT_QTY: int = Field(default=1)
#     DEFAULT_PRODUCT_TYPE: str = Field(default="INTRADAY")
#     DEFAULT_VALIDITY: str = Field(default="DAY")

#     class Config:
#         env_file = ".env"
#         extra = "ignore"


# settings = Settings()

# # ensure dirs
# os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
# os.makedirs(os.path.dirname(settings.EXCEL_TRADE_LOG_PATH), exist_ok=True)


# import os
# from pydantic_settings import BaseSettings
# from pydantic import Field

# class Settings(BaseSettings):
#     API_KEY: str = Field(default="")
#     CLIENT_CODE: str = Field(default="")
#     MPIN: str = Field(default="")
#     TOTP_SECRET: str = Field(default="")
#     DATABASE_URL: str = Field(default="sqlite:///./excel_trades.db")
#     MAX_ORDERS_PER_UPLOAD: int = Field(default=20)
#     DRY_RUN: bool = Field(default=True)
#     INSTRUMENTS_URL: str = Field(default="https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json")
#     UPLOAD_DIR: str = Field(default="uploads")
#     EXCEL_TRADE_LOG_PATH: str = Field(default="logs/excel_trade.log")

#     class Config:
#         env_file = ".env"
#         extra = "ignore"

# settings = Settings()

# os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
# os.makedirs(os.path.dirname(settings.EXCEL_TRADE_LOG_PATH), exist_ok=True)
# ab hmae amin side upadte ekrn ah to muje kon jonnos file new add hogi or konis update hogi 