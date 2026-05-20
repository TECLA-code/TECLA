# ✅ Scripts d'Execució Creats

## 📦 6 Scripts Disponibles

He creat **6 scripts diferents** per executar TECLA Blocks segons les teves necessitats:

---

## 1. 🎹 **start.sh** - Launcher Complet
**El més recomanat per ús general**

### Característiques
- ✅ Comprova Node.js i npm
- ✅ Instal·la dependències automàticament si cal
- ✅ Banner amb colors
- ✅ Missatges clars i informatius
- ✅ Gestió d'errors

### Com executar
```bash
./start.sh
```

### Sortida
```
╔═══════════════════════════════════════╗
║         🎹  TECLA BLOCKS  🎹          ║
║   Programació Visual per TECLA        ║
╚═══════════════════════════════════════╝

📂 Directori: /Users/zen/Desktop/TECLA-Blocks
🔍 Comprovant Node.js...
✅ Node.js trobat: v20.x.x
✅ npm trobat: v10.x.x

🚀 Iniciant TECLA Blocks...
```

---

## 2. 🛠️ **start-dev.sh** - Mode Desenvolupament
**Per desenvolupadors i debugging**

### Característiques
- ✅ Obre DevTools automàticament
- ✅ Variable NODE_ENV=development
- ✅ Ideal per veure consola JavaScript
- ✅ Debugging de blocs

### Com executar
```bash
./start-dev.sh
```

### Quan usar-lo
- Desenvolupar noves funcionalitats
- Debugar problemes
- Veure errors de JavaScript
- Inspeccionar DOM

---

## 3. ⚡ **start-simple.sh** - Launcher Mínim
**Ultra-ràpid, només 1 línia**

### Característiques
- ✅ Execució instantània
- ❌ Sense comprovacions
- ❌ Sense missatges
- ✅ Perfecte per scripts automatitzats

### Com executar
```bash
./start-simple.sh
```

### Codi
```bash
#!/bin/bash
cd "$(dirname "$0")" && npm start
```

---

## 4. 🖱️ **TECLA Blocks.command** - Doble-Click
**El més fàcil per usuaris no tècnics**

### Característiques
- ✅ Doble-click des del Finder
- ✅ Obre Terminal automàticament
- ✅ Comprova Node.js
- ✅ Instal·la dependències si cal
- ✅ Espera abans de tancar

### Com executar
```
Doble-click al fitxer "TECLA Blocks.command"
```

### Primera vegada
1. Doble-click
2. Si diu "cannot be opened": Click dret → Obrir → Confirmar
3. A partir d'ara funciona amb doble-click normal

### Ideal per
- Alumnes de primària
- Professors a classe
- Usuaris finals
- Accés ràpid sense Terminal

---

## 5. 📦 **build-app.sh** - Crear Aplicació
**Genera .app distribuïble**

### Característiques
- ✅ Crea aplicació .app completa
- ✅ Llesta per distribuir
- ✅ Instal·la electron-packager si cal
- ✅ Output a carpeta `build/`

### Com executar
```bash
./build-app.sh
```

### Resultat
```
build/
└── TECLA Blocks-darwin-x64/
    └── TECLA Blocks.app  ← Aplicació completa
```

### Distribució
1. Executa `./build-app.sh`
2. Espera ~5 minuts
3. Copia "TECLA Blocks.app" a /Applications
4. Ja pots executar des de Launchpad
5. No cal Terminal mai més

---

## 6. 🎮 **menu.sh** - Menú Interactiu
**Interfície visual amb opcions**

### Característiques
- ✅ Menú amb colors
- ✅ 6 opcions:
  1. Executar TECLA Blocks
  2. Mode Desenvolupament
  3. Build aplicació
  4. Instal·lar dependències
  5. Comprovar sistema
  6. Obrir documentació
  0. Sortir

### Com executar
```bash
./menu.sh
```

### Sortida
```
╔════════════════════════════════════════════════════════════╗
║                   🎹  TECLA BLOCKS  🎹                    ║
║            Programació Visual per TECLA                ║
╚════════════════════════════════════════════════════════════╝

══════════════════════ MENÚ PRINCIPAL ══════════════════════

  1) 🚀 Executar TECLA Blocks
  2) 🛠️  Executar en mode Desenvolupament (DevTools)
  3) 📦 Build aplicació .app
  4) 🔧 Instal·lar/Actualitzar dependències
  5) 📊 Comprovar estat del sistema
  6) 📚 Obrir documentació
  0) ❌ Sortir

════════════════════════════════════════════════════════════

Escull una opció (0-6):
```

---

## 📊 Taula Comparativa

| Script | Facilitat | Complet | DevTools | Build | Menú |
|--------|-----------|---------|----------|-------|------|
| **start.sh** | ⭐⭐⭐ | ✅ | ❌ | ❌ | ❌ |
| **start-dev.sh** | ⭐⭐⭐ | ✅ | ✅ | ❌ | ❌ |
| **start-simple.sh** | ⭐⭐⭐⭐⭐ | ❌ | ❌ | ❌ | ❌ |
| **TECLA Blocks.command** | ⭐⭐⭐⭐⭐ | ✅ | ❌ | ❌ | ❌ |
| **build-app.sh** | ⭐⭐ | ✅ | ❌ | ✅ | ❌ |
| **menu.sh** | ⭐⭐⭐⭐ | ✅ | ✅ | ✅ | ✅ |

---

## 🎯 Quin Script Usar?

### Per Alumnes / Usuaris Finals
→ **TECLA Blocks.command** (doble-click)
```
El més fàcil: Doble-click i llest
```

### Per Ús Diari (Terminal)
→ **start.sh**
```bash
./start.sh
```

### Per Desenvolupament
→ **start-dev.sh**
```bash
./start-dev.sh
```

### Per Experimentar Opcions
→ **menu.sh**
```bash
./menu.sh
```

### Per Distribuir
→ **build-app.sh**
```bash
./build-app.sh
```

---

## ⚙️ Configuració Inicial

### Fer Executables (UNA VEGADA)
```bash
cd ~/Desktop/TECLA-Blocks
chmod +x *.sh
chmod +x "TECLA Blocks.command"
```

### Verificar Node.js
```bash
node --version
npm --version
```

### Instal·lar Dependències
```bash
npm install
```

---

## 🚀 Exemples d'Ús

### Exemple 1: Professor Preparant Classe
```bash
# Preparació (una vegada)
cd ~/Desktop/TECLA-Blocks
./build-app.sh

# Distribuir als ordinadors
cp -R "build/TECLA Blocks.app" /Applications

# Als alumnes: Doble-click des de Launchpad
```

### Exemple 2: Alumne a Casa
```bash
# Doble-click "TECLA Blocks.command"
# Primera vegada: Esperar instal·lació
# Següents vegades: Execució immediata
```

### Exemple 3: Desenvolupador
```bash
# Desenvolupament diari
./start-dev.sh

# Provar build abans de distribuir
./build-app.sh

# Usar menú per gestionar tot
./menu.sh
```

---

## 📂 Estructura de Fitxers

```
TECLA-Blocks/
├── start.sh                    ← Launcher complet ⭐
├── start-dev.sh                ← Mode dev ⭐
├── start-simple.sh             ← Mínim ⭐
├── TECLA Blocks.command        ← Doble-click ⭐
├── build-app.sh                ← Build .app ⭐
├── menu.sh                     ← Menú interactiu ⭐
├── SCRIPTS.md                  ← Documentació completa
├── INICI_RAPID.md              ← Guia ràpida
├── package.json
├── main.js
├── index.html
└── ...
```

---

## 🔧 Personalització

### Modificar Banner (start.sh)
Edita les línies del banner per canviar colors o text:
```bash
echo -e "${BLUE}║         🎹  TECLA BLOCKS  🎹          ║${NC}"
```

### Afegir Funcions (menu.sh)
Afegeix opcions al menú editant la funció `show_menu()`:
```bash
echo -e "  ${GREEN}7${NC}) 🆕 Nova funció"
```

### Canviar Port (si cal)
Edita `package.json` si necessites canviar el port d'Electron.

---

## 🐛 Troubleshooting

### "Permission denied"
```bash
chmod +x start.sh
chmod +x start-dev.sh
chmod +x start-simple.sh
chmod +x "TECLA Blocks.command"
chmod +x build-app.sh
chmod +x menu.sh
```

### Scripts no apareixen executables al Finder
```bash
# Fer-los executables
chmod +x *.sh *.command
```

### "command not found: node"
```bash
# Instal·lar Node.js
brew install node

# O descarregar de https://nodejs.org/
```

### Build falla
```bash
# Instal·lar electron-packager
npm install --save-dev electron-packager

# Tornar a intentar
./build-app.sh
```

---

## 📚 Documentació Relacionada

- **[SCRIPTS.md](SCRIPTS.md)** - Guia completa de scripts
- **[INICI_RAPID.md](INICI_RAPID.md)** - Guia ràpida
- **[README.md](README.md)** - Documentació principal

---

## ✅ Checklist de Configuració

- [ ] Node.js instal·lat
- [ ] Dependències instal·lades (`npm install`)
- [ ] Scripts fets executables (`chmod +x`)
- [ ] Provat `./start.sh`
- [ ] Provat "TECLA Blocks.command" (doble-click)
- [ ] (Opcional) Build creat amb `./build-app.sh`

---

## 🎉 Resum

**6 scripts creats i llests per usar:**
1. ✅ **start.sh** - Complet amb comprovacions
2. ✅ **start-dev.sh** - Mode desenvolupament
3. ✅ **start-simple.sh** - Ultra-ràpid
4. ✅ **TECLA Blocks.command** - Doble-click
5. ✅ **build-app.sh** - Crear .app
6. ✅ **menu.sh** - Menú interactiu

**Tots els scripts són executables i estan documentats!**

---

**Data:** 17 Novembre 2025  
**Versió:** 2.1  
**Plataforma:** macOS (adaptable a Linux/Windows)
