# 📦 TECLA Device Files

Aquest directori conté **tots els fitxers necessaris** per instal·lar el firmware TECLA en una **Raspberry Pi Pico** nova.

## 📋 Contingut

### **Fitxers Principals**
- `main.py` - Programa principal del controlador MIDI
- `reset.py` - Script de reset del dispositiu
- `boot_out.txt` - Informació de boot de CircuitPython

### **Directoris**

#### 📂 `config/`
Configuració del dispositiu:
- `tecla_config.json` - Configuració de bancs, modes i escales
- `settings.py` - Configuració general

#### 📂 `core/`
Mòduls essencials:
- `config_manager.py` - Gestor de configuració
- `layer_manager.py` - Gestor de capes
- `animations/` - Animacions per modes visuals

#### 📂 `modes/`
Tots els modes musicals:
- `base_mode.py` - Classe base per modes
- `mode_manager.py` - Gestor de modes
- `mode_keyboard.py` - Mode teclat amb escales i progressions
- 20+ modes musicals generatius

#### 📂 `effects/`
Sistema d'efectes MIDI:
- `base_effect.py` - Classe base per efectes
- `effect_manager.py` - Gestor d'efectes
- Efectes: Chorus, Reverb, Delay, Filter, Pan, etc.

#### 📂 `lib/`
Llibreries CircuitPython necessàries:
- `adafruit_midi/` - Biblioteca MIDI
- `adafruit_hid/` - Biblioteca HID (teclat/ratolí)

---

## 🚀 Instal·lació

### **Requisits Previs**
1. **Raspberry Pi Pico** amb **Adafruit CircuitPython 9.x** instal·lat
2. El dispositiu ha d'aparèixer com a volum `CIRCUITPY`

### **Mètode 1: Des de la GUI (Recomanat)**
1. Connecta la Raspberry Pi Pico al PC
2. Obre l'aplicació TECLA GUI
3. Click al botó "🔧 Instal·lar/Actualitzar Firmware"
4. Segueix les instruccions

### **Mètode 2: Manual**
1. Copia tot el contingut d'aquest directori a `/Volumes/CIRCUITPY/`
2. Reinicia el dispositiu

---

## ⚠️ Notes Importants

- **No modificar** els fitxers `._ *` (són metadades de macOS necessàries)
- **No esborrar** `boot_out.txt` (conté informació del sistema)
- Les llibreries a `lib/` són **essencials** per al funcionament

---

## 🔄 Actualització

Si ja tens TECLA instal·lat i vols actualitzar:
- La GUI detectarà els fitxers existents
- Només actualitzarà els fitxers modificats
- **La configuració (`config/`) es preserva**

---

## 📝 Versions

- **CircuitPython requerit:** 9.0.0 o superior
- **TECLA Firmware:** 2.1
- **Total fitxers:** 186

---

**🎹 TECLA - Controlador MIDI Generatiu**
