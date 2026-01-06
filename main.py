import logging
import threading
import time
import schedule
import datetime
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config.settings import BOT_TOKEN
from src.database import init_db, save_record
# AGGIUNTO get_jitter AGLI IMPORT
from src.network import check_ping, run_speedtest, get_jitter
from src.bot_handlers import start, daily_report, weekly_report, handle_buttons

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


# --- JOB SCHEDULATI (Background) ---

def job_ping_routine():
    ms = check_ping()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Se ms è 0, significa packet loss. Passiamo 0 agli altri campi.
    # Struttura: Data, Tipo, Ping, Jitter, Down, Up
    save_record(now, 'ping', ms, 0, 0, 0)


def job_speedtest_routine():
    # 1. Calcoliamo il Jitter (usando la tua funzione in network.py)
    jitter_val = get_jitter()

    # 2. Eseguiamo lo Speedtest
    # network.py restituisce 5 valori: (ping, down, up, client, server)
    # Usiamo _ per ignorare client e server che non salviamo nel CSV
    ping_val, down, up, _, _ = run_speedtest()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Salviamo tutto nel database
    # Struttura: Data, Tipo, Ping, Jitter, Down, Up
    save_record(now, 'speedtest', ping_val, jitter_val, down, up)

    print(f"✅ Speedtest salvato: Down:{down} Up:{up} Ping:{ping_val} Jitter:{jitter_val}")


def run_scheduler():
    """Ciclo infinito per gestire gli orari"""

    # Ping ogni 5 min
    schedule.every(5).minutes.do(job_ping_routine)

    # Speedtest ogni ora precisa (es. 14:00, 15:00)
    schedule.every().minutes.at(":00").do(job_speedtest_routine)

    # --- SE VUOI FARE TEST RAPIDI (Scommenta questa riga e commenta quella sopra) ---
    # schedule.every(1).minutes.do(job_speedtest_routine)

    while True:
        schedule.run_pending()
        time.sleep(1)


# --- AVVIO ---
if __name__ == '__main__':
    # 1. Inizializza DB
    init_db()

    # 2. Avvia Scheduler in thread separato
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()

    # 3. Avvia Bot Telegram
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Comandi
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('report', daily_report))
    app.add_handler(CommandHandler('week', weekly_report))

    # Gestione Bottoni
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("🚀 Bot Wi-Fi Monitor COMPLETO avviato...")
    app.run_polling()