# main.py
import logging
import threading
import time
import schedule
import datetime
from telegram.ext import ApplicationBuilder, CommandHandler
from config.settings import BOT_TOKEN
from src.database import init_db, save_record
from src.network import check_ping, run_speedtest
from src.bot_handlers import start, daily_report, weekly_report

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# --- JOB SCHEDULATI (Background) ---
def job_ping_routine():
    ms = check_ping()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Se ms è 0, significa packet loss
    save_record(now, 'ping', ms, 0, 0)


def job_speedtest_routine():
    ping_val, down, up = run_speedtest()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_record(now, 'speedtest', ping_val, down, up)


def run_scheduler():
    """Ciclo infinito per gestire gli orari"""
    # Ping ogni 5 min
    schedule.every(5).minutes.do(job_ping_routine)
    # Speedtest ogni ora precisa
    schedule.every().hour.at(":00").do(job_speedtest_routine)

    while True:
        schedule.run_pending()
        time.sleep(10)


# --- AVVIO ---
if __name__ == '__main__':
    # 1. Inizializza DB
    init_db()

    # 2. Avvia Scheduler in thread separato
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()

    # 3. Avvia Bot Telegram
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('report', daily_report))
    app.add_handler(CommandHandler('week', weekly_report))

    print("🚀 Bot Wi-Fi Monitor avviato in modalità Modulare...")
    app.run_polling()