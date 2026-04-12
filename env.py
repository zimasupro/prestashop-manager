from dotenv import load_dotenv
import os

load_dotenv()

APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")
STORAGE_SECRET = os.getenv("STORAGE_SECRET")
