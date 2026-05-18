"""Pedal - Drone de baix sostingut amb gate rítmic. X:gate Y:CC1 Z:octava. Doble clic: tonalitat."""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeLivePedal(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Pedal"
        self.key_idx = 0
        self.octave = 2
        self.active_notes = []
        self.gate_on = False
        self.gate_period = 0.4
        self.gate_last = 0.0
        self.gate_high = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.gate_last = time.monotonic()
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self._start()
        print(f"Pedal: {_KEYS[self.key_idx]}")

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, v):
        try: self.midi_out.send(ControlChange(cc, max(0, min(127, v))))
        except: pass

    def _stop(self):
        for n in self.active_notes:
            self.midi_out.send(self.note_off(n, 0))
        self.active_notes = []

    def _start(self):
        self._stop()
        root = self._root()
        for iv in (0, 7, 12):
            note = max(24, min(96, root + iv))
            self.active_notes.append(note)
            self.midi_out.send(self.note_on(note, 80))
        self._cc(11, 127)

    def _dbl(self, button_states, now):
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < 0.4:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self._start()
                    print(f"Pedal: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self._cc(1, y)
        new_oct = 1 + int((z / 127.0) * 2.99)
        if new_oct != self.octave:
            self.octave = new_oct
            self._start()
        if x < 8:
            if self.gate_on:
                self.gate_on = False
                self._cc(11, 127)
        else:
            self.gate_on = True
            self.gate_period = max(0.05, 0.50 - (x / 127.0) * 0.45)
            elapsed = now - self.gate_last
            if self.gate_high and elapsed >= self.gate_period * 0.5:
                self.gate_high = False
                self.gate_last = now
                self._cc(11, 0)
            elif not self.gate_high and elapsed >= self.gate_period * 0.5:
                self.gate_high = True
                self.gate_last = now
                self._cc(11, 127)
        self._dbl(button_states, now)
        return {'key': _KEYS[self.key_idx], 'oct': self.octave, 'gate': self.gate_on}

    def cleanup(self):
        self._stop()
        self._cc(11, 127); self._cc(1, 0); self._cc(64, 0); self._cc(123, 0)
