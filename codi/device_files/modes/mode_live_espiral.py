"""Espiral - Patró en espiral creixent i decreixent. X:velocitat Y:CC1 Z:octava. Doble clic: tonalitat."""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PENTA = (0, 2, 4, 7, 9)
_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeLiveEspiral(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Espiral"
        self.key_idx = 0
        self.octave = 4
        self.pos = 0       # posició dins l'espiral (0..max_pos)
        self.dir = 1       # +1 puja, -1 baixa
        self.max_pos = len(_PENTA) * 2 - 1   # 9
        self.last_note = -1
        self.next_t = 0.0
        self.interval = 0.20
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.next_t = time.monotonic()
        self.pos = 0
        self.dir = 1
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        print(f"Espiral: {_KEYS[self.key_idx]}")

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, v):
        try: self.midi_out.send(ControlChange(cc, max(0, min(127, v))))
        except: pass

    def _note_for_pos(self, pos):
        n = len(_PENTA)
        if pos < n:
            return _PENTA[pos]
        else:
            return _PENTA[n - 1] + 12 + _PENTA[pos - n]

    def _dbl(self, button_states, now):
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < 0.4:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self.pos = 0; self.dir = 1
                    print(f"Espiral: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self.interval = max(0.07, 0.45 - (x / 127.0) * 0.38)
        self._cc(1, y)
        self.octave = 3 + int((z / 127.0) * 2.99)
        if now >= self.next_t:
            note = max(24, min(108, self._root() + self._note_for_pos(self.pos)))
            vel = 65 + int((self.pos / self.max_pos) * 55)
            if self.last_note >= 0:
                self.midi_out.send(self.note_off(self.last_note, 0))
            self.midi_out.send(self.note_on(note, vel))
            self.last_note = note
            self.pos += self.dir
            if self.pos >= self.max_pos:
                self.dir = -1
            elif self.pos <= 0:
                self.dir = 1
            self.next_t = now + self.interval
        self._dbl(button_states, now)
        return {'key': _KEYS[self.key_idx], 'pos': self.pos, 'dir': self.dir}

    def cleanup(self):
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.last_note = -1
        self._cc(1, 0); self._cc(64, 0); self._cc(123, 0)
