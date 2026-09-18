"""
Mode Bossa - Cançó de bossa nova: baix sincopat, guitarra al contratemps i una veu que respira
X: Tempo  Y: Jazz (de les notes de l'acord a les extensions i el cromatisme)  Z: Registre
Configuració de Modes: Volum · Síncope · Densitat | Frase · Acord de fons · Tonalitat
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (Z tria l'eix).

De la família de Cançó: un període de quatre frases (pregunta, resposta,
frase oberta i tancament) que es genera amb la gramàtica d'una cançó, i
aquí la cançó és una bossa nova. L'acompanyament és el de la guitarra de
João Gilberto: el baix fa fonamental i quinta a l'u i al tres, amb la
corxera amb punt que s'hi avança, i els acords —tercera, setena i novena,
mai la fonamental— cauen al contratemps en un dibuix de dos compassos.
Els acords són de setena, els diatònics de la tonalitat, i les
progressions són les de la bossa: la de la Garota (I · ii-V), la
descendent per graus i el ii-V-I.

La melodia és el que la bossa té de més seu: poques notes, notes
repetides, atacs al contratemps i silencis que respiren. El pot Y és el
JAZZ: a l'esquerra la veu canta les notes de l'acord al temps; cap a la
dreta hi entren la novena i la tretzena, les notes d'aproximació
cromàtica i els salts. La SÍNCOPE diu quantes notes cauen fora del temps
i la DENSITAT quantes n'hi ha. El generador és determinista: cada
període en canvia la llavor.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 5, 7, 9, 11)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
# Quatre frases de quatre acords (grau de l'escala; l'acord és el de setena)
_PROGRESSIONS = (
    ('Garota', ((0, 0, 1, 4), (0, 0, 1, 4), (3, 3, 2, 5), (1, 4, 0, 0))),
    ('Descendent', ((0, 0, 6, 6), (5, 5, 4, 4), (3, 3, 2, 2), (1, 4, 0, 0))),
    ('ii-V-I', ((1, 4, 0, 0), (1, 4, 0, 0), (5, 5, 1, 4), (1, 4, 0, 0))),
)
_FINALS = (1, 0, 4, 0)
_SETENA = (0, 2, 4, 6)                    # graus de l'acord de setena
_EXTENS = (0, 2, 4, 6, 8, 12)             # amb la novena i la tretzena
# El baix: (semicorxera del compàs, fonamental o quinta, força)
_BAIX = ((0, 0, 80), (6, 0, 56), (8, 4, 70), (14, 4, 56))
# La guitarra: semicorxeres amb acord, al compàs parell i al senar
_GUITARRA = ((3, 6, 10, 13), (2, 6, 10, 14))
_COMPASSOS = (2, 4, 8)
# Cèl·lules d'un temps (semicorxeres amb atac); () és silenci, (-1,) manté la nota
_CELLES = ((0,), (0, 2), (2,), (3,), (0, 3), (), (-1,))


class ModeBossa(BaseMode):
    PARAMS = ('Tempo', 'Jazz', 'Registre', 'Síncope', 'Densitat', 'Frase',
              'Acord de fons', 'Tonalitat')
    POTS = ('Tempo', 'Jazz', 'Registre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Bossa"
        self.key = 5                  # fa major
        self.octave = 4
        self.bpm = 128.0
        self.speed = 60.0 / self.bpm / 4.0
        self.jazz = 0.4
        self.sincope = 0.5
        self.dens = 0.6
        self.llarg = 4
        self.prog = 0
        self.frase = 0
        self.compas = 0
        self.semi = 0                 # semicorxera dins del compàs (0-15)
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.off_t = 0.0
        self.baix = -1
        self.arrel_ant = -1
        self.acord = []
        self.off_acord = 0.0
        self._llavor = 1958
        self._llavor0 = 1958
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.frase = 0
        self.compas = 0
        self.semi = 0
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.baix = -1
        self.arrel_ant = -1
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
            b = 96.0 + f * 64.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.speed = 60.0 / b / 4.0
        elif nom == 'Jazz':
            self.jazz = f
        elif nom == 'Registre':
            if not self.neg_active:
                self.octave = 3 + int(f * 2.99)
        elif nom == 'Síncope':
            self.sincope = f
        elif nom == 'Densitat':
            self.dens = f
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
        p = (self.compas * 16 + self.semi) * 4 // (self.llarg * 16)
        return _PROGRESSIONS[self.prog][1][self.frase][p]

    def _de_lacord(self, g):
        acord_g = self._acord_g()
        graus = _EXTENS if self.jazz > 0.5 else _SETENA
        millor = g
        dist = 99
        for k in (-7, 0, 7):
            for a in graus:
                cand = acord_g + a + k
                if abs(cand - g) < dist:
                    dist = abs(cand - g)
                    millor = cand
        return millor

    def _seguent_grau(self):
        j = self.jazz
        lo = -2
        hi = 9 + int(3.0 * j)
        objectiu = _FINALS[self.frase] + (4 if self.frase == 2 else 0)
        resta = self.llarg * 16 - (self.compas * 16 + self.semi)
        if resta <= 6:
            return objectiu
        d = objectiu - self.grau
        cap = 1 if d > 0 else (-1 if d < 0 else 0)
        r = self._atzar(1000) / 1000.0
        p_conj = 0.6 - 0.25 * j
        p_salt = 0.2 + 0.35 * j
        if r < p_conj:
            interval = 1
        elif r < p_conj + p_salt:
            interval = 2 + self._atzar(3)
        else:
            interval = 0                              # la nota repetida, tan de bossa
        if abs(d) * 3 > resta or self._atzar(100) < 55 + int(15 * j):
            sentit = cap if cap != 0 else (1 if self._atzar(2) else -1)
        else:
            sentit = 1 if self._atzar(2) else -1
        g = self.grau + sentit * interval
        if self.semi % 4 == 0 and self._atzar(100) < 60 - int(35 * j):
            g = self._de_lacord(g)
        if g > hi:
            g = hi - self._atzar(3)
        if g < lo:
            g = lo + self._atzar(3)
        return g

    def _tria_cella(self):
        if self.compas == self.llarg - 1 and self.semi >= 12:
            return (0,)
        r = self._atzar(100)
        if r < 55 - int(45 * self.dens):
            return _CELLES[6] if self.sonant >= 0 and self._atzar(2) else _CELLES[5]
        s = self.sincope
        r = self._atzar(100)
        a = 40 - int(30 * s)
        b = a + 25 - int(10 * s)
        c = b + 12 + int(15 * s)
        d = c + 8 + int(15 * s)
        if r < a:
            return _CELLES[0]
        if r < b:
            return _CELLES[1]
        if r < c:
            return _CELLES[2]
        if r < d:
            return _CELLES[3]
        return _CELLES[4]

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

    def _pas(self, now):
        s = self.semi
        pos = s % 4
        tonica = (self.octave * 12 + self.key) % 12
        acord_g = self._acord_g()
        for (q, rel, vel) in _BAIX:
            if q == s:
                if s == 8 and acord_g != self.arrel_ant:
                    rel = 0                            # l'acord ha canviat a mig compàs
                if rel == 0:
                    self.arrel_ant = acord_g
                self._apaga_baix()
                n = self._nota(acord_g, self.octave - 1)
                if rel:
                    n = n + 7 if n + 7 <= (self.octave - 1) * 12 + tonica + 9 else n - 5
                n = self.negharm(n, tonica)
                if 12 <= n <= 96:
                    self.send_note_on(n, vel)
                    self.baix = n
        if s in _GUITARRA[self.compas % 2]:
            self._apaga_acord()
            # Tercera, setena i novena (o quinta): la fonamental ja la diu el baix
            for a in (2, 6, 8 if self.jazz > 0.35 else 4):
                n = self.negharm(self._nota(acord_g + a, self.octave), tonica)
                if 24 <= n <= 96:
                    self.send_note_on(n, 48)
                    self.acord.append(n)
            self.off_acord = now + self.speed * 2.5
        if pos == 0:
            self.cella = self._tria_cella()
            if not self.cella:
                self._apaga()
        if pos not in self.cella:
            return
        g = self._seguent_grau()
        self.grau = g
        nota = self._nota(g, self.octave + 1)
        # Aproximació cromàtica: al contratemps, mig to per sota
        if pos != 0 and self._atzar(100) < int(45 * self.jazz):
            nota -= 1
        nota = self.negharm(nota, tonica)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        n = 0
        for p in self.cella:
            if p > pos:
                n = p - pos
                break
        tot = self.llarg * 16
        arc = 1.0 - abs(((self.compas * 16 + s) / float(tot - 1)) * 2.0 - 1.0)
        vel = int(62 + 30 * arc - (8 if pos else 0) + (8 if self.frase == 2 else 0))
        vel = 30 if vel < 30 else (120 if vel > 120 else vel)
        self._apaga()
        self.send_note_on(nota, vel)
        self.sonant = nota
        if n:
            durada = self.speed * n * 0.9
        else:
            durada = self.speed * 6.0                  # dura fins a la nota o el silenci següents
        if self.compas == self.llarg - 1 and s >= 12:
            durada = self.speed * 10.0
        self.off_t = now + durada

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)

        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        if self.acord and now >= self.off_acord:
            self._apaga_acord()
        if self.toca('semi', self.speed):
            self._pas(now)
            self.semi += 1
            if self.semi >= 16:
                self.semi = 0
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
                'jazz': int(self.jazz * 100)}

    def cleanup(self):
        self._apaga()
        self._apaga_baix()
        self._apaga_acord()
        self.stop_tracked_notes()
