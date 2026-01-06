# src/database.py
import csv
import os
import pandas as pd
from config.settings import DB_FILE


def init_db():
    """Crea il file CSV con gli header corretti se non esiste"""
    # Se il file esiste ma è vuoto o corrotto, lo sovrascriviamo
    should_create = False
    if not os.path.exists(DB_FILE):
        should_create = True
    elif os.stat(DB_FILE).st_size == 0:
        should_create = True

    if should_create:
        with open(DB_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            # ECCO LA NUOVA COLONNA 'jitter'
            writer.writerow(["timestamp", "type", "ping", "jitter", "download", "upload"])


def save_record(timestamp, test_type, ping_ms, jitter_ms, down_mbps, up_mbps):
    """Salva una riga nel database incluso il Jitter"""
    init_db()  # Controllo sicurezza

    with open(DB_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, test_type, ping_ms, jitter_ms, down_mbps, up_mbps])


def get_dataframe():
    """Restituisce i dati come Pandas DataFrame"""
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()

    try:
        return pd.read_csv(DB_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()