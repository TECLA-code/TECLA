"""Caos - Generatiu aleatori controlat sobre pentatònica. X:intensitat Y:CC1 Z:octava. Doble clic: tonalitat."""
import time, random
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PENTA = (0, 2, 4, 7, 9, 12, 14, 16, 19, 21)
_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeLiveCaos(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Caos"
        self.key_idx = 0
        self.octave = 4
        self.notes_on = []
        self.next_t = 0.0
        self.intensity = 0.5
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.next_t = time.monotonic()
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        print(f"Caos: {_KEYS[self.key_idx]}")

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, v):
        try: self.midi_out.send(ControlChange(cc, max(0, min(127, v))))
        except: pass

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
                    print(f"Caos: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self.poll_negharm(button_states, z)
        self.intensity = x / 127.0
        self._cc(1, y)
        if not self.neg_active:  # Z congelada mentre tria l'eix neg.
            self.octave = 3 + int((z / 127.0) * 2.99)
        still = []
        for (n, off_t) in self.notes_on:
            if now >= off_t:
                self.midi_out.send(self.note_off(n, 0))
            else:
                still.append((n, off_t))
        self.notes_on = still
        if now >= self.next_t:
            n_notes = 1 + int(self.intensity * 3)
            root = self._root()
            for _ in range(n_notes):
                iv = _PENTA[random.randint(0, len(_PENTA) - 1)]
                oct_offset = random.randint(-1, 1) * 12
                note = max(24, min(108, root + iv + oct_offset))
                note = self.negharm(note, self._root() % 12)
                vel = int(40 + self.intensity * random.uniform(40, 87))
                dur = random.uniform(0.05, 0.40 + self.intensity * 0.35)
                self.midi_out.send(self.note_on(note, vel))
                self.notes_on.append((note, now + dur))
            gap = max(0.03, 0.50 - self.intensity * 0.44) + random.uniform(0, 0.15)
            self.next_t = now + gap
        self._dbl(button_states, now)
        return {'key': _KEYS[self.key_idx], 'intensity': round(self.intensity, 2)}

    def cleanup(self):
        for (n, _) in self.notes_on:
            self.midi_out.send(self.note_off(n, 0))
        self.notes_on = []
        self._cc(1, 0); self._cc(64, 0); self._cc(123, 0)
