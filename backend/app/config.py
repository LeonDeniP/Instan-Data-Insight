# app/config.py
import os
import warnings
from dotenv import load_dotenv

# Sembunyikan warning dari google core api
warnings.simplefilter(action='ignore', category=FutureWarning)

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PROJECT_NAME: str = "Instant Data Insight Suite"
    VERSION: str = "3.0"

settings = Settings()