# src/graphics.py
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import io  # <--- NUOVO IMPORT FONDAMENTALE


def create_chart(df, days):
    """Crea il grafico e lo ritorna come oggetto in memoria (Buffer)"""
    if df.empty:
        return None

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Filtro ultimi N giorni
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    df = df[df['timestamp'] > cutoff]

    df_speed = df[df['type'] == 'speedtest']

    if df_speed.empty:
        return None

    plt.figure(figsize=(10, 6))

    # Disegno grafico
    plt.plot(df_speed['timestamp'], df_speed['download'], label='Download', color='green', marker='o')
    plt.plot(df_speed['timestamp'], df_speed['upload'], label='Upload', color='blue', marker='x')

    plt.title(f'Network Performance (Ultimi {days} giorni)')
    plt.ylabel('Mbps')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.gcf().autofmt_xdate()

    # --- MODIFICA CHIAVE: SALVATAGGIO IN RAM ---
    buf = io.BytesIO()  # Crea un file "virtuale" in memoria
    plt.savefig(buf, format='png')
    plt.close()  # Chiude il grafico di matplotlib
    buf.seek(0)  # Riavvolge il nastro all'inizio del file

    return buf  # Ritorna l'oggetto, non il percorso