import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    CORS_ORIGINS = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()]
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
