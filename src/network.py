# src/network.py
import speedtest
from ping3 import ping
import logging
import time

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


def get_jitter(host='8.8.8.8', count=10):
    """Calcola il Jitter facendo 10 ping rapidi"""
    latencies = []
    try:
        for _ in range(count):
            lat = ping(host, unit='ms', timeout=1)
            if lat is not None:
                latencies.append(lat)
            time.sleep(0.1)  # Piccola pausa tra i ping

        if len(latencies) < 2:
            return 0  # Dati insufficienti

        # Il jitter è la media delle differenze assolute tra ping consecutivi
        diffs = [abs(latencies[i] - latencies[i + 1]) for i in range(len(latencies) - 1)]
        jitter = sum(diffs) / len(diffs)
        return round(jitter, 2)
    except Exception as e:
        logger.error(f"Errore Jitter: {e}")
        return 0


def run_speedtest():
    """Esegue speedtest completo. Ritorna (ping, down, up, client, server)"""
    try:
        st = speedtest.Speedtest()
        logger.info("Cercando il server migliore...")
        st.get_best_server()

        down = st.download() / 1_000_000
        up = st.upload() / 1_000_000
        ping_val = st.results.ping

        # Info extra per il report
        client_info = st.results.client
        server_info = st.results.server

        return round(ping_val, 2), round(down, 2), round(up, 2), client_info, server_info
    except Exception as e:
        logger.error(f"Errore Speedtest: {e}")
        return 0, 0, 0, {}, {}