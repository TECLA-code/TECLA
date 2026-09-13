"""
Mode Núvol - Soroll de debò fet amb massa notes: del degoteig a la paret, del blanc al marró
X: Densitat  Y: Color  Z: Cruixent

El TECLA no té generador de soroll: té setze tecles i un port MIDI. Però el
soroll és, en el fons, massa esdeveniments alhora, i això sí que ho pot
fer. La densitat va d'una espurna cada segon a una allau de seixanta notes
per segon (més d'una per volta del bucle), i el CRUIXENT escurça cada nota
fins que el note-off surt tot seguit del note-on: el que se sent ja no és
una nota sinó un clic, i tres-cents clics per segon són soroll. El COLOR és
el de l'espectre: a l'esquerra el blanc, cada nota independent de
l'anterior i repartida per tot el rang; a la dreta el marró, un passeig
aleatori que es queda a prop d'on era i sona a fregadís. Entremig, el rosa.
El centre i l'amplada retallen la banda; la força, el guany.
"""
import time
from modes.base_mode import BaseMode


class ModeNuvol(BaseMode):
    PARAMS = ('Densitat', 'Color', 'Cruixent', 'Centre', 'Amplada', 'Força')
    POTS = ('Densitat', 'Color', 'Cruixent')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Núvol"
        self.densitat = 0.35
        self.color = 0.5
        self.cruixent = 0.5
        self.centre = 60.0
        self.amplada = 30.0
        self.forca = 1.0
        self.pos = 60.0
        self.pend = []
        self._llavor = 2024

    def setup(self):
        self.initialized = True
        self.pend = []
        self.pos = self.centre
        self._polsos = {}
        print("%s: %s" % (self.name, self._color_nom()))

    def _color_nom(self):
        c = self.color
        return 'blanc' if c < 0.25 else ('rosa' if c < 0.6 else ('vermell' if c < 0.85 else 'marró'))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Densitat':
            self.densitat = f
        elif nom == 'Color':
            abans = self._color_nom()
            self.color = f
            if self._color_nom() != abans:
                print("%s: %s" % (self.name, self._color_nom()))
        elif nom == 'Cruixent':
            self.cruixent = f
        elif nom == 'Centre':
            self.centre = 36.0 + f * 56.0
        elif nom == 'Amplada':
            self.amplada = 3.0 + f * 45.0
        elif nom == 'Força':
            self.forca = 0.25 + f * 0.75
        else:
            return False
        return True

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

    def _espurna(self, now):
        # Blanc: uniforme dins la banda. Marró: passeig aleatori de pas petit.
        c = self.color
        a = self.amplada
        salt_blanc = self._atzar(int(2 * a) + 1) - a
        salt_marro = (self._atzar(200) - 100) / 100.0 * (1.0 + a * 0.08)
        self.pos = self.centre + (self.pos - self.centre) * c + salt_blanc * (1.0 - c) + salt_marro * c
        if self.pos < self.centre - a:
            self.pos = self.centre - a + (self.centre - a - self.pos)
        if self.pos > self.centre + a:
            self.pos = self.centre + a - (self.pos - self.centre - a)
        n = int(self.pos)
        n = 12 if n < 12 else (115 if n > 115 else n)
        durada = 0.004 + (1.0 - self.cruixent) * (1.0 - self.cruixent) * 0.5
        vel = int((45 + self._atzar(60)) * self.forca)
        for p in self.pend:
            if p[0] == n:
                self.send_note_off(n, 0)
                self.pend.remove(p)
                break
        self.send_note_on(n, max(1, min(127, vel)))
        if durada < 0.006:
            self.send_note_off(n, 0)          # el clic: apagada tot seguit
        else:
            self.pend.append([n, now + durada])

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.potes(pot_values)
        self._allibera(now)
        taxa = 1.0 + self.densitat * self.densitat * 59.0      # espurnes per segon
        periode = 1.0 / taxa
        if self.toca('espurna', periode):
            # A densitat alta la taxa passa la del bucle: unes quantes per volta
            n = 1 if periode > 0.008 else 2 + int(self.densitat * 2)
            for _ in range(n):
                if len(self.pend) < 16:
                    self._espurna(now)
        return {'densitat': int(self.densitat * 100), 'color': self._color_nom(), 'notes': len(self.pend)}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
