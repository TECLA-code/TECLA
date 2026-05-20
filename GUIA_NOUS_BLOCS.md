# 🎯 Guia Ràpida - Nous Blocs v3.0

## ⚙️ Control Avançat

### Break
```python
Surt del bucle actual
```
**Ús:** Atura un bucle quan es compleix una condició.

### Continue
```python
Salta a la següent iteració
```
**Ús:** Omet el codi restant i continua amb la següent iteració.

### Try/Except
```python
Gestiona errors sense aturar el programa
```
**Ús:** Captura errors i defineix com actuar.

---

## ⏰ Temps i Temporitzadors

### Temps Actual
Retorna segons des de l'inici.  
**Exemple:** Cronòmetre, mesura de durades.

### Mil·lisegons
Temps en ms per a temporitzacions precises.  
**Exemple:** Animacions, seqüenciadors ràpids.

### Iniciar Temporitzador
Guarda el temps actual en una variable.  
**Exemple:** `timer_start = temps_actual`

### Temps Transcorregut
Calcula quant temps ha passat.  
**Exemple:** `temps_actual - timer_start`

### Dormir (ms)
Pausa en mil·lisegons.  
**Exemple:** `sleep(100)` = 0.1 segons

---

## 📝 String Avançat

### Replace
```
"Hola món".replace("món", "TECLA") → "Hola TECLA"
```

### Split
```
"Do,Re,Mi".split(",") → ["Do", "Re", "Mi"]
```

### Join
```
["Do", "Re", "Mi"].join("-") → "Do-Re-Mi"
```

### Format
```
"Temp: {}".format(25) → "Temp: 25"
```

### Contains
```
"TECLA Blocks" conté "Blocks" → True
```

---

## 📐 Matemàtiques Avançades

### Trigonometria
- `sin(radians)` - Sinus
- `cos(radians)` - Cosinus
- `tan(radians)` - Tangent

**Exemple:** Ones, moviments circulars, LFO.

### Logaritmes
- `log(x)` - Logaritme natural
- `exp(x)` - e^x

**Exemple:** Escalat exponencial, reverb.

### Conversions
- `degrees(π)` → 180
- `radians(180)` → π

### Bitwise
- `A & B` - AND
- `A | B` - OR
- `A ^ B` - XOR
- `A << 2` - Left shift
- `A >> 2` - Right shift

**Exemple:** Màscares de bits, protocols.

---

## 💡 NeoPixels

### Configurar
```
NeoPixels pin 5, 30 LEDs
```

### Establir Color
```
LED 0: R=255, G=0, B=0 (vermell)
```

### Actualitzar
```
Mostra els canvis al strip
```

### Apagar
```
Tots els LEDs a (0,0,0)
```

### Arc de Sant Martí
```
Efecte rainbow amb offset animat
```

**Projecte:** Visualitzador de música, ambient lighting.

---

## 🖥️ Display OLED/LCD

### Configurar
Escull OLED 128x64 o LCD 16x2.

### Mostrar Text
```
Text "Hola" a posició X=0, Y=0
```

### Netejar
Esborra tota la pantalla.

### Pixel/Línia/Rectangle
Gràfics simples.

**Projecte:** VU meter, menús, gràfics temps real.

---

## 🎛️ Motors i Servos

### Servo
```
Configurar pin 5
Angle 90° (centre)
```
**Rang:** 0-180 graus

### Motor DC
```
Configurar pins 10, 11
Velocitat 50 Endavant
```
**Direccions:** Endavant, Enrere, Aturar

**Projecte:** Robot, braç mecànic, instrument motoritzat.

---

## 👁️ Sensors Extra

### Llum
```
Sensor pin A0 → 0-100%
```
**Ús:** Control automàtic, dia/nit.

### So
```
Micròfon pin A1 → 0-100%
```
**Ús:** VU meter, trigger per so.

### Humitat
```
Terra pin A2 → 0-100%
```
**Ús:** Reg automàtic.

### PIR
```
Moviment pin 15 → True/False
```
**Ús:** Detector presència.

### Botó Extern
```
Pin 16, Pull Up/Down → True/False
```
**Ús:** Controls addicionals.

---

## 📶 PWM Avançat

### Configurar
```
PWM pin 5, freqüència 1000 Hz
```

### Duty Cycle
```
50% → Mig voltatge
```
**Rang:** 0-100%

**Ús:** Dimming LEDs, tons preciso, control motors.

---

## 💾 Emmagatzematge

### Guardar
```
clau="preset1", valor=440
```

### Llegir
```
freq = llegir "preset1"
```

### Existeix
```
si existeix "preset1": ...
```

### Eliminar
```
eliminar "preset1"
```

**Ús:** Presets, configuracions, calibracions.

---

## 🔧 Sistema

### Reiniciar
Soft reset del dispositiu.

### Memòria Lliure
Bytes disponibles de RAM.  
**Ús:** Debug, optimització.

### Temperatura CPU
Monitoratge tèrmic.  
**Ús:** Protecció overheating.

### Voltatge Bateria
Nivell d'alimentació.  
**Ús:** Indicador bateria baixa.

---

## 🎨 Projectes Exemple

### 1. Termòmetre amb Display
```
[Configurar Display OLED]
[Repetir per sempre]
  ├─ temp = [Temperatura CPU]
  ├─ text = [Format "{}°C" temp]
  ├─ [Mostrar text 0, 0]
  └─ [Esperar 1s]
```

### 2. NeoPixel Rainbow
```
[Configurar NeoPixels pin 5, 30]
offset = 0
[Repetir per sempre]
  ├─ [Rainbow offset]
  ├─ offset = offset + 5
  └─ [Dormir 50ms]
```

### 3. Robot Detector
```
[Configurar Motor pins 10, 11]
[Configurar PIR pin 15]
[Repetir per sempre]
  ├─ Si [PIR detecta]:
  │   └─ [Motor 50 Endavant]
  ├─ Sinó:
  │   └─ [Motor Aturar]
  └─ [Dormir 100ms]
```

### 4. VU Meter amb LEDs
```
[Configurar NeoPixels 30]
[Configurar Sensor So pin A1]
[Repetir per sempre]
  ├─ nivell = [Sensor So]
  ├─ leds_on = nivell * 30 / 100
  ├─ Per i de 0 a 29:
  │   ├─ Si i < leds_on:
  │   │   └─ [LED i: 0,255,0]
  │   ├─ Sinó:
  │   │   └─ [LED i: 0,0,0]
  ├─ [Actualitzar]
  └─ [Dormir 50ms]
```

---

## ⚡ Consells

### Rendiment
- Usa `sleep_ms` en comptes de `sleep` per més precisió
- Temporitzadors per mesures no-blocking
- `break`/`continue` per optimitzar bucles

### Memòria
- Comprova `memòria_lliure` si tens problemes
- Strings llargues consumeixen RAM
- Usa emmagatzematge per dades grans

### Hardware
- NeoPixels: Pin amb PWM capaç
- Servos: 5V regulat, PWM 50Hz
- I2C: SDA/SCL per displays

### Debug
- `try/except` per capturar errors
- Serial print per traces
- Temperatura CPU per overhead

---

## 📚 Recursos

- **CircuitPython Libraries:** https://circuitpython.org/libraries
- **NeoPixel Guide:** Adafruit NeoPixel Überguide
- **Display Setup:** SSD1306 OLED tutorials
- **Motor Control:** L298N, DRV8833 datasheets

---

**Versió:** 3.0  
**Data:** 17 Novembre 2025  
**Nous Blocs:** 78  
**Total Blocs:** ~148
