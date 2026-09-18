"""
Mode Bressol - Cançó de bressol en sis per vuit: una melodia que s'adorm sobre un balanceig
X: Tempo  Y: Son (com més amunt, més s'adorm: menys notes, més fluix, més lent)  Z: Registre
Configuració de Modes: Volum · Balanceig · Articulació | Frase · Acord de fons · Tonalitat
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (Z tria l'eix).

De la família de Cançó: la melodia no està escrita, es genera amb la
gramàtica d'un període de quatre frases (pregunta, resposta, frase oberta
i tancament), cadascuna amb el seu acord de fons. Aquí la gramàtica és la
d'una cançó de bressol: compàs de sis per vuit, un balanceig al baix
(fonamental, quinta, tercera) que gronxa com un bressol, i una melodia
estreta, gairebé pentatònica, que va per graus conjunts amb el ritme de
sempre —llarga-curta, llarga-curta— i acaba cada frase baixant cap a la
tònica.

El pot Y és el SON. A l'esquerra la cançó és desperta: totes les notes,
la veu clara. Cap a la dreta la melodia perd notes, s'afluixa, s'alenteix
i s'estreny; al final només queda el balanceig, amb alguna nota perduda,
com qui canta mig adormit. El generador és determinista: la mateixa
tonalitat i el mateix son donen la mateixa cançó, i cada període en canvia
la llavor.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 5, 7, 9, 11)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
# Dos acords per frase (grau de l'escala), quatre frases
_PROGRESSIONS = (('I-V · V-I', (0, 4, 4, 0, 0, 3, 4, 0)),
                 ('I-vi · IV-V', (0, 5, 3, 4, 5, 3, 4, 0)),
                 ('I-IV · I-V', (0, 3, 0, 4, 3, 0, 4, 0)))
_FINALS = (2, 0, 4, 0)             # on acaba cada frase (grau)
_ACORD = (0, 2, 4)
_COMPASSOS = (2, 4, 8)             # compassos per frase
# El balanceig: què sona a cada corxera del compàs, per nivell
_BALANCEIG = ((0,), (0, 3), (0, 2, 3, 5), (0, 1, 2, 3, 4, 5))
_GRONXA = (0, 4, 2, 0, 4, 2)       # grau de l'acord a cada corxera (0 = fonamental, greu)


class ModeBressol(BaseMode):
    PARAMS = ('Tempo', 'Son', 'Registre', 'Balanceig', 'Articulació', 'Frase',
              'Acord de fons', 'Tonalitat')
    POTS = ('Tempo', 'Son', 'Registre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Bressol"
        self.key = 0
        self.octave = 4
        self.bpm = 56.0               # negres amb punt per minut
        self.speed = 60.0 / self.bpm / 3.0
        self.son = 0.2
        self.balanceig = 2
        self.artic = 0.95
        self.llarg = 2
        self.prog = 0
        self.frase = 0
        self.compas = 0
        self.cx = 0                   # corxera dins del compàs (0-5)
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.off_t = 0.0
        self.baix = -1
        self._llavor = 3131
        self._llavor0 = 3131
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.frase = 0
        self.compas = 0
        self.cx = 0
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.baix = -1
        self._polsos = {}
        self._llavor = self._llavor0
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %d BPM" % (self.name, _KEYS[self.key], int(self.bpm)))

    # ── Comandaments ────────────────────────────────────────────────────────
    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 40.0 + f * 50.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.speed = 60.0 / b / 3.0
        elif nom == 'Son':
            self.son = f
        elif nom == 'Registre':
            if not self.neg_active:
                self.octave = 3 + int(f * 2.99)
        elif nom == 'Balanceig':
            self.balanceig = int(f * 3.99)
        elif nom == 'Articulació':
            self.artic = 0.5 + f * 0.5
        elif nom == 'Frase':
            l = _COMPASSOS[min(2, int(f * 2.99))]
            if l != self.llarg:
                self.llarg = l
                print("%s: frases de %d compassos" % (self.name, l))
        elif nom == 'Acord de fons':
            p = min(len(_PROGRESSIONS) - 1, int(f * len(_PROGRESSIONS)))
            if p != self.prog:
                self.prog = p
                print("%s: %s" % (self.name, _PROGRESSIONS[p][0]))
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

    def _nota(self, grau, octava):
        return octava * 12 + self.key + _ESCALA[grau % 7] + 12 * (grau // 7)

    def _acord_g(self):
        segon = 1 if self.compas * 2 >= self.llarg else 0
        return _PROGRESSIONS[self.prog][1][self.frase * 2 + segon]

    def _seguent_grau(self):
        """Per graus conjunts, atreta cap al final de la frase i sense els
        graus que fan aspre (quart i setè) als temps forts."""
        s = self.son
        lo = -2
        hi = 7 - int(4.0 * s)
        objectiu = _FINALS[self.frase] + (3 if self.frase == 2 else 0)
        objectiu = lo if objectiu < lo else (hi if objectiu > hi else objectiu)
        resta = self.llarg * 6 - (self.compas * 6 + self.cx)
        if resta <= 3:
            return objectiu
        d = objectiu - self.grau
        cap = 1 if d > 0 else (-1 if d < 0 else 0)
        r = self._atzar(100)
        if r < 78:
            interval = 1
        elif r < 90:
            interval = 0
        else:
            interval = 2
        if abs(d) * 2 > resta or self._atzar(100) < 60:
            sentit = cap if cap != 0 else (1 if self._atzar(2) else -1)
        else:
            sentit = 1 if self._atzar(2) else -1
        g = self.grau + sentit * interval
        if self.cx % 3 == 0:
            if g % 7 in (3, 6) and self._atzar(100) < 70:
                g += sentit if sentit != 0 else 1
            elif self._atzar(100) < 45:
                g = self._de_lacord(g)
        if g > hi:
            g = hi - self._atzar(2)
        if g < lo:
            g = lo + self._atzar(2)
        return g

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

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def _apaga_baix(self):
        if self.baix >= 0:
            self.send_note_off(self.baix, 0)
            self.baix = -1

    def _gronxa(self, cx):
        """El balanceig: greu a l'u i al quatre, quinta i tercera entremig."""
        if cx not in _BALANCEIG[self.balanceig]:
            return
        acord_g = self._acord_g()
        greu = cx % 3 == 0
        n = self._nota(acord_g + _GRONXA[cx], self.octave - (1 if greu else 0))
        n = self.negharm(n, (self.octave * 12 + self.key) % 12)
        self._apaga_baix()
        if 12 <= n <= 96:
            vel = int((50 if greu else 42) * (1.0 - 0.35 * self.son))
            self.send_note_on(n, max(16, vel))
            self.baix = n

    def _pas(self, now):
        cx = self.cx
        pos = cx % 3
        if pos == 0:
            # La cèl·lula rítmica del temps: llarga-curta, llarga, tres o silenci
            ultim = self.compas == self.llarg - 1 and cx == 3
            p_sil = int(max(0.0, self.son - 0.25) * 90)
            r = self._atzar(100)
            if ultim:
                self.cella = (0,)
            elif r < p_sil:
                self.cella = ()
            else:
                r = self._atzar(100)
                if r < 50 - int(25 * self.son):
                    self.cella = (0, 2)
                elif r < 80:
                    self.cella = (0,)
                else:
                    self.cella = (0, 1, 2)
        self._gronxa(cx)
        if pos in self.cella:
            g = self._seguent_grau()
            self.grau = g
            nota = self._nota(g, self.octave + 1)
            nota = self.negharm(nota, (self.octave * 12 + self.key) % 12)
            nota = 24 if nota < 24 else (108 if nota > 108 else nota)
            # Fins al proper atac de la cèl·lula, o fins al temps següent
            n = 3 - pos
            for p in self.cella:
                if p > pos:
                    n = p - pos
                    break
            tot = self.llarg * 6
            arc = 1.0 - abs(((self.compas * 6 + cx) / float(tot - 1)) * 2.0 - 1.0)
            vel = int((46 + 28 * arc + (6 if pos == 0 else 0)) * (1.0 - 0.45 * self.son))
            vel = 20 if vel < 20 else (100 if vel > 100 else vel)
            self._apaga()
            self.send_note_on(nota, vel)
            self.sonant = nota
            durada = self.speed * n * self.artic
            if self.compas == self.llarg - 1 and cx >= 3:
                durada = self.speed * 4.0           # l'última nota de la frase s'allarga
            self.off_t = now + durada
        elif pos == 0 and not self.cella:
            self._apaga()

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)

        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        # Amb el son el pols s'alenteix; el final de frase respira, i el del
        # període encara més
        mult = 1.0 + 0.35 * self.son
        if self.compas == self.llarg - 1 and self.cx >= 4:
            mult *= 1.4
            if self.frase == 3:
                mult *= 1.0 + 0.4 * self.son
        if self.toca('cx', self.speed * mult):
            self._pas(now)
            self.cx += 1
            if self.cx >= 6:
                self.cx = 0
                self.compas += 1
                if self.compas >= self.llarg:
                    self.compas = 0
                    self.frase = (self.frase + 1) % 4
                    if self.frase == 0:
                        self._llavor0 = (self._llavor0 + 7919) & 0x7FFFFFFF
                        self._llavor = self._llavor0

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
                'son': int(self.son * 100)}

    def cleanup(self):
        self._apaga()
        self._apaga_baix()
        self.stop_tracked_notes()
