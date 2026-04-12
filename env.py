# env.py
import os

from dotenv import load_dotenv

load_dotenv()

APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")
STORAGE_SECRET = os.getenv("STORAGE_SECRET")

if not APP_USERNAME:
    raise ValueError("APP_USERNAME is required in .env")
if not APP_PASSWORD:
    raise ValueError("APP_PASSWORD is required in .env")
if not STORAGE_SECRET:
    raise ValueError("STORAGE_SECRET is required in .env")
