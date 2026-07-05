"""
Mode Phase - Phasing minimalista a l'estil Steve Reich.
Dues veus toquen la mateixa cel.lula melodica; la segona avanca una mica
mes de pressa i es va desfasant, creant patrons d'interferencia que
muten lentament. Procés sonor diferent de Glass (arpegis) o Einaudi.
X: Tempo (velocitat base)
Y: Desfasament (com de mes rapida va la veu B)
Z: Separacio d'octava de la veu B
Doble clic: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode

# Cel.lula tipus Piano Phase (graus sobre tonica), 12 notes
_CELL = (0, 2, 4, 7, 9, 11, 9, 7, 4, 2, 0, -1)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')


class ModePhase(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Phase"
        self.key = 0
        self.octave = 4
        self.stepA = 0; self.stepB = 0
        self.tA = 0.0; self.tB = 0.0
        self.durA = 0.16; self.durB = 0.16
        self.lastA = -1; self.lastB = -1
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        now = time.monotonic()
        self.tA = now; self.tB = now
        self.stepA = 0; self.stepB = 0
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        print("Phase: %s" % _KEYS[self.key])

    def _note(self, deg, oct_off=0):
        n = (self.octave + oct_off) * 12 + self.key + deg
        return max(24, min(108, n))

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        base = 0.34 - (x / 127.0) * 0.28        # 0.34s lent -> 0.06s rapid
        self.durA = base
        drift = (y / 127.0) * 0.30               # 0..30% mes rapid
        self.durB = max(0.03, base * (1.0 - drift))
        oct_off = int((z / 127.0) * 2.99)        # 0, 1, 2

        # Veu A (canal 0)
        if now - self.tA >= self.durA:
            self.tA = now
            if self.lastA >= 0:
                self.send_note_off(self.lastA, 0, 0)
            n = self._note(_CELL[self.stepA % len(_CELL)], 0)
            self.send_note_on(n, 95, 0)
            self.lastA = n
            self.stepA = (self.stepA + 1) % len(_CELL)

        # Veu B (canal 1) - desfasada
        if now - self.tB >= self.durB:
            self.tB = now
            if self.lastB >= 0:
                self.send_note_off(self.lastB, 0, 1)
            n = self._note(_CELL[self.stepB % len(_CELL)], oct_off)
            self.send_note_on(n, 78, 1)
            self.lastB = n
            self.stepB = (self.stepB + 1) % len(_CELL)

        # Doble clic: canvi de tonalitat
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < 0.4:
                    self.last_release[i] = 0.0
                    self.key = (self.key + 1) % 12
                    print("Phase: %s" % _KEYS[self.key])
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        offset = (self.stepA - self.stepB) % len(_CELL)
        return {'key': _KEYS[self.key], 'phase': offset, 'drift': round(drift, 2)}

    def stop(self):
        self.cleanup()

    def cleanup(self):
        if self.lastA >= 0:
            self.send_note_off(self.lastA, 0, 0); self.lastA = -1
        if self.lastB >= 0:
            self.send_note_off(self.lastB, 0, 1); self.lastB = -1
        self.stop_tracked_notes()
