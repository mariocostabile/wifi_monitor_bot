import logging
import threading
import time
import schedule
import datetime
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import NetworkError
from config.settings import BOT_TOKEN, ADMIN_ID
from src.database import init_db, save_record, get_dataframe
from src.network import check_ping, run_speedtest, get_jitter
# --- MODIFICA QUI: Aggiunto manual_speedtest agli import ---
from src.bot_handlers import start, daily_report, weekly_report, get_stats_message, handle_buttons, manual_speedtest
from src.graphics import create_chart
import os

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# --- VARIABILI GLOBALI PER LO STATO CONNESSIONE ---
IS_ONLINE = True
DOWN_START_TIME = None


# --- GESTORE ERRORI TELEGRAM (Così non crasha se manca internet) ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce gli errori di connessione silenziosamente"""
    if isinstance(context.error, NetworkError):
        # Se è un errore di rete, lo scriviamo nel log in modo pulito senza traceback
        logging.warning(f"⚠️ Telegram Network Error: Connessione persa. Riprovo a connettermi... ({context.error})")
    else:
        # Per altri errori imprevisti, stampiamo tutto per fare debug
        logging.error("Eccezione non gestita:", exc_info=context.error)


# --- JOB MONITORAGGIO ---
def job_ping_routine(app_instance):
    global IS_ONLINE, DOWN_START_TIME

    # 1. Esegui Ping
    ms = check_ping()
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 2. Salva sempre nel DB (così hai lo storico dei buchi)
    # 6 argomenti: timestamp, type, ping, jitter(0), down(0), up(0)
    save_record(now_str, 'ping', ms, 0, 0, 0)

    # 3. Logica Rilevamento Caduta Connessione
    if ms == 0:
        # Se il ping è 0, la connessione è CADUTA
        if IS_ONLINE:
            # Era online fino a un attimo fa, segniamo l'inizio del disservizio
            IS_ONLINE = False
            DOWN_START_TIME = now_dt
            print(f"⚠️ [{now_str}] Connessione PERSA! Inizio conteggio downtime...")

    else:
        # Se il ping è > 0, la connessione è ATTIVA
        if not IS_ONLINE:
            # Era offline, ora è tornata! Calcoliamo quanto è durata.
            if DOWN_START_TIME:
                duration = now_dt - DOWN_START_TIME
                minutes = int(duration.total_seconds() / 60)
                seconds = int(duration.total_seconds() % 60)

                msg = (
                    f"✅ **Connessione RIPRISTINATA**\n\n"
                    f"🚫 La linea è caduta per: **{minutes} min e {seconds} sec**\n"
                    f"🕒 Dalle: {DOWN_START_TIME.strftime('%H:%M:%S')} alle {now_dt.strftime('%H:%M:%S')}"
                )

                print(f"✅ [{now_str}] Connessione TORNATA! Invio notifica...")

                # Inviamo il messaggio Telegram (creando un loop temporaneo)
                async def send_alert():
                    try:
                        await app_instance.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')
                    except Exception as e:
                        print(f"❌ Errore invio alert ripristino: {e}")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_alert())
                loop.close()

            # Resettiamo lo stato
            IS_ONLINE = True
            DOWN_START_TIME = None


def job_speedtest_routine():
    # 1. Calcoliamo il Jitter
    jitter_val = get_jitter()

    # 2. Eseguiamo lo speedtest
    # Usiamo *_ per prendere ping, down, up e ignorare client/server info
    ping_val, down, up, *_ = run_speedtest()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Salviamo con tutti i dati corretti
    # Ordine: Data, Tipo, Ping, JITTER, Down, Up
    save_record(now, 'speedtest', ping_val, jitter_val, down, up)

    print(f"✅ Test Completo: D:{down} U:{up} P:{ping_val} J:{jitter_val}")


# --- JOB REPORT AUTOMATICO ---
def job_weekly_automated(app_instance):
    """Invia il report settimanale automaticamente"""
    print("📅 Esecuzione Report Domenicale Automatico...")

    async def send_routine():
        try:
            df = get_dataframe()

            # 1. Testo
            msg = get_stats_message(df, days=7)
            if msg:
                await app_instance.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')

            # 2. Grafico (RAM)
            img_buffer = create_chart(df, days=7)
            if img_buffer:
                # Passiamo direttamente il buffer
                await app_instance.bot.send_photo(chat_id=ADMIN_ID, photo=img_buffer)

            print("✅ Report settimanale inviato.")
        except Exception as e:
            print(f"❌ Errore report automatico: {e}")

    # Eseguiamo la funzione asincrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_routine())
    loop.close()


# --- SCHEDULER ---
def run_scheduler(app_instance):
    """Ciclo infinito per gestire gli orari"""

    # MODIFICA: Ping ogni 1 minuto per rilevare cadute rapidamente
    # Passiamo 'app_instance' per poter inviare messaggi di allarme
    schedule.every(1).minutes.do(lambda: job_ping_routine(app_instance))

    # --- MODIFICA: Speedtest ogni 30 minuti (precisi) ---
    schedule.every().hour.at(":00").do(job_speedtest_routine)
    schedule.every().hour.at(":30").do(job_speedtest_routine)

    # REPORT AUTOMATICO: Ogni Domenica alle 09:00
    schedule.every().sunday.at("09:00").do(lambda: job_weekly_automated(app_instance))

    while True:
        schedule.run_pending()
        time.sleep(1)


# --- AVVIO ---
if __name__ == '__main__':
    # 1. Inizializza DB
    init_db()

    # Costruiamo l'app PRIMA del thread
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # AGGIUNTO: Error Handler per evitare crash visivi quando cade la rete
    app.add_error_handler(error_handler)

    # 2. Avvia Scheduler in thread separato (passando l'app)
    t = threading.Thread(target=run_scheduler, args=(app,), daemon=True)
    t.start()

    # 3. Setup Comandi
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('report', daily_report))
    app.add_handler(CommandHandler('week', weekly_report))

    # Gestione Bottoni: ATTIVATA
    # L'handler gestisce TUTTO il testo che non è un comando.
    # La logica "if testo == 'Test Immediato' -> manual_speedtest" è dentro handle_buttons in bot_handlers.py
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("🚀 Bot Wi-Fi Monitor COMPLETO avviato...")
    app.run_polling()