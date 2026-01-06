# config/settings.example.py
# Rinomina questo file in 'settings.py' e inserisci i tuoi dati

import os

BOT_TOKEN = "INSERISCI_QUI_IL_TUO_TOKEN"
ADMIN_ID = 00000000

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_FILE = os.path.join(DATA_DIR, 'wifi_stats.csv')
LOG_FILE = os.path.join(DATA_DIR, 'bot.log')

os.makedirs(DATA_DIR, exist_ok=True)