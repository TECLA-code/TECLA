# 🎹 Exemple: Sintetitzador Gestual Avançat

## 📋 Descripció del Projecte

**Nom:** Sintetitzador Gestual Avançat  
**Fitxer:** `exemple_sintetitzador_gestual.tblocks`  
**Nivell:** Avançat  
**Durada construcció:** 30-45 minuts  

---

## 🎯 Què fa aquest projecte?

Un sintetitzador complet que:
- ✅ Genera so amb **síntesi FM**
- ✅ Es controla amb **moviments** (acceleròmetre)
- ✅ Té un **seqüenciador** amb llistes
- ✅ Aplica **efectes** (Reverb, Delay)
- ✅ Utilitza **funcions** personalitzades
- ✅ Té **envolvent ADSR** i **LFO**

---

## 🎮 Com s'usa?

### Botó 1: Mode Gestual
```
Prem Botó 1
    ↓
Mou el dispositiu (eix X)
    ↓
El so canvia segons el moviment
    + Síntesi FM
    + Reverb
```

### Botó 2: Mode Seqüenciador
```
Prem Botó 2
    ↓
Seqüència automàtica de 4 notes
    Do (60) → Mi (64) → Sol (67) → Do alt (72)
    + Delay amb feedback
```

---

## 🏗️ Estructura del Programa (Blocs)

### 1. **Inicialització de Variables**

```
┌─────────────────────────────────┐
│ Variables                        │
├─────────────────────────────────┤
│ freq_base = 220                  │
│ notes_list = [60, 64, 67, 72]   │
└─────────────────────────────────┘
```

**Blocs utilitzats:**
- `variables_set` (assignar valor)
- `math_number` (números)
- `lists_create_with` (crear llista)

---

### 2. **Funció: tocar_amb_gest()**

Aquesta funció controla el sintetitzador amb moviment:

```
┌────────────────────────────────────────────┐
│ 🔧 Definir funció "tocar_amb_gest"         │
├────────────────────────────────────────────┤
│                                            │
│  ┌─────────────────────────────────┐      │
│  │ accel_x = Acceleròmetre eix X   │      │
│  └─────────────────────────────────┘      │
│                  ↓                         │
│  ┌─────────────────────────────────┐      │
│  │ Escalar valor:                  │      │
│  │ de -10 a 10 (acceleròmetre)     │      │
│  │ a 48 a 84 (notes MIDI)          │      │
│  │ → nota_mapejada                 │      │
│  └─────────────────────────────────┘      │
│                  ↓                         │
│  ┌─────────────────────────────────┐      │
│  │ 🌊 Oscil·lador Sinusoidal       │      │
│  │ freq: nota_mapejada             │      │
│  │ amp: 100                        │      │
│  └─────────────────────────────────┘      │
│                  ↓                         │
│  ┌─────────────────────────────────┐      │
│  │ 🎚️ Modulació FM                 │      │
│  │ carrier: nota_mapejada          │      │
│  │ modulator: 220                  │      │
│  │ depth: 50                       │      │
│  └─────────────────────────────────┘      │
│                                            │
└────────────────────────────────────────────┘
```

**Blocs utilitzats:**
- `tecla_function_define` (definir funció)
- `tecla_sensor_accelerometer` (llegir sensor)
- `tecla_math_map` (escalar valors)
- `tecla_oscillator` (oscil·lador)
- `tecla_modulation` (síntesi FM)

**Conceptes:**
- **Mapping:** Converteix moviment físic (-10 a 10) a notes musicals (48-84)
- **Síntesi FM:** Crea sons complexos modulant una portadora amb una moduladora
- **Control gestual:** El pitch canvia segons la inclinació del dispositiu

---

### 3. **Funció: sequenciador()**

Reprodueix una seqüència de notes automàticament:

```
┌────────────────────────────────────────────┐
│ 🔧 Definir funció "sequenciador"           │
├────────────────────────────────────────────┤
│                                            │
│  ┌─────────────────────────────────┐      │
│  │ Per i de 0 a len(notes_list)-1: │      │
│  │                                 │      │
│  │  ┌──────────────────────────┐   │      │
│  │  │ nota_actual =            │   │      │
│  │  │ notes_list[i]            │   │      │
│  │  └──────────────────────────┘   │      │
│  │            ↓                     │      │
│  │  ┌──────────────────────────┐   │      │
│  │  │ 🎵 Tocar nota            │   │      │
│  │  └──────────────────────────┘   │      │
│  │            ↓                     │      │
│  │  ┌──────────────────────────┐   │      │
│  │  │ ⏱️ Esperar 0.1s          │   │      │
│  │  └──────────────────────────┘   │      │
│  │                                 │      │
│  └─────────────────────────────────┘      │
│                                            │
└────────────────────────────────────────────┘
```

**Blocs utilitzats:**
- `controls_for` (bucle for)
- `tecla_list_length` (longitud llista)
- `tecla_list_get` (obtenir element)
- `tecla_play_note` (tocar nota)
- `tecla_wait` (esperar)

**Conceptes:**
- **Iteració:** Recorre tots els elements de la llista
- **Seqüenciador:** Patró rítmic repetitiu
- **Arrays:** Emmagatzematge de múltiples notes

---

### 4. **Configuració de So**

```
┌─────────────────────────────────┐
│ 📢 Print "Iniciat!"             │
└─────────────────────────────────┘
                ↓
┌─────────────────────────────────┐
│ 📈 Envolvent ADSR               │
│ Attack: 10ms                    │
│ Decay: 50ms                     │
│ Sustain: 70%                    │
│ Release: 100ms                  │
└─────────────────────────────────┘
                ↓
┌─────────────────────────────────┐
│ 🌊 LFO Sinusoidal               │
│ Rate: 2 Hz                      │
│ Target: Pitch                   │
│ Depth: 30                       │
└─────────────────────────────────┘
```

**Blocs utilitzats:**
- `tecla_serial_print` (missatge)
- `tecla_envelope` (ADSR)
- `tecla_lfo` (modulació automàtica)

**Conceptes:**
- **ADSR:** Controla l'evolució del so en el temps
- **LFO:** Modula el pitch automàticament (vibrato)

---

### 5. **Bucle Principal**

```
┌─────────────────────────────────────────────┐
│ 🔁 Repetir per sempre                       │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────┐          │
│  │ Si Botó 1 premut:            │          │
│  │  ├─ Cridar tocar_amb_gest()  │          │
│  │  └─ Aplicar Reverb 50%       │          │
│  │                               │          │
│  │ Sinó si Botó 2 premut:       │          │
│  │  ├─ Cridar sequenciador()    │          │
│  │  └─ Aplicar Delay 300ms/50%  │          │
│  └──────────────────────────────┘          │
│                  ↓                          │
│  ┌──────────────────────────────┐          │
│  │ ⏱️ Esperar 0.05s             │          │
│  └──────────────────────────────┘          │
│                                             │
└─────────────────────────────────────────────┘
```

**Blocs utilitzats:**
- `tecla_repeat_forever` (bucle infinit)
- `controls_if` (condicionals)
- `tecla_read_button` (llegir botó)
- `tecla_function_call` (cridar funció)
- `tecla_effect_reverb` (efecte)
- `tecla_effect_delay` (efecte)

**Conceptes:**
- **Event loop:** Comprova contínuament l'estat dels botons
- **Condicionals:** Respon diferent segons quin botó es prem
- **Efectes:** Processa el so amb Reverb o Delay

---

## 🎨 Visualització del Workspace

### Vista General

```
WORKSPACE TECLA BLOCKS
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║  ┌─ Variables ──────────────────────────────────┐        ║
║  │ freq_base = 220                              │        ║
║  │ notes_list = [60, 64, 67, 72]                │        ║
║  └──────────────────────────────────────────────┘        ║
║                  ↓                                        ║
║  ┌─ Funcions ──────────────────────────────────┐         ║
║  │ 🔧 tocar_amb_gest()                          │         ║
║  │   ├─ Acceleròmetre → Map → Oscil·lador      │         ║
║  │   └─ Modulació FM                            │         ║
║  │                                               │         ║
║  │ 🔧 sequenciador()                            │         ║
║  │   └─ For loop per notes_list                │         ║
║  └──────────────────────────────────────────────┘        ║
║                  ↓                                        ║
║  ┌─ Configuració So ──────────────────────────┐          ║
║  │ Print "Iniciat"                             │          ║
║  │ ADSR                                        │          ║
║  │ LFO                                         │          ║
║  └──────────────────────────────────────────────┘        ║
║                  ↓                                        ║
║  ┌─ Bucle Principal ─────────────────────────┐           ║
║  │ 🔁 Repetir per sempre                      │           ║
║  │   Si Botó 1 → Mode Gestual + Reverb       │           ║
║  │   Si Botó 2 → Seqüenciador + Delay        │           ║
║  │   Esperar 0.05s                            │           ║
║  └──────────────────────────────────────────────┘        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 🧩 Blocs Utilitzats per Categoria

### 🌊 Síntesi Avançada (3 blocs)
- `tecla_oscillator` - Oscil·lador sinusoidal
- `tecla_modulation` - Síntesi FM
- `tecla_lfo` - LFO per vibrato

### 📡 Sensors (1 bloc)
- `tecla_sensor_accelerometer` - Control gestual

### 🔢 Matemàtiques (2 blocs)
- `tecla_math_map` - Escalar valors
- `math_number` - Constants

### 📋 Llistes (3 blocs)
- `lists_create_with` - Crear llista de notes
- `tecla_list_get` - Obtenir nota
- `tecla_list_length` - Longitud

### 🔧 Funcions (4 blocs)
- `tecla_function_define` (x2) - Definir funcions
- `tecla_function_call` (x2) - Cridar funcions

### ⏱️ Control de Flux (5 blocs)
- `tecla_repeat_forever` - Bucle principal
- `controls_for` - Iteració seqüenciador
- `controls_if` (x2) - Condicionals
- `tecla_wait` (x2) - Temporitzacions

### 🎵 Música (2 blocs)
- `tecla_play_note` - Tocar nota
- `tecla_envelope` - ADSR

### ✨ Efectes (2 blocs)
- `tecla_effect_reverb` - Reverberació
- `tecla_effect_delay` - Retard

### 📊 Variables (4 blocs)
- `variables_set` (x4) - Assignacions
- `variables_get` (x6) - Lectures

### 📝 Comunicació (1 bloc)
- `tecla_serial_print` - Missatge d'inici

### 🎛️ Hardware (1 bloc)
- `tecla_read_button` (x2) - Llegir botons

**TOTAL: ~35-40 blocs**

---

## 📚 Conceptes Apresos

### Nivell Bàsic
- ✅ Variables i constants
- ✅ Bucles i condicionals
- ✅ Funcions

### Nivell Intermedi
- ✅ Llistes i arrays
- ✅ Iteració sobre dades
- ✅ Control amb sensors

### Nivell Avançat
- ✅ Síntesi de so (FM)
- ✅ Mapping de valors
- ✅ Envolvent ADSR
- ✅ LFO i modulació
- ✅ Processament d'efectes

---

## 🎯 Variants i Ampliacions

### Variant 1: Més Notes al Seqüenciador
```
notes_list = [60, 62, 64, 65, 67, 69, 71, 72]
// Escala de Do Major completa
```

### Variant 2: Control amb Potenciòmetres
```
Afegir:
- Pot X → Controla la freqüència del LFO
- Pot Y → Controla la profunditat FM
- Pot Z → Controla el mix Reverb/Delay
```

### Variant 3: Més Eixos
```
Acceleròmetre Y → Controla amplitud
Acceleròmetre Z → Controla filtre
Magnitude → Controla distorsió
```

### Variant 4: Sensor de Distància
```
Si tens sensor HC-SR04:
Distància → Controla pitch (Teremín!)
```

---

## 🔊 Sortida Sonora Esperada

### Mode Gestual (Botó 1)
```
So: Sinusoidal + FM
Característiques:
- Pitch varia amb moviment (48-84 MIDI)
- Modulació FM afegeix harmònics
- Reverb crea espai
- LFO afegeix vibrato subtil (2Hz)
- ADSR suavitza atac i release

Sona com: Sintetitzador analògic amb vibrato
```

### Mode Seqüenciador (Botó 2)
```
So: Seqüència Do-Mi-Sol-Do
Característiques:
- 4 notes en bucle
- Velocitat: 10 notes/segon
- Delay crea eco rítmic
- ADSR dona caràcter a cada nota

Sona com: Arpeggiador de sintetitzador
```

---

## 💡 Per Professors

### Durada de la Classe
- **Explicació:** 15 minuts
- **Construcció:** 30-45 minuts
- **Prova i experimentació:** 15 minuts
- **Total:** 60-75 minuts

### Prerequisits
- Coneixement de variables
- Experiència amb funcions
- Entendre llistes bàsiques
- Conceptes de síntesi (introductori)

### Objectius d'Aprenentatge
1. Integrar múltiples sistemes (sensors + so + efectes)
2. Organitzar codi amb funcions
3. Utilitzar llistes per seqüències
4. Aplicar matemàtiques (mapping)
5. Entendre síntesi bàsica

---

## 🚀 Com Obrir i Usar l'Exemple

### Pas 1: Descarregar
```
Fitxer: exemple_sintetitzador_gestual.tblocks
Ubicació: /Users/zen/Desktop/
```

### Pas 2: Obrir amb TECLA Blocks
1. Obre l'aplicació **TECLA Blocks**
2. Menú: **Arxiu → Obrir Projecte**
3. Selecciona `exemple_sintetitzador_gestual.tblocks`
4. El workspace es carregarà amb tots els blocs

### Pas 3: Explorar
- Desplaça't pel workspace
- Examina cada bloc
- Llegeix els comentaris (si n'hi ha)
- Prova a modificar valors

### Pas 4: Pujar a TECLA
1. Connecta TECLA via USB
2. Click **"⬆️ Pujar a TECLA"**
3. Escull un slot (1, 2, 3 o 4)
4. Espera confirmació

### Pas 5: Executar
1. Desconnecta USB
2. Encén TECLA
3. Long press botó corresponent (1.5s)
4. Experimenta amb Botó 1 i Botó 2!

---

## 🎓 Reptes Addicionals

### Repte 1: Afegir Més Modes
```
Botó 3 → Mode Aleatori
  - Genera notes random
  - Utilitza tecla_math_random_int
```

### Repte 2: Gravar Seqüència
```
Botó 4 → Mode Gravació
  - Grava les notes que toques
  - Afegeix a notes_list amb tecla_list_add
  - Reprodueix després
```

### Repte 3: Waveshaper
```
Afegir distorsió variable:
  - Pot Z → Controla quantitat de waveshaper
  - Tipus: Fuzz per sons agressius
```

---

## 📊 Resum Executiu

### Què demostra aquest exemple?

- ✅ **Complexitat:** 35-40 blocs integrats
- ✅ **Funcionalitats:** 12 categories de blocs
- ✅ **Conceptes:** Des de bàsic a avançat
- ✅ **Usabilitat:** Interfície intuïtiva (2 botons)
- ✅ **Versatilitat:** Música + Sensors + Efectes
- ✅ **Organització:** Funcions i modularitat
- ✅ **Creativitat:** Sons únics amb control gestual

**Aquest projecte mostra que TECLA Blocks és una eina completa per crear instruments musicals interactius avançats! 🎹✨**

---

**Arxiu:** `exemple_sintetitzador_gestual.tblocks`  
**Versió:** 2.0  
**Data:** 17 Novembre 2025  
**Autor:** TECLA Blocks Team  
**Llicència:** Educativa - Ús lliure
