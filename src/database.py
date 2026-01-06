# src/database.py
import csv
import os
import pandas as pd
from config.settings import DB_FILE

def init_db():
    """Crea il file CSV con gli header se non esiste"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "type", "ping", "download", "upload"])

def save_record(timestamp, test_type, ping_ms, down_mbps, up_mbps):
    """Salva una riga nel database"""
    with open(DB_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, test_type, ping_ms, down_mbps, up_mbps])

def get_dataframe():
    """Restituisce i dati come Pandas DataFrame"""
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    return pd.read_csv(DB_FILE)
