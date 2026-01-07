import os
import asyncio
import logging
import datetime
import pandas as pd
from telegram import Update, InputFile, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_ID
from src.database import get_dataframe, save_record
from src.graphics import create_chart
from src.network import run_speedtest, get_jitter, check_ping


# --- SICUREZZA ---
def restricted(func):
    """Decoratore: blocca chi non è Admin CON LOG VISIBILI"""

    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id

        # LOG DI CONTROLLO ID (Uso logging direttamente qui per sicurezza)
        # logging.getLogger(__name__).info(f"🔍 Controllo Accesso: User {user_id} vs Admin {ADMIN_ID}")

        try:
            admin_id_int = int(ADMIN_ID)
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ ERRORE SETTINGS: L'ADMIN_ID '{ADMIN_ID}' non è un numero! {e}")
            return

        if user_id != admin_id_int:
            logging.getLogger(__name__).warning(f"⛔ ACCESSO NEGATO: User {user_id} non corrisponde a {admin_id_int}")
            return

        return await func(update, context, *args, **kwargs)

    return wrapped


# --- CALCOLO STATISTICHE ---
def get_stats_message(df, days):
    """Calcola le medie e prepara il testo del messaggio"""
    if df.empty:
        return None

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    df_filtered = df[df['timestamp'] > cutoff]

    df_speed = df_filtered[df_filtered['type'] == 'speedtest']

    if df_speed.empty:
        return None

    avg_down = df_speed['download'].mean()
    avg_up = df_speed['upload'].mean()
    avg_ping = df_speed['ping'].mean()
    avg_jitter = df_speed['jitter'].mean() if 'jitter' in df_speed.columns else 0
    count = len(df_speed)

    if days == 7:
        titolo = "📅 Report Ultima Settimana"
    elif days == 1:
        titolo = "📊 Report Ultime 24 Ore"
    else:
        titolo = f"Report Ultimi {days} Giorni"

    msg = (
        f"**{titolo}**\n"
        f"_(Analizzati {count} test)_\n\n"
        f"📉 **Download Medio:** {avg_down:.2f} Mbps\n"
        f"📈 **Upload Medio:** {avg_up:.2f} Mbps\n"
        f"📶 **Ping Medio:** {avg_ping:.2f} ms\n"
        f"⚡ **Jitter Medio:** {avg_jitter:.2f} ms"
    )
    return msg


async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, days=1):
    """Invia PRIMA il testo e POI il grafico (RAM)"""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    df = get_dataframe()

    if df.empty:
        await update.message.reply_text("⚠️ Il database è vuoto. Attendi il primo test.")
        return

    text_msg = get_stats_message(df, days)

    if text_msg:
        await update.message.reply_text(text_msg, parse_mode='Markdown')
    else:
        periodo = "settimana" if days == 7 else "24 ore"
        await update.message.reply_text(f"⚠️ Nessun dato 'speedtest' trovato nell'ultima {periodo}.")
        return

    wait_msg = await update.message.reply_text("🎨 Generazione grafico...")
    img_buffer = await asyncio.to_thread(create_chart, df, days)

    if img_buffer:
        try:
            await update.message.reply_photo(photo=img_buffer)
        except Exception as e:
            logging.getLogger(__name__).error(f"Errore invio foto: {e}")
            await update.message.reply_text(f"❌ Errore invio foto: {e}")
        finally:
            await wait_msg.delete()
    else:
        await wait_msg.edit_text("❌ Impossibile creare il grafico (dati insufficienti).")


async def manual_speedtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Esegue un test manuale su richiesta"""
    # Usiamo il logger locale per evitare errori di scope
    log = logging.getLogger(__name__)

    status_msg = await update.message.reply_text("🚀 **Avvio test in corso...**\n_(Attendere...)_",
                                                 parse_mode='Markdown')
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        jitter_val = await asyncio.to_thread(get_jitter)


        results = await asyncio.to_thread(run_speedtest)
        ping_val, down, up, *_ = results

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_record(now, 'speedtest', ping_val, jitter_val, down, up)

        msg = (
            f"✅ **TEST COMPLETATO**\n\n"
            f"📉 **Download:** {down} Mbps\n"
            f"📈 **Upload:** {up} Mbps\n"
            f"📶 **Ping:** {ping_val} ms\n"
            f"⚡ **Jitter:** {jitter_val} ms"
        )

        await status_msg.delete()
        await update.message.reply_text(msg, parse_mode='Markdown')
        log.info("✅ Speedtest completato e inviato.")

    except Exception as e:
        log.error(f"❌ CRASH TEST MANUALE: {e}")
        await status_msg.edit_text(f"❌ Errore: {e}")


# --- GESTIONE BOTTONI E COMANDI ---

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🚀 Test Immediato", "📊 Report 24h"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "✅ **Bot Wi-Fi Monitor Attivo**\nUsa i pulsanti in basso.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


@restricted
async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, days=1)


@restricted
async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, days=7)


@restricted
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    log = logging.getLogger(__name__)

    log.info(f"🔘 RICEVUTO TESTO: '{text}'")

    if "Report" in text and "24h" in text:
        log.info("➡️ Riconosciuto comando: Report 24h")
        await daily_report(update, context)

    elif "Test" in text and "Immediato" in text:
        log.info("➡️ Riconosciuto comando: Test Immediato -> Chiamo manual_speedtest")
        await manual_speedtest(update, context)

    else:
        log.warning(f"❓ Testo NON riconosciuto: '{text}'")
        await update.message.reply_text(f"❓ Comando non capito: {text}")