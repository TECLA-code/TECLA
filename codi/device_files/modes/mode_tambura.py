"""
Mode Tambura - Quatre cordes que es polsen en cicle i ressonen l'una sobre l'altra
X: Tempo  Y: Ressonància  Z: Octava
Doble clic a qualsevol tecla: canvi de tonalitat (Sa).

La tambura és el drone de tota la música índia, i és un drone que es MOU:
quatre cordes que es polsen en un cicle constant —Pa, Sa, Sa i el Sa greu—
i que segueixen ressonant mentre es polsa la següent, de manera que el que
se sent és una massa que batega al ritme del cicle. Aquí cada corda és una
nota que s'engega quan es polsa i s'apaga quan la ressonància s'esgota (el
pot Y: a la dreta, cada corda sona fins que li torna el torn i les quatre
se superposen; a l'esquerra, un pluc sec). El tempo és el del cicle, i
l'afinació de la primera corda es tria entre Pa, Ma i Ni, com fan els músics
segons la raga. Una expressió lenta (CC11) fa respirar el conjunt.
"""
import time
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_PRIMERA = (('Pa', 7), ('Ma', 5), ('Ni', 11))


class ModeTambura(BaseMode):
    PARAMS = ('Tempo', 'Ressonància', 'Octava', 'Afinació', 'Respiració', 'Tonalitat')
    POTS = ('Tempo', 'Ressonància', 'Octava')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Tambura"
        self.key = 0
        self.octave = 3
        self.periode = 0.55           # segons entre cordes
        self.resso = 0.8              # 0..1: quant dura cada corda, en cicles
        self.primera = 0
        self.respir = 0.4             # profunditat de l'expressió
        self.corda = 0
        self.sonant = [(-1, 0.0)] * 4 # (nota, off_t) de cada corda
        self.fase = 0.0
        self.expr = -1
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.corda = 0
        self.sonant = [(-1, 0.0)] * 4
        self.expr = -1
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s (%s)" % (self.name, _KEYS[self.key], _PRIMERA[self.primera][0]))

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            self.periode = 1.4 - f * 1.2            # de 0,7 a 5 cordes per segon
        elif nom == 'Ressonància':
            self.resso = 0.15 + f * 3.85            # de sec a quatre cicles sencers
        elif nom == 'Octava':
            self.octave = 2 + int(f * 2.99)
        elif nom == 'Afinació':
            p = min(2, int(f * 3))
            if p != self.primera:
                self.primera = p
                print("%s: primera corda %s" % (self.name, _PRIMERA[p][0]))
        elif nom == 'Respiració':
            self.respir = f
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _notes(self):
        sa = self.octave * 12 + self.key
        return (sa + _PRIMERA[self.primera][1], sa, sa, sa - 12)

    def _apaga(self, i):
        n, _ = self.sonant[i]
        if n >= 0:
            self.send_note_off(n, 0)
            self.sonant[i] = (-1, 0.0)

    def _polsa(self, now):
        i = self.corda
        self._apaga(i)
        n = self._notes()[i]
        if 0 <= n <= 127:
            vel = 74 if i == 3 else (62 if i == 0 else 56)
            self.send_note_on(n, vel)
            self.sonant[i] = (n, now + self.periode * self.resso)
        self.corda = (i + 1) % 4

    def _cc(self, cc, v):
        try:
            from adafruit_midi.control_change import ControlChange
            self.midi_out.send(ControlChange(cc, max(0, min(127, int(v)))))
        except Exception:
            pass

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.potes(pot_values)
        for i in range(4):
            n, off = self.sonant[i]
            if n >= 0 and now >= off:
                self._apaga(i)
        if self.toca('corda', self.periode):
            self._polsa(now)
        # La respiració: un CC11 que puja i baixa cada vuit cicles
        if self.toca('respir', 0.05):
            self.fase = (self.fase + 0.05 / (self.periode * 32.0)) % 1.0
            tri = 1.0 - abs(self.fase * 2.0 - 1.0)
            e = int(127 - self.respir * 70 * (1.0 - tri))
            if e != self.expr:
                self.expr = e
                self._cc(11, e)
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
        return {'key': _KEYS[self.key], 'corda': self.corda + 1, 'interval': self.periode}

    def cleanup(self):
        for i in range(4):
            self._apaga(i)
        self._cc(11, 127)
        self.stop_tracked_notes()
