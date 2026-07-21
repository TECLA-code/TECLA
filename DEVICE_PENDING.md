# Canvis pendents al dispositiu TECLA

## 0. v3.3.1 — Poliment final: pantalla cuidada + estat firmware net — 2026-07-21

✅ INSTAL·LAT AL DISPOSITIU (v3.3.1) I A PUNT PER PUBLICAR.

- **Pantalla sense faltes d'ortografia**: mapa d'accents (Dòric, Conducció,
  Expressió…) aplicat al text; la mida de la lletra s'adapta a la llargada
  perquè els noms llargs es llegeixin sempre.
- **Pantalla no és la consola**: fora el "(pot)" (firmware i pantalla). La
  funció d'octava per pot ja no xoca amb la Tonalitat (imprimia 🎵).
- **Efectes temporals de la capa MODES a la pantalla**: activació/ciclat de
  latch, Config Modes i octava de modes ja hi surten (referència del que
  passa quan el configurador altera els potes).
- **Centrat perfecte** a qualsevol mida (dins l'app i en finestra PiP): el cos
  de la pantalla ara creix amb el panell (`flex:1`).
- **PiP manté l'aparença de l'app**: es copia la classe de tema del `body` a
  la finestra desancorada (abans perdia el tema).
- **Pestanya Firmware**: fora la fila "Mode Bootloader"; "Firmware TECLA"
  mostra només "TECLA vX.X.X" (sense "(web install)").

---

## 0. v3.3.0 — TANCAMENT: Pantalla viva, simulador complet, acompanyaments — 2026-07-19

✅ TOT INSTAL·LAT AL DISPOSITIU I PUBLICAT. Recull de les versions 3.2.x:

- **Pantalla virtual** (botó "Pantalla"): connexió automàtica de port, acords
  amb nomenclatura professional (C, Am7, F/A… també els MANUALS agrupant notes
  simultànies), funcions amb el color de l'app, looper elegant, testimonis de
  pots, logo de fons segons el tema, arrossegable/redimensionable i
  desancorable (PiP). Animacions REACTIVES als potes per família de mode:
  anell (teclat, color per fonamental), oscil·loscopi (ones), equalitzador
  (ritmes), orbes (clàssics), camp d'estrelles (generatius).
- **Simulador**: diagrama flotant idèntic a Dispositiu, capes il·limitades
  ciclables amb la tecla 13 (creació amb tipologia + esborrat), lateral
  drag&drop "Modes i funcions" idèntic a Dispositiu, sync automàtic amb el
  dispositiu físic (mode controlador), pots X/Y ben mapats.
- **Capa teclat**: acompanyaments personalitzats (seqüències per graus amb
  octava/brillantor/BPM/gate), 12 formes de conducció de veus (inversions
  incloses), sustain per trams, potes només-MIDI.
- **Firmware**: testimonis per a la Pantalla amb cost zero sense consola i a
  prova de bombes (mai poden trencar el so); octaves amb numeració del
  dispositiu; primera lectura de pots silenciosa (res de fantasmes al canvi
  de capa).
- PENDENT (fora del tancament): i18n ES/EN de les funcions noves (Pantalla,
  xips del sim, editor d'acompanyaments — ara en català); motor d'àudio,
  OLED i mode controlador ampliat per a la revisió Pico 2.

---

## 0. v3.2.0 — Acompanyaments custom, VL ampliada, sync simulador, monitor — 2026-07-18

✅ JA INSTAL·LAT AL DISPOSITIU (instal·lació directa incremental, 9 fitxers).

- **Acompanyaments personalitzats**: nou apartat "Acompanyaments" a la capa
  teclat de l'app — seqüències per graus de l'escala amb passos (4-16), octava
  (−2..+2), brillantor, velocitat (BPM propi) i durada de nota (gate). La tecla
  'Base (acomp.)' els cicla després dels 4 integrats. `custom_accompaniments`
  per-capa; motor: accompaniment._make_custom (mirall JS makeCustomPattern).
- **Conducció de veus ampliada (12 formes)**: + Descendent, Tancat,
  Fonamental, 1a Inversió, 2a Inversió (les "Inversions Harmòniques" òrfenes
  viuen ara aquí), Drop 2 i Pèndol. L'antic apartat d'inversions i el pot
  "Inversió d'Acord" (que no feien res) s'han retirat de app i firmware.
- **Sustain per TRAMS**: OFF · 0.5 · 1.2 · 2.5 · 5 · 8s · ∞ (el tram infinit
  ara comença a 118 — abans 125, inabastable amb l'escalat real de l'ADC).
  Tram anunciat per consola; histèresi anti-soroll.
- **Sync amb el simulador (mode controlador)**: botó "🔌 Sync dispositiu" a la
  pestanya Simulador — el TECLA físic controla el simulador pel canal de dades
  USB (core/sim_link ara SÍ cablejat a main.py; el so local es pausa mentre
  està connectat, protocol de la v2).
- **Monitor del dispositiu**: botó "Monitor" a la capçalera de l'app — consola
  virtual minimalista per WebSerial (notes ♪ i acords ▣ amb noms C-D-E,
  funcions on/off, canvis de capa, errors) sense executar main.py des del shell.
- **Capes IL·LIMITADES a app i simulador**: el límit de 6 queda només per al
  DISPOSITIU (buildDeviceConfig exporta les 6 primeres i avisa).
- App: popup de confirmació d'"Instal·lar firmware" eliminat; opció OLED
  oculta; res d'àudio al simulador (efectes Àudio 1-6 i funcions synth fora
  del lateral i del panell Config).
- Tests: 229 en verd (nous: acompanyaments custom ×4, formes VL ×8, trams
  de sustain).

---

## 1. v3.1.3 — STOP a prova de DAW + Config Modes només-MIDI — 2026-07-16

✅ JA INSTAL·LAT AL DISPOSITIU (falta DESENDOLLAR i tornar a endollar: el
dispositiu va quedar penjat durant les proves per sèrie i necessita el reinici
físic; el disc ja porta la v3.1.3 i arrencarà net).

- **STOP a prova de DAW**: a més de CC64/120/123 + pitch bend per canal, ara
  envia NoteOff EXPLÍCIT per a les 128 notes al canal de sortida — molts
  instruments dins un DAW (AUs de tercers) ignoren All Notes Off i eren
  la via per la qual "el botó 16 no aturava el so".
- **Config Modes = NOMÉS efectes MIDI estàndard** (funciona amb qualsevol
  DAW): catàleg del configurador i capes per defecte amb la mateixa família
  de funcions que els potes del teclat — Volum, Expressió, Modulació,
  Brillantor (CC74), Timbre (CC71), Pan, Reverb, Chorus, Atac, Release,
  Portamento i CC lliures. Res del sinte intern.
- **Opció de pantalla OLED oculta** a la pestanya Firmware (reservada per a la
  revisió Pico 2, com el motor d'àudio).
- **Bug "acords diatònics + octava 4 + notes enganxades"**: el motor s'ha
  EXONERAT amb un test exhaustiu (octaves 3/4/5 × 7 funcions harmòniques ×
  toc simple i legato: zero desbalanç NoteOn/NoteOff, zero notes actives
  residuals). Sospita principal: l'instrument del DAW (vegeu el pla de prova
  al resum de sessió). El STOP nou amb 128 NoteOff l'hauria de tallar sempre.

---

## 1. v3.1.2 — Efectes temporals sanejats, STOP total, boot a capa 1 — 2026-07-16

✅ JA INSTAL·LAT AL DISPOSITIU (instal·lació directa per USB, arrencada
verificada per sèrie: "Capa actual: Teclat"). Només cal GUARDAR la config des
de l'app si configures les noves capes de pots de Config Modes.

- **Nota enganxada (botó 1) que STOP no aturava**: l'efecte Sustain de la capa
  de modes envia CC64=127 (pedal) a tots els canals; l'emergency stop marcava
  els efectes com a inactius SENSE cridar el seu on_deactivate → el pedal
  quedava premut al synth i qualsevol nota posterior s'enganxava. Ara STOP
  desactiva TOTS els efectes de veritat (CC64=0) + effect_manager.deactivate().
- **STOP total**: també apaga Config Modes i Loop, el PWM intern i els efectes
  encara que estiguin desincronitzats.
- **Efectes temporals NO persistents**: canviar de MODE desactiva l'efecte
  actiu (Sustain, Pausa, Gate…). Únics supervivents: 'Config Modes' i 'Loop'.
  Passar a una capa de TECLAT també els desactiva (si no, el pedal CC64
  enganxava les notes del teclat).
- **Boot SEMPRE a la capa 1**: la config porta el current_bank seleccionat a
  l'app (útil per al hot-reload), però l'arrencada freda força el banc 0.
- **Efectes sense inundar l'USB**: update_params enviava 16 CCs per cicle
  (~8000 msg/s amb el bucle nou de 2ms); ara només envien quan el valor canvia
  (cache per CC + missatge reutilitzat).
- **EffectPitchBend**: en desactivar enviava PitchBend(0) = bend a fons AVALL
  (desafinava el synth); el centre és 8192. Corregit + throttle.
- **App: configurador de 'Config Modes'** (pestanya Dispositiu, capa de modes):
  fins a 4 capes de pots amb nom i funcions X/Y/Z (Volum, Expressió, Filtre,
  Reverb, Pan, Portamento, Trèmol, Phaser, CC lliures…). S'exporta com a
  'mode_pot_layers'; buit = defaults del firmware (Mescla/Timbre/Expressió).
- Tests nous: `tests/test_effects_lifecycle.py` (5).

---

## 1. v3.1.1 — MIDI "com la seda": latència, capes duplicades, sustain i STOP — 2026-07-15

REINSTAL·LA el firmware (Firmware → Instal·lar; incremental → segons) i DESPRÉS
guarda la configuració: el fix de capes és a l'app, així que cal re-exportar-la.

- **"Només em carrega una capa de teclat"**: el bug era a l'APP, no al firmware.
  El snapshot d'una capa de teclat nova/no editada quedava buit per sempre i
  `buildDeviceConfig` exportava la config de la capa SELECCIONADA per a TOTES
  les capes de teclat (al dispositiu: 2 bancs idèntics, verificat al JSON).
  Ara `_captureKb` fotografia TOTES les claus (null = default explícit).
  ⚠ Revisa la capa "Acords" a l'app (pot haver quedat amb defaults) i
  torna a GUARDAR la configuració al dispositiu.
- **Latència ("no va al toque")**: bucle principal de 20ms → 2ms (la pulsació
  podia esperar 20ms només per ser detectada); NoteOn/NoteOff POOLED a tot el
  camí calent del teclat (cada al·locació podia disparar un gc de 10-40ms);
  el PWM viu a `core/tone.py` (abans `import main` recompilava main.py sencer
  AL PRIMER TOC: centenars de ms de lag i pic de RAM).
- **Sustain**: amb acords o h.negativa actius el pot Z (Sustain) no feia res
  (restricció del disseny antic de capes de pots, retirades a v3.1). Ara el
  sustain funciona a tot arreu MENYS a l'arpegiador. Re-tocar una nota que
  ressonava cancel·la el seu note-off ajornat (abans la tallava al cap d'uns
  segons — el so "estrany").
- **Botó 16 (STOP)**: el pànic enviava >500 missatges MIDI (128 NoteOff + tots
  els CC × 16 canals × 2 passades, i CC11=127) i es repetia 3 cops — més d'un
  segon de bloqueig i salts de volum. Ara: UNA passada (CC64/120/123 + pitch
  bend per canal, 64 missatges, pooled).
- Tests nous: `tests/test_midi_fluid.py` (7) — sustain normal/acords/arp,
  re-articulació, pressupost del pànic, pool de missatges i core/tone.

---

## 1. v3.1.0 TANCAMENT — MIDI + PWM simple, acords sòlids, límit de capes — 2026-07-13

Reinstal·la el firmware (Firmware → Instal·lar). Canvis de tancament:

- **Acords que sonaven esglaonats**: dues causes mortes al camí calent de
  `_send_chord` — (1) missatge NoteOn POOLED (zero al·locacions dins l'acord:
  amb RAM justa, cada `NoteOn(...)` nou podia disparar un gc.collect de
  10-40ms entre notes) i (2) el càlcul/reconfiguració del PWM ara es fa DESPRÉS
  d'enviar tot l'acord per MIDI, no entre la 1a i la 2a nota.
- **Firmware tancat a MIDI + PWM monofònic simple** (com les primeres versions:
  `midi_to_frequency` + PWMOut GP22, fonamental de l'acord). `core/audio_engine`
  eliminat del firmware (queda al git per a la revisió Pico 2).
- **Capes de potes d'acords i d'harmonia negativa RETIRADES** (a tot arreu:
  firmware, app, simulador). Només queden teclat i arpegiador (+ Config Modes
  a la capa de modes).
- **Límit de capes = 6** (app i firmware; el firmware retalla amb avís si la
  config en porta més — protecció de RAM).
- **Diagnòstic per capa**: en activar una capa de teclat, la consola diu
  `config: pròpia` o `config: global`. Si una capa que has configurat surt
  "global", torna a guardar la configuració des de l'app amb aquella capa
  visitada (el snapshot es captura en seleccionar-la) i reinstal·la.

---

## 1. v3.1.0 — Fluïdesa, Config Modes, Loop i actualització ràpida — 2026-07-13

Reinstal·la el firmware des de la pestanya Firmware. La PRIMERA reinstal·lació
serà completa (estableix el manifest de hashos al dispositiu); a partir de la
següent, l'actualització és INCREMENTAL (només fitxers canviats → segons).

- **RAM/fluïdesa**: el motor d'àudio synthio ja NO s'engega (reservat per a la
  revisió Pico 2; es pot forçar amb `"internal_audio": true` a la config) —
  allibera diversos KB que causaven els MemoryError en carregar modes. El canvi
  de capa ja no llegeix el registre de modes si no hi ha modes custom, i s'han
  eliminat collects i logs redundants del camí calent.
- **'Config Modes'** (efecte per a tecles 14/15): tap = capa de potes següent
  (Mescla → Timbre → Expressió → OFF) per modificar el mode mentre sona, amb
  pickup. `modes/potlayers.py` (lazy).
- **'Loop'** (efecte per a tecles 14/15): grava el MIDI del mode (màx ~8s /
  96 esdeveniments) i el repeteix en bucle per tocar-hi a sobre; sobreviu el
  canvi de mode i de capa; STOP (tecla 16) l'esborra. `modes/modeloop.py` (lazy).
- Efectes disponibles per defecte: sense 'Àudio 1-6' (configuració d'àudio
  només al simulador en aquesta versió).

---

## 1. Tecla 13 = CICLAR CAPES + config de teclat PER-CAPA — 2026-07-13

Requereix REINSTAL·LAR el firmware (pestanya Firmware). Canvis:
- `main.py`: toc curt de T13 = capa següent (cicla TOTES les capes creades,
  teclat i modes, d'esquerra a dreta amb volta) · premuda llarga = capa
  anterior. Cada capa activa el motor del seu tipus; el KeyboardMode es RECREA
  a cada canvi perquè cada capa de teclat soni amb la SEVA config (abans la
  segona capa de teclat repetia la primera). L'arrencada i el hot-reload de
  config també respecten el tipus de la capa actual.
- `core/config_manager.py`: getters de teclat per-capa amb fallback global
  (`keyboard_button_functions`, harmonia negativa, diatòniques, conducció de
  veus, pots d'acords/negativa/àudio, arps i progressions custom) + migració
  de configs antigues (bancs sense `type` → 'modes' + capa de teclat garantida).
- `modes/mm_lifecycle.py`: 'Silenci'/'Teclat' són marcadors de tecla buida —
  ja no generen l'avís "Mode 'Silenci' no al registre".

---

## 1. Base d'acompanyament (nova funció de teclat 'accomp') — 2026-07-13

Requereix REINSTAL·LAR el firmware des de la pestanya Firmware (el manifest ja
inclou `modes/accompaniment.mpy` i els hooks a `kbd_buttons`, `mode_keyboard` i
`main.py`). Sense reinstal·lar, la tecla assignada a "Base (acomp.)" no farà res
al dispositiu (cap crash: els hooks són defensius i el mòdul és lazy).

---

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
