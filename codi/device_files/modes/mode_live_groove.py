"""Groove - Línia de baix caminant sobre pentatònica. X:tempo Y:CC1 Z:octava. Doble clic: tonalitat."""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PENTA = (0, 2, 4, 7, 9)
_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
_LINE = (0, 2, 4, 7, 9, 7, 4, 2, 0, 4, 7, 9, 7, 4, 2, 0)
_VELS = (100, 70, 80, 90, 75, 65, 75, 70, 95, 75, 85, 90, 70, 65, 70, 85)


class ModeLiveGroove(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Groove"
        self.key_idx = 0
        self.octave = 2
        self.step = 0
        self.last_note = -1
        self.next_t = 0.0
        self.interval = 0.22
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.next_t = time.monotonic()
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.step = 0
        print(f"Groove: {_KEYS[self.key_idx]}")

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
                    self.step = 0
                    print(f"Groove: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self.interval = max(0.08, 0.40 - (x / 127.0) * 0.32)
        self._cc(1, y)
        self.octave = 1 + int((z / 127.0) * 2.99)
        if now >= self.next_t:
            idx = self.step % len(_LINE)
            note = max(24, min(84, self._root() + _LINE[idx]))
            vel = _VELS[idx]
            if self.last_note >= 0:
                self.midi_out.send(self.note_off(self.last_note, 0))
            self.midi_out.send(self.note_on(note, vel))
            self.last_note = note
            self.step += 1
            self.next_t = now + self.interval
        self._dbl(button_states, now)
        return {'key': _KEYS[self.key_idx], 'step': self.step % len(_LINE)}

    def cleanup(self):
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.last_note = -1
        self._cc(1, 0); self._cc(64, 0); self._cc(123, 0)
