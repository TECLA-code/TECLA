#!/bin/bash

# Obtenir el directori on es troba aquest script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Canviar al directori del script
cd "$DIR"

# Missatge inicial
echo "🎹 Iniciant servidor TECLA..."
echo ""

# Llançar el servidor Python
python3 server.py

# Quan s'aturi el servidor (Ctrl+C), mantenir la finestra oberta
echo ""
echo "Prem qualsevol tecla per tancar aquesta finestra..."
read -n 1
