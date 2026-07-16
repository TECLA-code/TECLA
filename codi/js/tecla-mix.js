/**
 * TeclaMix — lògica pura (testejable headless) de la capa MIX.
 *
 * Una capa MIX barreja, A LA MATEIXA capa, els MODES reals (mode_*.py via el
 * motor de modes) amb el TECLAT (notes, escales, acords, arp, looper…). El
 * teclat sempre està "a sobre": es pot tocar mentre sona un mode.
 *
 * Aquest mòdul NO toca el DOM ni el simulador: només resol decisions
 * (què significa prémer una tecla · de qui són els potes ara mateix), perquè es
 * pugui verificar amb `node tools/test_mix.mjs` i, més endavant, portar el mateix
 * algorisme al firmware del device (Python).
 *
 * Dos conceptes:
 *   1. resolveKey()  — prioritat per tecla en una capa MIX (mode > stop > looper > teclat).
 *   2. MixPotRouter  — màquina d'estats del "pot-takeover": mentre es manté (hold) o
 *      es fixa (latch) una tecla-mode i hi ha un mode actiu, els potes editen el
 *      MODE; si no, tornen al TECLAT. És exactament el patró contextual que el
 *      teclat ja fa servir (arp/acord/harmonia/àudio) estès a la convivència amb modes.
 */

// ── 1) Prioritat de tecla en una capa MIX ───────────────────────────────────

/**
 * Resol què significa prémer la tecla `idx` en una capa MIX.
 * Mirall EXACTE de la prioritat d'onKeyDown a index.html (capa híbrida):
 *   tecla 13 (idx 12)            → 'layer'   (canvi/creació de capa)
 *   modes[idx] = 'accomp:TIPUS'  → 'accomp'  (patró d'acompanyament on/off)
 *   modes[idx] = fitxer de mode  → 'mode'    (dispara el mode Pyodide)
 *   tecla 16 (idx 15) sense mode → 'stop'    (atura tot)
 *   funció de teclat 'looper'    → 'looper'
 *   funció de teclat 'looper_dub'→ 'looper_dub'
 *   resta                        → 'keyboard' (nota/funció del teclat)
 *
 * @param {number} idx  índex de tecla 0-15
 * @param {{modes?:Array<string>}} bank  banc MIX actiu
 * @param {Array<string>|null} kbFns  funcions del teclat per tecla (kbMode._btnFns)
 * @returns {{kind:string, pattern?:string, file?:string}}
 */
export function resolveKey(idx, bank, kbFns) {
    if (idx === 12) return { kind: 'layer' };
    const m = (idx < 12 && bank && bank.modes && bank.modes[idx]) || '';
    if (m.indexOf('accomp:') === 0) return { kind: 'accomp', pattern: m.slice(7) };
    if (m) return { kind: 'mode', file: m };
    if (idx === 15) return { kind: 'stop' };
    const fn = kbFns && kbFns[idx];
    if (fn === 'looper') return { kind: 'looper' };
    if (fn === 'looper_dub') return { kind: 'looper_dub' };
    return { kind: 'keyboard' };
}

/** True si la tecla `idx` és un trigger de MODE (mode real, no acompanyament). */
export function isModeKey(idx, bank) {
    const m = (idx < 12 && bank && bank.modes && bank.modes[idx]) || '';
    return !!m && m.indexOf('accomp:') !== 0;
}

// ── 1b) Editor visual de la capa MIX (drag & drop, color-coded) ──────────────
// La paleta de la pestanya Mix arrossega 3 tipus d'element cap a les tecles:
//   · funció de teclat → string pla amb l'id (p. ex. "arp")
//   · mode             → JSON {type:'mode', name, file}
//   · acompanyament    → JSON {type:'accomp', pat, name}
// Aquestes funcions són PURES (sense DOM) perquè es puguin testejar headless i
// compartir la mateixa semàntica que el dispositiu.

/** Interpreta el payload d'un drag. @returns {{kind:'fn',fn}|{kind:'mode',file,name}|{kind:'accomp',pat,name}|null} */
export function parseMixPayload(payload) {
    if (payload == null || payload === '') return null;
    let obj = null;
    try { obj = JSON.parse(payload); } catch { obj = null; }
    if (obj && obj.type === 'mode' && obj.file) return { kind: 'mode', file: obj.file, name: obj.name || obj.file };
    if (obj && obj.type === 'accomp' && obj.pat) return { kind: 'accomp', pat: obj.pat, name: obj.name || obj.pat };
    if (obj && obj.type === 'effect' && obj.name) return { kind: 'effect', name: obj.name };
    if (typeof payload === 'string') return { kind: 'fn', fn: payload };
    return null;
}

/**
 * Aplica un drop a la tecla `idx` d'un banc MIX (mutant `bank.modes`/`bank.kbFns`).
 * Una tecla és O un mode/acompanyament (bank.modes[idx]) O una funció de teclat
 * (bank.kbFns[idx]) — mai totes dues. Modes/acomp només a les tecles 0-11.
 * `opts.multi` (Set d'ids de funció que admeten duplicats) controla la deduplicació.
 * @returns {object|null} el resultat de parseMixPayload, o null si no aplica.
 */
export function applyMixDrop(bank, idx, payload, opts = {}) {
    const p = parseMixPayload(payload);
    if (!p) return null;
    if (!bank.modes) bank.modes = Array(12).fill('');
    if (!bank.kbFns) bank.kbFns = Array(16).fill('');
    if (!bank.efectos) bank.efectos = {};
    if (p.kind === 'mode' || p.kind === 'accomp') {
        if (idx >= 12) return null;                       // modes/acomp només a 1-12
        bank.modes[idx] = (p.kind === 'accomp') ? ('accomp:' + p.pat) : p.file;
        bank.kbFns[idx] = '';                             // la tecla deixa de ser teclat
        delete bank.efectos[idx];                         // … ni efecte
    } else if (p.kind === 'effect') {
        if (idx < 12) bank.modes[idx] = '';
        bank.kbFns[idx] = '';
        bank.efectos[idx] = p.name;                       // efecte temporal a la tecla
    } else {                                              // funció de teclat
        if (idx < 12) bank.modes[idx] = '';               // deixa de ser mode
        delete bank.efectos[idx];                         // … ni efecte
        const multi = opts.multi;
        if (!(multi && multi.has && multi.has(p.fn))) {   // dedup si no és 'multi'
            bank.kbFns = bank.kbFns.map((f, j) => (f === p.fn && j !== idx) ? '' : f);
        }
        bank.kbFns[idx] = p.fn;
    }
    return p;
}

/** Buida una tecla (treu mode/acomp, efecte i funció). */
export function clearMixKey(bank, idx) {
    if (bank.modes && idx < bank.modes.length) bank.modes[idx] = '';
    if (bank.kbFns && idx < bank.kbFns.length) bank.kbFns[idx] = '';
    if (bank.efectos) delete bank.efectos[idx];
}

/** Classifica què hi ha a la tecla `idx`. @returns {{kind:'mode'|'accomp'|'effect'|'fn'|'note', value:string}} */
export function classifyMixKey(bank, idx) {
    const m = (bank && bank.modes && bank.modes[idx]) || '';
    if (m.indexOf('accomp:') === 0) return { kind: 'accomp', value: m.slice(7) };
    if (m) return { kind: 'mode', value: m };
    const eff = bank && bank.efectos && bank.efectos[idx];
    if (eff) return { kind: 'effect', value: eff };
    const fn = (bank && bank.kbFns && bank.kbFns[idx]) || '';
    if (fn) return { kind: 'fn', value: fn };
    return { kind: 'note', value: '' };
}

// ── 2) Pot-takeover ──────────────────────────────────────────────────────────

export const POT_TAKEOVER_MODES = ['hold', 'latch'];

/**
 * Decideix de qui són els potes ara mateix.
 *
 *  - mode 'hold':  els potes són del MODE mentre es manté premuda una tecla-mode;
 *                  en deixar-la anar, tornen al TECLAT. (Prioritza el teclat.)
 *  - mode 'latch': un toc a una tecla-mode FIXA els potes al mode fins a un altre
 *                  toc (a la mateixa tecla o quan s'atura el mode). Mans lliures.
 *
 * Sempre retorna 'keyboard' si no hi ha cap mode actiu.
 */
export class MixPotRouter {
    constructor(takeover = 'hold') {
        this.mode = (takeover === 'latch') ? 'latch' : 'hold';
        this._held = new Set();   // tecles-mode premudes ara (mode 'hold')
        this._latched = null;     // tecla-mode fixada (mode 'latch'), o null
        this._modeActive = false; // hi ha un mode realment sonant?
    }

    /** Canvia el comportament del takeover ('hold' | 'latch'). Reinicia l'estat. */
    setTakeover(takeover) {
        this.mode = (takeover === 'latch') ? 'latch' : 'hold';
        this.clear();
    }

    /** El simulador/firmware informa si hi ha un mode actiu. En aturar-se, neteja l'estat. */
    setModeActive(active) {
        this._modeActive = !!active;
        if (!this._modeActive) this.clear();
    }

    /** Premuda d'una tecla-mode. En 'latch' commuta la fixació; en 'hold' l'afegeix. */
    pressModeKey(idx) {
        if (this.mode === 'latch') {
            this._latched = (this._latched === idx) ? null : idx;
        } else {
            this._held.add(idx);
        }
    }

    /** Release d'una tecla-mode (només rellevant en 'hold'). */
    releaseModeKey(idx) {
        if (this.mode === 'hold') this._held.delete(idx);
    }

    /** Neteja tot l'estat de takeover (STOP, canvi de capa…). */
    clear() {
        this._held.clear();
        this._latched = null;
    }

    /** @returns {'mode'|'keyboard'} de qui són els potes ara. */
    owner() {
        if (!this._modeActive) return 'keyboard';
        if (this.mode === 'latch') return (this._latched !== null) ? 'mode' : 'keyboard';
        return this._held.size > 0 ? 'mode' : 'keyboard';
    }

    /**
     * Quina tecla-mode rep els potes EN DIRECTE ara mateix (per editar-ne els seus
     * paràmetres). Els altres modes actius conserven els seus potes congelats.
     *   - 'hold':  l'última tecla-mode premuda (Set preserva l'ordre d'inserció).
     *   - 'latch': la tecla-mode fixada.
     * @returns {number|null} índex de tecla, o null si els potes són del teclat.
     */
    editTarget() {
        if (this.owner() !== 'mode') return null;
        if (this.mode === 'latch') return this._latched;
        const arr = [...this._held];
        return arr.length ? arr[arr.length - 1] : null;
    }
}

/**
 * Assignador de canals MIDI per als modes simultanis d'una capa MIX. Cada mode
 * actiu agafa un canal lliure del pool; en aturar-se, el retorna. El nombre de
 * canals del pool fixa el màxim de modes simultanis (per defecte 4).
 */
export class MixChannelPool {
    constructor(channels = [4, 5, 6, 7]) {
        this._full = channels.slice();   // pool màxim (setCapacity retalla)
        this._all = channels.slice();
        this._byKey = new Map();   // keyIdx → canal
    }

    /**
     * Limita quants modes poden sonar alhora (1..mida del pool). Paritat amb
     * MixRunner.set_max_modes del firmware (config 'mix_max_modes', defecte 1:
     * un mode fa relleu de l'altre, mai sobreposats). No allibera els actius
     * sobrants: atura'ls abans de retallar.
     */
    setCapacity(n) {
        n = Math.max(1, Math.min(this._full.length, (n | 0) || 1));
        this._all = this._full.slice(0, n);
    }

    /** Màxim de modes simultanis. */
    get capacity() { return this._all.length; }
    /** Modes actius ara mateix. */
    get size() { return this._byKey.size; }
    /** True si encara hi ha algun canal lliure. */
    get hasFree() { return this._byKey.size < this._all.length; }

    /** Canal assignat a una tecla (o null si no en té). */
    channelOf(key) { return this._byKey.has(key) ? this._byKey.get(key) : null; }

    /**
     * Reserva el primer canal lliure per a `key`. Si la tecla ja en tenia un, el manté.
     * @returns {number|null} canal assignat, o null si el pool és ple.
     */
    acquire(key) {
        if (this._byKey.has(key)) return this._byKey.get(key);
        const used = new Set(this._byKey.values());
        const free = this._all.find(c => !used.has(c));
        if (free === undefined) return null;
        this._byKey.set(key, free);
        return free;
    }

    /** Allibera el canal d'una tecla. @returns {number|null} el canal alliberat. */
    release(key) {
        const ch = this._byKey.has(key) ? this._byKey.get(key) : null;
        this._byKey.delete(key);
        return ch;
    }

    /** Allibera tots els canals. */
    clear() { this._byKey.clear(); }

    /** Llista [keyIdx, canal] de tots els modes actius. */
    entries() { return [...this._byKey.entries()]; }
}
