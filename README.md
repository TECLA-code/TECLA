# 🎹 TECLA Blocks

**Aplicació educativa per aprendre programació amb blocs visuals**

TECLA Blocks és una eina educativa dissenyada per ensenyar els fonaments de la programació a alumnes de primària mitjançant una interfície visual estil Scratch/Blockly, específicament adaptada per programar el dispositiu TECLA.

## ✨ Característiques

- 🧩 **Programació visual amb blocs** - Interfície intuïtiva estil Scratch
- 🎵 **Blocs musicals específics** - Notes, acords, escales
- 🎮 **Control interactiu** - Botons i potenciòmetres
- ✨ **Efectes d'àudio** - Delay, reverb, filtres
- 🔄 **Generació de codi Python** - Converteix blocs a CircuitPython
- 📱 **Simulador integrat** - Prova el teu programa sense hardware
- ⬆️ **Upload directe** - Puja el codi al dispositiu TECLA via USB
- 💾 **Guardar i obrir projectes** - Format .tblocks

## 🚀 Instal·lació

### Prerequisits

- Node.js 18+ i npm
- macOS 10.13+, Windows 10+, o Linux

### Passos

1. **Clonar o descarregar** aquest repositori
2. **Instal·lar dependències:**

```bash
cd TECLA-Blocks
npm install
```

3. **Executar l'aplicació:**

#### Opció A: Scripts d'execució (Recomanat)
```bash
# Launcher complet amb comprovacions
./start.sh

# Mode desenvolupament (amb DevTools)
./start-dev.sh

# Doble-click macOS
Doble-click "TECLA Blocks.command"
```

#### Opció B: npm directament
```bash
npm start
```

**📖 Més informació:** Consulta [SCRIPTS.md](SCRIPTS.md) per tots els scripts disponibles

### Crear executables

Per generar aplicacions natives per diferents plataformes:

```bash
# macOS
npm run build-mac

# Windows
npm run build-win

# Linux
npm run build-linux
```

Els executables es generaran a la carpeta `dist/`.

## 📚 Com utilitzar TECLA Blocks

### 1. Crear un programa

1. Arrossega blocs de la **caixa d'eines** a l'esquerra
2. Connecta'ls per crear el teu programa
3. Veure el **codi Python generat** al panell lateral

### 2. Provar el programa

- **Simulador**: Prova el programa virtualment
- **Exportar**: Guarda el codi Python generat

### 3. Pujar al dispositiu TECLA

1. Connecta el teu dispositiu TECLA via USB
2. Espera que es munti com a drive **CIRCUITPY**
3. Prem el botó **"⬆️ Pujar a TECLA"**
4. El programa s'executarà automàticament!

## 🎨 Tipus de blocs disponibles

### 🎵 Música
- **Tocar nota** - Toca una nota musical individual
- **Tocar acord** - Toca múltiples notes simultàniament
- **Tocar escala** - Executa una escala completa
- **Canviar octava** - Modifica l'octava actual

### 🎛️ Control
- **Llegir botó** - Detecta si un botó està premut
- **Llegir potenciòmetre** - Obté el valor d'un pot (0-127)
- **Quan es prem botó** - Executa accions en prémer un botó

### ✨ Efectes
- **Delay** - Efecte d'eco amb temps i feedback ajustables
- **Reverb** - Reverberació amb intensitat variable
- **Filtre** - Filtres passa-baix, passa-alt i passa-banda

### ⏱️ Temps
- **Esperar** - Pausa l'execució durant X segons
- **Repetir per sempre** - Bucle infinit
- **Repetir N vegades** - Bucle amb comptador

### 🔧 Lògica
- Condicionals (si/aleshores)
- Operadors lògics (i, o, no)
- Comparacions (=, <, >)
- Variables i operacions matemàtiques

## 🎓 Exemples pedagògics

### Exemple 1: Primera melodia

```
[Bloc: Tocar nota Do, velocitat 100, durada 0.5]
[Bloc: Tocar nota Re, velocitat 100, durada 0.5]
[Bloc: Tocar nota Mi, velocitat 100, durada 0.5]
```

### Exemple 2: Botó interactiu

```
[Bloc: Repetir per sempre]
  └─ [Bloc: Quan es prem botó 1]
       └─ [Bloc: Tocar acord Do Major, durada 1.0]
```

### Exemple 3: Potenciòmetre controlant velocitat

```
[Bloc: Variables - definir velocitat = Llegir pot X]
[Bloc: Tocar nota Do, velocitat=velocitat, durada 1.0]
```

## 🛠️ Desenvolupament

### Estructura del projecte

```
TECLA-Blocks/
├── main.js              # Main process d'Electron
├── preload.js           # Bridge segur entre processos
├── index.html           # Interfície principal
├── styles.css           # Estils de l'aplicació
├── app.js               # Lògica del renderer process
├── blocks/
│   └── tecla_blocks.js  # Definició dels blocs Blockly
├── generators/
│   └── tecla_python.js  # Generador de codi Python
└── assets/              # Icones i recursos
```

### Tecnologies utilitzades

- **Electron** - Framework per aplicacions d'escriptori
- **Blockly** - Llibreria de programació visual de Google
- **Node.js** - Runtime JavaScript
- **SerialPort** - Comunicació amb dispositius USB

## 🔌 Compatibilitat amb TECLA

TECLA Blocks genera codi **CircuitPython** compatible amb:

- Raspberry Pi Pico executant CircuitPython 8.0+
- Dispositiu TECLA v1.0 i posteriors
- Qualsevol microcontrolador amb CircuitPython i MIDI

### Format del codi generat

El codi generat inclou:
- Imports necessaris (time, board, usb_midi, adafruit_midi)
- Inicialització del hardware
- Funció main() amb el programa de l'usuari
- Gestió d'errors i neteja de recursos

## 📖 Recursos educatius

### Per a professors

- Guies didàctiques per nivells
- Activitats per al currículum de primària
- Rúbriques d'avaluació
- Projectes d'exemple progressius

### Per a alumnes

- Tutorials interactius
- Reptes de programació
- Galeria de projectes inspiradors
- Fòrum de comunitat

## 🤝 Contribuir

Les contribucions són benvingudes! Si vols afegir:

- Nous blocs musicals
- Millores a la interfície
- Exemples educatius
- Traduccions

Si us plau, obre un issue o pull request al repositori.

## 📄 Llicència

MIT License - Veure fitxer LICENSE per detalls

## 👥 Autors

**Projecte TECLA** - Sintetitzador MIDI educatiu

## 🙏 Agraïments

- Google Blockly per la llibreria de programació visual
- Electron per facilitar aplicacions multiplataforma
- Comunitat CircuitPython per l'ecosistema de hardware educatiu
- Tots els educadors que utilitzen TECLA a les seves aules

---

**Fet amb ❤️ per l'educació musical i la programació**
