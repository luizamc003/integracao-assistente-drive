import os

from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "./credentials.json")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
TOP_K = int(os.getenv("TOP_K", "4"))
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "22"))
N8N_SYNC_WEBHOOK_URL = os.getenv("N8N_SYNC_WEBHOOK_URL", "http://localhost:5678/webhook/sync")
