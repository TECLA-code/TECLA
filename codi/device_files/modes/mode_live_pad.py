"""Pad - Acord sostingut de 4 veus. X:tipus acord Y:CC1 Z:octava. Doble clic: tonalitat.
Mantenir premut botó 16: harmonia negativa (pot Z tria l'eix; re-voca l'acord)."""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_CHORDS = (
    (0, 4, 7, 12),     # Major
    (0, 3, 7, 12),     # Menor
    (0, 2, 7, 12),     # Sus2
    (0, 5, 7, 12),     # Sus4
    (0, 4, 7, 11),     # Maj7
    (0, 3, 7, 10),     # Min7
    (0, 3, 6, 10),     # Dim7
)
_CNAMES = ('Maj', 'Min', 'Sus2', 'Sus4', 'Maj7', 'Min7', 'Dim7')
_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeLivePad(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Pad"
        self.key_idx = 0
        self.octave = 3
        self.chord_idx = 0
        self.active_notes = []
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self._start()
        print(f"Pad: {_KEYS[self.key_idx]}{_CNAMES[self.chord_idx]}")

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
        for iv in _CHORDS[self.chord_idx]:
            note = self.negharm(max(24, min(108, root + iv)), self._root() % 12)
            self.active_notes.append(note)
            self.midi_out.send(self.note_on(note, 75))
        self._cc(11, 127)

    def _dbl(self, button_states, now):
        for i in range(min(len(button_states), 16)):
            if i == 15:
                continue
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < 0.4:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self._start()
                    print(f"Pad: {_KEYS[self.key_idx]}{_CNAMES[self.chord_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        prev_neg = (self.neg_active, self.neg_axis)
        self.poll_negharm(button_states, z)
        new_chord = min(6, int((x / 127.0) * 7))
        if new_chord != self.chord_idx:
            self.chord_idx = new_chord
            self._start()
        self._cc(1, y)
        if not self.neg_active:  # Z congelada mentre tria l'eix d'harmonia negativa
            new_oct = 2 + int((z / 127.0) * 2.99)
            if new_oct != self.octave:
                self.octave = new_oct
                self._start()
        if (self.neg_active, self.neg_axis) != prev_neg:  # re-voca en negatiu
            self._start()
        self._dbl(button_states, now)
        return {'key': _KEYS[self.key_idx], 'chord': _CNAMES[self.chord_idx],
                'neg': self.neg_active,
                'axis': self.negharm_axis_name() if self.neg_active else '-'}

    def cleanup(self):
        self._stop()
        self._cc(1, 0); self._cc(11, 127); self._cc(64, 0); self._cc(123, 0)
