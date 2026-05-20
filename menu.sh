#!/bin/bash

##############################################
# TECLA Blocks - Menú Interactiu
# Launcher amb opcions visuals
##############################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Directori
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Funció per mostrar el banner
show_banner() {
    clear
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}║                   ${WHITE}🎹  TECLA BLOCKS  🎹${BLUE}                    ║${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}║            ${CYAN}Programació Visual per TECLA${BLUE}                ║${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Funció per mostrar el menú
show_menu() {
    echo -e "${YELLOW}══════════════════════ MENÚ PRINCIPAL ══════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}1${NC}) 🚀 Executar TECLA Blocks"
    echo -e "  ${CYAN}2${NC}) 🛠️  Executar en mode Desenvolupament (DevTools)"
    echo -e "  ${PURPLE}3${NC}) 📦 Build aplicació .app"
    echo -e "  ${BLUE}4${NC}) 🔧 Instal·lar/Actualitzar dependències"
    echo -e "  ${YELLOW}5${NC}) 📊 Comprovar estat del sistema"
    echo -e "  ${WHITE}6${NC}) 📚 Obrir documentació"
    echo -e "  ${RED}0${NC}) ❌ Sortir"
    echo ""
    echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Funció per comprovar sistema
check_system() {
    echo ""
    echo -e "${YELLOW}🔍 Comprovant sistema...${NC}"
    echo ""
    
    # Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✅ Node.js:${NC} $NODE_VERSION"
    else
        echo -e "${RED}❌ Node.js no instal·lat${NC}"
    fi
    
    # npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}✅ npm:${NC} v$NPM_VERSION"
    else
        echo -e "${RED}❌ npm no disponible${NC}"
    fi
    
    # node_modules
    if [ -d "node_modules" ]; then
        MODULE_COUNT=$(ls -1 node_modules | wc -l | tr -d ' ')
        echo -e "${GREEN}✅ Dependències:${NC} $MODULE_COUNT mòduls instal·lats"
    else
        echo -e "${YELLOW}⚠️  Dependències no instal·lades${NC}"
    fi
    
    # Dispositiu CIRCUITPY
    if [ -d "/Volumes/CIRCUITPY" ]; then
        echo -e "${GREEN}✅ TECLA connectat:${NC} /Volumes/CIRCUITPY"
    else
        echo -e "${CYAN}ℹ️  TECLA no connectat${NC}"
    fi
    
    echo ""
    read -p "Prem Enter per continuar..."
}

# Funció per instal·lar dependències
install_deps() {
    echo ""
    echo -e "${YELLOW}📦 Instal·lant dependències...${NC}"
    echo ""
    npm install
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Dependències instal·lades correctament${NC}"
    else
        echo ""
        echo -e "${RED}❌ Error instal·lant dependències${NC}"
    fi
    
    echo ""
    read -p "Prem Enter per continuar..."
}

# Funció per obrir documentació
open_docs() {
    echo ""
    echo -e "${YELLOW}📚 Documentació disponible:${NC}"
    echo ""
    echo "  1) README.md (Guia principal)"
    echo "  2) SCRIPTS.md (Scripts d'execució)"
    echo "  3) MULTI_SLOT.md (Múltiples projectes)"
    echo "  4) EXEMPLE_SINTETITZADOR.md (Exemple avançat)"
    echo "  5) INICI_RAPID.md (Guia ràpida)"
    echo "  0) Tornar"
    echo ""
    read -p "Escull una opció (0-5): " doc_choice
    
    case $doc_choice in
        1) open README.md 2>/dev/null || cat README.md | less ;;
        2) open SCRIPTS.md 2>/dev/null || cat SCRIPTS.md | less ;;
        3) open MULTI_SLOT.md 2>/dev/null || cat MULTI_SLOT.md | less ;;
        4) open EXEMPLE_SINTETITZADOR.md 2>/dev/null || cat EXEMPLE_SINTETITZADOR.md | less ;;
        5) open INICI_RAPID.md 2>/dev/null || cat INICI_RAPID.md | less ;;
        0) return ;;
        *) echo -e "${RED}Opció no vàlida${NC}" ;;
    esac
}

# Bucle principal
while true; do
    show_banner
    show_menu
    
    read -p "Escull una opció (0-6): " choice
    
    case $choice in
        1)
            echo ""
            echo -e "${GREEN}🚀 Iniciant TECLA Blocks...${NC}"
            echo ""
            npm start
            echo ""
            read -p "Prem Enter per continuar..."
            ;;
        2)
            echo ""
            echo -e "${CYAN}🛠️  Iniciant en mode Desenvolupament...${NC}"
            echo ""
            NODE_ENV=development npm start
            echo ""
            read -p "Prem Enter per continuar..."
            ;;
        3)
            echo ""
            echo -e "${PURPLE}📦 Iniciant build...${NC}"
            echo ""
            ./build-app.sh
            read -p "Prem Enter per continuar..."
            ;;
        4)
            install_deps
            ;;
        5)
            check_system
            ;;
        6)
            open_docs
            ;;
        0)
            echo ""
            echo -e "${BLUE}👋 Fins aviat!${NC}"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo -e "${RED}❌ Opció no vàlida${NC}"
            echo ""
            sleep 1
            ;;
    esac
done
