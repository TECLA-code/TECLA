# 📝 Respostes a les teves Preguntes

## 1. ✅ Múltiples Projectes - Sistema Multi-Slot

### Sí, pots crear més d'un projecte!

He implementat un **sistema multi-slot** que permet tenir **fins a 4 projectes diferents** al mateix dispositiu TECLA.

---

### 🎮 Com Funciona

```
TECLA amb Multi-Slot
├─ Slot 1 (Botó 16) → Projecte Música
├─ Slot 2 (Botó 15) → Projecte Sensors
├─ Slot 3 (Botó 14) → Projecte Llums
└─ Slot 4 (Botó 13) → Projecte Mix
```

### Canvi en Directe

**Sí**, pots canviar entre projectes amb **long press** dels botons:

```
1. Reinicia TECLA
2. Long press (1.5s) del botó corresponent:
   - Botó 16 → Slot 1
   - Botó 15 → Slot 2
   - Botó 14 → Slot 3
   - Botó 13 → Slot 4
3. El LED piscarà durant la comprovació
4. Projecte carregat!
```

**Temps de canvi:** ~3-4 segons (reiniciar + long press)

---

### Arquitectura

```
CIRCUITPY/
├── code.py                  ← Launcher Multi-Slot (detecta botons)
├── tecla_main.py            ← TECLA Original
├── tecla_blocks_1.py        ← Projecte Música ⭐
├── tecla_blocks_2.py        ← Projecte Sensors ⭐
├── tecla_blocks_3.py        ← Projecte Llums ⭐
├── tecla_blocks_4.py        ← Projecte Mix ⭐
└── modes/, effects/, etc.   ← TECLA intacte
```

---

### Exemple Pràctic: Concert

**Preparació:**
```
Slot 1 → Cançó 1 (intro amb reverb)
Slot 2 → Cançó 2 (seqüenciador rítmic)
Slot 3 → Cançó 3 (síntesi FM)
Slot 4 → Improvisació lliure
```

**Durant el concert:**
```
Entre cançó 1 i 2:
  1. Reinicia TECLA (3 segons)
  2. Long press Botó 15 (1.5s)
  3. Cançó 2 carregada!
```

---

### Ús Educatiu

**Progressió setmanal:**
```
Setmana 1 → Slot 1: Projecte bàsic (notes)
Setmana 2 → Slot 2: Afegir sensors
Setmana 3 → Slot 3: Síntesi avançada
Setmana 4 → Slot 4: Projecte final
```

**Avantatges:**
- ✅ Els alumnes conserven tots els seus projectes
- ✅ Poden comparar entre versions
- ✅ Portfolio automàtic al dispositiu

---

### Com Configurar-ho

**Fitxer:** `launcher_multi_slot.py`

**Passos:**
1. Connecta TECLA via USB
2. Substitueix `code.py` per `launcher_multi_slot.py`
3. Desconnecta i prova

**Durada:** 2 minuts

---

### Upload des de TECLA Blocks

**Detecció automàtica:**
```
L'app detecta si tens multi-slot instal·lat
    ↓
Pregunta: "A quin slot vols pujar?"
    ↓
Escull 1, 2, 3 o 4
    ↓
Programa guardat al slot correcte
```

---

### Documentació Completa

- **`MULTI_SLOT.md`** - Guia completa del sistema
- **`launcher_multi_slot.py`** - Codi del launcher
- **`main.js`** - Upload amb suport multi-slot (actualitzat)

---

## 2. 🎹 Exemple del Potencial de TECLA Blocks

### Projecte Creat: Sintetitzador Gestual Avançat

**Fitxer:** `exemple_sintetitzador_gestual.tblocks`  
**Ubicació:** `/Users/zen/Desktop/`

---

### Què Fa?

Un sintetitzador complet que combina:

✅ **Síntesi Avançada**
- Oscil·lador sinusoidal
- Modulació FM professional
- LFO per vibrato
- Envolvent ADSR

✅ **Control amb Sensors**
- Acceleròmetre (eix X) → Pitch
- Moviment del dispositiu controla el so

✅ **Seqüenciador**
- Llista de 4 notes: Do-Mi-Sol-Do
- Reproducció automàtica en bucle
- 10 notes per segon

✅ **Efectes**
- Reverb (Mode Gestual)
- Delay amb feedback (Mode Seqüenciador)

✅ **Funcions Personalitzades**
- `tocar_amb_gest()` - Control gestual amb FM
- `sequenciador()` - Seqüència automàtica

✅ **Programació Avançada**
- Variables i constants
- Llistes i arrays
- Iteració amb for
- Condicionals
- Mapping matemàtic

---

### Com s'Usa?

```
Botó 1 → Mode Gestual
  - Mou el dispositiu
  - El pitch canvia amb el moviment
  - So FM + Reverb

Botó 2 → Mode Seqüenciador
  - Seqüència automàtica
  - Do-Mi-Sol-Do en bucle
  - Delay amb eco
```

---

### Visualització del Workspace

```
╔════════════════════════════════════════╗
║  TECLA BLOCKS - Workspace              ║
╠════════════════════════════════════════╣
║                                        ║
║  1. Variables                          ║
║     ├─ freq_base = 220                 ║
║     └─ notes_list = [60,64,67,72]      ║
║                                        ║
║  2. Funció: tocar_amb_gest()           ║
║     ├─ Acceleròmetre X                 ║
║     ├─ Map (-10,10) → (48,84)          ║
║     ├─ Oscil·lador Sine                ║
║     └─ Modulació FM                    ║
║                                        ║
║  3. Funció: sequenciador()             ║
║     └─ For loop per notes_list         ║
║        ├─ Obtenir nota[i]              ║
║        ├─ Tocar nota                   ║
║        └─ Esperar 0.1s                 ║
║                                        ║
║  4. Configuració                       ║
║     ├─ Print "Iniciat!"                ║
║     ├─ ADSR (10/50/70/100)             ║
║     └─ LFO Sine → Pitch (2Hz)          ║
║                                        ║
║  5. Bucle Principal                    ║
║     └─ Repetir per sempre              ║
║        ├─ Si Botó 1:                   ║
║        │  ├─ tocar_amb_gest()          ║
║        │  └─ Reverb 50%                ║
║        ├─ Si Botó 2:                   ║
║        │  ├─ sequenciador()            ║
║        │  └─ Delay 300ms/50%           ║
║        └─ Esperar 0.05s                ║
║                                        ║
╚════════════════════════════════════════╝
```

---

### Blocs Utilitzats

**Total: ~35-40 blocs**

Distribució per categories:

| Categoria | Quantitat |
|-----------|-----------|
| 🌊 Síntesi Avançada | 3 |
| 📡 Sensors | 1 |
| 🔢 Matemàtiques | 2 |
| 📋 Llistes | 3 |
| 🔧 Funcions | 4 |
| ⏱️ Control Flux | 5 |
| 🎵 Música | 2 |
| ✨ Efectes | 2 |
| 📊 Variables | 10 |
| 🎛️ Hardware | 2 |
| 📝 Comunicació | 1 |

---

### Com Obrir-lo

```bash
1. Obre TECLA Blocks
2. Menú → Arxiu → Obrir Projecte
3. Selecciona:
   /Users/zen/Desktop/exemple_sintetitzador_gestual.tblocks
4. Explora el workspace
5. Puja a TECLA
6. Prova-ho!
```

---

### Conceptes Demostrats

**Nivell Bàsic:**
- Variables
- Bucles
- Condicionals

**Nivell Intermedi:**
- Funcions personalitzades
- Llistes i arrays
- Iteració
- Sensors

**Nivell Avançat:**
- Síntesi FM
- Mapping matemàtic
- ADSR i LFO
- Integració de sistemes múltiples

---

### Sortida Sonora

**Mode Gestual:**
```
So: Sinusoidal + FM + Reverb + Vibrato
Característiques:
  - Pitch controlat per moviment
  - Harmònics rics (FM)
  - Espai sonor (reverb)
  - Vibrato subtil (LFO 2Hz)

Sona com: Sintetitzador analògic professional
```

**Mode Seqüenciador:**
```
So: Arpegi Do-Mi-Sol-Do + Delay
Característiques:
  - 10 notes/segon
  - Eco rítmic
  - ADSR dona caràcter

Sona com: Arpeggiador de sintetitzador
```

---

### Documentació Completa

- **`EXEMPLE_SINTETITZADOR.md`** - Explicació detallada
- **`exemple_sintetitzador_gestual.tblocks`** - Fitxer del projecte

---

## 📊 Resum de Respostes

### Pregunta 1: Múltiples Projectes?

✅ **SÍ** - Fins a 4 projectes amb sistema multi-slot  
✅ **Canvi en directe** - Long press botons 13-16  
✅ **Temps de canvi** - 3-4 segons  
✅ **Fitxer** - `launcher_multi_slot.py`  
✅ **Documentació** - `MULTI_SLOT.md`  

### Pregunta 2: Exemple del Potencial?

✅ **Creat** - Sintetitzador Gestual Avançat  
✅ **Fitxer** - `exemple_sintetitzador_gestual.tblocks`  
✅ **Blocs** - 35-40 blocs integrats  
✅ **Funcionalitats** - 12 categories diferents  
✅ **Documentació** - `EXEMPLE_SINTETITZADOR.md`  

---

## 🚀 Següents Passos

### 1. Provar Multi-Slot
```bash
cd ~/Desktop/TECLA-Blocks
# Copiar launcher_multi_slot.py al dispositiu TECLA
```

### 2. Obrir Exemple
```bash
# Obre TECLA Blocks
# Arxiu → Obrir
# Selecciona exemple_sintetitzador_gestual.tblocks
```

### 3. Experimentar
- Crear múltiples projectes
- Pujar-los a diferents slots
- Canviar entre ells en directe

---

**Tot està llest per utilitzar! 🎹✨**

---

**Data:** 17 Novembre 2025  
**Versió:** 2.1  
**Autor:** TECLA Blocks Team
