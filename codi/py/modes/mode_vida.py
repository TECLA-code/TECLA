"""
Mode Vida - El Joc de la vida de Conway, una graella que sona per columnes
X: Tempo  Y: Llavor (planador, intermitent, gripau, R-pentòmino, atzar)  Z: Octava

Una graella de 12 × 8 amb les vores enganxades (un tor). La regla és la de
sempre: una cèl·lula viva sobreviu amb dues o tres veïnes, una de morta neix
amb exactament tres. A cada generació, cada columna que té cèl·lules vives
sona: la columna és el grau (dotze graus de pentatònica, dues octaves i
mitja) i quantes n'hi ha és la força. Un planador travessa la graella i se
sent com una escala que gira; l'intermitent alterna dues notes; el gripau
en fa quatre; l'R-pentòmino, que amb cinc cèl·lules triga mil generacions
a estabilitzar-se, és el que més dura i el més imprevisible. Quan la vida
s'extingeix o es queda encallada en un cicle curt, es torna a sembrar amb la
llavor triada. Y tria la llavor (a la dreta del tot, a l'atzar), X el tempo
i Z l'octava.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 7, 9)
_W, _H = 12, 8
_LLAVORS = ('planador', 'intermitent', 'gripau', 'R-pentomino', 'atzar')
# Cada llavor: cel·les (x, y) relatives al centre
_FORMES = (
    ((1, 0), (2, 1), (0, 2), (1, 2), (2, 2)),                    # planador
    ((0, 1), (1, 1), (2, 1)),                                    # intermitent
    ((1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2)),            # gripau
    ((1, 0), (2, 0), (0, 1), (1, 1), (1, 2)),                    # R-pentòmino
)
_GATE = 0.55


class ModeVida(BaseMode):
    PARAMS = ('Tempo', 'Llavor', 'Octava', 'Gate', 'Força', 'Tonalitat')
    POTS = ('Tempo', 'Llavor', 'Octava')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Vida"
        self.bpm = 100.0
        self.step_dur = 60.0 / self.bpm / 2.0
        self.llavor_i = 0
        self.octave = 3
        self.key = 0
        self.gate = _GATE
        self.forca = 1.0
        self.g = [[0] * _W for _ in range(_H)]
        self.hist = []
        self.gen = 0
        self.pend = []
        self._llavor = 31415

    def setup(self):
        self.initialized = True
        self._sembra()
        self.gen = 0
        self.pend = []
        self._polsos = {}
        print("%s: %s" % (self.name, _LLAVORS[self.llavor_i]))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _sembra(self):
        self.g = [[0] * _W for _ in range(_H)]
        self.hist = []
        if self.llavor_i >= len(_FORMES):
            for y in range(_H):
                for x in range(_W):
                    self.g[y][x] = 1 if self._atzar(100) < 28 else 0
        else:
            ox = 4 + self._atzar(3)
            oy = 2 + self._atzar(3)
            for x, y in _FORMES[self.llavor_i]:
                self.g[(oy + y) % _H][(ox + x) % _W] = 1
        if self._viva() == 0:
            self.g[_H // 2][_W // 2] = 1

    def _viva(self):
        t = 0
        for f in self.g:
            for c in f:
                t += c
        return t

    def _generacio(self):
        g = self.g
        nou = []
        for y in range(_H):
            fila = []
            dalt = g[y - 1]
            mig = g[y]
            baix = g[(y + 1) % _H]
            for x in range(_W):
                e = x - 1
                d = (x + 1) % _W
                n = (dalt[e] + dalt[x] + dalt[d] + mig[e] + mig[d]
                     + baix[e] + baix[x] + baix[d])
                if mig[x]:
                    fila.append(1 if (n == 2 or n == 3) else 0)
                else:
                    fila.append(1 if n == 3 else 0)
            nou.append(fila)
        self.g = nou
        # Empremta de la graella per detectar cicles curts (període 1 o 2)
        h = 0
        for y in range(_H):
            for x in range(_W):
                h = (h * 3 + nou[y][x] + x) & 0xFFFFFF
        self.hist.append(h)
        if len(self.hist) > 6:
            self.hist.pop(0)
        if self._viva() == 0 or (len(self.hist) >= 6 and self.hist[-1] == self.hist[-3]
                                 and self.hist[-2] == self.hist[-4]):
            self._sembra()
            print("%s: resembra" % self.name)

    def _nota(self, col):
        n = len(_ESCALA)
        return self.octave * 12 + self.key + _ESCALA[col % n] + 12 * (col // n)

    def _allibera(self, now, totes=False):
        if not self.pend:
            return
        queden = []
        for p in self.pend:
            if totes or now >= p[1]:
                self.send_note_off(p[0], 0)
            else:
                queden.append(p)
        self.pend = queden

    def _pas(self, now):
        self._generacio()
        self.gen += 1
        for x in range(_W):
            n = 0
            for y in range(_H):
                n += self.g[y][x]
            if n == 0:
                continue
            nota = self._nota(x)
            if nota > 120:
                continue
            vel = int((48 + n * 14) * self.forca)
            for p in self.pend:
                if p[0] == nota:
                    self.send_note_off(nota, 0)
                    self.pend.remove(p)
                    break
            self.send_note_on(nota, vel if vel < 127 else 127)
            self.pend.append([nota, now + self.step_dur * self.gate])

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 50.0 + f * 130.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.step_dur = 60.0 / b / 2.0
        elif nom == 'Llavor':
            s = min(len(_LLAVORS) - 1, int(f * len(_LLAVORS)))
            if s != self.llavor_i:
                self.llavor_i = s
                self._sembra()
                print("%s: %s" % (self.name, _LLAVORS[s]))
        elif nom == 'Octava':
            self.octave = 2 + int(f * 2.99)
        elif nom == 'Gate':
            self.gate = 0.1 + f * 0.9
        elif nom == 'Força':
            self.forca = 0.3 + f * 0.7
        elif nom == 'Tonalitat':
            self.key = min(11, int(f * 12))
        else:
            return False
        return True

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self._allibera(now)
        self.potes(pot_values)
        if self.toca('pas', self.step_dur):
            self._pas(now)
        return {'llavor': _LLAVORS[self.llavor_i], 'gen': self.gen, 'bpm': int(self.bpm),
                'vives': self._viva()}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
