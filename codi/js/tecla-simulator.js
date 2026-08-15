/**
 * TECLASimulator — Motor del simulador web amb Pyodide
 *
 * Executa els fitxers .py dels modes TECLA al navegador via WebAssembly Python (Pyodide).
 * El pont Python→JS intercepta les crides MIDI i les redirigeix a WebMidiManager.
 *
 * Ús:
 *   const sim = new TECLASimulator(webMidi, onLog);
 *   await sim.initPyodide();
 *   await sim.loadMode(pyCode, 'mode_todrone.py');
 *   sim.startLoop();
 */
import { WebMidiManager } from './tecla-webmidi.js';

export class TECLASimulator {
    /** Pot per nom (X, Y, Z) → índex dins pot_values, com al dispositiu. */
    static VIS_TO_FRAME = [1, 0, 2];

    /**
     * Període del bucle d'actualització, en ms.
     *
     * El dispositiu no espera: el seu bucle principal crida update() tan de
     * pressa com pot. Aquí hi havia 50 ms (20 Hz) i això posava un sostre a
     * tot — un mode no podia emetre més de 20 esdeveniments per segon, els
     * ritmes quedaven quantitzats a 50 ms i el soroll no arribava a ser
     * soroll. Un tick mesurat costa ~0,3 ms, o sigui que a 10 ms el motor va
     * al 3% de CPU amb un mode i a un ~12% amb quatre de la capa MIX.
     */
    static TICK_MS = 10;

    constructor(webMidi, onLog) {
        this.webMidi = webMidi;          // WebMidiManager instance
        this.onLog = onLog || (() => { }); // callback(msg, type)
        this.pyodide = null;
        this.state = null;             // proxy de l'objecte _state Python
        this.isReady = false;
        this.isRunning = false;
        this._loopId = null;
        this.buttons = new Array(16).fill(false);
        this.pots = [0, 0, 0];        // 0-127
        this._modeName = null;

        // ── Multi-mode (capa MIX): fins a N modes reals corrent alhora ──────────
        // Cada mode actiu té el SEU canal MIDI (so propi); el pont MIDI hi força el
        // canal mentre s'actualitza aquell mode. mixEditTarget = la tecla-mode els
        // potes de la qual s'editen en directe (la resta conserven els seus congelats).
        this._mixModes = new Map();      // slot(keyIdx) → { channel }
        this._mixFrozenPots = new Map(); // slot → [p0,p1,p2] congelats
        this._forceChannel = null;       // canal forçat per a l'update en curs
        this.mixEditTarget = null;       // slot que rep els potes en directe
        // Capa de MODES pura (sense teclat a sobre): allà els potes no tenen amb qui
        // competir i van directes a tots els modes que sonen, com al dispositiu. La
        // presa per tecla ('hold'/'latch') només cal a la capa híbrida, on els potes
        // són del teclat mentre no mantinguis premuda la tecla d'un mode.
        this.potsToAllMix = false;

        // Últim estat que ha retornat el mode actiu (el mateix diccionari que
        // alimenta la pantalla del dispositiu). El constructor l'aprofita per fer
        // que la previsualització respiri amb el que sona de debò i no només amb
        // el que hi ha escrit al formulari.
        this.estat = null;
        this._tickN = 0;
        this._modGen = 0;      // generació del relleu en calent del mode únic
    }

    get mixCount() { return this._mixModes.size; }
    isMixActive(slot) { return this._mixModes.has(slot); }

    // ── Inicialitzar Pyodide ─────────────────────────────────────────────────

    async initPyodide(onProgress) {
        if (this.isReady) return;
        onProgress?.('Carregant Pyodide (Python al navegador)…');

        // loadPyodide és global, injectat per l'script CDN de Pyodide
        this.pyodide = await window.loadPyodide({
            indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.3/full/'
        });

        onProgress?.('Instal·lant mocks de CircuitPython…');

        // Exposa la funció MIDI bridge a Python. Si s'està actualitzant un mode MIX,
        // _forceChannel reescriu el canal perquè cada mode soni pel seu (sense haver de
        // tocar base_mode al simulador; al device es farà amb out_channel a base_mode).
        this.pyodide.globals.set('_js_midi_send', (type, a, b, ch) => {
            const outCh = (this._forceChannel != null) ? this._forceChannel : (ch | 0);
            this.webMidi.send(type, a | 0, b | 0, outCh);
        });

        // Carrega i executa els mocks
        const mocksRes = await fetch('./py/tecla_mocks.py');
        const mocksCode = await mocksRes.text();
        await this.pyodide.runPythonAsync(mocksCode);
        await this.pyodide.runPythonAsync('install_mocks()');

        // Configura el sistema de fitxers virtual per als imports Python
        this.pyodide.FS.mkdir('/tecla');
        this.pyodide.FS.mkdir('/tecla/modes');
        await this.pyodide.runPythonAsync("import sys; sys.path.insert(0, '/tecla')");

        // Carrega base_mode.py al VFS
        const baseRes = await fetch('./py/base_mode.py');
        const baseCode = await baseRes.text();
        this.pyodide.FS.writeFile('/tecla/modes/base_mode.py', baseCode);

        // Carrega negharm.py al VFS — dependència de base_mode.negharm() (harmonia
        // negativa). Sense això, activar l'efecte d'harmonia negativa al simulador
        // llançaria ImportError quan el mode reflecteix una nota.
        try {
            const negRes = await fetch('./py/modes/negharm.py');
            if (negRes.ok) {
                this.pyodide.FS.writeFile('/tecla/modes/negharm.py', await negRes.text());
            }
        } catch (e) { /* opcional: si no hi és, els modes sense negharm funcionen igual */ }

        // Guarda la referència a l'estat compartit
        this.state = this.pyodide.globals.get('_state');

        this.isReady = true;
        onProgress?.('Pyodide llest ✓');
        this._log('Motor Python inicialitzat correctament', 'ok');
    }

    // ── Carregar mode ────────────────────────────────────────────────────────

    /**
     * Carrega el mode únic. RELLEU EN CALENT: el mode nou es compila, s'instancia
     * i es prepara MENTRE el vell encara sona, i només al final es fa el canvi.
     *
     * Abans es feia al revés —aturar, netejar, importar, arrencar— i entremig hi
     * havia un forat de silenci de tot el que triga Python a importar el mòdul.
     * Com que el constructor recarrega el mode a cada canvi del formulari, aquell
     * forat era un tall a cada lliscador que moguessis. Ara el bucle no s'atura
     * en cap moment: el salt és d'una volta (10 ms).
     */
    async loadMode(pyCode, fileName) {
        if (!this.isReady) throw new Error('Pyodide no inicialitzat');

        // Cada relleu fa servir un nom de mòdul nou. Reutilitzar-lo obligava a
        // purgar sys.modules abans de compilar, i això és el que forçava a matar
        // el mode vell primer.
        const gen = ++this._modGen;
        const mod = `mode_live_${gen}`;
        this.pyodide.FS.writeFile(`/tecla/modes/${mod}.py`, pyCode);

        // 1) Compilar i preparar el NOU sense tocar el que sona.
        const result = await this.pyodide.runPythonAsync(`
import importlib
from adafruit_midi import MIDI
import usb_midi
from modes.base_mode import BaseMode

_nou_mod = importlib.import_module('modes.${mod}')
_nou_cls = None
for _v in vars(_nou_mod).values():
    if isinstance(_v, type) and _v is not BaseMode and issubclass(_v, BaseMode):
        _nou_cls = _v
        break
if _nou_cls is None:
    raise ValueError("No s'ha trobat cap classe que hereti de BaseMode a ${mod}")
_nou = _nou_cls(MIDI(midi_out=usb_midi.ports[1]))
_nou.setup()
_nou_cls.__name__
`);

        // 2) El canvi, en un sol pas: el tick següent ja fa servir el nou. El vell
        //    es neteja DESPRÉS (allibera les seves notes) i el seu mòdul es purga.
        await this.pyodide.runPythonAsync(`
import sys
_vell = globals().get('_active_mode')
_active_mode = _nou
del _nou
if _vell is not None:
    try: _vell.cleanup()
    except Exception: pass
for _k in list(sys.modules.keys()):
    if 'mode_live_' in _k and not _k.endswith('${mod}'):
        del sys.modules[_k]
`);
        // Els fitxers dels relleus vells no fan cap falta al disc virtual.
        for (let g = 1; g < gen; g++) {
            try { this.pyodide.FS.unlink(`/tecla/modes/mode_live_${g}.py`); } catch (e) { }
        }

        this._modeName = result;
        this._log(`Mode carregat: ${this._modeName}`, 'ok');
        return result;
    }

    // ── Multi-mode (capa MIX) ────────────────────────────────────────────────

    /**
     * Carrega un mode addicional que correrà ALHORA que els altres, al seu canal.
     * @param {string} pyCode  codi font .py del mode
     * @param {number} slot     identificador (índex de tecla) del mode
     * @param {number} channel  canal MIDI propi (so distint)
     */
    async loadMixMode(pyCode, slot, channel) {
        if (!this.isReady) throw new Error('Pyodide no inicialitzat');
        const mod = `mode_mix_${slot}`;
        this.pyodide.FS.writeFile(`/tecla/modes/${mod}.py`, pyCode);
        await this.pyodide.runPythonAsync(`
import sys, importlib
for _k in list(sys.modules.keys()):
    if '${mod}' in _k: del sys.modules[_k]
import modes.${mod} as _m
importlib.reload(_m)
from modes.base_mode import BaseMode
from adafruit_midi import MIDI
import usb_midi
_cls = None
for _v in vars(_m).values():
    if isinstance(_v, type) and _v is not BaseMode and issubclass(_v, BaseMode):
        _cls = _v; break
if _cls is None:
    raise ValueError("Cap classe BaseMode a ${mod}")
if '_mix_modes' not in globals():
    _mix_modes = {}
_inst = _cls(MIDI(midi_out=usb_midi.ports[1]))
_inst.setup()
_mix_modes[${slot}] = _inst
`);
        this._mixModes.set(slot, { channel });
        this._mixFrozenPots.set(slot, [...this.pots]);
    }

    /** Atura i descarrega un mode MIX (cleanup + All Notes Off del seu canal). */
    unloadMixMode(slot) {
        if (!this._mixModes.has(slot)) return;
        const info = this._mixModes.get(slot);
        try {
            this._forceChannel = info.channel;
            this.pyodide.runPython(`
if '_mix_modes' in globals() and ${slot} in _mix_modes:
    try: _mix_modes[${slot}].cleanup()
    except: pass
    del _mix_modes[${slot}]
`);
        } catch (e) { /* el cleanup mai no trenca */ }
        this._forceChannel = null;
        try { this.webMidi.send('control_change', 123, 0, info.channel); } catch (e) { } // All Notes Off del canal
        this._mixModes.delete(slot);
        this._mixFrozenPots.delete(slot);
        if (this.mixEditTarget === slot) this.mixEditTarget = null;
    }

    /** Atura i descarrega TOTS els modes MIX. */
    clearMixModes() {
        for (const slot of [...this._mixModes.keys()]) this.unloadMixMode(slot);
        this.mixEditTarget = null;
    }

    // ── Bucle d'actualització (20 Hz) ────────────────────────────────────────

    startLoop() {
        if (this.isRunning || !this.isReady) return;
        // Pot arrencar amb el mode únic (capa modes) O amb modes MIX (capa híbrida).
        if (!this.pyodide.globals.has('_active_mode') && this._mixModes.size === 0) {
            this._log('Cap mode carregat. Carrega un mode .py primer.', 'warn');
            return;
        }
        this.isRunning = true;
        this._loopId = setInterval(() => this._tick(), TECLASimulator.TICK_MS);
        this._log('Simulador iniciat', 'ok');
    }

    /** Para el rellotge del bucle i prou: no descarrega res ni apaga notes. */
    _pausaBucle() {
        this.isRunning = false;
        if (this._loopId) { clearInterval(this._loopId); this._loopId = null; }
    }

    stopLoop() {
        if (!this.isRunning) return;
        this._pausaBucle();

        // Crida cleanup + All Notes Off (mode únic + tots els modes MIX)
        try {
            this.pyodide.runPython(`
if '_active_mode' in globals() and hasattr(_active_mode, 'cleanup'):
    try: _active_mode.cleanup()
    except: pass
`);
        } catch { }
        try { this.clearMixModes(); } catch { }
        this.webMidi.allNotesOff();
        this._log('Simulador aturat', 'info');
    }

    _tick() {
        // Mode únic (capa modes / audició del constructor): rep botons i potes
        // en directe. Corre SEMPRE que hi sigui — també amb modes MIX a sobre,
        // perquè es puguin provar combinacions amb el mode que estàs fent.
        if (this.pyodide.globals.has('_active_mode')) {
            try {
                for (let i = 0; i < 16; i++) this.state.set_button(i, this.buttons[i]);
                for (let i = 0; i < 3; i++) this.state.set_pot(i, this.pots[i]);
                const res = this.pyodide.runPython(`
_active_mode.update(
    [_state.pots[0], _state.pots[1], _state.pots[2]],
    list(_state.buttons)
)
`);
                // El diccionari que torna el mode arriba com a PyProxy: convertir-lo
                // a cada volta seria car (i a 100 Hz, inútil), així que es recull un
                // cop cada cinc — 20 Hz, de sobres per moure una animació. El proxy
                // s'ha de destruir sempre o la memòria de Python se'n va.
                if (res && typeof res.toJs === 'function') {
                    if ((++this._tickN % 5) === 0) {
                        try { this.estat = Object.fromEntries(res.toJs()); } catch (e) { }
                    }
                    res.destroy();
                }
            } catch (e) {
                console.warn('[Simulator tick]', e.message);
            }
        }
        if (this._mixModes.size === 0) return;

        // Modes MIX: cada mode corre AUTÒNOM (botons neutres: el teclat es toca a part)
        // i pel SEU canal. Els potes només editen en directe el mode "objectiu"; la
        // resta conserven els seus potes congelats.
        for (let i = 0; i < 16; i++) this.state.set_button(i, false);
        const aTots = this.potsToAllMix && this.mixEditTarget === null;
        for (const [slot, info] of this._mixModes) {
            let pots = this._mixFrozenPots.get(slot) || [0, 0, 0];
            if (aTots || slot === this.mixEditTarget) { pots = [...this.pots]; this._mixFrozenPots.set(slot, pots); }
            try {
                for (let i = 0; i < 3; i++) this.state.set_pot(i, pots[i]);
                this._forceChannel = info.channel;
                this.pyodide.runPython(`_mix_modes[${slot}].update([_state.pots[0], _state.pots[1], _state.pots[2]], list(_state.buttons))`);
            } catch (e) {
                console.warn(`[Simulator mix ${slot}]`, e.message);
            } finally {
                this._forceChannel = null;
            }
        }
    }

    // ── Controls ─────────────────────────────────────────────────────────────

    pressButton(idx) { if (idx >= 0 && idx < 16) this.buttons[idx] = true; }
    releaseButton(idx) { if (idx >= 0 && idx < 16) this.buttons[idx] = false; }

    /** Índex DE TRAMA (el que arriba al mode com pot_values[idx]). */
    setPot(idx, value) { if (idx >= 0 && idx < 3) this.pots[idx] = Math.max(0, Math.min(127, value | 0)); }

    /**
     * Pot per NOM (0=X, 1=Y, 2=Z), tal com el veu qui toca l'aparell.
     *
     * Al dispositiu la trama de potes és [A0, A1, A2] (main.py) i modes/kbd_pots.py
     * hi llegeix X=pot_values[1], Y=pot_values[0], Z=pot_values[2]. El simulador ha
     * de passar el MATEIX ordre al Python o el que sona aquí no és el que sonarà al
     * dispositiu: girar la X mouria la funció de la Y.
     */
    setPotXYZ(vis, value) { this.setPot(TECLASimulator.VIS_TO_FRAME[vis] ?? vis, value); }

    // ── Log helper ───────────────────────────────────────────────────────────

    _log(msg, type = 'info') { this.onLog(msg, type); }
}
