"""
Mode Dub - Reggae/dub one-drop.
Baix profund, "skank" d'acord a contratemps i bateria one-drop (bombo i
caixa junts al tercer temps). Z afegeix retards/eco dub (CC91) i obre o
tanca el filtre (CC74). Genere i emfasi al contratemps, diferent de
qualsevol mode de bateria existent.
X: Tempo (60-95 BPM)
Y: Linia de baix (Roots, Walk, Sparse, Busy)
Z: Dub FX (filtre + eco)
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_KICK = 36; _SNARE = 38; _HH = 42
_DRUM_CH = 9; _BASS_CH = 0; _CHORD_CH = 1
_GATE = 0.05

# Linies de baix: 16 passos, grau d'escala menor o -1 (silenci)
_BASS = (
    (0, -1, -1, 0,  -1, -1, 0, -1,  3, -1, -1, 2,  -1, -1, 0, -1),   # Roots
    (0, -1, 0, -1,  5, -1, -1, -1,  3, -1, -1, -1,  5, -1, 4, -1),   # Walk
    (0, -1, -1, -1,  0, -1, -1, 3,  -1, -1, 2, -1,  0, -1, -1, -1),  # Sparse
    (0, 0, -1, 0,  -1, 7, -1, 5,  3, -1, 3, -1,  2, -1, 0, -1),      # Busy
)
_BNAMES = ('Roots', 'Walk', 'Sparse', 'Busy')
_MIN = (0, 2, 3, 5, 7, 8, 10, 12)   # escala menor natural (semitons)
_CHORD = (0, 3, 7)                  # acord menor per al skank


class ModeDub(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Dub"
        self.bpm = 75.0
        self.octave = 2
        self.step = 0
        self.step_dur = 0.2
        self.last_t = 0.0
        self.pat = 0
        self.pending = []   # (note, ch, off_t)
        self.bass_note = -1
        self._last_fx = -1

    def setup(self):
        self.initialized = True
        self.step = 0
        self._calc()
        self.last_t = time.monotonic()
        print("Dub: %s %dBPM" % (_BNAMES[self.pat], int(self.bpm)))

    def _calc(self):
        self.step_dur = 60.0 / self.bpm / 4.0

    def _cc(self, c, v, ch=0):
        try:
            self.midi_out.send(ControlChange(c, max(0, min(127, int(v))), channel=ch))
        except Exception:
            pass

    def _hit(self, note, vel, ch, now, gate=_GATE):
        self.send_note_on(note, vel, ch)
        self.pending.append((note, ch, now + gate))

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self.bpm = 60.0 + (x / 127.0) * 35.0
        self._calc()
        np = min(3, int((y / 127.0) * 4))
        if np != self.pat:
            self.pat = np
            print("Dub: %s" % _BNAMES[self.pat])
        fx = int((z / 127.0) * 127)
        if fx != self._last_fx:                            # filtre + eco (nomes si canvia)
            self._cc(74, fx, _CHORD_CH)
            self._cc(91, fx, _CHORD_CH)
            self._last_fx = fx

        # release de hits percutius
        still = []
        for (n, ch, off_t) in self.pending:
            if now >= off_t:
                self.send_note_off(n, 0, ch)
            else:
                still.append((n, ch, off_t))
        self.pending = still

        if now - self.last_t >= self.step_dur:
            self.last_t = now
            s = self.step
            # Baix
            deg = _BASS[self.pat][s]
            if deg >= 0:
                if self.bass_note >= 0:
                    self.send_note_off(self.bass_note, 0, _BASS_CH)
                bn = max(24, min(60, self.octave * 12
                                 + _MIN[deg % len(_MIN)] + 12 * (deg // len(_MIN))))
                self.send_note_on(bn, 112, _BASS_CH)
                self.bass_note = bn
            # One-drop: bombo + caixa junts al temps 3 (pas 8)
            if s == 8:
                self._hit(_KICK, 115, _DRUM_CH, now)
                self._hit(_SNARE, 100, _DRUM_CH, now)
            # Hi-hat i skank a contratemps (passos 2, 6, 10, 14)
            if s % 4 == 2:
                self._hit(_HH, 55, _DRUM_CH, now)
                root = (self.octave + 2) * 12
                for iv in _CHORD:
                    self._hit(root + iv, 68, _CHORD_CH, now, gate=self.step_dur * 0.6)
            self.step = (self.step + 1) % 16

        return {'pat': _BNAMES[self.pat], 'bpm': int(self.bpm),
                'fx': int((z / 127.0) * 127)}

    def stop(self):
        self.cleanup()

    def cleanup(self):
        for (n, ch, _) in self.pending:
            self.send_note_off(n, 0, ch)
        self.pending = []
        if self.bass_note >= 0:
            self.send_note_off(self.bass_note, 0, _BASS_CH); self.bass_note = -1
        self._cc(123, 0, _DRUM_CH); self._cc(123, 0, _BASS_CH); self._cc(123, 0, _CHORD_CH)
        self.stop_tracked_notes()
