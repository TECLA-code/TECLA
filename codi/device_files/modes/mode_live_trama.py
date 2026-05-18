"""Trama - Textura densa i ràpida (notes curtes solapades). X:densitat Y:CC1 Z:octava. Doble clic: tonalitat."""
import time, random
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PENTA = (0, 2, 4, 7, 9, 12, 14)
_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeLiveTrama(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Trama"
        self.key_idx = 0
        self.octave = 4
        self.notes_on = []
        self.next_t = 0.0
        self.interval = 0.12
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.next_t = time.monotonic()
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        print(f"Trama: {_KEYS[self.key_idx]}")

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, v):
        try: self.midi_out.send(ControlChange(cc, max(0, min(127, v))))
        except: pass

    def _dbl(self, button_states, now):
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < 0.4:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    print(f"Trama: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self.interval = max(0.04, 0.35 - (x / 127.0) * 0.31)
        self._cc(1, y)
        self.octave = 3 + int((z / 127.0) * 2.99)
        still = []
        for (n, off_t) in self.notes_on:
            if now >= off_t:
                self.midi_out.send(self.note_off(n, 0))
            else:
                still.append((n, off_t))
        self.notes_on = still
        if now >= self.next_t:
            iv = _PENTA[random.randint(0, len(_PENTA) - 1)]
            note = max(36, min(108, self._root() + iv))
            vel = random.randint(40, 85)
            dur = self.interval * random.uniform(0.6, 1.8)
            self.midi_out.send(self.note_on(note, vel))
            self.notes_on.append((note, now + dur))
            self.next_t = now + self.interval
        self._dbl(button_states, now)
        return {'key': _KEYS[self.key_idx], 'active': len(self.notes_on)}

    def cleanup(self):
        for (n, _) in self.notes_on:
            self.midi_out.send(self.note_off(n, 0))
        self.notes_on = []
        self._cc(1, 0); self._cc(64, 0); self._cc(123, 0)
