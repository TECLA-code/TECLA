"""
Mode Progressió - Una progressió d'acords amb conducció de veus
X: Tempo (ritme harmònic)  Y: Progressió  Z: Estil (bloc, arpegi, pols, balanç)
Configuració de Modes: Volum · Registre · Densitat | Baix · Conducció · Harmonia negativa | Tonalitat…
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (reflecteix cada acord).

La família dels acords en un sol mode. Quatre progressions que són tota una
lliçó d'harmonia: el ii–V–I amb el seu relatiu menor, els "Giant Steps" de
Coltrane (tres tonalitats a distància de tercera major), el blues de dotze
compassos amb sèptimes a tot arreu, i el cànon de Pachelbel que és el
fonament de mig pop. El que les fa sonar a música i no a taula d'acords és
la CONDUCCIÓ DE VEUS: cada veu va a la nota més propera de l'acord següent,
o sigui que d'un acord a l'altre només se sent el que de debò s'ha mogut. El
baix diu la fonamental. El pot Z tria com s'exposa l'acord: en bloc i
sostingut, arpegiat, repicat a cada pulsació, o en balanç (baix a l'u,
acord a dos i a quatre).
"""
import time
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_MAJ7 = (0, 4, 7, 11)
_M7 = (0, 3, 7, 10)
_DOM7 = (0, 4, 7, 10)
_MAJ = (0, 4, 7)
_MIN = (0, 3, 7)
# Cada acord: (semitons de la fonamental respecte la tònica, intervals, pulsacions)
_PROGRESSIONS = (
    ('ii-V-I',   ((2, _M7, 4), (7, _DOM7, 4), (0, _MAJ7, 4), (9, _M7, 4))),
    ('Coltrane', ((0, _MAJ7, 2), (3, _DOM7, 2), (8, _MAJ7, 2), (11, _DOM7, 2),
                  (4, _MAJ7, 2), (7, _DOM7, 2), (0, _MAJ7, 4))),
    ('Blues',    ((0, _DOM7, 4), (5, _DOM7, 4), (0, _DOM7, 4), (0, _DOM7, 4),
                  (5, _DOM7, 4), (5, _DOM7, 4), (0, _DOM7, 4), (0, _DOM7, 4),
                  (7, _DOM7, 4), (5, _DOM7, 4), (0, _DOM7, 4), (7, _DOM7, 4))),
    ('Pachelbel', ((0, _MAJ, 4), (7, _MAJ, 4), (9, _MIN, 4), (4, _MIN, 4),
                   (5, _MAJ, 4), (0, _MAJ, 4), (5, _MAJ, 4), (7, _MAJ, 4))),
)
_ESTILS = ('Bloc', 'Arpegi', 'Pols', 'Balanc')
_CONDUCCIONS = ('Proximitat', 'Obert', 'Tancat')
_BAIXOS = ('Sense', 'Greu', 'Mig')
_VEUS_MIN = 52       # E3: on viuen les veus (el Registre ho desplaça)
_VEUS_MAX = 79       # G5


class ModeProgressio(BaseMode):
    PARAMS = ('Tempo', 'Progressió', 'Estil', 'Registre', 'Densitat', 'Baix',
              'Conducció', 'Harmonia negativa', 'Tonalitat')
    POTS = ('Tempo', 'Progressió', 'Estil')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Progressió"
        self.key = 0
        self.bpm = 96.0
        self.prog = 0
        self.estil = 0
        self.registre = 0                # desplaçament de les veus en semitons (−12, 0, +12)
        self.dens = 1                    # 0 = corxeres · 1 = semicorxeres (arpegi i pols)
        self.baix_mode = 1               # 0 sense · 1 greu (C2) · 2 mig (C3)
        self.conduccio = 0
        self.neg_latch = False
        self.idx = 0                     # acord actual dins la progressió
        self.pols = 0                    # pulsació dins l'acord
        self.sub = 0
        self.veus = []                   # voicing actual
        self.sonant = []                 # notes ara sonant (veus + baix)
        self.arp_i = 0
        self.baix = -1
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.idx = 0
        self.pols = 0
        self.veus = []
        self.sonant = []
        self.arp_i = 0
        self.baix = -1
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %s" % (self.name, _KEYS[self.key], _PROGRESSIONS[self.prog][0]))

    # ── Comandaments ────────────────────────────────────────────────────────
    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 50.0 + f * 110.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
        elif nom == 'Progressió':
            p = min(3, int(f * 4))
            if p != self.prog:
                self.prog = p
                self.idx = 0
                self.pols = 0
                self.veus = []
                print("%s: %s" % (self.name, _PROGRESSIONS[p][0]))
                self.dispara('pols')
        elif nom == 'Estil':
            e = min(3, int(f * 4))
            if e != self.estil:
                self.estil = e
                print("%s: %s" % (self.name, _ESTILS[e]))
                self._calla()
                if e == 0 and self.veus:
                    self._nou_acord()
        elif nom == 'Registre':
            r = (min(2, int(f * 3)) - 1) * 12
            if r != self.registre:
                self.registre = r
                self.veus = []               # es torna a col·locar al registre nou
                if self.sonant:
                    self._nou_acord()
        elif nom == 'Densitat':
            self.dens = 1 if f >= 0.5 else 0
        elif nom == 'Baix':
            b = min(2, int(f * 3))
            if b != self.baix_mode:
                self.baix_mode = b
                print("%s: baix %s" % (self.name, _BAIXOS[b]))
                if self.sonant:
                    self._nou_acord()
        elif nom == 'Conducció':
            c = min(2, int(f * 3))
            if c != self.conduccio:
                self.conduccio = c
                print("%s: %s" % (self.name, _CONDUCCIONS[c]))
        elif nom == 'Harmonia negativa':
            latch = f >= 0.5
            if latch != self.neg_latch:
                self.neg_latch = latch
                print("%s: harmonia negativa %s" % (self.name, 'ON' if latch else 'OFF'))
                if self.veus:
                    self.neg_active = latch
                    self._nou_acord()
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                self.veus = []
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _calla(self):
        for n in self.sonant:
            self.send_note_off(n, 0)
        self.sonant = []

    def _acord(self):
        return _PROGRESSIONS[self.prog][1][self.idx]

    def _condueix(self, arrel_pc, intervals):
        """Conducció de veus: cada classe d'altura de l'acord nou va a la veu
        que menys s'ha de moure ('Proximitat'). 'Tancat' torna a col·locar
        cada acord en posició tancada (sense conduir). 'Obert' condueix i
        després baixa la segona veu de dalt una octava (drop 2)."""
        pcs = [(arrel_pc + iv) % 12 for iv in intervals]
        lo = _VEUS_MIN + self.registre
        hi = _VEUS_MAX + self.registre
        if not self.veus or self.conduccio == 2:
            base = 60 + self.registre + arrel_pc
            if base > 66 + self.registre:
                base -= 12
            veus = []
            for iv in intervals:
                n = base + iv
                while n > hi:
                    n -= 12
                veus.append(n)
            noves = sorted(veus)
        else:
            lliures = list(self.veus)
            noves = []
            for pc in pcs:
                millor = -1
                dist = 99
                triada = None
                for v in lliures:
                    d = (pc - v) % 12
                    if d > 6:
                        d -= 12
                    cand = v + d
                    if abs(d) < dist and lo <= cand <= hi:
                        dist = abs(d)
                        millor = cand
                        triada = v
                if millor < 0:
                    millor = 60 + self.registre + pc
                    triada = None
                noves.append(millor)
                if triada is not None and triada in lliures:
                    lliures.remove(triada)
            noves.sort()
            for i in range(1, len(noves)):
                if noves[i] == noves[i - 1] and noves[i] + 12 <= hi:
                    noves[i] += 12
            noves.sort()
        if self.conduccio == 1 and len(noves) >= 3:      # drop 2
            noves[-2] -= 12
            noves.sort()
        return noves

    def _nou_acord(self):
        arrel_pc, intervals, _ = self._acord()
        tonic_pc = self.key % 12
        self.veus = self._condueix((arrel_pc + self.key) % 12, intervals)
        self._calla()
        self.baix = -1
        if self.baix_mode > 0:
            baix = (2 + self.baix_mode) * 12 + (arrel_pc + self.key) % 12
            self.baix = self.negharm(baix, tonic_pc)
            self.send_note_on(self.baix, 72)
            self.sonant.append(self.baix)
        if self.estil == 0:                       # bloc: tot alhora, sostingut
            for v in self.veus:
                n = self.negharm(v, tonic_pc)
                self.send_note_on(n, 84)
                self.sonant.append(n)
        self.arp_i = 0
        try:
            from motor.kbd_notes import chord_label
            nom = chord_label(sorted(self.veus))
        except Exception:
            nom = _KEYS[(arrel_pc + self.key) % 12]
        print("%s: %s" % (self.name, nom))

    def _calla_veus(self):
        for s in list(self.sonant):
            if s != self.baix:
                self.send_note_off(s, 0)
                self.sonant.remove(s)

    def _subpuls(self, sub):
        """Subdivisió `sub` (0-3) dins la pulsació: arpegi, pols i balanç.
        Amb Densitat a corxeres només cauen les subdivisions 0 i 2."""
        if self.dens == 0 and sub % 2 == 1:
            return
        tonic_pc = self.key % 12
        if self.estil == 1:                       # arpegi: una veu per subdivisió
            v = self.veus[self.arp_i % len(self.veus)]
            self.arp_i += 1
            n = self.negharm(v, tonic_pc)
            self._calla_veus()
            self.send_note_on(n, 80 if sub == 0 else 66)
            self.sonant.append(n)
        elif self.estil == 2 and sub == 0:        # pols: l'acord repicat a cada pulsació
            self._calla_veus()
            for v in self.veus:
                n = self.negharm(v, tonic_pc)
                self.send_note_on(n, 88 if self.pols == 0 else 70)
                self.sonant.append(n)
        elif self.estil == 3:                     # balanç: acord a dos i a quatre
            if sub == 0 and self.pols % 2 == 1:
                for v in self.veus:
                    n = self.negharm(v, tonic_pc)
                    self.send_note_on(n, 78)
                    self.sonant.append(n)
            elif sub == 2 and self.pols % 2 == 1:
                self._calla_veus()

    def update(self, pot_values, button_states):
        now = time.monotonic()
        neg_abans = self.neg_active
        self.poll_negharm(button_states)
        if self.neg_latch:
            self.neg_active = True
        self.potes(pot_values)
        if self.neg_active != neg_abans and self.veus:
            self._nou_acord()                     # el reflex canvia les alçades

        pulsacio = 60.0 / self.bpm
        if self.toca('pols', pulsacio):
            _, _, durada = self._acord()
            if self.pols >= durada or not self.veus:
                if self.veus:
                    self.idx = (self.idx + 1) % len(_PROGRESSIONS[self.prog][1])
                self.pols = 0
                self._nou_acord()
            self.sub = 0
            self._subpuls(0)
            self.pols += 1
        if self.toca('semi', pulsacio / 4.0):
            s = self.sub + 1
            if 0 < s < 4 and self.veus:
                self.sub = s
                self._subpuls(s)

        for i in range(min(len(button_states), 15)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                if 0.05 < (now - self.last_rel[i]) < 0.4:
                    self.last_rel[i] = 0.0
                    self.key = (self.key + 1) % 12
                    self.veus = []
                    print("%s: %s" % (self.name, _KEYS[self.key]))
                else:
                    self.last_rel[i] = now
            self.last_btn[i] = cur
        return {'key': _KEYS[self.key], 'prog': _PROGRESSIONS[self.prog][0],
                'estil': _ESTILS[self.estil], 'bpm': int(self.bpm)}

    def cleanup(self):
        self._calla()
        self.stop_tracked_notes()
