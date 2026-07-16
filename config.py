import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-insegura')
    DB_PATH = os.getenv('DB_PATH', './data/odonto.db')
    ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = ENV == 'development'

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './data/uploads')
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB por upload

    WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL', '')
    WHATSAPP_API_KEY = os.getenv('WHATSAPP_API_KEY', '')
    WHATSAPP_INSTANCE = os.getenv('WHATSAPP_INSTANCE', '')

    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
