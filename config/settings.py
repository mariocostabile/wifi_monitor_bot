# config/settings.py
import os

# --- CREDENZIALI ---
BOT_TOKEN = "IL_TUO_TOKEN_QUI"
ADMIN_ID = 123456789  # Il tuo ID numerico

# --- PERCORSI ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_FILE = os.path.join(DATA_DIR, 'wifi_stats.csv')
LOG_FILE = os.path.join(DATA_DIR, 'bot.log')

# Assicuriamoci che la cartella data esista
os.makedirs(DATA_DIR, exist_ok=True)