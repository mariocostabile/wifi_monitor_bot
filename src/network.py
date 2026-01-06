# src/network.py
import speedtest
from ping3 import ping
import logging

# Configurazione Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ping(host='8.8.8.8'):
    """Esegue un ping rapido. Ritorna ms o 0 se fallito."""
    try:
        latency = ping(host, unit='ms', timeout=2)
        if latency is None:
            return 0
        return round(latency, 2)
    except Exception as e:
        logger.error(f"Errore Ping: {e}")
        return 0

def run_speedtest():
    """Esegue speedtest completo. Ritorna (ping, down, up)"""
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        down = st.download() / 1_000_000
        up = st.upload() / 1_000_000
        ping_val = st.results.ping
        return round(ping_val, 2), round(down, 2), round(up, 2)
    except Exception as e:
        logger.error(f"Errore Speedtest: {e}")
        return 0, 0, 0