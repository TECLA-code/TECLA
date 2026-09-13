"""
Mode Eixam - Un núvol de notes curtes que segueix un centre que vagareja
X: Densitat  Y: Dispersió  Z: Centre
Doble clic a qualsevol tecla: canvi de tonalitat (quan hi ha escala).

Una textura no és una melodia ni un ritme: és un conjunt de moltes coses
petites que, juntes, tenen una forma. Aquí les coses petites són notes molt
curtes que cauen a l'atzar al voltant d'un CENTRE, i la forma la posa el
centre mateix, que vagareja com un eixam que es desplaça (un passeig
aleatori que rebota als extrems). La densitat va d'una nota cada dos segons
a trenta per segon, i la dispersió d'una nota sola repetida a dues octaves
de núvol. L'escala pot ser cromàtica (l'eixam pur), pentatònica (el núvol
sona a acord) o de tons sencers (suspès, sense centre). Amb les ràfegues,
l'eixam s'aplega i es dispersa: densitat que puja i baixa sola en onades.
"""
import time
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_ESCALES = (('Cromàtica', None), ('Pentatònica', (0, 2, 4, 7, 9)), ('Tons sencers', (0, 2, 4, 6, 8, 10)))


class ModeEixam(BaseMode):
    PARAMS = ('Densitat', 'Dispersió', 'Centre', 'Durada', 'Escala', 'Vagareig', 'Ràfegues', 'Tonalitat')
    POTS = ('Densitat', 'Dispersió', 'Centre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Eixam"
        self.key = 0
        self.densitat = 0.4
        self.dispersio = 0.4
        self.centre = 64.0
        self.centre_pot = 64.0
        self.durada = 0.09
        self.escala = 0
        self.vagareig = 0.4
        self.rafegues = 0.0
        self.fase = 0.0
        self.pend = []
        self._llavor = 99
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.pend = []
        self.centre = self.centre_pot
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s" % (self.name, _ESCALES[self.escala][0]))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Densitat':
            self.densitat = f
        elif nom == 'Dispersió':
            self.dispersio = f
        elif nom == 'Centre':
            self.centre_pot = 36.0 + f * 56.0
            self.centre = self.centre_pot
        elif nom == 'Durada':
            self.durada = 0.02 + f * f * 0.9
        elif nom == 'Escala':
            e = min(2, int(f * 3))
            if e != self.escala:
                self.escala = e
                print("%s: %s" % (self.name, _ESCALES[e][0]))
        elif nom == 'Vagareig':
            self.vagareig = f
        elif nom == 'Ràfegues':
            self.rafegues = f
        elif nom == 'Tonalitat':
            self.key = min(11, int(f * 12))
        else:
            return False
        return True

    def _quantitza(self, n):
        e = _ESCALES[self.escala][1]
        if e is None:
            return n
        rel = (n - self.key) % 12
        millor = e[0]
        for g in e:
            if abs(g - rel) < abs(millor - rel):
                millor = g
        return n - rel + millor

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

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.potes(pot_values)
        self._allibera(now)
        # El centre vagareja (cada 50 ms un pas) i rebota als extrems
        if self.toca('vaga', 0.05):
            pas = (self._atzar(200) - 100) / 100.0 * self.vagareig * 1.5
            self.centre += pas
            if self.centre < 36.0:
                self.centre = 36.0 + (36.0 - self.centre)
            if self.centre > 92.0:
                self.centre = 92.0 - (self.centre - 92.0)
            if self.rafegues > 0.0:
                self.fase = (self.fase + 0.05 / (6.0 - self.rafegues * 4.0)) % 1.0
        # Densitat: d'una nota cada 2 s a 30 per segon; amb ràfegues, en onades
        d = self.densitat
        if self.rafegues > 0.0:
            ona = 0.5 - 0.5 * __import__('math').cos(self.fase * 6.2832)
            d = d * (0.15 + 0.85 * ona)
        taxa = 0.5 + d * d * 29.5
        if self.toca('nota', 1.0 / taxa):
            amplada = 1 + int(self.dispersio * 24)
            n = int(self.centre + self._atzar(2 * amplada + 1) - amplada)
            n = self._quantitza(n)
            n = 24 if n < 24 else (108 if n > 108 else n)
            vel = 40 + self._atzar(50) + int(20 * d)
            for p in self.pend:
                if p[0] == n:
                    self.send_note_off(n, 0)
                    self.pend.remove(p)
                    break
            if len(self.pend) < 12:
                self.send_note_on(n, min(127, vel))
                self.pend.append([n, now + self.durada])
        for i in range(min(len(button_states), 15)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                if 0.05 < (now - self.last_rel[i]) < 0.4:
                    self.last_rel[i] = 0.0
                    self.key = (self.key + 1) % 12
                    print("%s: %s" % (self.name, _KEYS[self.key]))
                else:
                    self.last_rel[i] = now
            self.last_btn[i] = cur
        return {'centre': int(self.centre), 'densitat': int(self.densitat * 100), 'escala': _ESCALES[self.escala][0]}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
