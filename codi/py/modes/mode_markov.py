"""
Mode Markov - Una melodia que surt d'una taula de probabilitats, i el caràcter és la taula
X: Tempo  Y: Caràcter (gregorià, infantil, jazz, ostinat)  Z: Inèrcia
Doble clic a qualsevol tecla: canvi de tonalitat.

Una cadena de Markov no sap res de música: només sap, des del grau on és,
amb quina probabilitat va a cada altre grau. I amb això n'hi ha prou perquè
surti música amb CARÀCTER, perquè la taula és el caràcter. El gregorià va
per graus conjunts i torna sempre a la finalis; l'infantil salta per les
notes de l'acord (do-mi-sol) i repeteix; el jazz fa salts grans, passa per
notes cromàtiques i resol a la setena; l'ostinat es queda en un cicle curt
que de tant en tant es trenca. La inèrcia és una memòria de segon ordre en
una sola xifra: la probabilitat de continuar en la mateixa direcció que el
pas anterior (a la dreta, les línies s'allarguen; a l'esquerra, la melodia
oscil·la). Les durades també surten de la taula: cada caràcter té les
seves. El generador és determinista: la mateixa tonalitat i caràcter donen
la mateixa peça.
"""
import time
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_MAJOR = (0, 2, 4, 5, 7, 9, 11)
# Per a cada caràcter: (nom, pesos dels intervals -4..+4 en graus, pesos de durada (1,2,3,4 corxeres), cromàtic)
_CARACTERS = (
    ('Gregorià', (0, 1, 3, 14, 6, 14, 3, 1, 0), (6, 3, 1, 1), 0),
    ('Infantil', (1, 2, 8, 6, 5, 6, 8, 2, 1), (8, 3, 0, 2), 0),
    ('Jazz', (4, 5, 4, 6, 1, 6, 4, 5, 4), (7, 2, 1, 0), 30),
    ('Ostinat', (0, 0, 9, 0, 0, 0, 9, 0, 2), (6, 0, 0, 0), 0),
)


class ModeMarkov(BaseMode):
    PARAMS = ('Tempo', 'Caràcter', 'Inèrcia', 'Registre', 'Articulació', 'Tonalitat')
    POTS = ('Tempo', 'Caràcter', 'Inèrcia')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Markov"
        self.key = 0
        self.octave = 4
        self.bpm = 108.0
        self.caracter = 0
        self.inercia = 0.5
        self.artic = 0.85
        self.grau = 0
        self.sentit = 1
        self.sonant = -1
        self.off_t = 0.0
        self.espera = 1               # corxeres que queden de la nota actual
        self.pas = 0
        self._llavor = 31337
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.grau = 0
        self.sentit = 1
        self.sonant = -1
        self.espera = 1
        self.pas = 0
        self._llavor = 31337 + self.caracter * 101 + self.key
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %s" % (self.name, _CARACTERS[self.caracter][0], _KEYS[self.key]))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _tria(self, pesos):
        total = 0
        for p in pesos:
            total += p
        r = self._atzar(total)
        for i, p in enumerate(pesos):
            r -= p
            if r < 0:
                return i
        return len(pesos) - 1

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            self.bpm = 60.0 + f * 120.0
        elif nom == 'Caràcter':
            c = min(3, int(f * 4))
            if c != self.caracter:
                self.caracter = c
                print("%s: %s" % (self.name, _CARACTERS[c][0]))
        elif nom == 'Inèrcia':
            self.inercia = f
        elif nom == 'Registre':
            self.octave = 3 + int(f * 2.99)
        elif nom == 'Articulació':
            self.artic = 0.3 + f * 0.7
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def _seguent(self):
        nom, pesos, durades, cromatic = _CARACTERS[self.caracter]
        # Inèrcia: si el sentit anterior era pujar, els intervals cap avall pesen menys
        ajust = []
        for i, p in enumerate(pesos):
            d = i - 4
            if d != 0 and (d > 0) != (self.sentit > 0):
                p = int(p * (1.0 - self.inercia * 0.8) + 0.5)
            ajust.append(p)
        i = self._tria(ajust)
        d = i - 4
        if d != 0:
            self.sentit = 1 if d > 0 else -1
        g = self.grau + d
        # Les vores: la melodia rebota
        if g > 9:
            g = 9 - self._atzar(3)
            self.sentit = -1
        if g < -3:
            g = -3 + self._atzar(3)
            self.sentit = 1
        # El gregorià torna a la finalis al final de cada frase de vuit
        if self.caracter == 0 and self.pas % 8 == 7:
            g = 0 if self._atzar(100) < 70 else 4
        self.grau = g
        nota = self.octave * 12 + self.key + _MAJOR[g % 7] + 12 * (g // 7)
        if cromatic and self._atzar(100) < cromatic and self.pas % 2 == 1:
            nota += 1 if self.sentit < 0 else -1      # nota de pas cromàtica
        self.espera = 1 + self._tria(durades)
        return nota

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)
        corxera = 30.0 / self.bpm
        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        if self.toca('corxera', corxera):
            self.espera -= 1
            if self.espera <= 0:
                nota = self._seguent()
                nota = self.negharm(nota, self.key)
                nota = 24 if nota < 24 else (108 if nota > 108 else nota)
                vel = 78 + (14 if self.pas % 4 == 0 else 0) + self._atzar(10)
                self._apaga()
                self.send_note_on(nota, min(127, vel))
                self.sonant = nota
                self.off_t = now + corxera * self.espera * self.artic
            self.pas += 1
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
        return {'key': _KEYS[self.key], 'caracter': _CARACTERS[self.caracter][0], 'bpm': int(self.bpm)}

    def cleanup(self):
        self._apaga()
        self.stop_tracked_notes()
