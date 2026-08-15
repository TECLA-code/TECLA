/**
 * TeclaThinLink — pont WebSerial entre el TECLA físic (firmware thin) i el navegador.
 *
 * El dispositiu thin envia trames d'entrada (16 botons + 3 pots) pel canal de dades
 * USB (usb_cdc.data); aquesta classe les parseja i les encamina cap als MATEIXOS
 * punts d'entrada que fan servir les tecles virtuals del simulador (onButton/onPot).
 * En sentit invers, envia trames per pintar l'OLED del dispositiu (sendScreen).
 *
 * Paral·lela a tecla-webmidi.js. WebSerial només a Chrome/Edge (com WebMIDI i
 * File System Access).
 *
 * Protocol (text, una línia per missatge, vegeu device_files_thin/code.py):
 *   Device → host:  "I <bitmask16_hex> <p0> <p1> <p2>"
 *   Host → device:  JSON, p. ex. {"s":"kbd","oct":4}
 */

/**
 * El diagnòstic que de fet passa: el dispositiu només exposa la consola.
 *
 * CircuitPython només crea el segon port CDC si el boot.py hi diu
 * `usb_cdc.enable(console=True, data=True)`. El boot.py del MacroPad el deixa
 * a `data=False` a posta (allà interessa que hi hagi un sol port a triar), i
 * si aquell boot.py acaba al dispositiu de l'Instrument, el Sync no pot
 * funcionar de cap manera: no hi ha canal de dades per on rebre les trames.
 */
const DIAG_SENSE_DADES =
    'El TECLA només exposa la consola: li falta el canal de dades. '
    + 'Al boot.py del dispositiu hi ha usb_cdc.enable(console=True, data=False) '
    + 'i cal data=True. Reinstal·la el firmware des de la pestanya Firmware i '
    + 'reinicia el dispositiu (el boot.py només s\'aplica en reiniciar).';

// ── Funcions pures (testejables headless) ───────────────────────────────────

/**
 * Parseja una línia d'entrada del dispositiu.
 * @returns {{mask:number, pots:number[]}|null}
 */
export function decodeInput(line) {
    if (!line) return null;
    const m = /^I\s+([0-9A-Fa-f]{1,4})\s+(\d+)\s+(\d+)\s+(\d+)\s*$/.exec(String(line).trim());
    if (!m) return null;
    const mask = parseInt(m[1], 16) & 0xFFFF;
    const pots = [m[2], m[3], m[4]].map(v => Math.max(0, Math.min(127, parseInt(v, 10) || 0)));
    return { mask, pots };
}

/** Serialitza una trama OLED cap al dispositiu (JSON + salt de línia). */
export function encodeScreen(frame) {
    return JSON.stringify(frame) + '\n';
}

// ── Capa WebSerial ──────────────────────────────────────────────────────────

export class TeclaThinLink {
    constructor() {
        this.port = null;
        this.reader = null;
        this.writer = null;
        this.baudRate = 115200;

        this._rxBuf = '';
        this._mask = 0;
        this._pots = [-1, -1, -1];
        this._readLoopActive = false;

        this.onButton = null;   // (idx, down)
        this.onPot = null;      // (idx, value 0-127)
        this.onStatus = null;   // (state, info)
        this.onLog = null;      // (msg, type)
        this.onDiag = null;     // (info) — resposta "D <json>" del firmware
    }

    isSupported() { return !!(navigator.serial); }
    isConnected() { return !!this.port; }

    /** Connexió AUTOMÀTICA: prova els ports ja autoritzats buscant el de
     *  DADES del TECLA (envia trames "I xxxx" tan bon punt s'obre — el
     *  firmware entra en mode controlador). Només mostra el selector si cap
     *  port autoritzat serveix. */
    async connectAuto() {
        if (!this.isSupported()) {
            return { success: false, error: 'WebSerial no disponible (cal Chrome/Edge)' };
        }
        let candidates = [];
        try { candidates = await navigator.serial.getPorts(); } catch { /* cap */ }
        const motius = [];
        for (const p of candidates) {
            const r = await this._probeDataPort(p);
            if (r.ok) return this._adopt(p);
            motius.push(r.motiu);
        }
        // Si TOTS els ports ja autoritzats són la consola, el selector no hi pot
        // fer res: el dispositiu no exposa canal de dades. Ensenyar-lo només fa
        // que triïs el mateix port una i altra vegada.
        if (candidates.length && motius.every(m => m === 'consola')) {
            return { success: false, sensePortDeDades: true, error: DIAG_SENSE_DADES };
        }
        // Cap port autoritzat vàlid → selector (únic cop; després queda memoritzat)
        let p;
        try { p = await navigator.serial.requestPort(); }
        catch (e) { return (e && e.name === 'NotFoundError') ? { success: false, aborted: true } : { success: false, error: e.message }; }
        const r = await this._probeDataPort(p, 2500);
        if (r.ok) return this._adopt(p);
        // Amb un sol port al sistema no hi ha cap "altre" per triar: el que
        // passa és que el canal de dades està apagat al boot.py.
        let altres = [];
        try { altres = await navigator.serial.getPorts(); } catch { /* cap */ }
        if (r.motiu === 'consola' && altres.length <= 1) {
            return { success: false, sensePortDeDades: true, error: DIAG_SENSE_DADES };
        }
        return {
            success: false,
            error: r.motiu === 'consola'
                ? 'Aquest port és la consola, no el de dades. Prem de nou i tria l\'altre — quedarà memoritzat.'
                : 'Aquest port no diu res. Comprova que el TECLA estigui endollat i prem de nou.',
        };
    }

    /**
     * Obre el port i espera una trama "I …" fins a `ms`. Tanca sempre.
     * @returns {{ok:boolean, motiu:'dades'|'consola'|'silenci'|'ocupat'}}
     *   Saber PER QUÈ ha fallat és el que permet donar un consell útil: un port
     *   que parla però no envia trames és la consola; un que no diu res pot ser
     *   qualsevol altre cacharro connectat a l'ordinador.
     */
    async _probeDataPort(port, ms = 1600) {
        try { await port.open({ baudRate: this.baudRate }); }
        catch { return { ok: false, motiu: 'ocupat' }; }
        const reader = port.readable.getReader();
        const dec = new TextDecoder();
        let buf = '', pending = null, found = false;
        const t0 = Date.now();
        while (Date.now() - t0 < ms) {
            if (!pending) pending = reader.read();
            const r = await Promise.race([pending, new Promise(res => setTimeout(() => res(null), 200))]);
            if (r === null) continue;
            pending = null;
            if (r.done) break;
            buf += dec.decode(r.value, { stream: true });
            if (/^I [0-9A-Fa-f]{1,4} \d+ \d+ \d+/m.test(buf)) { found = true; break; }
            if (buf.length > 4096) break;   // consola parlant: no és el de dades
        }
        try { await reader.cancel(); } catch { /* ja tancat */ }
        try { reader.releaseLock(); } catch { /* noop */ }
        try { await port.close(); } catch { /* noop */ }
        if (found) return { ok: true, motiu: 'dades' };
        // Ha dit alguna cosa però cap trama → la consola (REPL, prints…)
        return { ok: false, motiu: buf.length ? 'consola' : 'silenci' };
    }

    /** Adopta un port validat: reobre net i arrenca el bucle normal. */
    async _adopt(port) {
        try {
            this.port = port;
            await this.port.open({ baudRate: this.baudRate });
            this._watchUnplug();
            this.writer = this.port.writable.getWriter();
            this._rxBuf = '';
            this._mask = 0;
            this._pots = [-1, -1, -1];
            this._startReadLoop();
            this._status('connected');
            this._log('Dispositiu físic sincronitzat (port de dades detectat sol)', 'ok');
            return { success: true };
        } catch (e) {
            this.port = null;
            return { success: false, error: e.message };
        }
    }

    async connect() {
        if (!this.isSupported()) {
            return { success: false, error: 'WebSerial no disponible (cal Chrome/Edge)' };
        }
        try {
            this.port = await navigator.serial.requestPort();
            await this.port.open({ baudRate: this.baudRate });
            this._watchUnplug();
            this.writer = this.port.writable.getWriter();
            this._rxBuf = '';
            this._mask = 0;
            this._pots = [-1, -1, -1];
            this._startReadLoop();
            this._status('connected');
            this._log('Dispositiu físic connectat (thin / WebSerial)', 'ok');
            return { success: true };
        } catch (e) {
            this.port = null;
            if (e && e.name === 'NotFoundError') return { success: false, aborted: true };
            return { success: false, error: e.message };
        }
    }

    /** Desconnexió AUTOMÀTICA quan es desendolla el dispositiu: l'esdeveniment
     *  'disconnect' de WebSerial és més fiable que esperar que la lectura falli. */
    _watchUnplug() {
        if (this._unplugWatched) return;
        this._unplugWatched = true;
        navigator.serial.addEventListener('disconnect', (e) => {
            if (this.port && e.target === this.port) {
                this._log('Dispositiu desendollat — desconnexió automàtica', 'warn');
                this.disconnect();
            }
        });
    }

    async disconnect() {
        this._readLoopActive = false;
        try { if (this.reader) { await this.reader.cancel(); } } catch { /* ja tancat */ }
        try { if (this.writer) { this.writer.releaseLock(); } } catch { /* ja tancat */ }
        try { if (this.port) await this.port.close(); } catch { /* ja tancat */ }
        this.reader = null;
        this.writer = null;
        this.port = null;
        this._status('disconnected');
    }

    async _startReadLoop() {
        this._readLoopActive = true;
        const decoder = new TextDecoder();
        while (this._readLoopActive && this.port && this.port.readable) {
            this.reader = this.port.readable.getReader();
            try {
                while (this._readLoopActive) {
                    const { value, done } = await this.reader.read();
                    if (done) break;
                    if (value) this._onChunk(decoder.decode(value, { stream: true }));
                }
            } catch (e) {
                if (this._readLoopActive) this._log('Lectura interrompuda: ' + e.message, 'warn');
                break;
            } finally {
                try { this.reader.releaseLock(); } catch { /* noop */ }
                this.reader = null;
            }
        }
        // El bucle s'ha acabat sense que ho demanéssim → desconnexió física
        if (this._readLoopActive) {
            this._log('Dispositiu físic desconnectat', 'warn');
            await this.disconnect();
        }
    }

    _onChunk(text) {
        this._rxBuf += text;
        // Si en un mateix tros hi arriben diverses trames d'entrada (per una
        // pausa del navegador o una ràfega del dispositiu), les de BOTONS s'han
        // d'aplicar totes —si no, una premuda curta es perdria— però dels POTES
        // només interessa l'última: aplicar les velles afegeix latència visible
        // al knob per res.
        let ultimaPots = null;
        let nl;
        while ((nl = this._rxBuf.indexOf('\n')) >= 0) {
            const line = this._rxBuf.slice(0, nl);
            this._rxBuf = this._rxBuf.slice(nl + 1);
            const frame = decodeInput(line);
            if (frame) { ultimaPots = frame.pots; this._applyInput(frame, true); continue; }
            // Resposta de diagnòstic del firmware: "D <json>"
            if (line.startsWith('D ')) {
                try { if (this.onDiag) this.onDiag(JSON.parse(line.slice(2))); } catch { /* brossa */ }
            }
        }
        if (ultimaPots) this._aplicaPots(ultimaPots);
        if (this._rxBuf.length > 512) this._rxBuf = '';   // protecció anti-brossa
    }

    /** Demana el diagnòstic al firmware; la resposta arriba per onDiag. */
    async requestDiag() {
        await this.sendScreen({ s: 'diag' });
    }

    /**
     * @param {{mask:number, pots:number[]}} frame
     * @param {boolean} [nomesBotons] si és cert, els potes els aplica qui crida
     *   (amb l'última trama del tros) en comptes de trama a trama.
     */
    _applyInput({ mask, pots }, nomesBotons) {
        // Botons: emet només els bits que han canviat respecte la trama anterior.
        const changed = mask ^ this._mask;
        if (changed) {
            for (let i = 0; i < 16; i++) {
                if (changed & (1 << i)) {
                    const down = !!(mask & (1 << i));
                    try { if (this.onButton) this.onButton(i, down); } catch { /* noop */ }
                }
            }
            this._mask = mask;
        }
        if (!nomesBotons) this._aplicaPots(pots);
    }

    /** Pots: emet els que han canviat (la 1a trama sincronitza posicions inicials). */
    _aplicaPots(pots) {
        for (let i = 0; i < 3; i++) {
            if (pots[i] !== this._pots[i]) {
                this._pots[i] = pots[i];
                try { if (this.onPot) this.onPot(i, pots[i]); } catch { /* noop */ }
            }
        }
    }

    async sendScreen(frame) {
        if (!this.writer) return;
        try {
            await this.writer.write(new TextEncoder().encode(encodeScreen(frame)));
        } catch { /* port tancat */ }
    }

    _status(s, info) { try { if (this.onStatus) this.onStatus(s, info); } catch { /* noop */ } }
    _log(m, t) { try { if (this.onLog) this.onLog(m, t); } catch { /* noop */ } }
}
