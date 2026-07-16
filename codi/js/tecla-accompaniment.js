/**
 * Accompaniment — motor d'acompanyament lleuger per al firmware "Mix".
 *
 * Hostatja diversos PATRONS (ritme/baix/arpegi/seqüència) sobre un rellotge
 * compartit. Cada patró emet MIDI pel SEU canal (→ el seu so al sintetitzador)
 * i segueix un CONTEXT HARMÒNIC compartit (tònica + escala) que el TECLAT
 * actualitza quan canvies de to/escala. Així l'acompanyament encaixa amb el que
 * toques. (El ritme ignora l'harmonia.)
 *
 * Agnòstic de la sortida: rep una sendFn(type, a, b, ch) — al simulador és
 * webMidi.send; al device serà el midi_out. Algorisme idèntic per portar-lo a Python.
 *
 * Ús:
 *   const acc = new Accompaniment((t,a,b,ch) => webMidi.send(t,a,b,ch));
 *   acc.setContext(60, [0,2,4,5,7,9,11]);  // C major
 *   acc.addPattern('baix', 2);             // baix pel canal 2
 *   // a cada cicle:  acc.tick();
 */

// Cada patró: (n=pas global, ctx={root,scale}, rng) → llista d'events {note, dur, vel}.
// dur en PASSOS (corxeres de setze). El motor programa el note_off.
export const PATTERNS = {
    // Pols/Ritme: pulsació percussiva sobre la tònica greu, a la negra (no harmònic).
    pols(n, ctx) {
        return (n % 4 === 0) ? [{ note: ctx.root - 24, dur: 1, vel: 110 }] : [];
    },
    // Baix: tònica/quinta/octava de la tonalitat, una nota per negra.
    baix(n, ctx) {
        if (n % 4 !== 0) return [];
        const offs = [0, 7, 0, 12];                 // semitons des de la tònica
        return [{ note: ctx.root - 12 + offs[(n >> 2) % offs.length], dur: 3, vel: 100 }];
    },
    // Arpegi/Pad: arpegia la tríada diatònica de la tonalitat (graus 0,2,4 de l'escala).
    arpegi(n, ctx) {
        if (n % 2 !== 0) return [];
        const sc = ctx.scale;
        const triad = [sc[0], sc[2 % sc.length], sc[4 % sc.length]];
        return [{ note: ctx.root + triad[(n >> 1) % triad.length], dur: 2, vel: 85 }];
    },
    // Seqüència: melodia generativa dins l'escala (caminada determinista per al test).
    sequencia(n, ctx, rng) {
        if (n % 2 !== 0) return [];
        const deg = Math.floor(rng() * ctx.scale.length);
        return [{ note: ctx.root + 12 + ctx.scale[deg], dur: 1, vel: 90 }];
    },
};

function _mulberry(seed) {
    let a = seed >>> 0;
    return () => {
        a = (a + 0x6D2B79F5) | 0;
        let t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

export class Accompaniment {
    constructor(sendFn, now) {
        this.send = sendFn;
        this._now = now || (() => performance.now());
        this.bpm = 110;
        this.ctx = { root: 60, scale: [0, 2, 4, 5, 7, 9, 11] };
        this.patterns = [];        // [{type, channel, _rng}]
        this._step = 0;
        this._nextT = 0;
        this._running = false;
        this._noteOffs = [];       // [{t, note, ch}]
    }

    // El teclat ho crida quan canvia de to/escala perquè l'acompanyament el segueixi.
    setContext(root, scale) {
        this.ctx = { root, scale: (scale && scale.length) ? scale.slice() : [0, 2, 4, 5, 7, 9, 11] };
    }
    setTempo(bpm) { this.bpm = Math.max(40, Math.min(240, bpm)); }
    get stepMs() { return 60000 / this.bpm / 4; }   // ms per corxera de setze

    addPattern(type, channel) {
        if (!PATTERNS[type]) return false;
        if (this.patterns.some(p => p.channel === channel)) this.removePattern(channel);
        this.patterns.push({ type, channel, _rng: _mulberry(0x9E37 + channel * 131 + type.length) });
        this._ensureRunning();
        return true;
    }
    removePattern(channel) {
        this._channelOff(channel);
        this.patterns = this.patterns.filter(p => p.channel !== channel);
        if (!this.patterns.length) this._running = false;
    }
    clear() { this.allOff(); this.patterns = []; this._running = false; }

    _ensureRunning() {
        if (!this._running) { this._running = true; this._step = 0; this._nextT = this._now(); }
    }

    tick() {
        if (this._running) {
            const now = this._now();
            // Protecció: si ve d'un parón llarg, no disparis centenars de passos.
            if (now - this._nextT > this.stepMs * 8) this._nextT = now;
            let guard = 0;
            while (now >= this._nextT && guard++ < 64) {
                this._fireStep(this._step);
                this._step = (this._step + 1) % 65536;
                this._nextT += this.stepMs;
            }
        }
        this._flushOffs();
    }

    _fireStep(n) {
        const sMs = this.stepMs;
        for (const pat of this.patterns) {
            const fn = PATTERNS[pat.type]; if (!fn) continue;
            let events; try { events = fn(n, this.ctx, pat._rng) || []; } catch { events = []; }
            for (const ev of events) {
                const note = Math.max(0, Math.min(127, ev.note | 0));
                this.send('note_on', note, ev.vel || 100, pat.channel);
                this._noteOffs.push({ t: this._now() + (ev.dur || 1) * sMs * 0.9, note, ch: pat.channel });
            }
        }
    }

    _flushOffs() {
        const now = this._now(); const kept = [];
        for (const o of this._noteOffs) { if (now >= o.t) this.send('note_off', o.note, 0, o.ch); else kept.push(o); }
        this._noteOffs = kept;
    }
    _channelOff(ch) {
        const kept = [];
        for (const o of this._noteOffs) { if (o.ch === ch) this.send('note_off', o.note, 0, o.ch); else kept.push(o); }
        this._noteOffs = kept;
    }
    allOff() {
        for (const o of this._noteOffs) this.send('note_off', o.note, 0, o.ch);
        this._noteOffs = [];
    }
}
