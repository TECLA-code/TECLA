"""Pols - Pulsació rítmica d'acord (staccato). X:tempo Y:CC1 Z:octava. Doble clic: tonalitat."""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_CHORD = (0, 7, 12)    # quinta + octava (obert, neutre)
_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeLivePols(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Pols"
        self.key_idx = 0
        self.octave = 3
        self.active_notes = []
        self.next_on = 0.0
        self.next_off = 0.0
        self.interval = 0.50
        self.note_len = 0.08
        self.chord_on = False
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.next_on = time.monotonic()
        self.next_off = self.next_on + self.note_len
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        print(f"Pols: {_KEYS[self.key_idx]}")

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, v):
        try: self.midi_out.send(ControlChange(cc, max(0, min(127, v))))
        except: pass

    def _stop_notes(self):
        for n in self.active_notes:
            self.midi_out.send(self.note_off(n, 0))
        self.active_notes = []
        self.chord_on = False

    def _play_chord(self):
        self._stop_notes()
        root = self._root()
        for iv in _CHORD:
            note = max(24, min(108, root + iv))
            self.active_notes.append(note)
            self.midi_out.send(self.note_on(note, 90))
        self.chord_on = True

    def _dbl(self, button_states, now):
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < 0.4:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    print(f"Pols: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self.interval = max(0.12, 1.0 - (x / 127.0) * 0.88)
        self.note_len = self.interval * 0.15
        self._cc(1, y)
        self.octave = 2 + int((z / 127.0) * 2.99)
        if now >= self.next_on:
            self._play_chord()
            self.next_off = now + self.note_len
            self.next_on = now + self.interval
        if self.chord_on and now >= self.next_off:
            self._stop_notes()
        self._dbl(button_states, now)
        return {'key': _KEYS[self.key_idx], 'bpm': round(60 / self.interval)}

    def cleanup(self):
        self._stop_notes()
        self._cc(1, 0); self._cc(64, 0); self._cc(123, 0)
