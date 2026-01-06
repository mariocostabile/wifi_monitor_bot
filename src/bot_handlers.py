# src/bot_handlers.py
import os
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from config.settings import ADMIN_ID
from src.database import get_dataframe
from src.graphics import create_chart


# --- SICUREZZA ---
def restricted(func):
    """Decoratore: blocca chi non è Admin"""

    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return  # Silenzio totale per gli intrusi
        return await func(update, context, *args, **kwargs)

    return wrapped


# --- COMANDI ---
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot Wi-Fi Monitor Attivo e Protetto.")


async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, days=1):
    """Logica condivisa per inviare report"""
    msg = await update.message.reply_text("⏳ Analisi dati in corso...")

    df = get_dataframe()
    img_path = create_chart(df, days)

    if img_path:
        await update.message.reply_photo(photo=InputFile(img_path), caption=f"📊 Report ultimi {days} giorni")
        os.remove(img_path)
        await msg.delete()  # Rimuove il messaggio di attesa
    else:
        await msg.edit_text("❌ Dati insufficienti per generare il grafico.")


@restricted
async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, days=1)


@restricted
async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, days=7)