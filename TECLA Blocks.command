#!/bin/bash

##############################################
# TECLA Blocks - Launcher macOS
# Doble-click per executar
##############################################

# Canviar al directori del script
cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Banner compacte
echo ""
echo -e "${BLUE}🎹  TECLA BLOCKS  🎹${NC}"
echo ""

# Comprovar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no instal·lat"
    echo ""
    echo "Descarrega'l de: https://nodejs.org/"
    echo ""
    read -p "Prem Enter per tancar..."
    exit 1
fi

# Instal·lar dependències si cal
if [ ! -d "node_modules" ]; then
    echo "📦 Instal·lant dependències..."
    npm install
    echo ""
fi

# Executar
echo -e "${GREEN}🚀 Iniciant...${NC}"
echo ""
npm start

# Esperar abans de tancar
echo ""
echo "TECLA Blocks s'ha tancat"
echo ""
read -p "Prem Enter per tancar aquesta finestra..."
