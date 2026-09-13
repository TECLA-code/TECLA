"""
Mode Coral - Quatre veus a l'estil d'un coral: harmonia funcional i conducció de veus
X: Tempo  Y: Mode (major, menor)  Z: Registre
Doble clic a qualsevol tecla: canvi de tonalitat.

Un coral són quatre veus que es mouen juntes i cada una el mínim possible.
Aquí els acords surten de la gramàtica de l'harmonia funcional: de la
tònica es pot anar a qualsevol lloc, de la subdominant es va a la dominant
(o es torna), i de la dominant es torna a la tònica —i a cada frase de
quatre acords hi ha una cadència, plena o suspesa, que s'allarga com un
calderó. Les quatre veus (baix, tenor, contralt, soprano) tenen cada una el
seu registre, i a cada acord nou cada veu va a la nota de l'acord que té més
a prop, sense creuar-se amb les veïnes: la conducció de veus que fa que un
coral soni a coral i no a acords picats. El baix, en canvi, salta: fa
la fonamental, i a la cadència baixa a la tònica. En menor, la dominant és
major (la sensible) com a tot el repertori.
"""
import time
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_MAJOR = (0, 2, 4, 5, 7, 9, 11)
_MENOR = (0, 2, 3, 5, 7, 8, 11)          # harmònica: la sensible per a la dominant
# Graus següents possibles (pesos) des de cada funció: 0 I, 1 ii, 2 iii, 3 IV, 4 V, 5 vi, 6 vii°
_SEGUENT = (
    (1, 3, 1, 5, 4, 3, 1),               # des de I: a tot arreu, sobretot IV i V
    (0, 0, 0, 1, 7, 0, 2),               # ii → V
    (0, 0, 0, 2, 1, 5, 0),               # iii → vi, IV
    (2, 3, 0, 0, 6, 0, 1),               # IV → V, ii, I
    (7, 0, 0, 1, 0, 3, 0),               # V → I (o vi: cadència trencada)
    (0, 3, 0, 5, 1, 0, 0),               # vi → IV, ii
    (6, 0, 0, 0, 0, 0, 0),               # vii° → I
)
_RANG = ((36, 55), (48, 67), (55, 74), (60, 81))   # baix, tenor, contralt, soprano


class ModeCoral(BaseMode):
    PARAMS = ('Tempo', 'Mode', 'Registre', 'Cadència', 'Articulació', 'Tonalitat')
    POTS = ('Tempo', 'Mode', 'Registre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Coral"
        self.key = 0
        self.menor = False
        self.registre = 0             # semitons afegits a tot
        self.bpm = 66.0
        self.cadencia = 4             # acords per frase
        self.artic = 0.95
        self.grau = 0
        self.pas = 0
        self.veus = [-1, -1, -1, -1]
        self.off_t = 0.0
        self.sonant = False
        self._llavor = 4321
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.grau = 0
        self.pas = 0
        self.veus = [-1, -1, -1, -1]
        self.sonant = False
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %s" % (self.name, _KEYS[self.key], 'menor' if self.menor else 'major'))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            self.bpm = 40.0 + f * 80.0
        elif nom == 'Mode':
            m = f >= 0.5
            if m != self.menor:
                self.menor = m
                print("%s: %s" % (self.name, 'menor' if m else 'major'))
        elif nom == 'Registre':
            self.registre = (min(2, int(f * 3)) - 1) * 7
        elif nom == 'Cadència':
            self.cadencia = (2, 4, 8)[min(2, int(f * 3))]
        elif nom == 'Articulació':
            self.artic = 0.5 + f * 0.5
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _escala(self):
        return _MENOR if self.menor else _MAJOR

    def _classes(self, grau):
        """Les tres classes d'alçada (0-11) de la tríada sobre el grau."""
        e = self._escala()
        return tuple((self.key + e[(grau + k) % 7]) % 12 for k in (0, 2, 4))

    def _apaga(self):
        if self.sonant:
            for n in self.veus:
                if n >= 0:
                    self.send_note_off(n, 0)
            self.sonant = False

    def _mes_proper(self, veu, classes, minim, maxim, sota):
        """La nota de l'acord més a prop de la veu, dins del rang i per sobre de la veu de sota."""
        millor = -1
        dist = 999
        for n in range(max(minim, sota + 1), maxim + 1):
            if n % 12 in classes:
                d = abs(n - veu) if veu >= 0 else abs(n - (minim + maxim) // 2)
                if d < dist:
                    dist = d
                    millor = n
        return millor

    def _nou_acord(self, now, negra):
        # El grau següent, amb la cadència al final de la frase
        final = (self.pas % self.cadencia) == self.cadencia - 1
        if final:
            g = 0 if self.grau in (4, 6) or self._atzar(100) < 60 else 4   # plena, o suspesa a V
        else:
            pesos = list(_SEGUENT[self.grau])
            total = sum(pesos)
            r = self._atzar(total)
            g = 0
            for i, p in enumerate(pesos):
                r -= p
                if r < 0:
                    g = i
                    break
        self.grau = g
        classes = self._classes(g)
        self._apaga()
        noves = [-1, -1, -1, -1]
        # El baix fa la fonamental, dins del seu rang
        arrel = (self.key + self._escala()[g]) % 12
        b = 36 + ((arrel - 36) % 12)
        if self.veus[0] >= 0 and abs(b + 12 - self.veus[0]) < abs(b - self.veus[0]):
            b += 12
        noves[0] = b + self.registre
        sota = noves[0]
        for v in (1, 2, 3):
            lo, hi = _RANG[v]
            n = self._mes_proper(self.veus[v], classes, lo + self.registre, hi + self.registre, sota)
            if n < 0:
                n = sota + 3
            noves[v] = n
            sota = n
        vel_base = 72 if not final else 84
        for v in range(4):
            n = noves[v]
            n = 0 if n < 0 else (127 if n > 127 else n)
            self.send_note_on(n, vel_base + (8 if v == 3 else 0) - (6 if v in (1, 2) else 0))
            noves[v] = n
        self.veus = noves
        self.sonant = True
        durada = negra * (2.0 if final else 1.0)
        self.off_t = now + durada * self.artic
        self.pas += 1
        return final

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.potes(pot_values)
        negra = 60.0 / self.bpm
        if self.sonant and now >= self.off_t:
            self._apaga()
        final = (self.pas % self.cadencia) == 0 and self.pas > 0
        periode = negra * (2.0 if final else 1.0)           # el calderó de la cadència
        if self.toca('acord', periode):
            self._nou_acord(now, negra)
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
        return {'key': _KEYS[self.key], 'grau': self.grau + 1, 'bpm': int(self.bpm)}

    def cleanup(self):
        self._apaga()
        self.stop_tracked_notes()
