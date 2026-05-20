#!/bin/bash

##############################################
# TECLA Blocks - Script d'Inici
# Comprova dependències i executa l'aplicació
##############################################

# Colors per terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                       ║${NC}"
echo -e "${BLUE}║         🎹  TECLA BLOCKS  🎹          ║${NC}"
echo -e "${BLUE}║                                       ║${NC}"
echo -e "${BLUE}║   Programació Visual per TECLA        ║${NC}"
echo -e "${BLUE}║                                       ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Directori del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}📂 Directori:${NC} $SCRIPT_DIR"
echo ""

# Comprovar si Node.js està instal·lat
echo -e "${YELLOW}🔍 Comprovant Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js no està instal·lat${NC}"
    echo ""
    echo "Instal·la Node.js des de: https://nodejs.org/"
    echo "O amb Homebrew: brew install node"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js trobat:${NC} $NODE_VERSION"

# Comprovar si npm està disponible
echo -e "${YELLOW}🔍 Comprovant npm...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm no està disponible${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✅ npm trobat:${NC} v$NPM_VERSION"
echo ""

# Comprovar si node_modules existeix
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Instal·lant dependències...${NC}"
    echo "Això pot trigar uns minuts la primera vegada..."
    echo ""
    npm install
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error instal·lant dependències${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}✅ Dependències instal·lades correctament${NC}"
    echo ""
fi

# Executar l'aplicació
echo -e "${GREEN}🚀 Iniciant TECLA Blocks...${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

npm start

# Si l'aplicació es tanca
echo ""
echo -e "${BLUE}👋 TECLA Blocks s'ha tancat${NC}"
echo ""
