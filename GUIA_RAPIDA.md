# 🚀 Guia Ràpida - TECLA Blocks

## Per començar ara mateix:

### 1️⃣ Executar l'aplicació

```bash
cd ~/Desktop/TECLA-Blocks
npm start
```

L'aplicació s'obrirà en uns segons!

### 2️⃣ Crear el teu primer programa

1. **Arrossega un bloc** "🎵 Tocar nota" des del menú esquerre
2. **Canvia la nota** a la que vulguis (Do, Re, Mi...)
3. **Veure el codi generat** al panell dret

### 3️⃣ Pujar-ho al teu TECLA

1. **Connecta el dispositiu TECLA** via USB
2. **Espera** que aparegui el drive `CIRCUITPY`
3. **Prem el botó** "⬆️ Pujar a TECLA"
4. **El programa s'executarà** automàticament!

---

## 🎓 Tutorials per alumnes

### Tutorial 1: La meva primera melodia

**Objectiu:** Aprendre a tocar notes individuals

**Blocs necessaris:**
- 3x "Tocar nota"

**Passos:**
1. Arrossega 3 blocs "Tocar nota"
2. Connecta'ls un darrere l'altre
3. Configura: Do → Re → Mi
4. Puja-ho al TECLA i escolta!

**Conceptes apresos:**
- Seqüència d'instruccions
- Paràmetres (nota, velocitat, durada)

---

### Tutorial 2: Botó màgic

**Objectiu:** Fer que un botó toqui un acord

**Blocs necessaris:**
- 1x "Repetir per sempre"
- 1x "Quan es prem botó 1"
- 1x "Tocar acord Do Major"

**Passos:**
1. Col·loca el bloc "Repetir per sempre"
2. Dins, posa "Quan es prem botó 1"
3. Dins, posa "Tocar acord Do Major"
4. Puja-ho al TECLA
5. Prem el botó 1 del dispositiu!

**Conceptes apresos:**
- Bucles infinits
- Events (prémer botó)
- Condicionals

---

### Tutorial 3: Controlador amb potenciòmetre

**Objectiu:** Controlar la velocitat amb el potenciòmetre

**Blocs necessaris:**
- 1x "Variables - definir velocitat"
- 1x "Llegir potenciòmetre X"
- 1x "Tocar nota" (usar variable velocitat)

**Passos:**
1. Crea variable "velocitat"
2. Assigna: velocitat = Llegir pot X
3. Toca nota amb velocitat=velocitat
4. Mou el potenciòmetre per canviar el volum!

**Conceptes apresos:**
- Variables
- Entrada analògica
- Paràmetres dinàmics

---

## 🎯 Reptes progressius

### Nivell 1: Bàsic
- ✅ Tocar una escala completa
- ✅ Fer una melodia de 5 notes
- ✅ Fer que un botó toqui una nota

### Nivell 2: Intermedi
- 🎵 Crear un arpeggio amb bucle
- 🎸 Assignar diferents acords a 4 botons
- 🎛️ Usar 2 potenciòmetres (velocitat + efecte)

### Nivell 3: Avançat
- 🎹 Crear un mini seqüenciador de 8 passos
- 🎼 Sistema d'enregistrament i reproducció
- 🎚️ Efectes en temps real amb potenciòmetres

---

## 📊 Per a professors

### Integració curricular (Primària)

#### **Matemàtiques**
- Seqüències numèriques → Seqüències de notes
- Patrons i repetició → Bucles
- Operacions bàsiques → Control de paràmetres

#### **Música**
- Notes musicals i escales
- Ritme i tempo
- Acords i harmonia

#### **Tecnologia/Robòtica**
- Algorismes i programació
- Sensors i actuadors (botons, potenciòmetres)
- Pensament computacional

### Avaluació suggerida

**Criteri 1:** Comprensió de seqüències
- El programa executa instruccions en ordre correcte

**Criteri 2:** Ús de bucles
- Utilitza repeticions per optimitzar el codi

**Criteri 3:** Condicionals i events
- Respon correctament a entrades (botons)

**Criteri 4:** Creativitat
- Crea composicions musicals originals

---

## 🛠️ Solució de problemes

### No es detecta el dispositiu TECLA

**Comprovacions:**
1. ✓ Cable USB connectat correctament
2. ✓ Dispositiu encès
3. ✓ Drive `CIRCUITPY` visible a l'ordinador
4. ✓ Fitxer `boot_out.txt` present al drive

**Solució:** Desconnecta i torna a connectar el dispositiu

### El codi no s'executa

**Comprovacions:**
1. ✓ Fitxer `code.py` al drive CIRCUITPY
2. ✓ No hi ha errors de sintaxi (panell de codi)
3. ✓ El dispositiu s'ha reiniciat després de pujar

**Solució:** Prem el botó RESET del dispositiu

### L'aplicació no s'obre

**Comprovacions:**
1. ✓ Node.js instal·lat (`node --version`)
2. ✓ Dependències instal·lades (`npm install`)
3. ✓ Port 3000 no ocupat

**Solució:** Tanca altres aplicacions Electron i torna a intentar

---

## 📞 Suport

**Documentació completa:** README.md  
**Exemples:** Carpeta `examples/` (properament)  
**Comunitat:** [Forum TECLA](https://tecla-project.org/forum)

---

**Versió:** 1.0.0  
**Última actualització:** Novembre 2025
