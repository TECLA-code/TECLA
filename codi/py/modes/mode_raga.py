"""
Mode Raga - Una melodia índia que creix: alap lent, fraseig que puja i torna a Sa
X: Tempo  Y: Raga (Bhupali, Yaman, Kafi, Bhairav, Bhairavi)  Z: Ornament
Doble clic a qualsevol tecla: canvi de tonalitat (Sa).

Una raga no és una escala: és una manera de recórrer-la. Aquí la melodia va
per FRASES que pugen des de Sa cap a una nota cim i tornen a reposar sobre
Sa o Pa, i cada frase pot enfilar-se una mica més amunt que l'anterior: és
l'alap, el desplegament lent que obre tot recital, i quan la melodia ha
arribat a dalt de tot torna a començar per baix. Un drone de Sa i Pa sona
sempre per sota, com la tambura. Els ornaments són notes de gràcia molt
curtes (la veïna, un instant abans de la nota) i, al final de frase, una
nota que s'allarga i respira. El pot Y tria la raga i el Z quants ornaments
hi ha: a la dreta gairebé cada nota en porta un.
"""
import time
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_RAGUES = (('Bhupali', (0, 2, 4, 7, 9)), ('Yaman', (0, 2, 4, 6, 7, 9, 11)),
           ('Kafi', (0, 2, 3, 5, 7, 9, 10)), ('Bhairav', (0, 1, 4, 5, 7, 8, 11)),
           ('Bhairavi', (0, 1, 3, 5, 7, 8, 10)))
_GRACIA = 0.06                # segons de la nota de gràcia


class ModeRaga(BaseMode):
    PARAMS = ('Tempo', 'Raga', 'Ornament', 'Registre', 'Drone', 'Tonalitat')
    POTS = ('Tempo', 'Raga', 'Ornament')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Raga"
        self.key = 0
        self.octave = 4
        self.speed = 0.5              # segons per nota
        self.raga = 0
        self.ornament = 0.3
        self.drone_on = True
        self.grau = 0
        self.cim = 3                  # fins on puja aquesta frase (grau)
        self.frase_n = 0
        self.pas = 0
        self.llarg = 7
        self.pujant = True
        self.sonant = -1
        self.off_t = 0.0
        self.gracia = -1
        self.gracia_t = 0.0
        self.pendent = -1
        self.drone = []
        self._llavor = 777
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.grau = 0
        self.cim = 3
        self.frase_n = 0
        self.pas = 0
        self.pujant = True
        self.sonant = -1
        self.gracia = -1
        self.pendent = -1
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        self._engega_drone()
        print("%s: %s %s" % (self.name, _RAGUES[self.raga][0], _KEYS[self.key]))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _escala(self):
        return _RAGUES[self.raga][1]

    def _nota(self, grau):
        e = self._escala()
        n = len(e)
        return self.octave * 12 + self.key + e[grau % n] + 12 * (grau // n)

    # ── El drone: Sa i Pa, dues octaves per sota ──
    def _atura_drone(self):
        for n in self.drone:
            self.send_note_off(n, 0)
        self.drone = []

    def _engega_drone(self):
        self._atura_drone()
        if not self.drone_on:
            return
        base = (self.octave - 2) * 12 + self.key
        for n in (base, base + 7):
            if 0 <= n <= 127:
                self.send_note_on(n, 44)
                self.drone.append(n)

    # ── Comandaments ──
    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            self.speed = 1.1 - f * 0.95           # de 0,9 a 6,7 notes per segon
        elif nom == 'Raga':
            r = min(len(_RAGUES) - 1, int(f * len(_RAGUES)))
            if r != self.raga:
                self.raga = r
                self.grau = 0
                print("%s: %s" % (self.name, _RAGUES[r][0]))
        elif nom == 'Ornament':
            self.ornament = f
        elif nom == 'Registre':
            o = 3 + int(f * 2.99)
            if o != self.octave:
                self.octave = o
                self._engega_drone()
        elif nom == 'Drone':
            d = f >= 0.5
            if d != self.drone_on:
                self.drone_on = d
                self._engega_drone()
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                self._engega_drone()
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1
        if self.gracia >= 0:
            self.send_note_off(self.gracia, 0)
            self.gracia = -1

    def _seguent(self):
        """Puja cap al cim per graus (amb algun salt), i torna a Sa o Pa."""
        n = len(self._escala())
        if self.pas == 0:
            self.pujant = True
        if self.pujant:
            g = self.grau + (2 if self._atzar(100) < 20 else 1)
            if g >= self.cim:
                g = self.cim
                self.pujant = False
        else:
            g = self.grau - (2 if self._atzar(100) < 25 else 1)
            if self.pas >= self.llarg - 1:
                # Repòs: Sa, o Pa (la quinta) si la frase acaba a mig aire
                g = 0 if self._atzar(100) < 65 or self.cim < n else (n - 1 if n == 5 else 4)
            if g < 0:
                g = 0
        return g

    def _pas_nota(self, now):
        g = self._seguent()
        self.grau = g
        nota = self._nota(g)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        final = self.pas >= self.llarg - 1
        vel = 66 + min(30, g * 4) + (12 if final else 0)
        self._apaga()
        # Nota de gràcia: la veïna de dalt (o de baix), un instant abans
        if not final and self._atzar(1000) < int(self.ornament * 850):
            veina = self._nota(g + (1 if self._atzar(2) else -1))
            if 24 <= veina <= 108:
                self.send_note_on(veina, max(30, vel - 20))
                self.gracia = veina
                self.gracia_t = now + _GRACIA
                self.pendent = nota
                self.off_t = now + self.speed * (2.2 if final else 0.85)
                self.pas += 1
                return
        self.send_note_on(nota, vel)
        self.sonant = nota
        self.off_t = now + self.speed * (2.2 if final else 0.85)
        self.pas += 1

    def _nova_frase(self):
        n = len(self._escala())
        self.pas = 0
        self.frase_n += 1
        self.llarg = 5 + self._atzar(5)
        # L'alap: cada frase pot pujar una mica més; a dalt de tot, torna a baix
        if self.cim < 2 * n + 1 and self._atzar(100) < 70:
            self.cim += 1 + self._atzar(2)
        if self.cim > 2 * n + 1 or self.frase_n % 9 == 0:
            self.cim = 3

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.potes(pot_values)
        if self.gracia >= 0 and now >= self.gracia_t:
            self.send_note_off(self.gracia, 0)
            self.gracia = -1
            if self.pendent >= 0:
                self.send_note_on(self.pendent, 80)
                self.sonant = self.pendent
                self.pendent = -1
        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        periode = self.speed * (2.6 if self.pas >= self.llarg else 1.0)
        if self.toca('nota', periode):
            if self.pas >= self.llarg:
                self._nova_frase()
            self._pas_nota(now)
        for i in range(min(len(button_states), 15)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                if 0.05 < (now - self.last_rel[i]) < 0.4:
                    self.last_rel[i] = 0.0
                    self.key = (self.key + 1) % 12
                    self._engega_drone()
                    print("%s: %s" % (self.name, _KEYS[self.key]))
                else:
                    self.last_rel[i] = now
            self.last_btn[i] = cur
        return {'raga': _RAGUES[self.raga][0], 'key': _KEYS[self.key], 'cim': self.cim,
                'speed': self.speed}

    def cleanup(self):
        self._apaga()
        self._atura_drone()
        self.stop_tracked_notes()
