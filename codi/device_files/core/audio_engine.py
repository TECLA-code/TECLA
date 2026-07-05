"""
AudioEngine — Motor de síntesi synthio per a TECLA (RP2040 / CircuitPython 10).

Mirall EXACTE del motor Web Audio del simulador (codi/js/tecla-synth.js): el
model de veu i el "patch" de paràmetres són idèntics perquè el so del maquinari
i el del simulador coincideixin.

    oscil·lador (forma d'ona)  →  filtre biquad  →  envolupant ADSR  →  màster
    + LFO de vibrato (to via bend)  + LFO de trèmolo (amplitud)

Sortida: synthio renderitza l'àudio i el treu pel MATEIX pin GP22 que feia servir
el PWM, ara via audiopwmio.PWMAudioOut (PWM + DMA en segon pla). Per a so net cal
un filtre RC al pin; sense filtre sona igualment (més brut).

INTEGRITAT PER DAVANT DE TOT: si synthio/audiopwmio fallen o l'API no coincideix,
el motor queda en mode inactiu (self.ok = False) i mai no llança cap excepció que
pugui aturar el bucle MIDI. main.py manté el camí PWM antic com a alternativa.

CONTRACTE compartit JS ↔ Python: PATCH_DEFAULT i PRESETS han de tenir els mateixos
noms i rangs que tecla-synth.js.
"""
import math
import array
import board
import audiopwmio
import synthio

AUDIO_PIN = board.GP22
SAMPLE_RATE = 22050
_WAVE_LEN = 256
_WAVE_AMP = 30000

# ── Patch per defecte (idèntic a PATCH_DEFAULT de tecla-synth.js) ─────────────
PATCH_DEFAULT = {
    'wave': 'sawtooth',     # 'sine' | 'sawtooth' | 'triangle' | 'square'
    'amp': 0.32,
    'attack': 0.006,
    'decay': 0.12,
    'sustain': 0.72,
    'release': 0.18,
    'filter': 'lowpass',    # 'off' | 'lowpass' | 'highpass' | 'bandpass'
    'cutoff': 4200,
    'q': 0.8,
    'vibratoRate': 5.0,
    'vibratoDepth': 0,      # cents
    'tremoloRate': 0,
    'tremoloDepth': 0,      # 0..1
    # Nivell 1 — filtre expressiu
    'filterEnvAmount': 0,   # 0..1 → fins a 4 octaves d'obertura del cutoff
    'filterEnvDecay': 0.25, # segons
    'lfoCutoffDepth': 0,    # 0..1 → wobble del cutoff (LFO, rate = vibratoRate)
    # Ampliació — més paràmetres
    'detune': 0,            # cents de desafinació fixa (±50)
    'pitchEnvAmount': 0,    # 0..1 → envolupant de to (la nota comença pujada i cau)
}

# ── Presets (idèntics a PRESETS de tecla-synth.js) ───────────────────────────
PRESETS = {
    'Square (clàssic)': {'wave': 'square', 'amp': 0.24, 'attack': 0.002, 'decay': 0.05, 'sustain': 1.0, 'release': 0.04, 'filter': 'off', 'cutoff': 8000, 'q': 0.7, 'vibratoRate': 5, 'vibratoDepth': 0, 'tremoloRate': 0, 'tremoloDepth': 0},
    'Saw pad':          {'wave': 'sawtooth', 'amp': 0.28, 'attack': 0.18, 'decay': 0.3, 'sustain': 0.75, 'release': 0.5, 'filter': 'lowpass', 'cutoff': 2600, 'q': 1.2, 'vibratoRate': 4.5, 'vibratoDepth': 6, 'tremoloRate': 0, 'tremoloDepth': 0},
    'Pluck':            {'wave': 'triangle', 'amp': 0.34, 'attack': 0.002, 'decay': 0.16, 'sustain': 0.0, 'release': 0.12, 'filter': 'lowpass', 'cutoff': 1800, 'q': 2.0, 'vibratoRate': 5, 'vibratoDepth': 0, 'tremoloRate': 0, 'tremoloDepth': 0, 'filterEnvAmount': 0.6, 'filterEnvDecay': 0.18},
    'Bass':             {'wave': 'sawtooth', 'amp': 0.4, 'attack': 0.004, 'decay': 0.1, 'sustain': 0.6, 'release': 0.1, 'filter': 'lowpass', 'cutoff': 700, 'q': 1.6, 'vibratoRate': 5, 'vibratoDepth': 0, 'tremoloRate': 0, 'tremoloDepth': 0, 'filterEnvAmount': 0.45, 'filterEnvDecay': 0.22},
    'Acid':             {'wave': 'sawtooth', 'amp': 0.34, 'attack': 0.002, 'decay': 0.1, 'sustain': 0.4, 'release': 0.08, 'filter': 'lowpass', 'cutoff': 600, 'q': 7.0, 'vibratoRate': 5, 'vibratoDepth': 0, 'tremoloRate': 0, 'tremoloDepth': 0, 'filterEnvAmount': 0.8, 'filterEnvDecay': 0.3},
    'Organ':            {'wave': 'sine', 'amp': 0.3, 'attack': 0.005, 'decay': 0.0, 'sustain': 1.0, 'release': 0.06, 'filter': 'off', 'cutoff': 8000, 'q': 0.7, 'vibratoRate': 6, 'vibratoDepth': 0, 'tremoloRate': 5.5, 'tremoloDepth': 0.22},
    'Wobble':           {'wave': 'sawtooth', 'amp': 0.32, 'attack': 0.01, 'decay': 0.2, 'sustain': 0.8, 'release': 0.2, 'filter': 'lowpass', 'cutoff': 500, 'q': 4.0, 'vibratoRate': 4, 'vibratoDepth': 0, 'tremoloRate': 0, 'tremoloDepth': 0, 'lfoCutoffDepth': 0.7},
}

_FILTER_MODES = ('lowpass', 'highpass', 'bandpass')


def midi_to_frequency(midi_note):
    return 440 * (2 ** ((midi_note - 69) / 12))


def _make_wave(kind):
    """Construeix un període d'una forma d'ona com array.array('h') (int16),
    que synthio accepta directament com a waveform."""
    n = _WAVE_LEN
    buf = array.array('h', bytes(2 * n))
    for i in range(n):
        ph = i / n
        if kind == 'sawtooth':
            v = 2 * ph - 1
        elif kind == 'triangle':
            v = 4 * abs(ph - 0.5) - 1
        elif kind == 'square':
            v = 1.0 if ph < 0.5 else -1.0
        else:  # sine
            v = math.sin(2 * math.pi * ph)
        buf[i] = int(v * _WAVE_AMP)
    return buf


def _make_decay_wave():
    """Forma d'ona de decay (1.0 → 0.0) per a l'envelope de filtre via LFO(once).
    El LFO la recorre una vegada: el cutoff comença obert i decau a la base."""
    n = 64
    buf = array.array('h', bytes(2 * n))
    for i in range(n):
        buf[i] = int(32767 * (1.0 - i / (n - 1)))
    return buf


class AudioEngine:
    def __init__(self, pin=AUDIO_PIN, sample_rate=SAMPLE_RATE):
        self.ok = False
        self.audio = None
        self.synth = None
        self.patch = dict(PATCH_DEFAULT)
        self.notes = {}      # midi → synthio.Note
        self._filters = {}   # midi → synthio.Biquad (per a cutoff/Q en viu)
        self._base = {}      # midi → amplitud base (per a volum/expression en viu)
        self._vol = 1.0
        self._expr = 1.0
        self._mod_vibrato = 0.0   # CC1 → cents addicionals de vibrato
        self._waves = {}
        try:
            for k in ('sine', 'sawtooth', 'triangle', 'square'):
                self._waves[k] = _make_wave(k)
            self._decay_wave = _make_decay_wave()
            self.audio = audiopwmio.PWMAudioOut(pin)
            self.synth = synthio.Synthesizer(sample_rate=sample_rate, channel_count=1)
            self.audio.play(self.synth)
            self.ok = True
        except Exception as e:
            print("AudioEngine inactiu:", e)
            self.ok = False

    # ── Patch / presets ──────────────────────────────────────────────────────

    def set_patch(self, **kw):
        self.patch.update(kw)

    def set_preset(self, name):
        if name in PRESETS:
            self.patch = dict(PATCH_DEFAULT)
            self.patch.update(PRESETS[name])

    # ── Volum (CC7) / expression (CC11) ──────────────────────────────────────

    def _apply_levels(self):
        g = self._vol * self._expr
        p = self.patch
        if p['tremoloDepth'] > 0:
            return  # el trèmolo controla l'amplitud; no la sobreescriguis
        for midi, note in self.notes.items():
            try:
                note.amplitude = self._base.get(midi, 1.0) * g
            except Exception:
                pass

    def set_volume(self, v01):
        self._vol = max(0.0, min(1.0, v01))
        self._apply_levels()

    def set_expression(self, v01):
        self._expr = max(0.0, min(1.0, v01))
        self._apply_levels()

    def set_mod(self, v01):
        # CC1: fins a 50 cents de vibrato addicional (paritat amb tecla-synth.js)
        self._mod_vibrato = max(0.0, min(1.0, v01)) * 50.0

    # ── Notes ────────────────────────────────────────────────────────────────

    def _make_filter(self):
        """Retorna (biquad, dinàmic). 'dinàmic' = el cutoff el mou un bloc
        (envelope i/o LFO) → no s'actualitza en viu amb set_cutoff."""
        p = self.patch
        if p['filter'] not in _FILTER_MODES:
            return None, False
        try:
            mode = {
                'lowpass': synthio.FilterMode.LOW_PASS,
                'highpass': synthio.FilterMode.HIGH_PASS,
                'bandpass': synthio.FilterMode.BAND_PASS,
            }[p['filter']]
        except Exception:
            return None, False

        base = p['cutoff']
        env_amt = p.get('filterEnvAmount', 0) or 0
        lfo_depth = p.get('lfoCutoffDepth', 0) or 0
        try:
            if env_amt > 0 or (lfo_depth > 0 and p['vibratoRate'] > 0):
                # Envelope de filtre (LFO once, forma de decay) i/o wobble (LFO sine)
                sweep = min(18000, base * (2 ** (env_amt * 4))) - base
                decay = max(0.02, p.get('filterEnvDecay', 0.25))
                use_env = env_amt > 0
                use_lfo = lfo_depth > 0 and p['vibratoRate'] > 0
                if use_env and use_lfo:
                    env_b = synthio.LFO(waveform=self._decay_wave, rate=1.0 / decay, scale=sweep, offset=0.0, once=True)
                    wob_b = synthio.LFO(rate=p['vibratoRate'], scale=base * lfo_depth, offset=0.0)
                    freq = synthio.Math(synthio.MathOperation.SUM, base, env_b, wob_b)
                elif use_env:
                    freq = synthio.LFO(waveform=self._decay_wave, rate=1.0 / decay, scale=sweep, offset=base, once=True)
                else:
                    freq = synthio.LFO(rate=p['vibratoRate'], scale=base * lfo_depth, offset=base)
                return synthio.Biquad(mode, frequency=freq, Q=p['q']), True
            return synthio.Biquad(mode, frequency=base, Q=p['q']), False
        except Exception:
            # Fallback robust: filtre estàtic (sense env/LFO) si l'API de blocs falla
            try:
                return synthio.Biquad(mode, frequency=base, Q=p['q']), False
            except Exception:
                return None, False

    def note_on(self, midi, vel=100):
        if not self.ok:
            return
        try:
            if midi in self.notes:
                self.note_off(midi)

            p = self.patch
            env = synthio.Envelope(
                attack_time=max(0.001, p['attack']),
                decay_time=max(0.001, p['decay']),
                release_time=max(0.001, p['release']),
                attack_level=1.0,
                sustain_level=max(0.0, min(1.0, p['sustain'])),
            )
            base_amp = p['amp'] * (vel / 127.0)
            amp = base_amp * self._vol * self._expr

            freq = midi_to_frequency(midi)
            if p.get('detune', 0):
                freq = freq * (2 ** (p['detune'] / 1200.0))   # desafinació fixa
            kwargs = {
                'frequency': freq,
                'waveform': self._waves.get(p['wave'], self._waves['sine']),
                'envelope': env,
                'amplitude': amp,
            }
            filt, filt_dynamic = self._make_filter()
            if filt is not None:
                kwargs['filter'] = filt
                if not filt_dynamic:
                    self._filters[midi] = filt   # només estàtics → cutoff/Q en viu
            # Bend: vibrato (LFO) i/o pitch env (LFO once amb forma de decay). Si tots
            # dos, se sumen amb Math. Bend en octaves (1.0 = +1 octava).
            bend_blocks = []
            pe = p.get('pitchEnvAmount', 0) or 0
            if pe > 0:
                try:
                    bend_blocks.append(synthio.LFO(waveform=self._decay_wave, rate=1.0 / 0.14, scale=pe * 2, offset=0.0, once=True))
                except Exception:
                    pass
            vib_depth = p['vibratoDepth'] + self._mod_vibrato
            if vib_depth > 0 and p['vibratoRate'] > 0:
                bend_blocks.append(synthio.LFO(rate=p['vibratoRate'], scale=vib_depth / 1200.0))
            try:
                if len(bend_blocks) == 2:
                    kwargs['bend'] = synthio.Math(synthio.MathOperation.SUM, bend_blocks[0], bend_blocks[1], 0.0)
                elif len(bend_blocks) == 1:
                    kwargs['bend'] = bend_blocks[0]
            except Exception:
                if bend_blocks:
                    kwargs['bend'] = bend_blocks[0]

            note = synthio.Note(**kwargs)

            # Trèmolo: amplitud com a LFO (oscil·la offset ± scale)
            if p['tremoloDepth'] > 0 and p['tremoloRate'] > 0:
                d = min(1.0, p['tremoloDepth'])
                try:
                    note.amplitude = synthio.LFO(rate=p['tremoloRate'], scale=amp * d / 2, offset=amp * (1 - d / 2))
                except Exception:
                    pass

            self.synth.press(note)
            self.notes[midi] = note
            self._base[midi] = base_amp
        except Exception:
            pass

    def note_off(self, midi):
        if not self.ok:
            return
        note = self.notes.pop(midi, None)
        self._base.pop(midi, None)
        self._filters.pop(midi, None)
        if note is not None:
            try:
                self.synth.release(note)
            except Exception:
                pass

    def all_off(self):
        if not self.ok:
            return
        try:
            self.synth.release_all()
        except Exception:
            for note in list(self.notes.values()):
                try:
                    self.synth.release(note)
                except Exception:
                    pass
        self.notes.clear()
        self._base.clear()
        self._filters.clear()

    # ── Bus de paràmetres del sinte (mateix mapeig que tecla-synth.js) ───────

    def set_waveform_cc(self, v):
        waves = ('sine', 'sawtooth', 'triangle', 'square')
        self.patch['wave'] = waves[max(0, min(3, int(v / 32)))]

    def set_cutoff(self, v):
        hz = 80 * (100 ** (v / 127.0))   # 80 Hz … 8 kHz log
        self.patch['cutoff'] = hz
        if self.patch['filter'] == 'off':
            self.patch['filter'] = 'lowpass'
        for filt in self._filters.values():
            try:
                filt.frequency = hz
            except Exception:
                pass

    def set_resonance(self, v):
        q = 0.3 + (v / 127.0) * 11.7
        self.patch['q'] = q
        for filt in self._filters.values():
            try:
                filt.Q = q
            except Exception:
                pass

    def set_vibrato_rate(self, v):
        self.patch['vibratoRate'] = 0.1 + (v / 127.0) * 11.9

    def set_vibrato_depth(self, v):
        self.patch['vibratoDepth'] = (v / 127.0) * 100

    # Nivell 1 — filtre expressiu (afecten les notes noves)
    def set_filter_env_amount(self, v):
        self.patch['filterEnvAmount'] = v / 127.0
        if self.patch['filter'] == 'off':
            self.patch['filter'] = 'lowpass'

    def set_filter_env_decay(self, v):
        self.patch['filterEnvDecay'] = 0.02 + (v / 127.0) * 1.98

    def set_lfo_cutoff_depth(self, v):
        self.patch['lfoCutoffDepth'] = v / 127.0
        if self.patch['filter'] == 'off':
            self.patch['filter'] = 'lowpass'

    def set_filter_type_cc(self, v):
        # 0..127 → passa-baixos / passa-alts / passa-banda (afecta les notes noves)
        self.patch['filter'] = ('lowpass', 'highpass', 'bandpass')[max(0, min(2, int(v / 43)))]

    # ── Pont MIDI ────────────────────────────────────────────────────────────

    def handle_message(self, msg):
        """Alimenta el motor amb un missatge adafruit_midi (NoteOn/NoteOff/CC).
        Mirall de TeclaSynth.handleMidi del simulador. Mai no llança."""
        try:
            cls = type(msg).__name__
            if cls == 'NoteOn':
                if msg.velocity > 0:
                    self.note_on(msg.note, msg.velocity)
                else:
                    self.note_off(msg.note)
            elif cls == 'NoteOff':
                self.note_off(msg.note)
            elif cls == 'ControlChange':
                c = msg.control
                v = msg.value
                if c == 7:
                    self.set_volume(v / 127.0)
                elif c == 11:
                    self.set_expression(v / 127.0)
                elif c == 1:
                    self.set_mod(v / 127.0)
                elif c == 70:
                    self.set_waveform_cc(v)
                elif c == 74:
                    self.set_cutoff(v)
                elif c == 71:
                    self.set_resonance(v)
                elif c == 73:
                    self.patch['attack'] = (v / 127.0) * 1.2
                elif c == 75:
                    self.patch['decay'] = (v / 127.0) * 1.5
                elif c == 72:
                    self.patch['release'] = 0.01 + (v / 127.0) * 2.0
                elif c == 76:
                    self.set_vibrato_rate(v)
                elif c == 77:
                    self.set_vibrato_depth(v)
                elif c == 78:
                    self.set_filter_env_amount(v)
                elif c == 79:
                    self.set_filter_env_decay(v)
                elif c == 80:
                    self.set_lfo_cutoff_depth(v)
                elif c == 81:
                    self.patch['sustain'] = v / 127.0
                elif c == 82:
                    self.patch['tremoloDepth'] = v / 127.0
                elif c == 83:
                    self.patch['tremoloRate'] = 0.1 + (v / 127.0) * 11.9
                elif c == 85:
                    self.patch['detune'] = (v / 127.0) * 100 - 50
                elif c == 86:
                    self.set_filter_type_cc(v)
                elif c == 87:
                    self.patch['pitchEnvAmount'] = v / 127.0
                elif c == 120 or c == 123:
                    self.all_off()
        except Exception:
            pass  # el so mai no ha de trencar el flux MIDI

    def attach_to_midi(self, midi_out):
        """Embolcalla midi_out.send perquè CADA mode que enviï MIDI soni pel
        motor, igual que el wrap webMidi.send del simulador. Idempotent."""
        if not self.ok or getattr(midi_out, '_tecla_audio_attached', False):
            return
        _orig_send = midi_out.send

        def _send_with_audio(msg, *a, **k):
            if isinstance(msg, (list, tuple)):
                for _m in msg:
                    self.handle_message(_m)
            else:
                self.handle_message(msg)
            return _orig_send(msg, *a, **k)

        midi_out.send = _send_with_audio
        midi_out._tecla_audio_attached = True
