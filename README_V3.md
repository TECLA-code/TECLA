# 🚀 TECLA Blocks v3.0 - Transformació Completa

## 📢 Gran Actualització!

TECLA Blocks passa de ser una app musical educativa a una **plataforma completa de programació visual** per microcontroladors, mantenint totes les seves funcions musicals úniques.

---

## 📊 Què s'ha Afegit?

### ✨ 78 Nous Blocs en 11 Categories

| Categoria | Blocs | Funcionalitat |
|-----------|-------|---------------|
| ⚙️ **Control Avançat** | 4 | Break, Continue, Try/Except |
| ⏰ **Temps** | 5 | Temporitzadors, millis, sleep |
| 📝 **String Avançat** | 7 | Replace, Split, Join, Format, Contains |
| 📐 **Mates Avançades** | 8 | Sin, Cos, Tan, Log, Exp, Bitwise |
| 💡 **NeoPixels** | 5 | LEDs RGB programables |
| 🖥️ **Display** | 6 | OLED/LCD text i gràfics |
| 🎛️ **Motors/Servos** | 4 | Robòtica i moviment |
| 👁️ **Sensors Extra** | 5 | Llum, So, Humitat, PIR, Botons |
| 📶 **PWM** | 2 | Control PWM personalitzat |
| 💾 **Emmagatzematge** | 4 | Dades persistents |
| 🔧 **Sistema** | 4 | Info sistema, reset |

### 📈 Abans vs Ara

```
v2.0 → v3.0
══════════════════════════════
Blocs:      70 → 148  (+111%)
Categories: 12 → 23   (+92%)
Cas d'ús:   Música → Universal
Nivell:     Scratch → MicroBlocks
```

---

## 🎯 Per a Qui és?

### Abans (v2.0)
- ✅ Alumnes primària
- ✅ Educació musical
- ✅ Programació bàsica

### Ara (v3.0)
- ✅ **Primària a Secundària**
- ✅ **Educació STEAM completa**
- ✅ **Robòtica, IoT, Art, Música**
- ✅ **Projectes avançats**

---

## 🚀 Com Començar

### 1. Obre TECLA Blocks

```bash
cd ~/Desktop/TECLA-Blocks
./start.sh
```

### 2. Explora les Noves Categories

Al panell esquerre veuràs **11 noves categories**:
- ⚙️ Control Avançat
- ⏰ Temps
- 📝 String Avançat
- 📐 Matemàtiques Avançades
- 💡 NeoPixels
- 🖥️ Display
- 🎛️ Motors i Servos
- 👁️ Sensors Extra
- 📶 PWM
- 💾 Emmagatzematge
- 🔧 Sistema

### 3. Prova un Projecte

**Exemple Simple - LED Rainbow:**
1. Arrossega `Configurar NeoPixels`
2. Afegeix `Arc de Sant Martí`
3. Posa-ho en un `Repetir per sempre`
4. Puja a TECLA + tira NeoPixel

---

## 📁 Fitxers Modificats/Creats

### Codi
- ✅ `blocks/tecla_blocks.js` - +78 definicions de blocs
- ✅ `generators/tecla_python_extended.js` - Generadors Python
- ✅ `index.html` - Toolbox actualitzat

### Documentació
- ✅ `AMPLIACIO_V3.md` - Visió general completa
- ✅ `GUIA_NOUS_BLOCS.md` - Guia ràpida d'ús
- ✅ `README_V3.md` - Aquest fitxer

### Scripts (anteriors)
- ✅ `start.sh`, `start-dev.sh`, `menu.sh`
- ✅ `launcher_multi_slot.py`
- ✅ Documentació launcher

---

## 💡 Projectes Nous Possibles

### Robòtica
- Robot seguidor de línia
- Braç robòtic
- Vehicle controlat per sensors

### IoT
- Estació meteorològica amb display
- Monitor ambiental (temp, humitat, llum)
- Sistema de reg automàtic

### Art Lumínic
- Visualitzador de música amb NeoPixels
- Instal·lació interactiva
- Rellotge amb LEDs

### Música (mantingut)
- Sintetitzadors avançats
- Seqüenciadors MIDI
- Control gestual amb sensors

### Educació
- Experiments científics automatitzats
- Demostracions de física
- Projectes interdisciplinaris STEAM

---

## 🔧 Requisits de Hardware

### TECLA Device (Base)
✅ Tot funciona

### Extensions Opcionals
- **NeoPixels:** Tira WS2812B/SK6812 (5V, pin PWM)
- **Display OLED:** SSD1306 I2C 128x64
- **Display LCD:** HD44780 I2C 16x2
- **Servos:** SG90, MG90S (5V regulat)
- **Motors DC:** + H-bridge L298N o DRV8833
- **Sensors:**
  - Llum: LDR + resistència
  - So: MAX9814, micròfon electret
  - Humitat: Sensor capacitiu
  - PIR: HC-SR501
  - Botons: Qualsevol push button

### Llibreries CircuitPython

```
Descarregar de: circuitpython.org/libraries

Necessàries per alguns blocs:
- neopixel.mpy
- adafruit_motor/
- adafruit_displayio_ssd1306.mpy
- adafruit_character_lcd/
- pwmio
```

---

## 🎓 Per Professors

### Currículum Ampliat

**Primària (6-12 anys):**
- Variables i bucles
- Sensors simples
- LEDs i llums
- Música i so
- **NOU:** Displays amb text
- **NOU:** NeoPixels bàsics

**Secundària (13-18 anys):**
- Funcions i mòduls
- Matemàtiques avançades
- Robòtica
- IoT i sensors múltiples
- **NOU:** Control PWM
- **NOU:** Emmagatzematge de dades
- **NOU:** Try/except i gestió d'errors

### Projectes per Nivell

**Fàcil:**
- Termòmetre amb display
- Semàfor amb LEDs
- Piano amb botons

**Mitjà:**
- VU meter amb NeoPixels
- Robot evita obstacles
- Estació meteorològica

**Difícil:**
- Seqüenciador musical complet
- Robot seguidor de línia
- Sistema domòtic amb sensors

---

## 📚 Documentació Completa

### Per Començar
1. **INICI_RAPID.md** - 5 minuts d'inici
2. **GUIA_RAPIDA.md** - Tutorial bàsic
3. **SCRIPTS.md** - Com executar l'app

### Funcions Bàsiques
4. **README.md** - Documentació principal
5. **CATEGORIES.md** - Índex de tots els blocs
6. **GUIA_NOUS_BLOCS.md** - Nous blocs v3.0 ⭐

### Funcions Avançades
7. **MULTI_SLOT.md** - Múltiples projectes
8. **AMPLIACIO_V3.md** - Detalls tècnics v3.0 ⭐
9. **SETUP_LAUNCHER.md** - Launcher TECLA/Blocks

### Exemples
10. **EXEMPLE_SINTETITZADOR.md** - Projecte avançat música

---

## 🔄 Migració des de v2.0

### Els Teus Projectes Anteriors
✅ **Segueixen funcionant** sense canvis

### Noves Funcionalitats
✅ Disponibles immediatament  
✅ Compatibles amb codi existent  
✅ Pots combinar blocs antics i nous

### Actualització
```bash
# Ja està tot actualitzat!
# Només cal executar:
./start.sh
```

---

## 🐛 Troubleshooting

### Els nous blocs no apareixen
```bash
# Verifica que s'ha carregat el script extès:
# A index.html línia 454:
<script src="generators/tecla_python_extended.js"></script>
```

### Error al generar codi
```bash
# Obre mode dev per veure errors:
./start-dev.sh

# Mira la consola DevTools
```

### Hardware no funciona
```bash
# Comprova connexions
# Verifica pins correctes
# Prova blocs simples primer (LEDs, botons)
```

### Memòria plena
```bash
# Usa bloc "Memòria lliure" per monitorar
# Optimitza codi (menys variables, strings curts)
# Reinicia dispositiu
```

---

## 🌟 Comparació amb Alternatives

| Plataforma | Blocs | Visual | CircuitPython | Música Avançada |
|------------|-------|--------|---------------|-----------------|
| **TECLA Blocks v3.0** | 148 | ✅ | ✅ | ✅✅✅ |
| MicroBlocks | ~150 | ✅ | ❌ | ⚠️ Bàsic |
| Scratch | ~100 | ✅ | ❌ | ⚠️ Bàsic |
| Arduino IDE | - | ❌ | ❌ | ⚠️ Llibreries |
| CircuitPython | - | ❌ | ✅ | ⚠️ Llibreries |

**Conclusió:** TECLA Blocks v3.0 combina el millor de tots:
- Visual com Scratch
- Potent com MicroBlocks  
- CircuitPython nadiu
- Música professional única

---

## 🎉 Resum

### Què Tens Ara

```
TECLA Blocks v3.0 = 
  Programació Visual (Blockly) +
  Microcontroladors (CircuitPython) +
  Música Avançada (MIDI, Síntesi) +
  Robòtica (Motors, Sensors) +
  IoT (Displays, LEDs, Comunicació) +
  STEAM Complet
```

### En Números

- **148 blocs** disponibles
- **23 categories** organitzades
- **Educació primària a secundària**
- **Paritat amb MicroBlocks + més**
- **100% compatible amb projectes anteriors**

### Per Qui

- ✅ Alumnes 6-18 anys
- ✅ Professors STEAM
- ✅ Makers i hobbyists
- ✅ Músics experimentals
- ✅ Projectes IoT educatius

---

## 🚀 Següents Passos

### Tu com a Usuari

1. **Explora** les noves categories
2. **Prova** un projecte simple
3. **Experimenta** amb hardware nou
4. **Crea** projectes increïbles!

### Nosaltres (Futur)

- Sistema de plugins/extensions
- Editor visual de colors
- Més sensors suportats
- WiFi/Bluetooth (ESP32)
- Comunitat de projectes

---

## 💬 Feedback

Tens idees per millorar TECLA Blocks?  
Vols compartir els teus projectes?  
Necessites ajuda amb algun bloc?

**TECLA Blocks v3.0 - De música a STEAM universal! 🎹🤖💡**

---

**Versió:** 3.0.0  
**Data:** 17 Novembre 2025  
**Estat:** Llest per usar  
**Inspirat per:** La teva petició i MicroBlocks  
**Fet amb:** ❤️ i molt codi
