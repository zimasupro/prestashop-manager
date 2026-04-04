from dotenv import load_dotenv
import os

load_dotenv()

PRESTA_URL = os.getenv("PRESTA_URL")
PRESTA_API_KEY = os.getenv("PRESTA_API_KEY")
APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")
STORAGE_SECRET = os.getenv("STORAGE_SECRET")
