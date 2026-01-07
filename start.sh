#!/bin/bash

# Loop infinito per il riavvio automatico
while true
do
    echo "🚀 Avvio WiFi Bot..."

    # Avvia lo script python.
    # Nota: 'sudo' è solitamente richiesto per gestire le interfacce di rete su Linux.
    # Se sei su Termux (root), potresti dover usare 'tsu' o rimuovere sudo se sei già root.
    sudo python3 main.py

    echo "⚠️ Il bot si è chiuso o è crashato!"
    echo "🔄 Riavvio automatico tra 5 secondi..."
    echo "Premi CTRL+C rapidamente per interrompere il loop."

    sleep 5
done