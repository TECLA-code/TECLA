# 📑 Índex de Categories - TECLA Blocks v2.0

## Resum ràpid de totes les categories de blocs

---

## 1. 🎵 Música Bàsica (4 blocs)
**Objectiu:** Introducció a la música per principiants

| Bloc | Descripció | Paràmetres |
|------|------------|------------|
| Tocar nota | Toca una nota MIDI individual | Nota (Do-Si), Velocitat, Durada |
| Tocar acord | Toca múltiples notes simultàniament | Acord (14 opcions), Durada |
| Tocar escala | Executa una escala musical completa | Tipus, Tonalitat |
| Canviar octava | Modifica l'octava de reproducció | Octava (1-7) |

---

## 2. 🌊 Síntesi Avançada (5 blocs)
**Objectiu:** Creació de sons sintètics professionals

| Bloc | Descripció | Paràmetres |
|------|------------|------------|
| Oscil·lador | Generador de forma d'ona bàsic | Tipus (6 opcions), Freq, Amp |
| LFO | Modulació automàtica de paràmetres | Forma, Velocitat, Target, Prof. |
| Envolvent ADSR | Controla l'evolució temporal del so | Attack, Decay, Sustain, Release |
| Modulació | Síntesi FM/AM/PM/Ring | Tipus, Carrier, Modulator, Depth |
| Waveshaper | Distorsió i saturació | Tipus (5 opcions), Quantitat |

**Aplicacions:** Sintetitzadors DX7-style, pads, baixos, efectes especials

---

## 3. 🎛️ Control Hardware (3 blocs)
**Objectiu:** Interacció amb el hardware TECLA

| Bloc | Descripció | Retorna |
|------|------------|---------|
| Llegir botó | Estat d'un botó (1-16) | Boolean |
| Llegir potenciòmetre | Valor d'un pot (X/Y/Z) | Number (0-127) |
| Quan es prem botó | Event de premsa de botó | - |

---

## 4. ✨ Efectes Àudio (3 blocs)
**Objectiu:** Processament d'àudio en temps real

| Bloc | Descripció | Paràmetres |
|------|------------|------------|
| Delay | Eco/retard | Temps, Feedback |
| Reverb | Reverberació | Quantitat |
| Filtre | Filtratge de freqüències | Tipus (3), Freqüència |

---

## 5. 💡 GPIO - Pins Digitals/Analògics (4 blocs)
**Objectiu:** Control d'entrada/sortida de pins

| Bloc | Descripció | Tipus |
|------|------------|-------|
| Escriure digital | Activa/desactiva un pin | Acció (HIGH/LOW) |
| Llegir digital | Llegeix estat d'un pin | Lectura (Boolean) |
| Escriure PWM | Control analògic variable | Acció (0-65535) |
| Llegir analògic | Llegeix valor ADC | Lectura (0-65535) |

**Aplicacions:** LEDs, motors, sensors, interfícies personalitzades

---

## 6. 📡 Sensors (3 blocs)
**Objectiu:** Lectura de sensors físics

| Bloc | Descripció | Retorna |
|------|------------|---------|
| Temperatura CPU | Temp. interna del μC | Number (°C) |
| Acceleròmetre | Moviment i orientació | Number (m/s²) |
| Distància | Sensor ultrasònic | Number (cm) |

**Aplicacions:** Instruments gestuals, control per moviment, teremín

---

## 7. ⏱️ Temps i Bucles (5 blocs)
**Objectiu:** Control del flux temporal

| Bloc | Descripció | Paràmetres |
|------|------------|------------|
| Esperar | Pausa l'execució | Segons |
| Repetir per sempre | Bucle infinit | - |
| Repetir N vegades | Bucle amb comptador | N |
| Mentre/Fins | Bucle condicional | Condició |
| Per (for) | Iteració amb variable | Des de, Fins, Pas |

---

## 8. 🔧 Lògica (8 blocs)
**Objectiu:** Control de flux i decisions

| Bloc | Descripció |
|------|------------|
| Si / Aleshores | Condicional simple |
| Si / Aleshores / Sinó | Condicional amb alternativa |
| Comparació | =, ≠, <, >, ≤, ≥ |
| Operació lògica | I, O |
| No (negació) | Inverteix Boolean |
| Boolean | Cert / Fals |
| Null | Valor nul |
| Ternari | Condició ? A : B |

---

## 9. 🔢 Matemàtiques (10 blocs)
**Objectiu:** Operacions matemàtiques

| Bloc | Descripció |
|------|------------|
| Número | Valor numèric constant |
| Aritmètica | +, -, ×, ÷, ^ |
| Aleatori | Random entre A i B |
| Escalar (map) | Converteix rang A→B |
| Limitar | Constrain entre min-max |
| Trigonomètrica | sin, cos, tan, etc. |
| Arrel/Abs/etc. | Operacions avançades |
| Arrodonir | Round, floor, ceil |

**Aplicacions:** LFOs matemàtics, escalar sensors, aleatorietat

---

## 10. 📝 Text (6 blocs)
**Objectiu:** Manipulació de strings

| Bloc | Descripció |
|------|------------|
| Text | String literal |
| Print | Mostra text |
| Unir | Concatenació |
| Longitud | Nombre de caràcters |
| Conté | Cerca substring |
| Append | Afegir a variable |

---

## 11. 📋 Llistes (6 blocs)
**Objectiu:** Col·leccions ordenades

| Bloc | Descripció |
|------|------------|
| Crear llista | [] buida |
| Crear amb elements | [a, b, c] |
| Afegir | Append |
| Obtenir | Get per índex |
| Longitud | len() |
| És buida? | isEmpty |

**Aplicacions:** Seqüenciadors, patrons, memòria d'acords

---

## 12. 📊 Variables
**Objectiu:** Emmagatzematge de dades

- Crear variable
- Assignar valor
- Obtenir valor
- Canviar per X

---

## 13. 🔧 Funcions (2 blocs)
**Objectiu:** Codi reutilitzable

| Bloc | Descripció |
|------|------------|
| Definir funció | Crea procediment |
| Cridar funció | Executa procediment |

**Avantatges:** Organització, modularitat, reutilització

---

## 14. 📡 Comunicació (4 blocs)
**Objectiu:** Interfície amb exterior

| Bloc | Descripció | Protocol |
|------|------------|----------|
| Serial Print | Envia text | USB |
| Serial Read | Rep text | USB |
| I2C Write | Envia dades | I2C |
| I2C Read | Rep dades | I2C |

**Aplicacions:** Depuració, OLED, sensors I2C, expansors GPIO

---

## 📊 Resum Numèric

| Categoria | Nombre de blocs |
|-----------|-----------------|
| Música Bàsica | 4 |
| Síntesi Avançada | 5 |
| Control Hardware | 3 |
| Efectes Àudio | 3 |
| GPIO | 4 |
| Sensors | 3 |
| Temps i Bucles | 5 |
| Lògica | 8 |
| Matemàtiques | 10 |
| Text | 6 |
| Llistes | 6 |
| Variables | ∞ (dinàmiques) |
| Funcions | 2 |
| Comunicació | 4 |
| **TOTAL** | **70+** |

---

## 🎯 Recomanacions per nivell

### 🟢 Principiants (6-8 anys)
- Música Bàsica
- Control Hardware (botons)
- Temps (Esperar, Repetir per sempre)
- Lògica bàsica (Si/Aleshores)

### 🟡 Intermedi (9-11 anys)
- Efectes Àudio
- Variables
- Llistes (seqüenciadors)
- Matemàtiques bàsiques
- GPIO (LEDs)

### 🟠 Avançat (12-14 anys)
- Síntesi Avançada
- Sensors
- Funcions personalitzades
- I2C
- Matemàtiques avançades

### 🔴 Expert (15+ anys / Adults)
- Tot el conjunt
- Projectes complexos amb múltiples categories
- Síntesi FM
- IoT Musical

---

**Versió:** 2.0  
**Última actualització:** Novembre 2025
