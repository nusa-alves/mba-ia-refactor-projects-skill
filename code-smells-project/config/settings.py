import os
import secrets


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32)
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    PORT = int(os.environ.get("PORT", "5000"))
    CORS_ORIGINS = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()]
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    SEED_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(24)
    SEED_CUSTOMER_PASSWORD = os.environ.get("SEED_CUSTOMER_PASSWORD") or secrets.token_urlsafe(24)
    SEED_SECOND_CUSTOMER_PASSWORD = os.environ.get("SEED_SECOND_CUSTOMER_PASSWORD") or secrets.token_urlsafe(24)

