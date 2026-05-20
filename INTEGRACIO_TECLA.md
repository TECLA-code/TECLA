# 🔗 Integració TECLA Blocks ↔ TECLA App

## Problema a Resoldre

Actualment:
- **TECLA App** té tots els modes, efectes, configuració (code.py)
- **TECLA Blocks** genera codi que sobreescriu code.py
- ⚠️ **Conflicte:** Quan puges des de Blocks, perds TECLA

---

## 💡 Solució Proposada: Sistema Dual amb Selector

### Arquitectura Nova

```
CIRCUITPY/
├── code.py                 ← BOOT SELECTOR (NOU)
├── tecla_main.py           ← TECLA Original (renombrat)
├── tecla_blocks.py         ← Codi generat per TECLA Blocks
├── modes/                  ← Modes TECLA
├── effects/                ← Efectes TECLA
├── core/
└── config/
```

### Funcionament

#### 1. Boot Selector (`code.py`)

```python
"""
TECLA - Boot Mode Selector
Permet escollir entre TECLA Principal o TECLA Blocks
"""
import board
import digitalio
import time

# LED d'estat (opcional)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Botó selector (Botó 16)
selector_button = digitalio.DigitalInOut(board.GP14)
selector_button.direction = digitalio.Direction.INPUT
selector_button.pull = digitalio.Pull.DOWN

def boot_animation():
    """Animació durant selecció"""
    for _ in range(3):
        led.value = True
        time.sleep(0.1)
        led.value = False
        time.sleep(0.1)

def select_mode():
    """Selecciona quin mode executar"""
    print("╔══════════════════════════════════╗")
    print("║   TECLA - Boot Mode Selector    ║")
    print("╚══════════════════════════════════╝")
    print()
    print("🔵 Mode per defecte: TECLA Principal")
    print("🟢 Prem Botó 16 per: TECLA Blocks")
    print()
    print("Esperant selecció...")
    
    boot_animation()
    time.sleep(1.5)  # Temps per prémer
    
    if selector_button.value:
        # Mode TECLA Blocks
        print("\n✅ Mode TECLA Blocks seleccionat")
        print("   (Programa generat amb blocs)\n")
        led.value = True
        time.sleep(0.5)
        
        try:
            import tecla_blocks
        except ImportError:
            print("❌ Error: tecla_blocks.py no trobat")
            print("   Puja un programa des de TECLA Blocks primer")
            while True:
                time.sleep(1)
    else:
        # Mode TECLA Principal
        print("\n✅ Mode TECLA Principal seleccionat")
        print("   (Tots els modes i configuració)\n")
        led.value = False
        
        try:
            import tecla_main
        except ImportError:
            print("❌ Error: tecla_main.py no trobat")
            while True:
                time.sleep(1)

# Executar selector
if __name__ == "__main__":
    select_mode()
```

---

## 🔄 Workflow Proposat

### Per a Professors

#### Configuració Inicial (UNA VEGADA)
1. Renombrar `code.py` → `tecla_main.py`
2. Copiar el nou `code.py` (boot selector) al dispositiu
3. Verificar que funciona (encendre sense prémer botó)

#### Ús Diari
- **Concert/Ús Professional:** Encendre normalment → TECLA amb tots els modes
- **Classe de Programació:** Mantenir Botó 16 + Encendre → Mode educatiu

### Per a Alumnes

#### Crear Programa amb TECLA Blocks
1. Obrir TECLA Blocks a l'ordinador
2. Crear programa amb blocs
3. Connectar TECLA via USB
4. Prémer "⬆️ Pujar a TECLA"
   - L'app detecta l'estructura i guarda com `tecla_blocks.py`
   - NO sobreescriu `code.py` ni `tecla_main.py`

#### Executar el Programa
1. Desconnectar TECLA
2. **Mantenir Botó 16 premut**
3. Encendre el dispositiu
4. Veure missatge "Mode TECLA Blocks seleccionat"
5. El programa s'executa!

#### Tornar a Mode Normal
1. Reiniciar sense prémer Botó 16
2. TECLA funciona normalment

---

## 🎯 Avantatges del Sistema

### Educatius
- ✅ Els alumnes **no trenquen res** - TECLA sempre funcional
- ✅ **Experimentació segura** - poden provar sense por
- ✅ **Transició natural** - del mode educatiu al professional
- ✅ **Múltiples alumnes** - poden compartir dispositiu

### Tècnics
- ✅ **Sense conflictes** - Dos sistemes independents
- ✅ **Reversible** - Sempre pots tornar a TECLA
- ✅ **Actualitzacions** - TECLA i Blocks s'actualitzen separadament
- ✅ **Depuració fàcil** - Saps quin codi s'executa

### Pràctics
- ✅ **Un sol dispositiu** - Per classe i concert
- ✅ **Canvi ràpid** - 2 segons entre modes
- ✅ **Visual** - LED indica el mode actiu

---

## 🔧 Modificacions a TECLA Blocks (App Electron)

### Actualització del Upload

```javascript
// main.js - Modificar la funció d'upload

async function uploadToDevice(pythonCode, portPath) {
  try {
    const circuitPyPath = await findCircuitPythonDrive();
    
    if (circuitPyPath) {
      // Detectar si té boot selector
      const codeMain = path.join(circuitPyPath, 'tecla_main.py');
      const hasBootSelector = await fileExists(codeMain);
      
      if (hasBootSelector) {
        // Sistema dual - guardar com tecla_blocks.py
        const targetPath = path.join(circuitPyPath, 'tecla_blocks.py');
        await fs.writeFile(targetPath, pythonCode, 'utf8');
        
        return {
          success: true,
          method: 'dual',
          message: 'Programa pujat a tecla_blocks.py!\n\n' +
                   '🎮 Per executar:\n' +
                   '1. Mantén Botó 16 premut\n' +
                   '2. Encén el dispositiu\n\n' +
                   '💡 Per tornar a TECLA: Reinicia sense prémer'
        };
      } else {
        // Sistema simple - guardar com code.py
        const targetPath = path.join(circuitPyPath, 'code.py');
        await fs.writeFile(targetPath, pythonCode, 'utf8');
        
        return {
          success: true,
          method: 'simple',
          message: 'Programa pujat correctament!\n\n' +
                   '⚠️ Consell: Configura el Boot Selector\n' +
                   'per no perdre els modes TECLA'
        };
      }
    }
    
    return { 
      success: false, 
      error: 'No s\'ha trobat el dispositiu CIRCUITPY'
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}
```

---

## 📋 Checklist d'Implementació

### Fase 1: Boot Selector (Prioritat Alta)
- [ ] Crear `code.py` amb selector de mode
- [ ] Renombrar `main.py` original → `tecla_main.py`
- [ ] Provar amb dispositiu real
- [ ] Documentar per professors

### Fase 2: Integració TECLA Blocks (Prioritat Alta)
- [ ] Modificar funció upload a `main.js`
- [ ] Detectar sistema dual automàticament
- [ ] Guardar com `tecla_blocks.py`
- [ ] Mostrar instruccions d'ús a l'usuari

### Fase 3: Millores UI (Prioritat Mitjana)
- [ ] Botó "Configurar Boot Selector" a TECLA Blocks
- [ ] Wizard de configuració inicial
- [ ] Indicador visual del mode detectat
- [ ] Tutorial interactiu

### Fase 4: Funcions Avançades (Prioritat Baixa)
- [ ] Múltiples slots de programes (`blocks_1.py`, `blocks_2.py`, etc.)
- [ ] Selector de programa via botons (no només dual)
- [ ] Backup automàtic abans d'upload
- [ ] Sistema de versions

---

## 🎓 Casos d'Ús

### Cas 1: Classe de Primària
**Situació:** 20 alumnes, 5 dispositius TECLA

**Workflow:**
1. Professor configura Boot Selector als 5 dispositius (una vegada)
2. Alumnes programen per parelles amb TECLA Blocks
3. Cada parella puja el seu programa
4. Per executar: Mantenen Botó 16 + Encenen
5. Al final de classe: Reinicien sense botó → TECLA normal

### Cas 2: Concert
**Situació:** Músic professional amb TECLA

**Workflow:**
1. Durant assaig: Prova modes TECLA (encendre normal)
2. Vol experimentar amb síntesi FM (Blocks)
3. Crea programa ràpid amb TECLA Blocks
4. Puja amb Botó 16
5. Si no agrada: Reinicia → Tots els modes disponibles

### Cas 3: Taller STEAM
**Situació:** Workshop de 4 hores

**Mati:** Aprendre TECLA Blocks
- Mode Blocks (amb Botó 16)
- Experimentació lliure

**Tarda:** Modes avançats TECLA
- Reiniciar a mode normal
- Explorar Cascada, Jazz Chords, etc.

**Tot en el mateix dispositiu!**

---

## 🔜 Roadmap Futur

### v2.1 - Integració Bàsica
- ✅ Boot Selector funcional
- ✅ Upload dual des de TECLA Blocks

### v2.2 - Multi-Slot
- [ ] Múltiples programes guardats
- [ ] Selector de programa via botons

### v2.3 - Híbrid Avançat
- [ ] Modes Blocks integrats dins TECLA
- [ ] `mode_custom_blocks.py` com a mode regular
- [ ] Pots afegir efectes TECLA al codi Blocks

### v3.0 - Ecosistema Complet
- [ ] TECLA Blocks genera modes compatibles
- [ ] Editor visual de configuració TECLA
- [ ] Sincronització cloud de programes

---

## 📞 Suport Tècnic

### Per a Professors
Si tens problemes amb la configuració del Boot Selector:
1. Connecta TECLA via USB
2. Obre el drive CIRCUITPY
3. Fes backup de `code.py` actual
4. Copia el nou `code.py` (selector)
5. Renombra l'antic `code.py` → `tecla_main.py`

### Per a Alumnes
Si el programa no s'executa:
1. Verifica que s'ha pujat correctament
2. Comprova que mantens Botó 16 durant arrancar
3. Mira els missatges al terminal USB

---

**Versió:** 2.1 (Proposta)  
**Estat:** Disseny completat - Pendent implementació  
**Prioritat:** Alta (educació)
