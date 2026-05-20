# Historial de canvis - TECLA Blocks

## [2.0.0] - 2025-11-17 **🚀 VERSIÓ AMPLIADA**

### ✨ Novetats majors

#### 🌊 Síntesi Avançada (5 blocs nous)
- **Oscil·lador** amb 6 formes d'ona (sinusoidal, quadrada, triangular, dent de serra, pols, soroll)
- **LFO** (Low Frequency Oscillator) amb modulació automàtica de paràmetres
- **Envolvent ADSR** per controlar l'evolució del so
- **Modulació** (FM, AM, PM, Ring Modulation) per síntesi complexa
- **Waveshaper** amb 5 tipus de distorsió i efectes

#### 💡 GPIO i Hardware (4 blocs nous)
- Control de pins digitals (HIGH/LOW)
- Lectura de pins digitals
- Control PWM analògic (0-65535)
- Lectura analògica ADC

#### 📡 Sensors (3 blocs nous)
- Temperatura CPU del microcontrolador
- Acceleròmetre (X, Y, Z, magnitud)
- Sensor de distància ultrasònic HC-SR04

#### 🔢 Matemàtiques Avançades (4 blocs nous)
- Números aleatoris entre rangs
- Escalar valors (map) entre rangs
- Limitar valors (constrain)
- Funcions trigonomètriques (sin, cos, tan, asin, acos, atan)

#### 📝 Text i Strings (3 blocs nous)
- Unir textos
- Longitud de text
- Comprovar si conté text

#### 📋 Llistes/Arrays (4 blocs nous)
- Crear llista buida
- Afegir element a llista
- Obtenir element per índex
- Longitud de llista

#### 📡 Comunicació (4 blocs nous)
- Serial Print (USB)
- Serial Read
- I2C Write (comunicació amb dispositius)
- I2C Read

#### 🔧 Funcions Personalitzades (2 blocs nous)
- Definir funció pròpia
- Cridar funció definida

### 📊 Estadístiques
- **Total de blocs:** 70+ blocs (abans: 18)
- **Categories:** 14 categories (abans: 6)
- **Generadors Python:** Tots els blocs implementats

### 🎯 Casos d'ús nous
- Sintetitzadors FM professionals
- Control gestual amb acceleròmetre
- Teremín sense contacte amb sensor de distància
- Seqüenciadors amb llistes
- Projectes IoT musicals
- Interfícies amb sensors I2C

### Documentació
- Nou fitxer README_AMPLIACIO.md amb guia completa
- Exemples per a cada categoria de blocs
- Comparació amb Scratch i MicroBlocks
- Casos d'ús avançats documentats

---

## [1.0.0] - 2025-11-17

### Llançament inicial

#### Funcionalitats principals
- **Interfície Blockly** amb tema fosc optimitzat
- **15+ blocs personalitzats** per TECLA:
  - Música: Notes, acords, escales, octaves
  - Control: Botons, potenciòmetres, events
  - Efectes: Delay, reverb, filtres
  - Temps: Esperes, bucles
  - Lògica: Condicionals, variables
- **Generador de Python** CircuitPython per TECLA
- **Simulador integrat** amb visualització del dispositiu
- **Gestió de projectes**: Guardar/Obrir (.tblocks)
- **Exportació de codi** Python
- **Upload directe** al dispositiu TECLA via USB

#### Plataformes suportades
- macOS 10.13+
- Windows 10+
- Linux (Ubuntu 20.04+, Fedora, etc.)

#### Educació
- Guia ràpida per alumnes
- 3 tutorials progressius
- Reptes per nivells
- Material per professors

### 🎨 Interfície
- Tema fosc modern
- Panell lateral amb 3 pestanyes (Codi, Simulador, Ajuda)
- Barra d'estat amb informació del dispositiu
- Animacions fluides

### 🔧 Tècnic
- Electron 28.0.0
- Blockly 10.4.0
- SerialPort 12.0.0
- Arquitectura modular
- Generació de codi optimitzada

---

## Properes versions

### [1.1.0] - Planificada

#### Funcionalitats noves
- [ ] Més blocs musicals (MIDI CC, Program Change)
- [ ] Sistema de biblioteques de blocs personalitzats
- [ ] Mode visualització en temps real (oscil·loscopi)
- [ ] Enregistrament de seqüències MIDI
- [ ] Integració amb DAWs (Ableton, Logic, etc.)

#### Millores
- [ ] Simulador més realista amb àudio
- [ ] Mode col·laboratiu (múltiples usuaris)
- [ ] Traducció a més idiomes (Castellà, Anglès, Francès)
- [ ] Biblioteca d'exemples integrada

#### Correccions
- [ ] Millora de rendiment amb projectes grans
- [ ] Sincronització més robusta amb el dispositiu
- [ ] Gestió d'errors més detallada

---

## Contribuir

Si vols contribuir al desenvolupament de TECLA Blocks:

1. Fork del repositori
2. Crea una branca per la nova funcionalitat
3. Commits amb missatges descriptius
4. Pull request amb descripció detallada

**Àrees on necessitem ajuda:**
- 🎨 Disseny d'icones i recursos visuals
- 📚 Documentació i tutorials
- 🌍 Traduccions
- 🐛 Testeig i detecció de bugs
- ✨ Noves funcionalitats

---

**Mantingut per:** Projecte TECLA  
**Llicència:** MIT
