"""
Mode Havanera - Cançó de taverna de mar: el ritme d'havanera al baix, estrofa en menor i tornada en major
X: Tempo  Y: Veus (de la veu sola a les terceres i sextes paral·leles)  Z: Registre
Configuració de Modes: Volum · Onatge · Tornada | Frase · Articulació · Tonalitat
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (Z tria l'eix).

De la família de Cançó: un període de quatre frases (pregunta, resposta,
frase oberta i tancament) que es genera amb la gramàtica d'una cançó, i
aquí la cançó és una havanera. El que la fa havanera és el baix: la cèl·lula
de corxera amb punt, semicorxera i dues corxeres —tam, ta-tam-tam— que no
para en tot el compàs de dos per quatre, amb un rasgueig de guitarra al
contratemps. I la forma: l'ESTROFA va en menor, amb la sensible de la menor
harmònica, i la TORNADA passa al relatiu major, com a totes les havaneres
de Calella. El pot Tornada diu si la cançó es queda en menor, si alterna
estrofa i tornada, o si és tota tornada.

El pot Y són les VEUS: a l'esquerra canta una veu sola; cap al mig s'hi
afegeix una segona veu a la tercera inferior a les notes llargues, i a la
dreta la segona veu va sempre, per terceres a l'estrofa i per sextes a la
tornada, com quan canta tota la taula. L'ONATGE gronxa el tempo i la força
al llarg del període, com el mar sota la barca. El generador és
determinista: cada període en canvia la llavor.
"""
import math
import time
from modes.base_mode import BaseMode

_MAJOR = (0, 2, 4, 5, 7, 9, 11)
_MENOR = (0, 2, 3, 5, 7, 8, 11)          # menor harmònica
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
# Quatre frases de quatre acords (grau de l'escala): estrofa i tornada
_PROG_MENOR = ((0, 0, 4, 4), (4, 4, 0, 0), (3, 3, 0, 4), (3, 4, 0, 0))
_PROG_MAJOR = ((0, 0, 4, 4), (4, 4, 0, 0), (3, 0, 1, 4), (1, 4, 0, 0))
_FINALS = (1, 0, 4, 0)
_ACORD = (0, 2, 4)
# El baix d'havanera: (semicorxera del compàs, grau de l'acord, força)
_BAIX = ((0, 0, 76), (3, 4, 58), (4, 0, 66), (6, 4, 58))
_GUITARRA = (2, 6)                        # el rasgueig, al contratemps
# Cèl·lules d'un temps (semicorxeres 0-3 amb atac)
_CELLES = ((0,), (0, 2), (0, 3), (0, 2, 3), (2,), ())
_COMPASSOS = (2, 4, 8)


class ModeHavanera(BaseMode):
    PARAMS = ('Tempo', 'Veus', 'Registre', 'Onatge', 'Tornada', 'Frase',
              'Articulació', 'Tonalitat')
    POTS = ('Tempo', 'Veus', 'Registre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Havanera"
        self.key = 9                  # la menor: l'havanera hi és a casa
        self.octave = 4
        self.bpm = 76.0
        self.speed = 60.0 / self.bpm / 4.0
        self.veus = 0.5
        self.onatge = 0.4
        self.tornada = 0.5
        self.artic = 0.85
        self.llarg = 4
        self.major = False
        self.periode = 0
        self.frase = 0
        self.compas = 0
        self.semi = 0                 # semicorxera dins del compàs (0-7)
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.sonant2 = -1
        self.off_t = 0.0
        self.baix = -1
        self.acord = []
        self.off_acord = 0.0
        self._llavor = 1714
        self._llavor0 = 1714
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.major = self.tornada > 0.8
        self.periode = 0
        self.frase = 0
        self.compas = 0
        self.semi = 0
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.sonant2 = -1
        self.baix = -1
        self.acord = []
        self._polsos = {}
        self._llavor = self._llavor0
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %d BPM" % (self.name, _KEYS[self.key], int(self.bpm)))

    # ── Comandaments ────────────────────────────────────────────────────────
    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 56.0 + f * 56.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.speed = 60.0 / b / 4.0
        elif nom == 'Veus':
            self.veus = f
        elif nom == 'Registre':
            if not self.neg_active:
                self.octave = 3 + int(f * 2.99)
        elif nom == 'Onatge':
            self.onatge = f
        elif nom == 'Tornada':
            self.tornada = f
            if self.frase == 0 and self.compas == 0 and self.semi == 0 and (f > 0.8 or f < 0.2):
                self.major = f > 0.8                   # abans de començar, a l'acte
        elif nom == 'Frase':
            l = _COMPASSOS[min(2, int(f * 2.99))]
            if l != self.llarg:
                self.llarg = l
                print("%s: frases de %d compassos" % (self.name, l))
        elif nom == 'Articulació':
            self.artic = 0.4 + f * 0.6
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _tonica(self):
        return (self.key + 3) % 12 if self.major else self.key

    def _nota(self, grau, octava):
        e = _MAJOR if self.major else _MENOR
        return octava * 12 + self._tonica() + e[grau % 7] + 12 * (grau // 7)

    def _acord_g(self):
        p = (self.compas * 8 + self.semi) * 4 // (self.llarg * 8)
        prog = _PROG_MAJOR if self.major else _PROG_MENOR
        return prog[self.frase][p]

    def _de_lacord(self, g):
        acord_g = self._acord_g()
        millor = g
        dist = 99
        for k in (-7, 0, 7):
            for a in _ACORD:
                cand = acord_g + a + k
                if abs(cand - g) < dist:
                    dist = abs(cand - g)
                    millor = cand
        return millor

    def _seguent_grau(self):
        lo = -3
        hi = 9
        objectiu = _FINALS[self.frase] + (3 if self.frase == 2 else 0)
        resta = self.llarg * 8 - (self.compas * 8 + self.semi)
        if resta <= 4:
            return objectiu
        d = objectiu - self.grau
        cap = 1 if d > 0 else (-1 if d < 0 else 0)
        r = self._atzar(100)
        if r < 62:
            interval = 1
        elif r < 84:
            interval = 2 + self._atzar(2)             # tercera o quarta
        else:
            interval = 0
        if abs(d) * 2 > resta or self._atzar(100) < 60:
            sentit = cap if cap != 0 else (1 if self._atzar(2) else -1)
        else:
            sentit = 1 if self._atzar(2) else -1
        g = self.grau + sentit * interval
        if self.semi % 4 == 0 and self._atzar(100) < 55:
            g = self._de_lacord(g)
        if g > hi:
            g = hi - self._atzar(3)
        if g < lo:
            g = lo + self._atzar(3)
        return g

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1
        if self.sonant2 >= 0:
            self.send_note_off(self.sonant2, 0)
            self.sonant2 = -1

    def _apaga_baix(self):
        if self.baix >= 0:
            self.send_note_off(self.baix, 0)
            self.baix = -1

    def _apaga_acord(self):
        for n in self.acord:
            self.send_note_off(n, 0)
        self.acord = []

    def _ona(self):
        """El mar sota la barca: una ona lenta que dura tot el període."""
        tot = 4 * self.llarg * 8
        pos = (self.frase * self.llarg * 8 + self.compas * 8 + self.semi) / float(tot)
        return math.sin(6.2832 * pos)

    def _pas(self, now, ona):
        s = self.semi
        pos = s % 4
        tonica = self._tonica()
        acord_g = self._acord_g()
        for (q, rel, vel) in _BAIX:
            if q == s:
                self._apaga_baix()
                n = self._nota(acord_g, self.octave - 1)
                if rel:
                    # La quinta: per sobre, o per sota si surt de l'octava del baix
                    n = n + 7 if n + 7 <= (self.octave - 1) * 12 + tonica + 9 else n - 5
                n = self.negharm(n, tonica)
                if 12 <= n <= 96:
                    self.send_note_on(n, vel + int(10 * ona * self.onatge))
                    self.baix = n
        if s in _GUITARRA:
            self._apaga_acord()
            for a in _ACORD:
                n = self.negharm(self._nota(acord_g + a, self.octave), tonica)
                if 24 <= n <= 108:
                    self.send_note_on(n, 40)
                    self.acord.append(n)
            self.off_acord = now + self.speed * 1.5
        if pos == 0:
            if self.compas == self.llarg - 1 and s == 4:
                self.cella = (0,)
            else:
                r = self._atzar(100)
                self.cella = _CELLES[0 if r < 30 else (1 if r < 52 else (2 if r < 70 else (
                    3 if r < 82 else (4 if r < 90 else 5))))]
        if pos not in self.cella:
            if pos == 0 and not self.cella:
                self._apaga()
            return
        g = self._seguent_grau()
        self.grau = g
        n = 4 - pos
        for p in self.cella:
            if p > pos:
                n = p - pos
                break
        nota = self.negharm(self._nota(g, self.octave + 1), tonica)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        tot = self.llarg * 8
        arc = 1.0 - abs(((self.compas * 8 + s) / float(tot - 1)) * 2.0 - 1.0)
        vel = int(64 + 34 * arc + (8 if pos == 0 else 0) + 14 * ona * self.onatge)
        vel = 30 if vel < 30 else (120 if vel > 120 else vel)
        self._apaga()
        self.send_note_on(nota, vel)
        self.sonant = nota
        # La segona veu: terceres a l'estrofa, sextes a la tornada
        if self.veus >= 0.15 and (self.veus >= 0.6 or n >= 2):
            n2 = self.negharm(self._nota(g - (5 if self.major else 2), self.octave + 1), tonica)
            if 24 <= n2 <= 108 and n2 != nota:
                self.send_note_on(n2, int(vel * 0.72))
                self.sonant2 = n2
        durada = self.speed * n * self.artic
        if self.compas == self.llarg - 1 and s >= 4:
            durada = self.speed * 6.0
        self.off_t = now + durada

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)

        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        if self.acord and now >= self.off_acord:
            self._apaga_acord()
        ona = self._ona()
        mult = 1.0 + 0.12 * self.onatge * ona
        if self.compas == self.llarg - 1 and self.semi >= 6:
            mult *= 1.3                                # el final de frase respira
        if self.toca('semi', self.speed * mult):
            self._pas(now, ona)
            self.semi += 1
            if self.semi >= 8:
                self.semi = 0
                self.compas += 1
                if self.compas >= self.llarg:
                    self.compas = 0
                    self.frase = (self.frase + 1) % 4
                    if self.frase == 0:
                        self.periode += 1
                        self._llavor0 = (self._llavor0 + 7919) & 0x7FFFFFFF
                        self._llavor = self._llavor0
                        t = self.tornada
                        major = True if t > 0.8 else (False if t < 0.2 else self.periode % 2 == 1)
                        if major != self.major:
                            self.major = major
                            print("%s: %s" % (self.name, 'tornada (major)' if major else 'estrofa (menor)'))

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
        return {'key': _KEYS[self.key], 'frase': self.frase + 1, 'bpm': int(self.bpm),
                'part': 'tornada' if self.major else 'estrofa'}

    def cleanup(self):
        self._apaga()
        self._apaga_baix()
        self._apaga_acord()
        self.stop_tracked_notes()
