# ⚙️ Configuració del TECLA Launcher

## 🎯 Objectiu
Permetre que **TECLA** i **TECLA Blocks** convisquin sense modificar el codi de TECLA.

---

## 📋 Passos (5 minuts)

### Pas 1: Connectar TECLA
1. Connecta TECLA via USB a l'ordinador
2. Hauria d'aparèixer el drive **CIRCUITPY**
3. Obre'l amb el Finder

### Pas 2: Backup (Recomanat)
1. Copia TOT el contingut de CIRCUITPY a una carpeta al Desktop
2. Anomena-la `TECLA_BACKUP_[data]`
3. Així sempre pots recuperar-ho

### Pas 3: Renombrar code.py
1. Dins CIRCUITPY, cerca el fitxer `code.py`
2. Renombra'l a **`tecla_main.py`**
   - Opció 1: Click dret → Rename
   - Opció 2: Seleccionar i prémer Enter

**Important:** Aquest fitxer conté tot el codi de TECLA. NO el modifiquem, només el renombrem.

### Pas 4: Copiar el Launcher
1. Obre la carpeta `TECLA-Blocks`
2. Cerca el fitxer `launcher_code.py`
3. Copia'l a CIRCUITPY
4. Renombra'l a **`code.py`**

### Pas 5: Verificar
Estructura final dins CIRCUITPY:

```
CIRCUITPY/
├── code.py              ← Launcher (NOU)
├── tecla_main.py        ← TECLA original (renombrat)
├── modes/
├── effects/
├── core/
├── config/
└── (altres fitxers de TECLA)
```

### Pas 6: Provar
1. **Desconnecta TECLA del USB**
2. **Encén normalment** (sense prémer res)
3. Hauria de funcionar com sempre (TECLA normal)
4. Si funciona → **Configuració completada! ✅**

---

## 🎮 Ús Diari

### Mode TECLA (Normal)
```
Encendre el dispositiu
    ↓
TECLA funciona com sempre
```

### Mode TECLA Blocks (Educatiu)
```
Encendre el dispositiu
    ↓
Mantenir Botó 16 durant 1.5 segons
(El LED piscarà durant la comprovació)
    ↓
S'executa el programa de blocs
```

**Important:** Com el Botó 13 per canviar de banc, cal **mantenir premut 1.5s** per evitar canvis accidentals.

---

## 🔄 Treballar amb TECLA Blocks

### 1. Crear programa
1. Obre **TECLA Blocks** a l'ordinador
2. Crea el teu programa amb blocs
3. Connecta TECLA via USB

### 2. Pujar programa
1. Click a **"⬆️ Pujar a TECLA"**
2. L'app guarda el codi com `tecla_blocks.py`
3. NO sobreescriu res de TECLA

### 3. Executar
1. Desconnecta USB
2. Encén TECLA
3. **Mantén Botó 16 durant 1.5s** (el LED piscarà)
4. Veuràs: "🟢 TECLA BLOCKS MODE"
5. El teu programa s'executa!

### 4. Tornar a TECLA
1. Simplement reinicia **sense prémer Botó 16**
2. TECLA torna al mode normal

---

## ❓ Troubleshooting

### "ERROR: tecla_main.py no trobat"
**Causa:** No has renombrat code.py

**Solució:**
1. Connecta TECLA via USB
2. Obre CIRCUITPY
3. Busca `code.py` original
4. Renombra'l a `tecla_main.py`

### "ERROR: tecla_blocks.py no trobat"
**Causa:** No has pujat cap programa des de TECLA Blocks

**Solució:**
1. Obre TECLA Blocks
2. Crea un programa (encara que sigui senzill)
3. Puja'l amb "⬆️ Pujar a TECLA"
4. Ara ja tens `tecla_blocks.py`

### TECLA no arrenca en cap mode
**Causa:** Problema amb el launcher

**Solució ràpida:**
1. Connecta via USB
2. Obre CIRCUITPY
3. Elimina `code.py` (launcher)
4. Renombra `tecla_main.py` → `code.py`
5. TECLA torna a funcionar normalment
6. Consulta el backup si cal

---

## 🔄 Desfer la configuració

Si vols tornar al sistema original (només TECLA):

1. Connecta TECLA via USB
2. Elimina `code.py` (launcher)
3. Renombra `tecla_main.py` → `code.py`
4. Elimina `tecla_blocks.py` (opcional)
5. TECLA funciona com sempre

**Temps:** 30 segons

---

## 📊 Comparació

### Abans (Sense Launcher)
```
TECLA Blocks sobreescriu code.py
    ↓
Perds tots els modes de TECLA
    ↓
Has de tornar a copiar tot ❌
```

### Després (Amb Launcher)
```
TECLA → tecla_main.py (intacte)
TECLA Blocks → tecla_blocks.py (separat)
Launcher → decideix quin executar
    ↓
Conviuen perfectament ✅
```

---

## 🎓 Per a Professors

### Configurar Múltiples Dispositius
Si tens 5-10 dispositius TECLA per una classe:

**Opció A - Manual (20 min total)**
1. Configura el primer amb aquest tutorial
2. Copia CIRCUITPY complet
3. Enganxa'l als altres dispositius

**Opció B - Individual (5 min cada)**
1. Segueix el tutorial per cada dispositiu

### Durant la Classe
- **Matí:** Mode TECLA normal (experimentar amb modes)
- **Tarda:** Mode Blocks (aprendre programació)
- **Canvi:** Només reiniciar amb/sense Botó 16

---

## 🚀 Següents Passos

Després de configurar:

1. ✅ Prova TECLA mode normal
2. ✅ Crea un programa simple amb TECLA Blocks
3. ✅ Puja'l i executa en mode Blocks
4. ✅ Alterna entre modes

Si tot funciona → **Sistema llest per producció!**

---

**Versió:** 2.1  
**Temps configuració:** 5 minuts  
**Dificultat:** Molt fàcil ⭐⭐☆☆☆  
**Reversible:** Sí (30 segons)
