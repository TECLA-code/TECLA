# ✅ Exemples Corregits - TECLA Blocks

## 🔧 Problema Solucionat

L'exemple anterior tenia un format massa complex que no coincidia amb el format real de TECLA Blocks.

**Format incorrecte (antic):**
```json
{
  "workspace": {
    "blocks": { ... estructura complexa ... }
  }
}
```

**Format correcte (nou):**
```json
{
  "name": "Nom del projecte",
  "version": "1.0",
  "blocks": "<xml>...</xml>",
  "timestamp": "2025-11-17T12:00:00.000Z"
}
```

---

## 📦 3 Nous Exemples Creats

### 1. 🎵 **exemple_simple_music.tblocks**
Exemple bàsic per començar.

**Què fa:**
- ✅ Defineix una variable `freq_base`
- ✅ Toca 3 notes: Do → Mi → Sol
- ✅ Amb pauses de 0.5s entre notes

**Blocs utilitzats:**
- Variables (assignar valor)
- Tocar nota (3x)
- Esperar (2x)

**Nivell:** Principiant  
**Durada:** 1.5 segons  

**Com provar-lo:**
1. Obre TECLA Blocks
2. Arxiu → Obrir Projecte
3. Selecciona `exemple_simple_music.tblocks`
4. Veuràs els blocs al workspace
5. Puja a TECLA

---

### 2. 🎮 **exemple_avançat_sensors.tblocks**
Control gestual amb acceleròmetre.

**Què fa:**
- ✅ Print missatge d'inici
- ✅ Configura envolvent ADSR
- ✅ Bucle infinit:
  - Llegeix acceleròmetre (eix X)
  - Escala valor a notes MIDI (48-84)
  - Si Botó 1 premut:
    - Oscil·lador sinusoidal amb freq. variable
    - Efecte Reverb
  - Espera 0.05s

**Blocs utilitzats:**
- Serial Print
- Envolvent ADSR
- Repetir per sempre
- Variables
- Sensor acceleròmetre
- Escalar valor (map)
- Condicional (if)
- Llegir botó
- Oscil·lador
- Efecte Reverb
- Esperar

**Nivell:** Avançat  
**Conceptes:** Sensors, síntesi, control gestual

**Com usar-lo:**
1. Puja a TECLA
2. Mou el dispositiu (eix X)
3. Prem Botó 1 per escoltar
4. El pitch canvia amb el moviment

---

### 3. 🎹 **exemple_sequencer.tblocks**
Seqüenciador amb llistes.

**Què fa:**
- ✅ Crea llista de 4 notes: [60, 64, 67, 72]
- ✅ Print missatge
- ✅ Bucle infinit:
  - Itera per cada nota de la llista
  - Toca la nota
  - Pausa 0.25s
  - Repeteix seqüència

**Blocs utilitzats:**
- Variables
- Crear llista amb elements
- Serial Print
- Repetir per sempre
- Bucle for
- Longitud de llista
- Obtenir element de llista
- Tocar nota
- Esperar

**Nivell:** Intermedi  
**Conceptes:** Llistes, iteració, seqüenciador

**Resultat sonor:**
```
Do (60) → Mi (64) → Sol (67) → Do alt (72) → [repeteix]
Velocitat: 4 notes/segon
```

---

## 📂 Ubicació

Tots els exemples són al **Desktop**:
```
~/Desktop/
├── exemple_simple_music.tblocks       ← Bàsic
├── exemple_avançat_sensors.tblocks    ← Avançat
└── exemple_sequencer.tblocks          ← Intermedi
```

---

## 🚀 Com Obrir els Exemples

### Mètode 1: Des de l'aplicació (Recomanat)
```
1. Obre TECLA Blocks
2. Menú: Arxiu → Obrir Projecte
3. Navega a Desktop
4. Selecciona un dels exemples
5. Click "Obrir"
```

### Mètode 2: Arrossegar i deixar anar
```
1. Obre TECLA Blocks
2. Arrossega el fitxer .tblocks
3. Deixa'l anar sobre la finestra de l'app
```

**Si no funciona:** Usa el Mètode 1

---

## 🎯 Progressió d'Aprenentatge

### Pas 1: Exemple Simple
```
exemple_simple_music.tblocks
  ↓
Aprèn: Variables, tocar notes, pauses
```

### Pas 2: Exemple Seqüenciador
```
exemple_sequencer.tblocks
  ↓
Aprèn: Llistes, bucles for, iteració
```

### Pas 3: Exemple Avançat
```
exemple_avançat_sensors.tblocks
  ↓
Aprèn: Sensors, síntesi, control gestual
```

---

## 🔍 Comparació

| Exemple | Blocs | Nivell | Conceptes Clau |
|---------|-------|--------|----------------|
| **Simple Music** | ~6 | Bàsic | Variables, notes |
| **Sequencer** | ~15 | Intermedi | Llistes, iteració |
| **Sensors** | ~20 | Avançat | Sensors, síntesi, control |

---

## 📝 Verificar Format

Si vols crear els teus propis exemples, aquest és el format correcte:

```json
{
  "name": "Nom del Projecte",
  "version": "1.0",
  "blocks": "<xml xmlns=\"https://developers.google.com/blockly/xml\">...blocs XML...</xml>",
  "timestamp": "2025-11-17T12:00:00.000Z"
}
```

**Important:** `blocks` és un string XML, no un objecte JSON!

---

## 🐛 Troubleshooting

### L'exemple no s'obre
1. Comprova que el fitxer té extensió `.tblocks`
2. Prova obrir des de: Arxiu → Obrir Projecte
3. No arrosseguis, usa el diàleg d'obertura

### Els blocs no apareixen
1. Mira la consola (Mode Dev: `./start-dev.sh`)
2. Comprova format JSON amb: `cat fitxer.tblocks | python -m json.tool`

### Error de format
```bash
# Validar JSON
cat exemple_simple_music.tblocks | python -m json.tool
```

---

## ✅ Verificació

He provat que els 3 exemples:
- ✅ Tenen el format correcte
- ✅ XML Blockly vàlid
- ✅ JSON ben format
- ✅ Es poden obrir amb TECLA Blocks

---

## 🎓 Per Professors

### Distribució a Classe
```bash
# Copiar exemples als ordinadors
cp ~/Desktop/exemple_*.tblocks /Users/Shared/TECLA-Exemples/

# Els alumnes poden obrir des de /Users/Shared
```

### Exercicis
1. **Modificar Simple:** Canviar notes Do-Mi-Sol → Do-Fa-La
2. **Ampliar Sequencer:** Afegir més notes a la llista
3. **Experimentar Sensors:** Canviar rang de mapping

---

## 📚 Documentació Relacionada

- **EXEMPLE_SINTETITZADOR.md** - Guia conceptual (encara vàlida)
- **README.md** - Documentació principal
- **GUIA_RAPIDA.md** - Tutorial bàsic

---

**Versió:** 2.1.1  
**Data:** 17 Novembre 2025  
**Format:** XML Blockly (correcte)
