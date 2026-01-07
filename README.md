# Wi-Fi Monitor Bot

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Bot Status](https://img.shields.io/badge/status-online-green)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)

Un bot Telegram modulare e robusto per il monitoraggio continuo della connessione Internet. Esegue test di velocità periodici, monitora la stabilità della connessione (Ping) e invia report dettagliati e grafici direttamente su Telegram.

Ideale per l'esecuzione su server dedicati o Raspberry Pi.

## Funzionalità

* **Monitoraggio Continuo (Ping):** Controlla la connessione ogni minuto per rilevare cadute di linea e notificarti la durata del disservizio al ripristino.
* **Speedtest Periodici:** Esegue test di velocità (Download, Upload, Ping, Jitter) ogni 30 minuti (intervallo personalizzabile).
* **Report Grafici:** Genera grafici dell'andamento della connessione (ultime 24h o 7 giorni).
* **Comandi Manuali:** Possibilità di richiedere un test immediato o un report aggiornato tramite pulsanti.
* **Archiviazione Dati:** Tutti i test vengono salvati in un file CSV locale per analisi future.
* **Sicurezza:** Accesso limitato tramite ADMIN_ID per impedire l'uso non autorizzato.
* **Gestione Errori:** Sistema resiliente che gestisce le cadute di connessione senza interrompere il processo.

## Installazione

### Prerequisiti

* Python 3.10 o superiore.
* Un bot Telegram creato tramite @BotFather.
* Il tuo ID numerico Telegram (ottenibile da bot come @userinfobot).

### 1. Clona il Repository

```bash
git clone [https://github.com/TUO_USERNAME/wifi_monitor_bot.git](https://github.com/TUO_USERNAME/wifi_monitor_bot.git)
cd wifi_monitor_bot

```

### 2. Configura l'Ambiente Virtuale (Consigliato)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

```

### 3. Installa le Dipendenze

```bash
pip install -r requirements.txt

```

### 4. Configurazione

Crea un file `settings.py` nella cartella `config/`.

1. Spostati nella cartella config: `cd config`
2. Crea il file (o rinomina `settings.example.py` se presente) con il seguente contenuto:

```python
# config/settings.py
import os

BOT_TOKEN = "IL_TUO_TOKEN_TELEGRAM_QUI"
ADMIN_ID = 123456789  # Il tuo ID numerico

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_FILE = os.path.join(DATA_DIR, 'wifi_stats.csv')

os.makedirs(DATA_DIR, exist_ok=True)

```

## Struttura del Progetto

```text
wifi_monitor_bot/
├── config/
│   └── settings.py       # Token e configurazioni
├── data/
│   └── wifi_stats.csv    # Database dei test (generato automaticamente)
├── src/
│   ├── bot_handlers.py   # Logica dei comandi Telegram
│   ├── database.py       # Gestione CSV
│   ├── graphics.py       # Generazione grafici con Matplotlib
│   └── network.py        # Funzioni Speedtest e Ping
├── main.py               # Punto di ingresso e Scheduler
└── requirements.txt      # Dipendenze Python

```

## Licenza

Questo progetto è distribuito sotto licenza Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International.