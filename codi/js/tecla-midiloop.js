/**
 * MidiLooper — looper/overdub a NIVELL MIDI, agnòstic de la font.
 *
 * A diferència del looper del teclat (kbMode), que grava PRESSES de tecla i només
 * serveix per al motor del teclat, aquest grava els esdeveniments MIDI que passen
 * per webMidi.send (note_on/note_off/control_change) vinguin d'on vinguin —d'un
 * mode autònom O del teclat— i els repeteix en bucle. És la base de la capa híbrida:
 * loop del ritme d'un mode + tocar notes a sobre amb el teclat.
 *
 * Ús:
 *   const loop = new MidiLooper((type,a,b,ch) => webMidi.send(type,a,b,ch));
 *   // a cada esdeveniment sortint:  loop.capture(type,a,b,ch);
 *   loop.toggle();        // grava → tanca i sona → pausa/repren
 *   loop.toggleOverdub(); // afegeix capes mentre sona
 *   loop.clear();
 *
 * El replay crida la MATEIXA send (embolcallada): sona pel sintetitzador i surt per
 * MIDI. Durant el replay, _playingBack evita que capture() es gravi a si mateix.
 */
export class MidiLooper {
    constructor(sendFn, now) {
        this.send = sendFn;
        this._now = now || (() => performance.now());
        this.state = 0;            // 0 aturat · 1 armat · 2 gravant · 3 sonant · 4 pausa
        this.events = [];          // {t, type, a, b, ch}  (t en ms relatius al loop)
        this.loopLen = 0;
        this.overdub = false;
        this._recT0 = 0;
        this._playT0 = 0;
        this._lastPos = 0;
        this._timer = null;
        this._playingBack = false;
        this._heldRec = new Set();     // notes premudes durant la gravació (per tancar-les)
        this._activeLoop = new Set();  // notes que el loop manté sonant (neteja al wrap)
        this.onState = null;           // callback(state)
        this.tickMs = 8;
    }

    // ── Captura (cridar per cada esdeveniment sortint de webMidi.send) ──────────
    capture(type, a, b, ch = 0) {
        if (this._playingBack) return;
        const recording = this.state === 2;
        const overdubbing = this.state === 3 && this.overdub;
        if (!recording && !overdubbing) return;
        let t = this._now() - (recording ? this._recT0 : this._playT0);
        if (overdubbing && this.loopLen > 0) t = ((t % this.loopLen) + this.loopLen) % this.loopLen;
        this.events.push({ t, type, a, b, ch });
        const key = (ch << 8) | (a & 0xff);
        if (type === 'note_on' && b > 0) this._heldRec.add(key);
        else if (type === 'note_off' || (type === 'note_on' && b === 0)) this._heldRec.delete(key);
    }

    // ── Gest principal ─────────────────────────────────────────────────────────
    toggle() {
        if (this.state === 0 || this.state === 1) this._startRecording();
        else if (this.state === 2) this._closeAndPlay();
        else if (this.state === 3) this._pause();
        else if (this.state === 4) this._resume();
        this.onState && this.onState(this.state);
        return this.state;
    }

    toggleOverdub() {
        if (this.state !== 3) return false;
        this.overdub = !this.overdub;
        return this.overdub;
    }

    clear() {
        this._stopTimer();
        this._silence();
        this.state = 0; this.events = []; this.loopLen = 0; this.overdub = false;
        this._heldRec.clear();
        this.onState && this.onState(0);
    }
    stop() { this.clear(); }

    // ── Intern ───────────────────────────────────────────────────────────────
    _startRecording() {
        this.events = []; this._heldRec.clear();
        this._recT0 = this._now();
        this.state = 2;
    }

    _closeAndPlay() {
        this.loopLen = this._now() - this._recT0;
        if (this.loopLen < 50) { this.clear(); return; }
        // Tanca les notes que han quedat premudes en tancar el loop (evita penjades)
        for (const key of this._heldRec) {
            const ch = key >> 8, a = key & 0xff;
            this.send('note_off', a, 0, ch);
            this.events.push({ t: this.loopLen - 1, type: 'note_off', a, b: 0, ch });
        }
        this._heldRec.clear();
        this.events.sort((x, y) => x.t - y.t);
        this._startPlayback();
    }

    _startPlayback() {
        this.state = 3;
        this._playT0 = this._now();
        this._lastPos = 0;
        this._activeLoop.clear();
        this._stopTimer();
        this._timer = setInterval(() => this._tick(), this.tickMs);
    }

    _tick() {
        if (this.state !== 3 || this.loopLen <= 0) return;
        const pos = (this._now() - this._playT0) % this.loopLen;
        this._playingBack = true;
        try {
            if (pos < this._lastPos) {        // s'ha tancat un cicle
                this._fire(this._lastPos, this.loopLen + 1);
                this._wrapCleanup();
                this._fire(0, pos);
            } else {
                this._fire(this._lastPos, pos);
            }
        } finally { this._playingBack = false; }
        this._lastPos = pos;
    }

    _fire(from, to) {
        for (const e of this.events) {
            if (e.t >= from && e.t < to) {
                this.send(e.type, e.a, e.b, e.ch);
                const key = (e.ch << 8) | (e.a & 0xff);
                if (e.type === 'note_on' && e.b > 0) this._activeLoop.add(key);
                else if (e.type === 'note_off' || (e.type === 'note_on' && e.b === 0)) this._activeLoop.delete(key);
            }
        }
    }

    _wrapCleanup() {
        for (const key of this._activeLoop) { const ch = key >> 8, a = key & 0xff; this.send('note_off', a, 0, ch); }
        this._activeLoop.clear();
    }

    _pause() { this.state = 4; this._stopTimer(); this._silence(); }
    _resume() { this._startPlayback(); }
    _stopTimer() { if (this._timer) { clearInterval(this._timer); this._timer = null; } }

    _silence() {
        this._playingBack = true;
        try { for (const key of this._activeLoop) { const ch = key >> 8, a = key & 0xff; this.send('note_off', a, 0, ch); } }
        finally { this._playingBack = false; }
        this._activeLoop.clear();
    }
}

MidiLooper.STATE_NAMES = ['aturat', 'armat', 'gravant', 'sonant', 'pausa'];
