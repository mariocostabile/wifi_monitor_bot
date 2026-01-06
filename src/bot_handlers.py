# src/bot_handlers.py
import os
import datetime
import asyncio
from telegram import Update, InputFile, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_ID
from src.database import get_dataframe, save_record
from src.graphics import create_chart
from src.network import run_speedtest, get_jitter


# --- UTILITY GRAFICA ---
def draw_bar(value, max_value=100, length=10):
    normalized = min(value, max_value)
    filled = int((normalized / max_value) * length)
    empty = length - filled
    return "▓" * filled + "░" * empty


# --- SICUREZZA ---
def restricted(func):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != ADMIN_ID:
            return
        return await func(update, context, *args, **kwargs)

    return wrapped


# --- LOGICA REPORT ---
async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, days=1):
    msg = await update.message.reply_text("⏳ *Analisi dati in corso...*", parse_mode='Markdown')
    df = await asyncio.to_thread(get_dataframe)
    img_path = await asyncio.to_thread(create_chart, df, days)

    if img_path:
        await update.message.reply_photo(photo=InputFile(img_path), caption=f"📊 Report ultimi {days} giorni")
        os.remove(img_path)
        await msg.delete()
    else:
        await msg.edit_text("❌ Dati insufficienti per generare il grafico.")


# --- COMANDI ---
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📊 Report 24h", "📅 Report 7 Giorni"], ["🔄 Test Immediato"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 **Wi-Fi Monitor Pro**\nPronto a monitorare la rete.", reply_markup=reply_markup,
                                    parse_mode='Markdown')


@restricted
async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, days=1)


@restricted
async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, days=7)


# --- LOGICA TEST IMMEDIATO ---
@restricted
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 Report 24h":
        await daily_report(update, context)
    elif text == "📅 Report 7 Giorni":
        await weekly_report(update, context)
    elif text == "🔄 Test Immediato":
        status_msg = await update.message.reply_text("🔄 Esecuzione del test in corso...", parse_mode='Markdown')

        # Eseguiamo i test
        jitter_val = await asyncio.to_thread(get_jitter)
        ping, down, up, client, server = await asyncio.to_thread(run_speedtest)

        # SALVIAMO NEL DB (Ora passiamo anche jitter_val)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_record(now, 'manual_speedtest', ping, jitter_val, down, up)

        # Report Grafico
        isp = client.get('isp', 'Sconosciuto')
        server_name = server.get('name', 'Auto')

        result_msg = (
            f"🌐 **REPORT CONNESSIONE**\n"
            f"👤 **ISP:** {isp}\n"
            f"🖥 **Server:** {server_name}\n\n"
            f"⬇️ **Down:** `{draw_bar(down, 100)}` {down} Mbps\n"
            f"⬆️ **Up:** `{draw_bar(up, 30)}` {up} Mbps\n"
            f"📶 **Ping:** {ping} ms | **Jitter:** {jitter_val} ms"
        )
        await status_msg.edit_text(result_msg, parse_mode='Markdown')