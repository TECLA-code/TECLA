"""
Mode Vals - Cançó en tres per quatre: baix a l'u, acord al dos i al tres, i una melodia que vola
X: Tempo  Y: Vol (de la melodia tranquil·la per graus a la que salta i corre)  Z: Registre
Configuració de Modes: Volum · Balanç · Rubato | Frase · Acord de fons · Tonalitat
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (Z tria l'eix).

De la família de Cançó: un període de quatre frases (pregunta, resposta,
frase oberta i tancament) que es genera amb la gramàtica d'una cançó, i
aquí la cançó és un vals. L'acompanyament és el de sempre i és el que el
fa vals: el baix diu la fonamental a l'u i l'acord contesta al dos i al
tres. La melodia va per compassos sencers —tres negres, blanca i negra,
negra i blanca, o una tirada de corxeres— i el pot Y, el VOL, diu quin
vals és: a l'esquerra va per graus conjunts i notes de l'acord, tranquil;
cap a la dreta hi entren els salts de sexta i d'octava, les tirades de
corxeres i les apoiatures a l'u (la nota de sobre que es resol al dos,
com a Chopin).

El BALANÇ és el del vals vienès: l'acord del dos s'avança una mica, i el
del tres arriba a l'hora. El RUBATO empeny el mig de la frase i frena el
final. Tres acords de fons: el vienès (I-V), el musette en menor amb la
seva sensible, i el de Chopin (I-vi-ii-V). El generador és determinista:
cada període en canvia la llavor.
"""
import time
from modes.base_mode import BaseMode

_MAJOR = (0, 2, 4, 5, 7, 9, 11)
_MENOR = (0, 2, 3, 5, 7, 8, 11)          # menor harmònica: la sensible del musette
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
# Nom, escala i quatre frases de quatre acords (grau de l'escala)
_PROGRESSIONS = (
    ('Vienès', _MAJOR, ((0, 0, 4, 4), (4, 4, 0, 0), (3, 3, 0, 0), (1, 4, 0, 0))),
    ('Musette', _MENOR, ((0, 0, 4, 4), (4, 4, 0, 0), (3, 0, 4, 0), (3, 4, 0, 0))),
    ('Chopin', _MAJOR, ((0, 5, 1, 4), (0, 5, 1, 4), (3, 3, 0, 5), (1, 4, 0, 0))),
)
_FINALS = (1, 0, 4, 0)
_ACORD = (0, 2, 4)
_COMPASSOS = (2, 4, 8)
# Cèl·lules rítmiques d'un compàs (corxeres 0-5 amb atac)
_CELLES = ((0, 2, 4), (0, 4), (0, 2), (0,), (0, 1, 2, 3, 4, 5), (0, 2, 3, 4), (0, 3, 4), (2, 4))


class ModeVals(BaseMode):
    PARAMS = ('Tempo', 'Vol', 'Registre', 'Balanç', 'Rubato', 'Frase',
              'Acord de fons', 'Tonalitat')
    POTS = ('Tempo', 'Vol', 'Registre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Vals"
        self.key = 0
        self.octave = 4
        self.bpm = 138.0              # negres per minut
        self.speed = 60.0 / self.bpm / 2.0
        self.vol = 0.35
        self.balanc = 0.5
        self.rubato = 0.12
        self.llarg = 4
        self.prog = 0
        self.frase = 0
        self.compas = 0
        self.cx = 0
        self.cella = ()
        self.grau = 0
        self.resol = -99              # apoiatura pendent de resoldre
        self.sonant = -1
        self.off_t = 0.0
        self.baix = -1
        self.acord = []
        self.off_acord = 0.0
        self.t_acord = 0.0
        self.acord_pendent = False
        self._llavor = 2718
        self._llavor0 = 2718
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.frase = 0
        self.compas = 0
        self.cx = 0
        self.cella = ()
        self.grau = 0
        self.resol = -99
        self.sonant = -1
        self.baix = -1
        self.acord = []
        self.acord_pendent = False
        self._polsos = {}
        self._llavor = self._llavor0
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %d BPM" % (self.name, _KEYS[self.key], int(self.bpm)))

    # ── Comandaments ────────────────────────────────────────────────────────
    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 84.0 + f * 100.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.speed = 60.0 / b / 2.0
        elif nom == 'Vol':
            self.vol = f
        elif nom == 'Registre':
            if not self.neg_active:
                self.octave = 3 + int(f * 2.99)
        elif nom == 'Balanç':
            self.balanc = f
        elif nom == 'Rubato':
            self.rubato = f * 0.5
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
        e = _PROGRESSIONS[self.prog][1]
        return octava * 12 + self.key + e[grau % 7] + 12 * (grau // 7)

    def _acord_g(self):
        p = (self.compas * 6 + self.cx) * 4 // (self.llarg * 6)
        return _PROGRESSIONS[self.prog][2][self.frase][p]

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
        v = self.vol
        lo = -3
        hi = 7 + int(5.0 * v)
        objectiu = _FINALS[self.frase] + (4 if self.frase == 2 else 0)
        resta = self.llarg * 6 - (self.compas * 6 + self.cx)
        if resta <= 6:
            return objectiu
        d = objectiu - self.grau
        cap = 1 if d > 0 else (-1 if d < 0 else 0)
        r = self._atzar(1000) / 1000.0
        p_conj = 0.8 - 0.4 * v
        p_salt = 0.12 + 0.45 * v
        if r < p_conj:
            interval = 1
        elif r < p_conj + p_salt:
            interval = 2 + self._atzar(2 + int(4 * v))    # de la tercera a l'octava
        else:
            interval = 0
        if abs(d) * 3 > resta or self._atzar(100) < 55 + int(15 * v):
            sentit = cap if cap != 0 else (1 if self._atzar(2) else -1)
        else:
            sentit = 1 if self._atzar(2) else -1
        g = self.grau + sentit * interval
        if self.cx % 2 == 0 and self._atzar(100) < 55 - int(30 * v):
            g = self._de_lacord(g)
        if g > hi:
            g = hi - self._atzar(3)
        if g < lo:
            g = lo + self._atzar(3)
        return g

    def _tria_cella(self):
        v = self.vol
        if self.compas == self.llarg - 1:
            return (0,)                                # l'últim compàs: la nota final
        if self.compas == self.llarg - 2:
            return (0, 2, 4)                           # el penúltim hi porta
        r = self._atzar(100)
        a = 30 - int(20 * v)
        b = a + 15 - int(10 * v)
        c = b + 10 - int(5 * v)
        d = c + 8 - int(5 * v)
        e = d + int(25 * v)
        f = e + 12 + int(5 * v)
        g = f + 8
        if r < a:
            return _CELLES[0]
        if r < b:
            return _CELLES[1]
        if r < c:
            return _CELLES[2]
        if r < d:
            return _CELLES[3]
        if r < e:
            return _CELLES[4]
        if r < f:
            return _CELLES[5]
        if r < g:
            return _CELLES[6]
        return _CELLES[7]

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def _apaga_baix(self):
        if self.baix >= 0:
            self.send_note_off(self.baix, 0)
            self.baix = -1

    def _apaga_acord(self):
        for n in self.acord:
            self.send_note_off(n, 0)
        self.acord = []

    def _toca_acord(self, now, vel):
        self._apaga_acord()
        acord_g = self._acord_g()
        tonica = (self.octave * 12 + self.key) % 12
        for a in _ACORD:
            n = self.negharm(self._nota(acord_g + a, self.octave), tonica)
            if 24 <= n <= 108:
                self.send_note_on(n, vel)
                self.acord.append(n)
        self.off_acord = now + self.speed * 1.3

    def _pas(self, now):
        cx = self.cx
        tonica = (self.octave * 12 + self.key) % 12
        if cx == 0:
            self.cella = self._tria_cella()
            self._apaga_baix()
            n = self.negharm(self._nota(self._acord_g(), self.octave - 1), tonica)
            if 12 <= n <= 96:
                self.send_note_on(n, 74)
                self.baix = n
        elif cx == 1 and self.balanc >= 0.05:
            # El dos del vals vienès s'avança
            self.t_acord = now + self.speed * (1.0 - 0.5 * self.balanc)
            self.acord_pendent = True
        elif cx == 2 and self.balanc < 0.05:
            self._toca_acord(now, 50)
        elif cx == 4:
            self._toca_acord(now, 44)
        if cx not in self.cella:
            return
        if self.resol > -99:
            g = self.resol
            self.resol = -99
        else:
            g = self._seguent_grau()
            if cx == 0 and 2 in self.cella and self.compas < self.llarg - 1 \
                    and self._atzar(100) < int(50 * self.vol):
                c = self._de_lacord(g)
                g = c + 1                              # apoiatura: la nota de sobre…
                self.resol = c                         # …que es resol al dos
        self.grau = g
        nota = self.negharm(self._nota(g, self.octave + 1), tonica)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        n = 6 - cx
        for p in self.cella:
            if p > cx:
                n = p - cx
                break
        tot = self.llarg * 6
        arc = 1.0 - abs(((self.compas * 6 + cx) / float(tot - 1)) * 2.0 - 1.0)
        vel = int(60 + 40 * arc + (10 if cx == 0 else 0) + (6 if self.frase == 2 else 0))
        vel = 30 if vel < 30 else (120 if vel > 120 else vel)
        self._apaga()
        self.send_note_on(nota, vel)
        self.sonant = nota
        durada = self.speed * n * 0.9
        if self.compas == self.llarg - 1:
            durada = self.speed * 7.0                  # la nota final s'allarga
        self.off_t = now + durada

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)

        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        if self.acord and now >= self.off_acord:
            self._apaga_acord()
        if self.acord_pendent and now >= self.t_acord:
            self.acord_pendent = False
            self._toca_acord(now, 56)
        # Rubato: el mig de la frase empeny, el final frena i respira
        tot = self.llarg * 6
        arc = 1.0 - abs(((self.compas * 6 + self.cx) / float(tot - 1)) * 2.0 - 1.0)
        if self.compas == self.llarg - 1 and self.cx >= 4:
            mult = 1.3 + 0.9 * self.rubato
        else:
            mult = 1.0 - 0.2 * self.rubato * arc
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
                'vol': int(self.vol * 100)}

    def cleanup(self):
        self._apaga()
        self._apaga_baix()
        self._apaga_acord()
        self.acord_pendent = False
        self.stop_tracked_notes()
