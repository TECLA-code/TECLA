# 🚀 TECLA Blocks - Versió Ampliada

## Novetats i Funcionalitats Avançades

TECLA Blocks ara és una **plataforma completa de programació visual** inspirada en MicroBlocks i Scratch, però especialitzada en música, síntesi de so i programació de microcontroladors.

---

## 📦 Categories de Blocs (Total: 70+ blocs)

### 🎵 Música Bàsica (4 blocs)
Blocs bàsics per començar amb música:
- **Tocar nota** - Notes individuals amb velocitat i durada
- **Tocar acord** - 14 acords majors i menors
- **Tocar escala** - 5 tipus d'escales (Major, Menor, Pentatònica, Blues, Cromàtica)
- **Canviar octava** - Controla l'octava (1-7)

### 🌊 Síntesi Avançada (5 blocs) **✨ NOU**
Síntesi de so professional:

#### **Oscil·lador**
- 6 formes d'ona: Sinusoidal, Quadrada, Triangular, Dent de serra, Pols, Soroll
- Control de freqüència i amplitud
- Ideal per crear sons sintètics des de zero

#### **LFO (Low Frequency Oscillator)**
- Modula automàticament paràmetres
- 4 formes d'ona: Sinusoidal, Triangular, Quadrada, Aleatòria
- Controla: Pitch, Amplitud, Filtre, Pan
- Velocitat i profunditat ajustables

#### **Envolvent ADSR**
- **Attack** - Temps de pujada
- **Decay** - Temps de caiguda
- **Sustain** - Nivell sostingut
- **Release** - Temps d'alliberament
- Crea evolucions naturals del so

#### **Modulació**
- **FM** (Síntesi de freqüència modulada)
- **AM** (Síntesi d'amplitud modulada)
- **PM** (Síntesi de fase modulada)
- **Ring Modulation** - Efecte metàl·lic
- Portadora, moduladora i profunditat configurables

#### **Waveshaper** (Distorsió)
- 5 tipus: Suau, Mitjà, Dur, Fuzz, Bitcrusher
- Control de quantitat
- Afegeix caràcter i textura al so

---

### 💡 GPIO (Pins Digitals/Analògics) (4 blocs) **✨ NOU**

#### Digital
- **Escriure pin digital** - HIGH/LOW a pins GPIO (0-29)
- **Llegir pin digital** - Llegeix estat d'un pin

#### Analògic / PWM
- **Escriure PWM** - Control analògic (0-65535)
- **Llegir analògic** - Llegeix valors ADC (A0, A1, A2)

**Aplicacions:**
- Controlar LEDs amb intensitat variable
- Llegir sensors analògics
- Controlar motors
- Interfícies personalitzades

---

### 📡 Sensors (3 blocs) **✨ NOU**

#### **Temperatura CPU**
- Llegeix la temperatura interna del microcontrolador
- Útil per monitoritzar el dispositiu

#### **Acceleròmetre**
- Eixos X, Y, Z
- Magnitud (vector resultant)
- Ideal per:
  - Controlar música amb moviment
  - Detectar orientació
  - Crear instruments gestuals

#### **Sensor de Distància**
- Compatible amb HC-SR04 (ultrasònic)
- Configuració de pins Trigger i Echo
- Mesura distàncies en cm
- Aplicacions:
  - Teremín sense contacte
  - Control gestual
  - Efectes per proximitat

---

### 🔢 Matemàtiques Avançades (6 blocs) **✨ NOU**

#### **Número Aleatori**
- Genera enters aleatoris entre dos valors
- Ideal per:
  - Música generativa
  - Variacions aleatòries
  - Experiments sonors

#### **Escalar valor (Map)**
- Converteix un valor d'un rang a un altre
- **Exemple:** Potenciòmetre (0-1023) → Velocitat MIDI (0-127)
- Essencial per interfícies

#### **Limitar valor (Constrain)**
- Manté un valor dins un rang
- Evita valors fora de límits

#### **Funcions Trigonomètriques**
- sin, cos, tan, asin, acos, atan
- Per LFOs complexos i modulacions matemàtiques

#### **Arrel quadrada, Valor absolut, etc.**
- Operacions matemàtiques estàndard

---

### 📝 Text / Strings (3 blocs) **✨ NOU**

- **Unir textos** - Concatenació
- **Longitud de text** - Nombre de caràcters
- **Conté text** - Cerca dins cadenes

**Aplicacions:**
- Missatges de depuració
- Interfícies de text
- Processa dades sèrie

---

### 📋 Llistes / Arrays (4 blocs) **✨ NOU**

- **Crear llista buida**
- **Afegir element** - Append
- **Obtenir element** - Per índex
- **Longitud de llista**

**Aplicacions musicals:**
- Seqüenciadors de notes
- Patrons rítmics
- Memòria de progres

sions
- Llistes de paràmetres

---

### 📡 Comunicació (4 blocs) **✨ NOU**

#### Serial (USB)
- **Print** - Envia dades al monitor sèrie
- **Read** - Llegeix dades entrants
- Depuració i interfícies amb ordinador

#### I2C (Comunicació amb dispositius)
- **Escriure I2C** - Envia dades a adreça
- **Llegir I2C** - Rep dades de dispositiu
- Compatible amb:
  - Pantalles OLED
  - Sensors I2C (temperatura, acceleròmetre, etc.)
  - DACs i ADCs externs
  - Expansors de GPIO

---

### 🔧 Funcions Personalitzades (2 blocs) **✨ NOU**

- **Definir funció** - Crea funcions reutilitzables
- **Cridar funció** - Executa una funció definida

**Avantatges:**
- Codi més organitzat
- Reutilització
- Modularitat
- Facilita col·laboració

**Exemple:**
```
Definir funció "tocar_melodia"
  ├─ Tocar nota Do
  ├─ Tocar nota Mi
  └─ Tocar nota Sol

Repetir 3 vegades
  └─ Cridar funció "tocar_melodia"
```

---

## 🎓 Casos d'Ús Avançats

### 1. Sintetitzador FM
```
Oscil·lador Sinusoidal (freq: 440, amp: 100)
↓
Modulació FM (carrier: 440, mod: 220, depth: 50)
↓
Envolvent ADSR (A:10, D:50, S:70, R:100)
↓
Waveshaper Suau (amount: 30)
```

### 2. Seqüenciador amb Llista
```
Crear llista "notes"
Afegir 60, 64, 67, 72 a llista

Repetir per sempre:
  Per i de 0 a (longitud llista - 1):
    nota = Obtenir element i de llista
    Tocar nota (nota)
    Esperar 0.5s
```

### 3. Control Gestual amb Acceleròmetre
```
x = Acceleròmetre eix X
velocitat = Escalar x de -10-10 a 0-127

Si velocitat > 64:
  Tocar acord amb velocitat alta
Altrament:
  Tocar nota suau
```

### 4. Sensor de Proximitat → Teremín
```
distancia = Sensor distància (Trig: 16, Echo: 17)
frequencia = Escalar distancia de 5-100 a 220-880

Oscil·lador Sinusoidal:
  freq: frequencia
  amp: 100
```

### 5. LFO Auto-Modulació
```
LFO Sinusoidal:
  velocitat: 2 Hz
  controla: Filtre
  profunditat: 80

Tocar acord Do Major
```

---

## 🎯 Comparació amb altres plataformes

| Característica | TECLA Blocks | Scratch | MicroBlocks | Arduino IDE |
|---|---|---|---|---|
| **Programació visual** | ✅ | ✅ | ✅ | ❌ |
| **Música/MIDI** | ✅✅✅ | ⚠️ | ⚠️ | ⚠️ |
| **Síntesi avançada** | ✅✅✅ | ❌ | ❌ | ✅ |
| **GPIO/Sensors** | ✅✅ | ❌ | ✅✅ | ✅✅ |
| **Variables i llistes** | ✅✅ | ✅✅ | ✅ | ✅✅ |
| **Funcions custom** | ✅ | ✅ | ✅ | ✅✅ |
| **I2C/SPI** | ✅ | ❌ | ✅ | ✅✅ |
| **Educació primària** | ✅✅✅ | ✅✅✅ | ✅✅ | ⚠️ |
| **Generació Python** | ✅✅ | ❌ | ⚠️ | ❌ |

**Llegenda:**
- ✅✅✅ Excellent
- ✅✅ Molt bo
- ✅ Bo
- ⚠️ Limitat
- ❌ No disponible

---

## 🆕 Exemples de Codi Generat

### Exemple 1: Oscil·lador amb LFO
**Blocs:**
```
Oscil·lador Sinusoidal (freq: 440, amp: 100)
LFO Triangular (rate: 3Hz, target: Pitch, depth: 20)
Repetir per sempre
```

**Python Generat:**
```python
# Configurar oscil·lador sine
oscillator_waveform = "sine"
oscillator_frequency = 440
oscillator_amplitude = 100

# LFO triangle -> pitch
lfo_rate = 3
lfo_target = "pitch"
lfo_depth = 20

while True:
    # Implementar modulació LFO aquí
    time.sleep(0.05)
```

### Exemple 2: Control GPIO amb Sensor
**Blocs:**
```
temp = Temperatura CPU
Si temp > 30:
  Pin digital 25 = HIGH
Altrament:
  Pin digital 25 = LOW
```

**Python Generat:**
```python
temp = microcontroller.cpu.temperature

if temp > 30:
    pin_25.value = 1
else:
    pin_25.value = 0
```

---

## 📚 Recursos d'Aprenentatge

### Per alumnes de primària:
1. **Nivell 1:** Música bàsica (notes, acords)
2. **Nivell 2:** Bucles i control (repeticions, botons)
3. **Nivell 3:** Variables i llistes (seqüències)
4. **Nivell 4:** Funcions (organització del codi)
5. **Nivell 5:** Sensors i GPIO (projectes físics)
6. **Nivell 6:** Síntesi avançada (sons personalitzats)

### Per secundària/batxillerat:
- Síntesi FM i modulació
- Programació de microcontroladors
- Comunicació I2C amb sensors
- Projectes IoT musicals

---

## 🔜 Properes millores

- [ ] **Blocs de Display OLED** - Visualització gràfica
- [ ] **Blocs de NeoPixel** - Control de LEDs RGB
- [ ] **Blocs de Servomotors** - Moviments sincronitzats
- [ ] **MIDI In** - Rebre MIDI extern
- [ ] **OSC (Open Sound Control)** - Comunicació amb DAWs
- [ ] **Biblioteca d'exemples** integrada a l'app
- [ ] **Mode col·laboratiu** - Programar en equip
- [ ] **Simulador amb àudio real** - Web Audio API

---

## 💡 Filosofia de disseny

**TECLA Blocks** combina:

1. **Accessibilitat de Scratch** - Interfície intuïtiva per nens
2. **Potència de MicroBlocks** - Control de hardware real
3. **Especialització musical** - Síntesi i MIDI avançats
4. **Educació STEAM** - Música + Tecnologia + Matemàtiques

És una eina **tant per principiants com per usuaris avançats**, amb una corba d'aprenentatge suau però sense límits en les possibilitats creatives.

---

**Fet amb ❤️ pel futur de l'educació musical i tecnològica**
