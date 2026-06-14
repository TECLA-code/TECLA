"""
Mode Gamelan - Inspirat en el gamelan balines/javanes.
Una melodia nucli (balungan) sona a sota; a sobre, dues figuracions
s'entrellacen (kotekan: polos i sangsih) formant una linia rapida, i un
gong greu marca el final de cada cicle. Escala Slendro o Pelog
(aproximacions temperades). Sonoritat i color molt diferents de la resta.
X: Tempo
Y: Escala (Slendro < 64 < Pelog)
Z: Registre / octava
"""
import time
from modes.base_mode import BaseMode

# Aproximacions temperades (semitons) de les escales de gamelan
_SLENDRO = (0, 2, 5, 7, 9)            # 5 notes ~equidistants
_PELOG = (0, 1, 3, 7, 8)             # 5 graus del pelog
_BALUNG = (0, 1, 2, 4, 2, 3, 1, 0)    # melodia nucli (graus)
_KOTEK_P = (0, 2, 0, 1, 0, 2, 0, 3)   # polos (graus)
_KOTEK_S = (1, 3, 2, 2, 1, 3, 4, 4)   # sangsih (entrellacat)


class ModeGamelan(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Gamelan"
        self.bpm = 120.0
        self.octave = 5
        self.scale = _SLENDRO
        self.use_pelog = False
        self.step = 0
        self.sub = 0
        self.step_dur = 0.12
        self.last_t = 0.0
        self.bal_note = -1
        self.gong_note = -1
        self.kot = []   # (note, off_t) al canal 1

    def setup(self):
        self.initialized = True
        self.step = 0; self.sub = 0
        self._calc()
        self.last_t = time.monotonic()
        print("Gamelan: Slendro")

    def _calc(self):
        self.step_dur = 60.0 / self.bpm / 4.0

    def _n(self, deg, oct_off=0):
        sc = self.scale
        d = deg % len(sc)
        o = deg // len(sc)
        n = (self.octave + oct_off + o) * 12 + sc[d]
        return max(24, min(108, n))

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        self.bpm = 80.0 + (x / 127.0) * 80.0
        self._calc()
        pelog = y >= 64
        if pelog != self.use_pelog:
            self.use_pelog = pelog
            self.scale = _PELOG if pelog else _SLENDRO
            print("Gamelan: %s" % ("Pelog" if pelog else "Slendro"))
        self.octave = 4 + int((z / 127.0) * 2.99)

        # apaga kotekan vencut
        still = []
        for (n, off_t) in self.kot:
            if now >= off_t:
                self.send_note_off(n, 0, 1)
            else:
                still.append((n, off_t))
        self.kot = still

        if now - self.last_t >= self.step_dur:
            self.last_t = now
            # kotekan a cada subpas: alterna polos / sangsih
            ki = self.sub % 8
            part = _KOTEK_P if (self.sub % 2 == 0) else _KOTEK_S
            kn = self._n(part[ki], 1)
            self.send_note_on(kn, 70, 1)
            self.kot.append((kn, now + self.step_dur * 0.9))

            # balungan cada 4 subpassos
            if self.sub % 4 == 0:
                if self.bal_note >= 0:
                    self.send_note_off(self.bal_note, 0, 0)
                bn = self._n(_BALUNG[self.step % len(_BALUNG)], 0)
                self.send_note_on(bn, 95, 0)
                self.bal_note = bn
                self.step = (self.step + 1) % len(_BALUNG)
                # gong a l'inici del cicle
                if self.step == 0:
                    if self.gong_note >= 0:
                        self.send_note_off(self.gong_note, 0, 0)
                    gn = self._n(0, -2)
                    self.send_note_on(gn, 112, 0)
                    self.gong_note = gn
            self.sub += 1

        return {'scale': 'Pelog' if self.use_pelog else 'Slendro',
                'oct': self.octave, 'bpm': int(self.bpm)}

    def stop(self):
        self.cleanup()

    def cleanup(self):
        for (n, _) in self.kot:
            self.send_note_off(n, 0, 1)
        self.kot = []
        if self.bal_note >= 0:
            self.send_note_off(self.bal_note, 0, 0); self.bal_note = -1
        if self.gong_note >= 0:
            self.send_note_off(self.gong_note, 0, 0); self.gong_note = -1
        self.stop_tracked_notes()
