"""
Mode Campanar - Volteig de campanes sobre un bordó que respira
X: Tempo  Y: Nombre de campanes (4-8)  Z: Ressò (durada de cada campanada)

El volteig anglès ("change ringing") no toca melodies: toca PERMUTACIONS.
Cada fila fa sonar totes les campanes una vegada, de la més aguda a la més
greu, i d'una fila a la següent només s'intercanvien parelles veïnes: el
"plain hunt", on cada campana va pujant i baixant per la fila com una
llançadora. Amb N campanes el cicle dura 2N files i, com que aquí de tant en
tant una parella "esquiva" (dodging), les files no tornen a coincidir en molta
estona. Entre cada dues files hi ha el silenci d'una campanada —la pausa de
"handstroke" dels campaners de debò— que és el que fa que es reconegui com
un campanar i no com un arpegi.

A sota, el BORDÓ: la campana grossa sostinguda una octava avall, que respira
a poc a poc i es torna a atacar quan el volum s'ha mogut prou (el mecanisme
del Dinamo). Per això el mode és de la família dels drones: el que dura és
el bordó, i les campanes hi passen per sobre. X és el tempo del volteig, Y
quantes campanes hi ha (de quatre a vuit), i Z quant dura cada campanada:
curt sona a carilló, llarg s'apila i esdevé una massa de bronze.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 5, 7, 9, 11)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_OCT = 5              # la campana més aguda viu aquí; les altres baixen per l'escala
_MAX = 8
_BORDO_PER = 9.0      # segons per respiració del bordó
_BORDO_PAS = 12


class ModeCampanar(BaseMode):
    PARAMS = ('Tempo', 'Campanes', 'Ressò', 'Bordó', 'Esquives', 'Tonalitat')
    POTS = ('Tempo', 'Campanes', 'Ressò')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Campanar"
        self.key = 0
        self.bpm = 100.0
        self.interval = 60.0 / self.bpm / 2.0     # una campanada
        self.n = 6
        self.resso = 0.6                          # 0 = curt · 1 = llarg
        self.fila = list(range(_MAX))             # ordre actual de les campanes
        self.pos = 0                              # campana que toca dins la fila
        self.n_fila = 0
        self.pausa = False                        # el silenci de handstroke
        self.pend = []
        self.bordo = -1
        self.bordo_on = False
        self.bordo_vel = 0
        self.bordo_fase = 0.0
        self.t = 0.0
        self.bordo_prof = 0.7
        self.esquives = 8
        self._llavor = 1357
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.fila = list(range(_MAX))
        self.pos = 0
        self.n_fila = 0
        self.pausa = False
        self.pend = []
        self.bordo_on = False
        self.bordo_fase = 0.0
        self.t = time.monotonic()
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %d campanes" % (self.name, _KEYS[self.key], self.n))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _nota_campana(self, c):
        """Campana c (0 = la més aguda) → nota. Baixen per l'escala major."""
        g = -c
        n = len(_ESCALA)
        return _OCT * 12 + self.key + _ESCALA[g % n] + 12 * (g // n)

    def _nota_bordo(self):
        return self._nota_campana(self.n - 1) - 12

    def _canvi(self):
        """Plain hunt: files parelles intercanvien (0,1)(2,3)…; les senars
        (1,2)(3,4)… De tant en tant una parella esquiva (dodge) i el cicle
        s'allarga sense trencar la regla de veïns."""
        f = self.fila
        n = self.n
        inici = 0 if self.n_fila % 2 == 0 else 1
        i = inici
        while i + 1 < n:
            if self._atzar(100) < self.esquives:  # esquiva: aquesta parella no canvia
                i += 2
                continue
            f[i], f[i + 1] = f[i + 1], f[i]
            i += 2
        self.n_fila += 1

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

    def _campanada(self, now):
        if self.pausa:                            # handstroke: un silenci
            self.pausa = False
            return
        c = self.fila[self.pos]
        nota = self._nota_campana(c)
        # La campana grossa sona més fort; la primera de la fila, accentuada
        vel = 70 + c * 5 + (14 if self.pos == 0 else 0)
        vel = 127 if vel > 127 else vel
        for p in self.pend:                       # una campana no es torna a atacar sobre si mateixa
            if p[0] == nota:
                self.send_note_off(nota, 0)
                self.pend.remove(p)
                break
        self.send_note_on(nota, vel)
        durada = self.interval * (0.8 + self.resso * 6.0)
        self.pend.append([nota, now + durada])
        self.pos += 1
        if self.pos >= self.n:
            self.pos = 0
            self._canvi()
            if self.n_fila % 2 == 0:
                self.pausa = True

    def _respira(self, dt):
        """El bordó puja i baixa a poc a poc i es re-ataca quan cal."""
        nota = self._nota_bordo()
        if self.bordo >= 0 and self.bordo != nota:
            if self.bordo_on:
                self.send_note_off(self.bordo, 0)
            self.bordo_on = False
        self.bordo = nota
        self.bordo_fase = (self.bordo_fase + dt / _BORDO_PER) % 1.0
        t = 1.0 - abs(2.0 * self.bordo_fase - 1.0)
        t = t * t * (3.0 - 2.0 * t)
        v = int((30 + 60 * t) * self.bordo_prof)
        if v < 8:
            if self.bordo_on:
                self.send_note_off(nota, 0)
                self.bordo_on = False
            return
        if not self.bordo_on or abs(v - self.bordo_vel) > _BORDO_PAS:
            if self.bordo_on:
                self.send_note_off(nota, 0)
            self.send_note_on(nota, v)
            self.bordo_on = True
            self.bordo_vel = v

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 60.0 + f * 120.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.interval = 60.0 / b / 2.0
        elif nom == 'Campanes':
            n = 4 + int(f * 4.99)
            if n != self.n:
                self.n = n
                self.pos = 0
                self.fila = list(range(_MAX))
                print("%s: %d campanes" % (self.name, n))
        elif nom == 'Ressò':
            self.resso = f
        elif nom == 'Bordó':
            self.bordo_prof = f                     # 0 = bordó mut · 1 = bordó ple
        elif nom == 'Esquives':
            self.esquives = int(f * 40)             # % de parelles que esquiven
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def update(self, pot_values, button_states):
        now = time.monotonic()
        dt = now - self.t
        self.t = now
        self._allibera(now)
        self.potes(pot_values)
        if dt < 0.25:
            self._respira(dt)
        if self.toca('campanada', self.interval):
            self._campanada(now)
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
        return {'key': _KEYS[self.key], 'campanes': self.n, 'fila': self.n_fila,
                'bpm': int(self.bpm)}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        if self.bordo_on:
            self.send_note_off(self.bordo, 0)
            self.bordo_on = False
        self.stop_tracked_notes()
