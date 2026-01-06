# src/graphics.py
import matplotlib

matplotlib.use('Agg')  # Fondamentale per server/termux
import matplotlib.pyplot as plt
import pandas as pd
import os


def create_chart(df, days, filename="chart.png"):
    """Crea il grafico e ritorna il percorso del file"""
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

    # Linee
    plt.plot(df_speed['timestamp'], df_speed['download'], label='Download', color='green', marker='o')
    plt.plot(df_speed['timestamp'], df_speed['upload'], label='Upload', color='blue', marker='x')

    plt.title(f'Network Performance (Ultimi {days} giorni)')
    plt.ylabel('Mbps')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.gcf().autofmt_xdate()  # Ruota le date per leggerle meglio

    path = os.path.abspath(filename)
    plt.savefig(path)
    plt.close()
    return path