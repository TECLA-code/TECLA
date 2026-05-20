# 🚀 Scripts d'Execució - TECLA Blocks

## 📋 Scripts Disponibles

### 1. 🎹 **start.sh** (Recomanat)
Script complet amb comprovacions i missatges clars.

**Què fa:**
- ✅ Comprova Node.js i npm
- ✅ Instal·la dependències si cal
- ✅ Mostra banner i informació
- ✅ Gestiona errors
- ✅ Missatges amb colors

**Com executar:**
```bash
cd ~/Desktop/TECLA-Blocks
./start.sh
```

O des de qualsevol lloc:
```bash
~/Desktop/TECLA-Blocks/start.sh
```

---

### 2. 🛠️ **start-dev.sh**
Mode desenvolupament amb DevTools.

**Què fa:**
- ✅ Obre DevTools automàticament
- ✅ Mode desenvolupament activat
- ✅ Ideal per debugging

**Com executar:**
```bash
cd ~/Desktop/TECLA-Blocks
./start-dev.sh
```

**Útil per:**
- Veure consola JavaScript
- Debugar blocs
- Desenvolupar noves funcionalitats

---

### 3. ⚡ **start-simple.sh**
Script mínim (1 línia).

**Què fa:**
- ✅ Executa directament npm start
- ❌ Sense comprovacions
- ❌ Sense missatges

**Com executar:**
```bash
./start-simple.sh
```

**Útil per:**
- Execució ràpida
- Scripts automàtics
- Usuaris avançats

---

### 4. 🖱️ **TECLA Blocks.command**
Launcher macOS amb doble-click.

**Què fa:**
- ✅ Doble-click des del Finder
- ✅ Obre Terminal automàticament
- ✅ Comprovacions bàsiques
- ✅ Missatge abans de tancar

**Com executar:**
```
Doble-click al fitxer "TECLA Blocks.command"
```

**Primera vegada:**
1. Doble-click al fitxer
2. Si diu "cannot be opened":
   - Click dret → Obrir
   - Confirma "Obrir"
3. A partir d'ara funciona amb doble-click

**Útil per:**
- Usuaris no tècnics
- Lliçons a classe
- Accés ràpid

---

### 5. 📦 **build-app.sh**
Crea aplicació .app empaquetat.

**Què fa:**
- ✅ Instal·la electron-packager si cal
- ✅ Crea .app complet
- ✅ Llest per distribuir
- ✅ Ubicat a carpeta `build/`

**Com executar:**
```bash
./build-app.sh
```

**Resultat:**
```
build/
└── TECLA Blocks-darwin-x64/
    └── TECLA Blocks.app  ← Aplicació completa
```

**Distribució:**
1. Executa build-app.sh
2. Copia "TECLA Blocks.app" a /Applications
3. Ja pots executar-la des de Launchpad
4. No cal Terminal

**Útil per:**
- Distribució a altres ordinadors
- Instal·lació permanent
- Usuaris finals

---

## 🔧 Gestió de Dependències

### Instal·lar Dependències
```bash
npm install
```

### Actualitzar Dependències
```bash
npm update
```

### Net Install (neteja completa)
```bash
rm -rf node_modules package-lock.json
npm install
```

---

## 🎯 Ús Recomanat per Perfil

### Alumnes / Usuaris Finals
→ **TECLA Blocks.command** (doble-click)
```
Més fàcil: Doble-click i llest
```

### Professors / Tècnics
→ **start.sh** (terminal amb comprovacions)
```bash
./start.sh
```

### Desenvolupadors
→ **start-dev.sh** (amb DevTools)
```bash
./start-dev.sh
```

### Distribució
→ **build-app.sh** (crear .app)
```bash
./build-app.sh
# Després: Distribuir build/TECLA Blocks.app
```

---

## 🐛 Troubleshooting

### "Permission denied"
```bash
# Fer executables els scripts
chmod +x *.sh
chmod +x "TECLA Blocks.command"
```

### "command not found: node"
```bash
# Instal·lar Node.js
brew install node

# O descarregar de:
# https://nodejs.org/
```

### "Cannot find module"
```bash
# Reinstal·lar dependències
rm -rf node_modules
npm install
```

### L'app no s'obre (macOS)
```bash
# Primera vegada amb .command:
# Click dret → Obrir → Confirmar
```

### Build falla
```bash
# Instal·lar electron-packager
npm install --save-dev electron-packager

# Tornar a intentar
./build-app.sh
```

---

## 📊 Comparació Scripts

| Script | Facilitat | Comprovacions | DevTools | Distribució |
|--------|-----------|---------------|----------|-------------|
| **start.sh** | ⭐⭐⭐ | ✅ Completes | ❌ | ❌ |
| **start-dev.sh** | ⭐⭐⭐ | ✅ Bàsiques | ✅ | ❌ |
| **start-simple.sh** | ⭐⭐⭐⭐⭐ | ❌ Cap | ❌ | ❌ |
| **TECLA Blocks.command** | ⭐⭐⭐⭐⭐ | ✅ Bàsiques | ❌ | ❌ |
| **build-app.sh** | ⭐⭐ | ✅ Completes | ❌ | ✅ |

---

## 💡 Consells

### Per Classes
1. **Primera vegada:** Executa `build-app.sh`
2. **Distribueix:** Copia .app als ordinadors
3. **Alumnes:** Doble-click a l'app

### Per Desenvolupament
1. **Editar codi:** Usa el teu editor (VS Code, etc.)
2. **Provar:** `./start-dev.sh`
3. **Veure errors:** DevTools obertes automàticament

### Per Producció
1. **Build final:** `./build-app.sh`
2. **Test:** Prova la .app generada
3. **Distribueix:** Comprimeix i comparteix

---

## 🔄 Actualitzacions

### Actualitzar TECLA Blocks
```bash
# Si tens el codi font amb git:
git pull
npm install

# Si és descàrrega manual:
# 1. Descarrega nova versió
# 2. npm install
# 3. Llest
```

### Rebuild després d'actualitzar
```bash
./build-app.sh
```

---

## 📂 Estructura de Fitxers

```
TECLA-Blocks/
├── start.sh                    ← Launcher complet
├── start-dev.sh                ← Mode desenvolupament
├── start-simple.sh             ← Launcher mínim
├── TECLA Blocks.command        ← Doble-click macOS
├── build-app.sh                ← Build .app
├── package.json                ← Dependències
├── main.js                     ← Electron main
├── index.html                  ← UI
├── app.js                      ← Lògica UI
├── blocks/                     ← Definicions blocs
├── generators/                 ← Generadors Python
└── build/                      ← Output builds
    └── TECLA Blocks.app        ← App distribuïble
```

---

## 🎓 Exemples d'Ús

### Exemple 1: Alumne a Casa
```bash
# Primera vegada
1. Doble-click "TECLA Blocks.command"
2. Esperar que s'instal·lin dependències
3. Usar l'app

# Següents vegades
1. Doble-click "TECLA Blocks.command"
2. Usar l'app
```

### Exemple 2: Professor a Classe
```bash
# Preparació (una vegada)
./build-app.sh
cp -R "build/TECLA Blocks-darwin-x64/TECLA Blocks.app" /Applications

# A cada ordinador
# Copiar /Applications/TECLA Blocks.app
# Alumnes fan doble-click des de Launchpad
```

### Exemple 3: Desenvolupador
```bash
# Desenvolupament
./start-dev.sh

# Editar codi...

# Provar canvis (recarrega automàtica amb Electron)

# Build final
./build-app.sh

# Distribuir
cp -R "build/TECLA Blocks.app" ~/Desktop/
```

---

## 🚀 Shortcuts

### Crear alias (opcional)
```bash
# Afegir al ~/.zshrc o ~/.bashrc
alias tecla="~/Desktop/TECLA-Blocks/start.sh"
alias tecla-dev="~/Desktop/TECLA-Blocks/start-dev.sh"

# Després:
tecla        # Executa TECLA Blocks
tecla-dev    # Executa en mode dev
```

### Crear AppleScript (avançat)
```applescript
-- Guardar com "TECLA Blocks.app" amb Script Editor
do shell script "cd ~/Desktop/TECLA-Blocks && npm start"
```

---

## 📞 Suport

### Si res funciona
1. Comprova Node.js: `node --version`
2. Reinstal·la dependències: `rm -rf node_modules && npm install`
3. Prova script simple: `./start-simple.sh`
4. Consulta errors al terminal

### Errors comuns
- **ENOENT**: Fitxer no trobat → Comprova ruta
- **EACCES**: Permisos → `chmod +x`
- **Module not found**: Dependències → `npm install`
- **Port in use**: Tanca altres instàncies

---

**Versió:** 2.1  
**Data:** 17 Novembre 2025  
**Plataforma:** macOS (adaptable a Linux/Windows)
