"""
Mode Autòmat - Les regles elementals de Wolfram, quinze cèl·lules, quinze notes
X: Tempo  Y: Regla (30, 90, 110, 150, 184, 54, 22, 126)  Z: Veus (quantes sonen alhora)

Una fila de quinze cèl·lules, vives o mortes. A cada pas, cada cèl·lula mira
les seves dues veïnes i a si mateixa —vuit veïnats possibles— i la REGLA diu
què surt de cadascun: vuit bits, un número de 0 a 255. Les cèl·lules vives
sonen: cada columna és un grau d'una pentatònica de tres octaves. La 90
dibuixa el triangle de Sierpinski i sona a fractal; la 30 és caos pur; la
110 és Turing-completa i fa estructures que viatgen; la 184 és trànsit de
cotxes; la 150 és una 90 més densa; la 54, la 22 i la 126 tenen cadascuna la
seva textura. Quan una regla mor o es queda encallada, es torna a sembrar.

El pot Z és el nombre de veus: amb una sola sona la cèl·lula viva més greu
(una melodia treta de l'autòmat) i amb vuit sona el clúster sencer. La
llavor és una sola cèl·lula al centre, la clàssica, i amb Y a la dreta del
tot es reparteix a l'atzar.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 7, 9)
_N = 15          # senar a posta: en un anell de 16 la regla 90 és nilpotent i mor cada 16 passos
_REGLES = (90, 30, 110, 150, 184, 54, 22, 126)
_OCT = 3
_GATE = 0.6


class ModeAutomat(BaseMode):
    PARAMS = ('Tempo', 'Regla', 'Veus', 'Octava', 'Gate', 'Força')
    POTS = ('Tempo', 'Regla', 'Veus')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Autòmat"
        self.bpm = 120.0
        self.step_dur = 60.0 / self.bpm / 4.0
        self.regla_i = 0
        self.veus = 4
        self.octava = _OCT
        self.gate = _GATE
        self.forca = 1.0
        self.fila = [0] * _N
        self.ant = [0] * _N
        self.encallat = 0
        self.gen = 0
        self.pend = []
        self._llavor = 9001

    def setup(self):
        self.initialized = True
        self._sembra(False)
        self.gen = 0
        self.pend = []
        self._polsos = {}
        print("%s: regla %d" % (self.name, _REGLES[self.regla_i]))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _sembra(self, atzar):
        if atzar:
            self.fila = [1 if self._atzar(100) < 30 else 0 for _ in range(_N)]
            if sum(self.fila) == 0:
                self.fila[_N // 2] = 1
        else:
            self.fila = [0] * _N
            self.fila[_N // 2] = 1
        self.ant = [0] * _N
        self.encallat = 0

    def _generacio(self):
        """Un pas de l'autòmat sobre una fila circular."""
        regla = _REGLES[self.regla_i]
        f = self.fila
        nova = []
        for i in range(_N):
            veinat = (f[i - 1] << 2) | (f[i] << 1) | f[(i + 1) % _N]
            nova.append((regla >> veinat) & 1)
        # Encallat o mort: si es repeteix (o alterna) unes quantes generacions, resembra
        if nova == f or nova == self.ant or sum(nova) == 0:
            self.encallat += 1
        else:
            self.encallat = 0
        self.ant = f
        self.fila = nova
        if self.encallat >= 6 or sum(nova) == 0:
            self._sembra(True)
            print("%s: resembra" % self.name)

    def _nota(self, col):
        n = len(_ESCALA)
        return self.octava * 12 + _ESCALA[col % n] + 12 * (col // n)

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
        vives = [i for i in range(_N) if self.fila[i]]
        if not vives:
            return
        # Quantes veus: si n'hi ha més que veus, es reparteixen per tota la fila
        if len(vives) > self.veus:
            pas = len(vives) / float(self.veus)
            tria = [vives[int(k * pas)] for k in range(self.veus)]
        else:
            tria = vives
        nascudes = sum(1 for i in tria if not self.ant[i])
        for i in tria:
            nota = self._nota(i)
            vel = int((74 + (18 if not self.ant[i] else 0) + min(20, nascudes * 4)) * self.forca)
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
            b = 60.0 + f * 120.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.step_dur = 60.0 / b / 4.0
        elif nom == 'Regla':
            r = min(len(_REGLES) - 1, int(f * len(_REGLES)))
            if r != self.regla_i:
                self.regla_i = r
                self._sembra(v > 120)
                print("%s: regla %d" % (self.name, _REGLES[r]))
        elif nom == 'Veus':
            self.veus = 1 + int(f * 7.99)
        elif nom == 'Octava':
            self.octava = 2 + int(f * 2.99)
        elif nom == 'Gate':
            self.gate = 0.1 + f * 0.9
        elif nom == 'Força':
            self.forca = 0.3 + f * 0.7
        else:
            return False
        return True

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self._allibera(now)
        self.potes(pot_values)
        if self.toca('pas', self.step_dur):
            self._pas(now)
        return {'regla': _REGLES[self.regla_i], 'gen': self.gen, 'bpm': int(self.bpm),
                'vives': sum(self.fila)}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
