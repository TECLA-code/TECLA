# Canvis pendents al dispositiu TECLA

Quan `/Volumes/TECLA` estigui muntat, aplica aquests canvis manualment
(o copia `modes/kbd_pots.py` via dev.sh, que ja és l'única que s'actualitzarà automàticament).

---

## 1. `modes/kbd_pots.py`  ← JA ACTUALITZAT LOCALMENT
`dev.sh` el sincronitzarà automàticament al executar-lo amb el dispositiu connectat.

---

## 2. `modes/mode_keyboard.py`  ← canvis manuals necessaris

### A `__init__` i `setup()`, afegir càrrega de les noves funcions de pot:

```python
# ── Chord pot functions ─────────────────────────────────
cpf = self.config_manager.get_chord_potentiometer_functions() if self.config_manager else {}
self.chord_pot_x_function = cpf.get('chord_pot_x', "Tipologia d'Acords")
self.chord_pot_y_function = cpf.get('chord_pot_y', "Inversió d'Acord")
self.chord_pot_z_function = cpf.get('chord_pot_z', 'Modulació')

# ── Neg harmony pot functions ────────────────────────────
npf = self.config_manager.get_neg_potentiometer_functions() if self.config_manager else {}
self.neg_pot_x_function = npf.get('neg_pot_x', "Eix d'Harmonia")
self.neg_pot_y_function = npf.get('neg_pot_y', "Inversió d'Acord")
self.neg_pot_z_function = npf.get('neg_pot_z', 'Modulació')
```

### Verificar que existeixin els atributs de mode (probablement ja hi són):
- `self.neg_harmony_active` → boolea (True quan H.Neg activada)
- `self.chord_mode_active`  → boolea (True quan mode acords actiu)
- `self.available_chord_types` → llista de tipus d'acords disponibles
- `self.chord_type_index`   → índex del tipus d'acord actiu

---

## 3. `core/config_manager.py`  ← canvis manuals necessaris

Afegir els dos mètodes (seguint el patró de `get_neg_harmony_axes`):

```python
def get_chord_potentiometer_functions(self):
    return self.config.get('chord_potentiometer_functions', {})

def get_neg_potentiometer_functions(self):
    return self.config.get('neg_potentiometer_functions', {})
```

---

## Nota sobre kbd_pots.py → atributs segurs

`update_parameters` usa `getattr(kbd, 'neg_harmony_active', False)` i
`getattr(kbd, 'chord_mode_active', False)`, de manera que si els atributs
no existeixen, simplament no canvia de capa (sense crash).
Les funcions `apply_chord_pot_function` i `apply_neg_pot_function` també
usen `getattr` amb defaults → funcionaran amb els valors per defecte fins
que es configurin des de l'app.
