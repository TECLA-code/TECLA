# ✅ Com Provar TECLA Blocks v3.0

## 🚀 Pas 1: Executar l'Aplicació

```bash
cd ~/Desktop/TECLA-Blocks
./start.sh
```

O doble-click a `TECLA Blocks.command`

---

## 👀 Pas 2: Verificar les Noves Categories

Al panell esquerre hauries de veure:

### Categories Originals (v2.0)
- 🎵 Música
- 🎮 Control
- 🌊 Síntesi Avançada
- 📊 GPIO
- 📡 Sensors
- 🔢 Matemàtiques
- 📝 Text
- 📋 Llistes
- 🔧 Funcions
- 💬 Comunicació

### Noves Categories (v3.0) ⭐
- ⚙️ **Control Avançat** ← NOU
- ⏰ **Temps** ← NOU
- 📝 **String Avançat** ← NOU
- 📐 **Matemàtiques Avançades** ← NOU
- 💡 **NeoPixels** ← NOU
- 🖥️ **Display** ← NOU
- 🎛️ **Motors i Servos** ← NOU
- 👁️ **Sensors Extra** ← NOU
- 📶 **PWM** ← NOU
- 💾 **Emmagatzematge** ← NOU
- 🔧 **Sistema** ← NOU

**Total:** 23 categories

---

## 🧪 Pas 3: Proves Ràpides

### Prova 1: Temps
```
1. Arrossega "⏰ Temps actual"
2. Arrossega "📝 Print"
3. Connecta Temps → Print
4. Genera codi (hauries de veure import time)
```

### Prova 2: String
```
1. Arrossega bloc Text "Hola"
2. Arrossega "📝 Replace"
3. Configura: Replace "Hola" "o" per "0"
4. Genera → hauries de veure .replace()
```

### Prova 3: NeoPixels
```
1. Arrossega "💡 Configurar NeoPixels"
2. Arrossega "💡 Arc de Sant Martí"
3. Arrossega "💡 Actualitzar"
4. Genera → hauries de veure import neopixel
```

### Prova 4: Display
```
1. Arrossega "🖥️ Configurar Display OLED"
2. Arrossega "🖥️ Mostrar text"
3. Genera → hauries de veure display setup
```

### Prova 5: Sistema
```
1. Arrossega "🔧 Memòria lliure"
2. Arrossega Print
3. Connecta
4. Genera → hauries de veure gc.mem_free()
```

---

## 🎨 Pas 4: Projecte Complet de Prova

### Termòmetre Simple

**Blocs necessaris:**
1. Print "Iniciant..."
2. Repetir per sempre:
   - temperatura = Temperatura CPU
   - text = Format "Temp: {}°C" temperatura
   - Print text
   - Esperar 1s

**Codi generat hauria de tenir:**
```python
import microcontroller
import time

print("Iniciant...")
while True:
    temperatura = microcontroller.cpu.temperature
    text = "Temp: {}°C".format(temperatura)
    print(text)
    time.sleep(1.0)
```

---

## 🔍 Pas 5: Verificació Avançada

### Mode Desenvolupador

```bash
./start-dev.sh
```

**Comprova:**
- [ ] DevTools s'obre automàticament
- [ ] No hi ha errors a la consola
- [ ] Tots els blocs es carreguen
- [ ] Generadors funcionen

### Consola JavaScript

A DevTools, escriu:
```javascript
// Comprova que els nous blocs existeixen
Blockly.Blocks['tecla_neopixel_setup']
Blockly.Blocks['tecla_display_setup']
Blockly.Blocks['tecla_motor_speed']
```

Hauries de veure els objectes, no `undefined`.

---

## 📊 Checklist de Funcionalitat

### Blocs Visibles
- [ ] 23 categories al toolbox
- [ ] Icones emoji visibles
- [ ] Colors diferenciats
- [ ] Blocs arrossegables

### Generació de Codi
- [ ] Codi Python es genera
- [ ] Imports correctes
- [ ] Sintaxi vàlida
- [ ] Comentaris apropiats

### Connexions
- [ ] Blocs es connecten correctament
- [ ] Values i statements funcionen
- [ ] Dropdowns amb opcions
- [ ] Shadow blocks per defecte

### Toolbox
- [ ] Categories expandeixen/colapsen
- [ ] Scroll funciona
- [ ] Cerca funciona (si disponible)
- [ ] Totes les categories accessibles

---

## 🐛 Problemes Comuns

### Els nous blocs no apareixen

**Solució 1:** Verifica scripts
```html
<!-- A index.html -->
<script src="generators/tecla_python_extended.js"></script>
```

**Solució 2:** Hard refresh
```
Cmd + Shift + R (Mac)
Ctrl + F5 (Windows/Linux)
```

**Solució 3:** Cache
```bash
# Neteja cache del navegador
# O reinicia l'app completament
```

### Error al generar codi

**Comprova:**
```bash
# Obre mode dev
./start-dev.sh

# Mira errors a consola
# Cerca "Uncaught" o "Error"
```

**Errors comuns:**
- `Blockly.Python['tecla_xxx'] is not a function`
  → Falta generador a tecla_python_extended.js
  
- `Cannot read property 'init' of undefined`
  → Falta definició a tecla_blocks.js

### Blocs sense color

**Causa:** Color no especificat o incorrecte

**Solució:**
```javascript
// A tecla_blocks.js
this.setColour('#FF9800'); // Format correcte
```

---

## 🎯 Tests Específics per Categoria

### Control Avançat
```
[ ] Break funciona dins bucle
[ ] Continue salta iteració
[ ] Try/Except captura errors
```

### Temps
```
[ ] Temps actual retorna número
[ ] Temporitzador funciona
[ ] Sleep(ms) pausa correctament
```

### String
```
[ ] Replace funciona
[ ] Split crea llista
[ ] Join uneix elements
[ ] Contains retorna boolean
```

### Matemàtiques
```
[ ] Sin/Cos/Tan amb radians
[ ] Log/Exp funcionen
[ ] Bitwise genera operadors correctes
```

### NeoPixels
```
[ ] Setup genera configuració
[ ] Set color amb RGB
[ ] Rainbow genera funció wheel
```

### Display
```
[ ] Setup diferencia OLED/LCD
[ ] Text, Clear, Pixel generen codi
```

### Motors
```
[ ] Servo genera PWM
[ ] Motor amb direccions
```

### Sensors
```
[ ] Sensors generen AnalogIn
[ ] PIR genera DigitalIn
```

### PWM
```
[ ] Setup amb freqüència
[ ] Duty cycle 0-100%
```

### Emmagatzematge
```
[ ] Write/Read generen codi
[ ] Exists retorna boolean
```

### Sistema
```
[ ] Reset genera microcontroller.reset()
[ ] Memory genera gc.mem_free()
[ ] Temp genera cpu.temperature
```

---

## 📈 Benchmark de Rendiment

### Temps de Càrrega
```
Esperat: < 3 segons
Amb 23 categories i 148 blocs
```

### Generació de Codi
```
Esperat: Instantani (<100ms)
Per programes de 50-100 blocs
```

### Memòria
```
Esperat: < 200MB RAM
Workspace gran amb 200+ blocs
```

---

## ✅ Prova Final

### Programa Complet Multi-Funcional

```
1. Variables:
   - contador = 0
   
2. Configuració:
   - NeoPixels pin 5, 10 LEDs
   - Display OLED
   
3. Bucle principal:
   - contador = contador + 1
   - temp = Temperatura CPU
   - memòria = Memòria lliure
   
   - Display clear
   - Display text "Contador: " + contador (0,0)
   - Display text "Temp: " + temp (0,10)
   
   - Per i de 0 a 9:
     - Si contador % 2 == 0:
       - LED i: (255,0,0)
     - Sinó:
       - LED i: (0,0,255)
   - Actualitzar NeoPixels
   
   - Esperar 0.5s
```

**Aquest programa usa:**
- ✅ Variables
- ✅ Matemàtiques
- ✅ Display
- ✅ NeoPixels
- ✅ Bucles
- ✅ Condicionals
- ✅ Sistema
- ✅ Temps

**Si genera codi correcte → Tot funciona! 🎉**

---

## 📝 Reportar Problemes

Si trobes errors:

1. **Descripció:** Què intentaves fer?
2. **Blocs:** Quins blocs usaves?
3. **Error:** Missatge d'error (captura de pantalla)
4. **Consola:** Errors a DevTools
5. **Codi generat:** Copia el Python generat

---

## 🎉 Èxit!

Si tots els tests passen:

```
✅ TECLA Blocks v3.0 funciona correctament
✅ 148 blocs disponibles
✅ 23 categories operatives
✅ Generadors Python funcionant
✅ Llest per crear projectes increïbles!
```

---

**Versió de Test:** 3.0.0  
**Data:** 17 Novembre 2025  
**Estat:** Llest per produir
