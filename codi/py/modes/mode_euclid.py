"""
Mode Euclid - Ritmes euclidians generats algorítmicament.
Reparteix K pulsacions el més uniformement possible sobre 16 passos
(algorisme de Bresenham, equivalent a Bjorklund per a usos musicals).
A diferencia de Techno/Groove (patrons escrits a ma), aqui els patrons
neixen de les matematiques i muten amb els potenciometres.
X: Tempo (90-150 BPM)
Y: Densitat (omple cada veu amb mes pulsacions)
Z: Rotacio (desplaca els accents dins el compas)
"""
import time
from modes.base_mode import BaseMode

_KICK = 36; _SNARE = 38; _HH = 42
_GATE = 0.045
_DRUM_CH = 9


def _euclid(k, n):
    """Distribueix k pulsacions sobre n passos (Bresenham)."""
    if k <= 0:
        return tuple(0 for _ in range(n))
    if k >= n:
        return tuple(1 for _ in range(n))
    pat = []
    bucket = 0
    for _ in range(n):
        bucket += k
        if bucket >= n:
            bucket -= n
            pat.append(1)
        else:
            pat.append(0)
    return tuple(pat)


def _rot(pat, r):
    n = len(pat)
    if n == 0:
        return pat
    r = r % n
    if not r:
        return pat
    return pat[-r:] + pat[:-r]


class ModeEuclid(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Euclid"
        self.bpm = 120.0
        self.step = 0
        self.step_dur = 0.125
        self.last_step_t = 0.0
        self.rot = 0
        self.k_kick = 4; self.k_snare = 2; self.k_hh = 8
        self._dirty = True
        self.p_kick = (); self.p_snare = (); self.p_hh = ()
        self.pending = []  # (note, channel, off_t)

    def setup(self):
        self.initialized = True
        self.step = 0
        self._calc()
        self._rebuild()
        self.last_step_t = time.monotonic()
        print("Euclid: K=%d S=%d H=%d" % (self.k_kick, self.k_snare, self.k_hh))

    def _calc(self):
        self.step_dur = 60.0 / self.bpm / 4.0

    def _rebuild(self):
        self.p_kick = _rot(_euclid(self.k_kick, 16), self.rot)
        self.p_snare = _rot(_euclid(self.k_snare, 16), self.rot + 4)
        self.p_hh = _rot(_euclid(self.k_hh, 16), self.rot)
        self._dirty = False

    def _release(self, now):
        still = []
        for (n, ch, off_t) in self.pending:
            if now >= off_t:
                self.send_note_off(n, 0, ch)
            else:
                still.append((n, ch, off_t))
        self.pending = still

    def _hit(self, note, vel, now):
        self.send_note_on(note, vel, _DRUM_CH)
        self.pending.append((note, _DRUM_CH, now + _GATE))

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        nb = 90.0 + (x / 127.0) * 60.0
        if abs(nb - self.bpm) > 0.4:
            self.bpm = nb; self._calc()
        fill = y / 127.0
        nk = 2 + int(fill * 6); ns = 1 + int(fill * 5); nh = 4 + int(fill * 9)
        nrot = int((z / 127.0) * 15.99)
        if nk != self.k_kick or ns != self.k_snare or nh != self.k_hh or nrot != self.rot:
            self.k_kick = nk; self.k_snare = ns; self.k_hh = nh; self.rot = nrot
            self._dirty = True
        if self._dirty:
            self._rebuild()
        self._release(now)
        if now - self.last_step_t >= self.step_dur:
            self.last_step_t = now
            s = self.step
            if self.p_kick[s]:
                self._hit(_KICK, 110, now)
            if self.p_snare[s]:
                self._hit(_SNARE, 95, now)
            if self.p_hh[s]:
                self._hit(_HH, 60 if s % 2 else 82, now)
            self.step = (self.step + 1) % 16
        return {'k': self.k_kick, 's': self.k_snare, 'h': self.k_hh,
                'rot': self.rot, 'bpm': int(self.bpm)}

    def stop(self):
        self.cleanup()

    def cleanup(self):
        for (n, ch, _) in self.pending:
            self.send_note_off(n, 0, ch)
        self.pending = []
        self.stop_tracked_notes()
