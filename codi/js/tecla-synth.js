/**
 * TeclaSynth — Motor de síntesi Web Audio per al simulador TECLA
 *
 * Mirall del motor `synthio` del dispositiu (RP2040 / CircuitPython). El model
 * de veu és deliberadament idèntic perquè el so del simulador i el del maquinari
 * coincideixin:
 *
 *     oscil·lador (forma d'ona)  →  filtre biquad  →  envolupant ADSR  →  màster
 *     + LFO de vibrato (to)  + LFO de trèmolo (volum)
 *
 * El "patch" (PATCH_DEFAULT / PRESETS) és el CONTRACTE compartit JS ↔ Python.
 * Qualsevol canvi de paràmetres aquí s'ha de reflectir a core/audio_engine.py
 * del dispositiu amb els mateixos noms i rangs.
 *
 * Polifònic: cada nota MIDI activa té la seva pròpia cadena de veu. Es dispara
 * amb noteOn(midi, vel) i s'allibera amb noteOff(midi) (release de l'ADSR).
 */

// ── Conversió nota MIDI → freqüència (idèntica a main.midi_to_frequency) ──────
export function midiToFreq(midi) {
    return 440 * Math.pow(2, (midi - 69) / 12);
}

// ── Patch per defecte: el contracte de paràmetres ────────────────────────────
// Temps en segons; sustain i amp i tremoloDepth en 0..1; cutoff en Hz; q = Q del
// filtre; vibratoDepth en cents; rates en Hz.
export const PATCH_DEFAULT = {
    wave: 'sawtooth',     // 'sine' | 'sawtooth' | 'triangle' | 'square'
    amp: 0.32,            // guany base per veu abans de la velocitat
    attack: 0.006,
    decay: 0.12,
    sustain: 0.72,
    release: 0.18,
    filter: 'lowpass',    // 'off' | 'lowpass' | 'highpass' | 'bandpass'
    cutoff: 4200,
    q: 0.8,
    vibratoRate: 5.0,
    vibratoDepth: 0,      // cents (0 = sense vibrato)
    tremoloRate: 0,
    tremoloDepth: 0,      // 0..1 (0 = sense trèmolo)
    // Nivell 1 — filtre expressiu
    filterEnvAmount: 0,   // 0..1 → fins a 4 octaves d'obertura del cutoff amb la nota
    filterEnvDecay: 0.25, // segons que triga el cutoff a tornar a la base
    lfoCutoffDepth: 0,    // 0..1 → fins a 2 octaves de wobble del cutoff (LFO, rate = vibratoRate)
    // Ampliació — més paràmetres del motor
    detune: 0,            // cents de desafinació fixa de l'oscil·lador (±50)
    pitchEnvAmount: 0,    // 0..1 → envolupant de to (la nota comença pujada i cau)
};

// ── Presets de veu ───────────────────────────────────────────────────────────
export const PRESETS = {
    'Square (clàssic)': { wave: 'square', amp: 0.24, attack: 0.002, decay: 0.05, sustain: 1.0, release: 0.04, filter: 'off', cutoff: 8000, q: 0.7, vibratoRate: 5, vibratoDepth: 0, tremoloRate: 0, tremoloDepth: 0 },
    'Saw pad':          { wave: 'sawtooth', amp: 0.28, attack: 0.18, decay: 0.3, sustain: 0.75, release: 0.5, filter: 'lowpass', cutoff: 2600, q: 1.2, vibratoRate: 4.5, vibratoDepth: 6, tremoloRate: 0, tremoloDepth: 0 },
    'Pluck':            { wave: 'triangle', amp: 0.34, attack: 0.002, decay: 0.16, sustain: 0.0, release: 0.12, filter: 'lowpass', cutoff: 1800, q: 2.0, vibratoRate: 5, vibratoDepth: 0, tremoloRate: 0, tremoloDepth: 0, filterEnvAmount: 0.6, filterEnvDecay: 0.18 },
    'Bass':             { wave: 'sawtooth', amp: 0.4, attack: 0.004, decay: 0.1, sustain: 0.6, release: 0.1, filter: 'lowpass', cutoff: 700, q: 1.6, vibratoRate: 5, vibratoDepth: 0, tremoloRate: 0, tremoloDepth: 0, filterEnvAmount: 0.45, filterEnvDecay: 0.22 },
    'Acid':             { wave: 'sawtooth', amp: 0.34, attack: 0.002, decay: 0.1, sustain: 0.4, release: 0.08, filter: 'lowpass', cutoff: 600, q: 7.0, vibratoRate: 5, vibratoDepth: 0, tremoloRate: 0, tremoloDepth: 0, filterEnvAmount: 0.8, filterEnvDecay: 0.3 },
    'Organ':            { wave: 'sine', amp: 0.3, attack: 0.005, decay: 0.0, sustain: 1.0, release: 0.06, filter: 'off', cutoff: 8000, q: 0.7, vibratoRate: 6, vibratoDepth: 0, tremoloRate: 5.5, tremoloDepth: 0.22 },
    'Wobble':           { wave: 'sawtooth', amp: 0.32, attack: 0.01, decay: 0.2, sustain: 0.8, release: 0.2, filter: 'lowpass', cutoff: 500, q: 4.0, vibratoRate: 4, vibratoDepth: 0, tremoloRate: 0, tremoloDepth: 0, lfoCutoffDepth: 0.7 },
};

export class TeclaSynth {
    /** Veus simultànies màximes abans de robar la més vella. */
    static MAX_VEUS = 48;

    /**
     * Corba de saturació suau: y = tanh(k·x)/k sobre −4..4 d'entrada.
     *
     * Dividir per k (i no pel màxim) deixa el pendent a l'origen exactament a 1:
     * el que ja sonava bé —una nota, un acord— passa igual, sense tocar-lo. El
     * sostre queda a 1/k, així que per molt que s'hi acumulin veus la sortida no
     * passa d'aquí i el que abans era retall digital ara és compressió.
     */
    static _corbaTanh(n = 4096, k = 1.4) {
        const c = new Float32Array(n);
        for (let i = 0; i < n; i++) {
            const x = (i / (n - 1)) * 8 - 4;          // −4 … 4
            c[i] = Math.tanh(k * x) / k;
        }
        return c;
    }

    constructor() {
        this.ctx = null;
        this.master = null;
        this.enabled = false;
        this.patch = { ...PATCH_DEFAULT };      // patch del TECLAT (canal per defecte)
        this.channelPatches = {};  // canal MIDI → patch propi (so per veu: teclat vs modes)
        this.voices = new Map();   // (canal*128+midi) → voice object
        this._masterVol = 1.0;     // CC7 volum (0..1)
        this._expr = 1.0;          // CC11 expression (0..1)
        this._modVibrato = 0;      // CC1 modulation → cents addicionals de vibrato
    }

    // ── Cicle de vida ────────────────────────────────────────────────────────

    /** Crea l'AudioContext. Cal cridar-ho des d'un gest d'usuari (autoplay). */
    enable() {
        if (this.ctx) { this.ctx.resume?.(); this.enabled = true; return; }
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        this.ctx = new AC();
        this.master = this.ctx.createGain();
        this.master.gain.value = this._masterVol * this._expr;

        // Saturació suau a la sortida. Una família de soroll pot posar quaranta
        // veus a sonar alhora i el màster arribava a un RMS de 3 — o sigui,
        // retallat digitalment, que és el pitjor soroll que hi ha: escarransit i
        // dolorós. Una tanh ho doblega en comptes de tallar-ho, que és el que fa
        // qualsevol etapa analògica quan la satures: se sent fort i greixós, no
        // trencat. Amb senyal petit no fa absolutament res (tanh(x) ≈ x).
        //
        // El «clic» en canviar d'acord al drone NO era això: era que _arrenca()
        // callava tot l'acord i l'atacava de nou, i el release del vell se
        // sumava a l'atac del nou —el doble de veus alhora, totes en fase— un
        // transitori que la tanh no pot arreglar. Es corregeix a l'origen, amb
        // conducció de veus al generador (mode_*.py, _arrenca): només es toca la
        // nota que de debò canvia. Un compressor aquí no hi feia res (el drone
        // sostingut viu sempre per sobre del llindar) i amb el guany de
        // compensació encara saturava més.
        this.limit = this.ctx.createWaveShaper();
        this.limit.curve = TeclaSynth._corbaTanh();
        this.limit.oversample = '2x';
        this.master.connect(this.limit).connect(this.ctx.destination);
        this.enabled = true;
    }

    disable() {
        this.allOff();
        this.enabled = false;
    }

    setPatch(partial) {
        Object.assign(this.patch, partial);
    }

    setPreset(name) {
        if (PRESETS[name]) this.patch = { ...PATCH_DEFAULT, ...PRESETS[name] };
    }

    // ── So per veu (canal MIDI) ──────────────────────────────────────────────
    // El teclat sona pel seu canal (this.patch); cada tecla-mode emet pel SEU
    // canal amb el SEU patch → sons diferents alhora.
    _patchFor(ch) { return this.channelPatches[ch] || this.patch; }
    setChannelPatch(ch, partial) {
        this.channelPatches[ch] = { ...(this.channelPatches[ch] || PATCH_DEFAULT), ...partial };
    }
    setChannelPreset(ch, name) {
        if (PRESETS[name]) this.channelPatches[ch] = { ...PATCH_DEFAULT, ...PRESETS[name] };
    }
    clearChannelPatch(ch) { delete this.channelPatches[ch]; }
    clearChannelPatches() { this.channelPatches = {}; }

    // ── Volum màster (CC7) / expression (CC11) ───────────────────────────────

    _applyMaster() {
        if (this.master) {
            const t = this.ctx.currentTime;
            this.master.gain.setTargetAtTime(this._masterVol * this._expr, t, 0.01);
        }
    }
    setVolume(v01) { this._masterVol = Math.max(0, Math.min(1, v01)); this._applyMaster(); }
    setExpression(v01) { this._expr = Math.max(0, Math.min(1, v01)); this._applyMaster(); }

    // ── Notes ────────────────────────────────────────────────────────────────

    noteOn(midi, vel = 100, ch = 0) {
        if (!this.enabled || !this.ctx) return;
        const key = ch * 128 + midi;
        if (this.voices.has(key)) this._killVoice(key, true);  // retrigger net

        // Sostre de veus: la família de soroll pot arribar a mil notes per segon
        // i cada veu són tres o quatre nodes de Web Audio. Passat el sostre, la
        // més vella deixa pas — robatori de veu, com qualsevol sintetitzador
        // polifònic. Sense això el navegador es queda sense àudio i calla del tot.
        if (this.voices.size >= TeclaSynth.MAX_VEUS) {
            this._killVoice(this.voices.keys().next().value, true);
        }

        const ctx = this.ctx;
        const t = ctx.currentTime;
        const p = this._patchFor(ch);
        const freq = midiToFreq(midi);

        // Oscil·lador
        const osc = ctx.createOscillator();
        osc.type = p.wave;
        if (p.detune) osc.detune.value = p.detune;   // desafinació fixa (el vibrato s'hi suma)
        // Envolupant de to: la nota comença pujada i cau a la freqüència real (zap/perc).
        if (p.pitchEnvAmount > 0) {
            const startF = freq * Math.pow(2, p.pitchEnvAmount * 2);   // fins a +2 octaves
            osc.frequency.setValueAtTime(Math.min(20000, startF), t);
            osc.frequency.setTargetAtTime(freq, t, 0.14 / 3);
        } else {
            osc.frequency.value = freq;
        }

        // Filtre (opcional)
        let node = osc;
        let filter = null;
        let lfoC = null;
        if (p.filter && p.filter !== 'off') {
            filter = ctx.createBiquadFilter();
            filter.type = p.filter;
            filter.Q.value = p.q;

            // Envelope de filtre: el cutoff s'obre amb la nota i decau (pluck/acid).
            const fEnvOct = (p.filterEnvAmount || 0) * 4;   // 0..4 octaves
            if (fEnvOct > 0) {
                const peakHz = Math.min(18000, p.cutoff * Math.pow(2, fEnvOct));
                filter.frequency.setValueAtTime(peakHz, t);
                filter.frequency.setTargetAtTime(p.cutoff, t + Math.max(0.001, p.attack), Math.max(0.02, p.filterEnvDecay) / 3);
            } else {
                filter.frequency.value = p.cutoff;
            }

            // LFO → cutoff (wobble), additiu sobre detune (cents → logarítmic/musical).
            if ((p.lfoCutoffDepth || 0) > 0 && p.vibratoRate > 0) {
                lfoC = ctx.createOscillator();
                lfoC.type = 'sine';
                lfoC.frequency.value = p.vibratoRate;
                const cg = ctx.createGain();
                cg.gain.value = p.lfoCutoffDepth * 2400;    // fins a 2 octaves
                lfoC.connect(cg).connect(filter.detune);
                lfoC.start(t);
            }

            node.connect(filter);
            node = filter;
        }

        // Envolupant ADSR (GainNode)
        const env = ctx.createGain();
        const peak = Math.max(0.0001, p.amp * (vel / 127));
        const sus = Math.max(0.0001, peak * p.sustain);
        env.gain.setValueAtTime(0.0001, t);
        env.gain.linearRampToValueAtTime(peak, t + Math.max(0.001, p.attack));
        env.gain.setTargetAtTime(sus, t + Math.max(0.001, p.attack), Math.max(0.005, p.decay) / 3);
        node.connect(env);

        const voice = { osc, filter, env, peak, sus, freq, lfoV: null, lfoT: null, lfoC, tremOffset: null, ch, rel: p.release };

        // LFO de trèmolo (volum): env → trem → màster, amb trem.gain = offset + lfo·depth
        if (p.tremoloDepth > 0 && p.tremoloRate > 0) {
            const trem = ctx.createGain();
            trem.gain.value = 1 - p.tremoloDepth;   // base; el ConstantSource el fixa
            const offset = ctx.createConstantSource();
            offset.offset.value = 1 - p.tremoloDepth;
            const lfo = ctx.createOscillator();
            lfo.type = 'sine';
            lfo.frequency.value = p.tremoloRate;
            const lg = ctx.createGain();
            lg.gain.value = p.tremoloDepth;
            offset.connect(trem.gain);
            lfo.connect(lg).connect(trem.gain);
            env.connect(trem);
            trem.connect(this.master);
            offset.start(t);
            lfo.start(t);
            voice.lfoT = lfo;
            voice.tremOffset = offset;
        } else {
            env.connect(this.master);
        }

        // LFO de vibrato (to) — combina patch + modulació CC1
        const vibDepth = p.vibratoDepth + this._modVibrato;
        if (vibDepth > 0 && p.vibratoRate > 0) {
            const lfo = ctx.createOscillator();
            lfo.type = 'sine';
            lfo.frequency.value = p.vibratoRate;
            const lg = ctx.createGain();
            lg.gain.value = vibDepth;          // cents
            lfo.connect(lg).connect(osc.detune);
            lfo.start(t);
            voice.lfoV = lfo;
        }

        osc.start(t);
        this.voices.set(key, voice);
    }

    noteOff(midi, ch = 0) {
        if (!this.enabled || !this.ctx) return;
        const key = ch * 128 + midi;
        const voice = this.voices.get(key);
        if (!voice) return;
        const ctx = this.ctx;
        const t = ctx.currentTime;
        const rel = Math.max(0.01, voice.rel ?? this.patch.release);

        // Release de l'ADSR
        voice.env.gain.cancelScheduledValues(t);
        voice.env.gain.setValueAtTime(Math.max(0.0001, voice.env.gain.value), t);
        voice.env.gain.setTargetAtTime(0.0001, t, rel / 3);

        const stopAt = t + rel * 3 + 0.05;
        try { voice.osc.stop(stopAt); } catch { }
        if (voice.lfoV) try { voice.lfoV.stop(stopAt); } catch { }
        if (voice.lfoT) try { voice.lfoT.stop(stopAt); } catch { }
        if (voice.lfoC) try { voice.lfoC.stop(stopAt); } catch { }
        if (voice.tremOffset) try { voice.tremOffset.stop(stopAt); } catch { }
        this.voices.delete(key);
    }

    _killVoice(key, immediate) {
        const voice = this.voices.get(key);
        if (!voice) return;
        const t = this.ctx.currentTime;
        try { voice.env.gain.cancelScheduledValues(t); } catch { }
        try { voice.env.gain.setTargetAtTime(0.0001, t, 0.005); } catch { }
        const stopAt = t + 0.05;
        try { voice.osc.stop(stopAt); } catch { }
        if (voice.lfoV) try { voice.lfoV.stop(stopAt); } catch { }
        if (voice.lfoT) try { voice.lfoT.stop(stopAt); } catch { }
        if (voice.lfoC) try { voice.lfoC.stop(stopAt); } catch { }
        if (voice.tremOffset) try { voice.tremOffset.stop(stopAt); } catch { }
        this.voices.delete(key);
    }

    allOff() {
        for (const key of [...this.voices.keys()]) this._killVoice(key, true);
        this.voices.clear();
    }

    // ── Pont MIDI: rep el que envia webMidi.send ─────────────────────────────

    handleMidi(type, a, b, ch = 0) {
        if (!this.enabled) return;
        if (type === 'note_on') {
            if (b > 0) this.noteOn(a, b, ch); else this.noteOff(a, ch);
        } else if (type === 'note_off') {
            this.noteOff(a, ch);
        } else if (type === 'control_change') {
            // CCs de mescla
            if (a === 7) this.setVolume(b / 127);            // Volum
            else if (a === 11) this.setExpression(b / 127);  // Expression
            else if (a === 1) this._modVibrato = (b / 127) * 50;  // Mod → fins 50 cents
            // CCs de so (Sound Controllers estàndard) → paràmetres del sinte
            else if (a === 70) this.setWaveformCC(b);        // Forma d'ona
            else if (a === 74) this.setCutoff(b);            // Filtre (Brightness)
            else if (a === 71) this.setResonance(b);         // Ressonància (Timbre)
            else if (a === 73) this.patch.attack = (b / 127) * 1.2;   // Atac
            else if (a === 75) this.patch.decay = (b / 127) * 1.5;    // Decay
            else if (a === 72) this.patch.release = 0.01 + (b / 127) * 2.0; // Release
            else if (a === 76) this.setVibratoRate(b);       // LFO: ritme (compartit)
            else if (a === 77) this.setVibratoDepth(b);      // LFO → to (vibrato)
            else if (a === 78) this.setFilterEnvAmount(b);   // Env de filtre: quantitat
            else if (a === 79) this.setFilterEnvDecay(b);    // Env de filtre: decay
            else if (a === 80) this.setLfoCutoffDepth(b);    // LFO → cutoff (wobble)
            else if (a === 81) this.patch.sustain = b / 127;            // Env Sustain
            else if (a === 82) this.patch.tremoloDepth = b / 127;       // Trèmol (profunditat)
            else if (a === 83) this.patch.tremoloRate = 0.1 + (b / 127) * 11.9; // Trèmol vel.
            else if (a === 85) this.patch.detune = (b / 127) * 100 - 50; // Detune ±50 cents
            else if (a === 86) this.setFilterTypeCC(b);                  // Filtre tipus (LP/HP/BP)
            else if (a === 87) this.patch.pitchEnvAmount = b / 127;      // Pitch env
            else if (a === 120 || a === 123) this.allOff();  // All Sound/Notes Off
        }
    }

    // ── Bus de paràmetres del sinte (mateix mapeig que core/audio_engine.py) ──

    setWaveformCC(v) {
        const waves = ['sine', 'sawtooth', 'triangle', 'square'];
        this.patch.wave = waves[Math.max(0, Math.min(3, Math.floor(v / 32)))];
        // afecta les notes noves; les actives continuen amb la seva forma d'ona
    }

    setCutoff(v) {
        const hz = 80 * Math.pow(100, v / 127);   // 80 Hz … 8 kHz log
        this.patch.cutoff = hz;
        if (this.patch.filter === 'off') this.patch.filter = 'lowpass';
        // En viu només si NO hi ha envelope de filtre (si n'hi ha, l'envelope
        // controla el cutoff; el nou valor és la base per a les notes següents).
        if (this.ctx && !(this.patch.filterEnvAmount > 0)) {
            const t = this.ctx.currentTime;
            for (const voice of this.voices.values()) {
                if (voice.filter) voice.filter.frequency.setTargetAtTime(hz, t, 0.01);
            }
        }
    }

    setResonance(v) {
        const q = 0.3 + (v / 127) * 11.7;
        this.patch.q = q;
        if (this.ctx) {
            const t = this.ctx.currentTime;
            for (const voice of this.voices.values()) {
                if (voice.filter) voice.filter.Q.setTargetAtTime(q, t, 0.01);
            }
        }
    }

    setVibratoRate(v) { this.patch.vibratoRate = 0.1 + (v / 127) * 11.9; }   // 0.1–12 Hz
    setVibratoDepth(v) { this.patch.vibratoDepth = (v / 127) * 100; }        // 0–100 cents

    // Nivell 1 — filtre expressiu (afecten les notes noves)
    setFilterEnvAmount(v) { this.patch.filterEnvAmount = v / 127; if (this.patch.filter === 'off') this.patch.filter = 'lowpass'; }
    setFilterEnvDecay(v) { this.patch.filterEnvDecay = 0.02 + (v / 127) * 1.98; }   // 0.02–2 s
    setLfoCutoffDepth(v) { this.patch.lfoCutoffDepth = v / 127; if (this.patch.filter === 'off') this.patch.filter = 'lowpass'; }

    // Tipus de filtre: 0..127 → passa-baixos / passa-alts / passa-banda. En viu i a les notes noves.
    setFilterTypeCC(v) {
        const types = ['lowpass', 'highpass', 'bandpass'];
        const t = types[Math.max(0, Math.min(2, Math.floor(v / 43)))];
        this.patch.filter = t;
        if (this.ctx) for (const voice of this.voices.values()) { if (voice.filter) voice.filter.type = t; }
    }
}
