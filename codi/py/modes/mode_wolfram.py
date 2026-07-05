"""
Mode Wolfram - Automat cel.lular elemental 1D (regles de Wolfram).
Una fila de 16 cel.lules evoluciona segons una regla binaria; cada
generacio, les cel.lules actives sonen com a notes d'una escala
pentatonica. A diferencia de Vida (2D), aqui emergeixen patrons
fractals tipus Sierpinski (regla 90) o caos (regla 30).
X: Tempo (velocitat de generacio)
Y: Regla (30, 90, 110, 150, 54, 60)
Z: Registre / octava
"""
import time
from modes.base_mode import BaseMode

_RULES = (30, 90, 110, 150, 54, 60)
_SCALE = (0, 2, 4, 7, 9)   # pentatonica major
_N = 16
_MAXVOICES = 6


class ModeWolfram(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Wolfram"
        self.bpm = 110.0
        self.gen_dur = 0.2
        self.last_t = 0.0
        self.rule_idx = 1
        self.octave = 4
        self.row = [0] * _N
        self.row[_N // 2] = 1
        self.playing = []   # notes sonant de la generacio anterior

    def setup(self):
        self.initialized = True
        self._reseed()
        self.last_t = time.monotonic()
        print("Wolfram: regla %d" % _RULES[self.rule_idx])

    def _reseed(self):
        self.row = [0] * _N
        self.row[_N // 2] = 1

    def _next(self, rule):
        r = self.row
        out = [0] * _N
        for i in range(_N):
            left = r[(i - 1) % _N]; c = r[i]; right = r[(i + 1) % _N]
            idx = (left << 2) | (c << 1) | right
            out[i] = (rule >> idx) & 1
        return out

    def _note(self, i):
        deg = _SCALE[i % len(_SCALE)]
        oct_off = i // len(_SCALE)
        n = self.octave * 12 + oct_off * 12 + deg
        return max(24, min(108, n))

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self.bpm = 60.0 + (x / 127.0) * 120.0
        self.gen_dur = 60.0 / self.bpm / 2.0
        ri = int((y / 127.0) * (len(_RULES) - 0.01))
        if ri != self.rule_idx:
            self.rule_idx = ri
            self._reseed()
            print("Wolfram: regla %d" % _RULES[self.rule_idx])
        self.octave = 3 + int((z / 127.0) * 3.99)

        if now - self.last_t >= self.gen_dur:
            self.last_t = now
            # apaga la generacio anterior
            for n in self.playing:
                self.send_note_off(n, 0, 0)
            self.playing = []
            self.row = self._next(_RULES[self.rule_idx])
            if not any(self.row):     # si tot s'apaga, resembra
                self._reseed()
            count = 0
            for i in range(_N):
                if self.row[i] and count < _MAXVOICES:
                    n = self._note(i)
                    self.send_note_on(n, 70 + (i % 4) * 8, 0)
                    self.playing.append(n)
                    count += 1
        return {'rule': _RULES[self.rule_idx], 'cells': sum(self.row),
                'oct': self.octave}

    def stop(self):
        self.cleanup()

    def cleanup(self):
        for n in self.playing:
            self.send_note_off(n, 0, 0)
        self.playing = []
        self.stop_tracked_notes()
