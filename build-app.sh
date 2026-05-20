#!/bin/bash

##############################################
# TECLA Blocks - Build macOS App
# Crea una aplicació .app empaquetat
##############################################

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     📦  BUILD TECLA BLOCKS  📦        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Directori del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Comprovar electron-packager
echo -e "${YELLOW}🔍 Comprovant electron-packager...${NC}"
if ! npm list electron-packager &> /dev/null; then
    echo -e "${YELLOW}📦 Instal·lant electron-packager...${NC}"
    npm install --save-dev electron-packager
fi

echo -e "${GREEN}✅ electron-packager disponible${NC}"
echo ""

# Build
echo -e "${YELLOW}🔨 Construint aplicació...${NC}"
echo "Això pot trigar uns minuts..."
echo ""

npx electron-packager . "TECLA Blocks" \
    --platform=darwin \
    --arch=x64 \
    --icon=assets/icon.icns \
    --out=build \
    --overwrite \
    --app-bundle-id=com.tecla.blocks \
    --app-version=2.0.0

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Build completat!${NC}"
    echo ""
    echo -e "${BLUE}Ubicació:${NC} $SCRIPT_DIR/build/TECLA Blocks-darwin-x64/"
    echo ""
    echo "Pots copiar l'aplicació a /Applications"
    
    # Preguntar si vol obrir la carpeta
    read -p "Vols obrir la carpeta build? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        open build
    fi
else
    echo ""
    echo -e "${RED}❌ Error durant el build${NC}"
    exit 1
fi

echo ""
