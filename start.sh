#!/bin/bash

# Loop infinito per il riavvio automatico
while true
do
    echo "🚀 Avvio WiFi Bot..."

    # Esegue lo script python.
    # Su Termux 'python' è solitamente Python 3.
    python main.py

    echo "⚠️ Il bot si è chiuso o è crashato!"
    echo "🔄 Riavvio automatico tra 5 secondi..."
    echo "Premi CTRL+C per interrompere."

    sleep 5
done