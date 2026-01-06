import logging
import threading
import time
import schedule
import datetime
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config.settings import BOT_TOKEN
from src.database import init_db, save_record
from src.network import check_ping, run_speedtest
from src.bot_handlers import start, daily_report, weekly_report, handle_buttons

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# --- JOB SCHEDULATI (Background) ---
# Queste sono le funzioni che erano andate perse!

def job_ping_routine():
    ms = check_ping()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Se ms è 0, significa packet loss
    save_record(now, 'ping', ms, 0, 0, 0)


def job_speedtest_routine():
    ping_val, down, up = run_speedtest()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_record(now, 'speedtest', ping_val, 0, down, up)


def run_scheduler():
    """Ciclo infinito per gestire gli orari"""
    # Ping ogni 5 min
    schedule.every(5).minutes.do(job_ping_routine)
    # Speedtest ogni ora precisa
    schedule.every().minutes.at(":00").do(job_speedtest_routine)

    while True:
        schedule.run_pending()
        time.sleep(10)


# --- AVVIO ---
if __name__ == '__main__':
    # 1. Inizializza DB
    init_db()

    # 2. Avvia Scheduler in thread separato
    # Ora la funzione run_scheduler esiste (linea 29), quindi non darà errore
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()

    # 3. Avvia Bot Telegram
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Comandi
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('report', daily_report))
    app.add_handler(CommandHandler('week', weekly_report))

    # Gestione Bottoni (Tutto il testo che NON è un comando inizia qui)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("🚀 Bot Wi-Fi Monitor COMPLETO avviato...")
    app.run_polling()