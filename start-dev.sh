#!/bin/bash

##############################################
# TECLA Blocks - Mode Desenvolupament
# Executa amb DevTools obertes
##############################################

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     TECLA BLOCKS - DEV MODE 🛠️        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Directori del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Comprovar dependències
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Instal·lant dependències...${NC}"
    npm install
fi

# Executar amb variable d'entorn de desenvolupament
echo -e "${GREEN}🚀 Iniciant en mode desenvolupament...${NC}"
echo -e "${YELLOW}💡 DevTools s'obriran automàticament${NC}"
echo ""

NODE_ENV=development npm start
