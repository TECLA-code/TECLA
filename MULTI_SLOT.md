# 🎮 Sistema Multi-Slot - Múltiples Projectes TECLA Blocks

## 🎯 Què és el Sistema Multi-Slot?

Permet tenir **fins a 4 projectes TECLA Blocks diferents** al mateix dispositiu i canviar entre ells amb botons.

---

## 📦 Escenaris d'Ús

### Exemple 1: Escola de Música
```
Slot 1 (Botó 16) → Projecte "Acords Jazz"
Slot 2 (Botó 15) → Projecte "Seqüenciador Rítmic"
Slot 3 (Botó 14) → Projecte "Síntesi FM"
Slot 4 (Botó 13) → Projecte "Control Gestual"
```

### Exemple 2: Concert en Directe
```
Slot 1 → Cançó 1 (intro amb efectes)
Slot 2 → Cançó 2 (seqüenciador)
Slot 3 → Cançó 3 (sintetitzador)
Slot 4 → Improvisació (control lliure)
```

### Exemple 3: Classe STEAM
```
Slot 1 → Projecte amb Música
Slot 2 → Projecte amb Sensors
Slot 3 → Projecte amb LEDs
Slot 4 → Projecte Final (combinat)
```

---

## 🔧 Com Funciona

### Arquitectura
```
CIRCUITPY/
├── code.py                  ← Launcher Multi-Slot
├── tecla_main.py            ← TECLA Original
├── tecla_blocks_1.py        ← Projecte Slot 1 ⭐
├── tecla_blocks_2.py        ← Projecte Slot 2 ⭐
├── tecla_blocks_3.py        ← Projecte Slot 3 ⭐
├── tecla_blocks_4.py        ← Projecte Slot 4 ⭐
└── modes/, effects/, etc.   ← TECLA
```

### Selecció de Projecte
```
Encendre TECLA
    ↓
Long press (1.5s) en un botó:
    ├─→ Botó 16 → Projecte 1
    ├─→ Botó 15 → Projecte 2
    ├─→ Botó 14 → Projecte 3
    ├─→ Botó 13 → Projecte 4
    └─→ Cap botó → TECLA Normal
```

**Feedback:** LED pisca durant comprovació, queda encès quan carrega

---

## ⚙️ Configuració

### Pas 1: Instal·lar Launcher Multi-Slot

```bash
# 1. Connecta TECLA via USB
# 2. Obre CIRCUITPY

# 3. Si ja tens launcher simple:
#    Substitueix code.py pel launcher_multi_slot.py

# 4. Si no tens launcher:
#    a) Renombra code.py → tecla_main.py
#    b) Copia launcher_multi_slot.py → code.py

# 5. Desconnecta i prova
```

### Pas 2: Crear Projectes

1. Obre **TECLA Blocks**
2. Crea el teu primer projecte (ex: Sintetitzador)
3. Guarda com "Projecte_Sintetitzador.tblocks"
4. Puja a TECLA
   - L'app detectarà múltiples slots disponibles
   - Preguntarà: "A quin slot vols pujar?" 
   - Escull Slot 1, 2, 3 o 4

Repeteix per cada projecte que vulguis tenir.

---

## 🎮 Ús en Directe

### Escenari: Concert

**Preparació (abans de pujar a l'escenari):**
```
1. Connecta TECLA
2. Verifica els 4 projectes:
   - Slot 1: Intro
   - Slot 2: Vers
   - Slot 3: Estribillo
   - Slot 4: Solo
3. Prova cada slot ràpidament
```

**Durant el concert:**
```
Entre cançó i cançó:
1. Reinicia TECLA
2. Long press Botó corresponent (15, 16, 14, 13)
3. Espera 1.5s (LED pisca)
4. Projecte carregat!
```

**Temps de canvi:** ~3-4 segons (reiniciar + long press)

---

## 📋 Gestió de Projectes

### Actualitzar un Projecte

1. Obre el projecte amb TECLA Blocks
2. Modifica'l
3. Puja seleccionant el mateix slot
4. Sobreescriu l'anterior

### Eliminar un Projecte

```bash
# Connecta TECLA via USB
# Elimina el fitxer corresponent:
rm /Volumes/CIRCUITPY/tecla_blocks_2.py
```

### Copiar entre Slots

```bash
# Duplicar Projecte 1 al Slot 3:
cp /Volumes/CIRCUITPY/tecla_blocks_1.py \
   /Volumes/CIRCUITPY/tecla_blocks_3.py
```

---

## 🎓 Per Educació

### Workflow per Alumnes

**Setmana 1: Aprendre bàsics**
```
Tots els alumnes treballen en Slot 1
- Projecte simple: Tocar notes amb botons
```

**Setmana 2: Sensors**
```
Tots treballen en Slot 2
- Projecte: Control amb acceleròmetre
- Slot 1 encara funciona (projecte anterior conservat)
```

**Setmana 3: Síntesi**
```
Slot 3 → Projecte síntesi FM
Slots 1-2 → Encara accessibles
```

**Setmana 4: Projecte final**
```
Slot 4 → Combina tot el après
Poden comparar amb slots anteriors
```

### Avantatges Educatius

- ✅ **Progressió visible** - Els alumnes veuen el seu progrés
- ✅ **No perden feina** - Projectes anteriors conservats
- ✅ **Comparació fàcil** - Poden alternar entre versions
- ✅ **Portfolio automàtic** - 4 projectes al dispositiu

---

## 🔄 Canvi Ràpid en Directe

### Opció A: Reiniciar (Recomanat)

**Passos:**
1. Reinicia el dispositiu (botó reset o apagar/encendre)
2. Long press botó del nou slot
3. ~3-4 segons total

**Pros:**
- ✅ Més segur
- ✅ Reset complet de l'estat
- ✅ No conflictes de memòria

**Contras:**
- ⚠️ S'atura la música actual
- ⚠️ Cal esperar reinici

### Opció B: Hot-Swap (Futura Implementació)

Idea per versió futura:
```python
# Durant execució, detectar combinació especial
# Ex: Potenciòmetre Z a 0 + Long press botó
# → Canvia a un altre slot sense reiniciar
```

**Estat:** No implementat (v2.1)  
**Raó:** Complexitat tècnica (gestió de memòria, MIDI cleanup, etc.)

---

## 📊 Comparació amb Alternatives

### vs Sistema Simple (1 Projecte)

| Aspecte | Simple | Multi-Slot |
|---------|--------|------------|
| **Projectes simultanis** | 1 | 4 |
| **Canvi de projecte** | Re-upload | Long press |
| **Temps de canvi** | 30s | 3-4s |
| **Ideal per** | Aprenentatge | Concert/Producció |

### vs Sistema de Carpetes

| Aspecte | Carpetes | Multi-Slot |
|---------|----------|------------|
| **Complexitat** | Alta | Baixa |
| **Selecció** | Menu/Serial | Botó físic |
| **Velocitat** | Variable | 3-4s |
| **Fiabilitat** | Mitjana | Alta |

---

## ⚡ Configuració Avançada

### Personalitzar Botons

Edita `launcher_multi_slot.py`:

```python
BUTTONS = {
    16: {'pin': board.GP14, 'file': 'projecte_musica.py', 'name': 'Música'},
    15: {'pin': board.GP13, 'file': 'projecte_sensors.py', 'name': 'Sensors'},
    14: {'pin': board.GP12, 'file': 'projecte_llums.py', 'name': 'LEDs'},
    13: {'pin': board.GP11, 'file': 'projecte_mix.py', 'name': 'Mix'}
}
```

### Ampliar a 8 Slots

```python
BUTTONS = {
    16: {...},
    15: {...},
    # ... fins a 8 botons
    9: {'pin': board.GP4, 'file': 'tecla_blocks_8.py', 'name': 'Projecte 8'}
}
```

### Long Press Personalitzat

```python
# Fer el long press més curt (1 segon)
LONG_PRESS_DURATION = 1.0

# O més llarg (2 segons - més segur)
LONG_PRESS_DURATION = 2.0
```

---

## 🐛 Troubleshooting

### "ERROR: tecla_blocks_X.py no trobat"

**Causa:** No has pujat cap projecte a aquest slot

**Solució:**
1. Obre TECLA Blocks
2. Crea/obre un projecte
3. Puja seleccionant el slot X

### LED pisca però no carrega

**Causa:** Long press no suficientment llarg

**Solució:**
- Mantén el botó premut fins que vegi el missatge de càrrega
- Compta fins a 10 piscades del LED

### Vull tornar a launcher simple

**Solució:**
```bash
# Substitueix code.py pel launcher_code.py original
# O elimina tots els tecla_blocks_X.py menys l'1
```

---

## 🎯 Millors Pràctiques

### Per Concerts

1. **Prova prèvia:** Verifica tots els slots abans
2. **Llista de setlist:** Anota quin botó correspon a cada cançó
3. **Backup:** Guarda còpies dels .tblocks a l'ordinador
4. **Reset entre cançons:** Més segur que hot-swap

### Per Educació

1. **Nomenclatura clara:** Slot 1 = Bàsic, Slot 2 = Intermedi, etc.
2. **Progressió:** Cada slot més complex que l'anterior
3. **Demostració:** Mostra com canviar de slot a classe
4. **Documentació:** Cada alumne documenta què té a cada slot

### Per Desenvolupament

1. **Slot 1:** Versió estable
2. **Slots 2-3:** Experiments
3. **Slot 4:** Última versió en desenvolupament

---

## 📈 Roadmap

### v2.2 - Multi-Slot Avançat
- [ ] Selector visual (pantalla OLED)
- [ ] Noms de projecte customitzables
- [ ] Metadata (autor, data, descripció)

### v2.3 - Hot-Swap
- [ ] Canvi sense reiniciar (experimental)
- [ ] Gestió de memòria avançada
- [ ] Crossfade entre projectes

### v3.0 - Cloud Sync
- [ ] Sincronitzar projectes amb el núvol
- [ ] Compartir entre dispositius
- [ ] Biblioteca de projectes comunitària

---

## 🎉 Resum

### Sistema Multi-Slot permet:

- ✅ **4 projectes** al mateix dispositiu
- ✅ **Canvi ràpid** amb long press (3-4s)
- ✅ **Feedback visual** (LED)
- ✅ **Ideal per concerts** i educació
- ✅ **Compatible** amb TECLA original
- ✅ **Fàcil de configurar** (5 minuts)

**Transforma TECLA en un instrument multi-funcional! 🎹🎮**

---

**Versió:** 2.1  
**Data:** 17 Novembre 2025  
**Estat:** Implementat i provat
