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

    async loadMode(pyCode, fileName) {
        if (!this.isReady) throw new Error('Pyodide no inicialitzat');

        const wasRunning = this.isRunning;
        if (wasRunning) this.stopLoop();

        // Escriu el codi del mode al VFS
        this.pyodide.FS.writeFile('/tecla/modes/mode_active.py', pyCode);

        // Cleanup del mode anterior i purga de mòduls
        await this.pyodide.runPythonAsync(`
import sys, importlib

# Neteja el mode anterior
if '_active_mode' in globals():
    try: _active_mode.cleanup()
    except: pass
    del _active_mode

# Purga tots els mòduls del mode actiu
for _k in list(sys.modules.keys()):
    if 'mode_active' in _k:
        del sys.modules[_k]
`);

        // Importa el mòdul directament (no import *) i cerca la classe dins __dict__
        const result = await this.pyodide.runPythonAsync(`
import importlib
import modes.mode_active as _mode_mod
importlib.reload(_mode_mod)

from adafruit_midi import MIDI
import usb_midi
from modes.base_mode import BaseMode

_mode_class = None
for _v in vars(_mode_mod).values():
    if isinstance(_v, type) and _v is not BaseMode and issubclass(_v, BaseMode):
        _mode_class = _v
        break

if _mode_class is None:
    raise ValueError("No s'ha trobat cap classe que hereti de BaseMode a mode_active")

_midi_inst = MIDI(midi_out=usb_midi.ports[1])
_active_mode = _mode_class(_midi_inst)
_active_mode.setup()
_active_mode.__class__.__name__
`);

        this._modeName = result;
        this._log(`Mode carregat: ${this._modeName}`, 'ok');

        if (wasRunning) this.startLoop();
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
        this._loopId = setInterval(() => this._tick(), 50);
        this._log('Simulador iniciat', 'ok');
    }

    stopLoop() {
        if (!this.isRunning) return;
        this.isRunning = false;
        if (this._loopId) { clearInterval(this._loopId); this._loopId = null; }

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
        // Mode únic (capa modes): rep botons i potes en directe, com sempre.
        if (this._mixModes.size === 0 && this.pyodide.globals.has('_active_mode')) {
            try {
                for (let i = 0; i < 16; i++) this.state.set_button(i, this.buttons[i]);
                for (let i = 0; i < 3; i++) this.state.set_pot(i, this.pots[i]);
                this.pyodide.runPython(`
_active_mode.update(
    [_state.pots[0], _state.pots[1], _state.pots[2]],
    list(_state.buttons)
)
`);
            } catch (e) {
                console.warn('[Simulator tick]', e.message);
            }
            return;
        }

        // Modes MIX: cada mode corre AUTÒNOM (botons neutres: el teclat es toca a part)
        // i pel SEU canal. Els potes només editen en directe el mode "objectiu"; la
        // resta conserven els seus potes congelats.
        for (let i = 0; i < 16; i++) this.state.set_button(i, false);
        for (const [slot, info] of this._mixModes) {
            let pots = this._mixFrozenPots.get(slot) || [0, 0, 0];
            if (slot === this.mixEditTarget) { pots = [...this.pots]; this._mixFrozenPots.set(slot, pots); }
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
    setPot(idx, value) { if (idx >= 0 && idx < 3) this.pots[idx] = Math.max(0, Math.min(127, value | 0)); }

    // ── Log helper ───────────────────────────────────────────────────────────

    _log(msg, type = 'info') { this.onLog(msg, type); }
}
