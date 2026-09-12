"""
Mode Polirítmia - Ritmes euclidians de llargades diferents que es persegueixen
X: Tempo  Y: Densitat (pulsacions per cicle)  Z: Gir (rotació de les veus)

L'essència de la família rítmica és el patró que surt d'una regla, i la
regla més fèrtil és la de Bjorklund: K pulsacions repartides el més
uniformement possible sobre N passos. D'aquí surten el tresillo (3/8), el
cinquillo (5/8), la bossa-nova (5/16) i mig folklore del món. Aquí hi ha
cinc veus, cadascuna amb el seu propi cicle —16, 12, 10, 7 i 11 passos— que
només tornen a coincidir al cap de milers de passos: és un motor de
polirítmia, i el que se sent és un ritme que gira sobre si mateix sense
repetir-se mai del tot. Quatre veus són percussió pel canal 10 i la
cinquena és un baix pentatònic que camina pel seu cicle d'onze. Quan diverses
veus cauen al mateix pas, el cop s'accentua. Y densifica totes les veus
alhora (de gairebé buit a gairebé ple) i Z fa girar les veus unes respecte
de les altres: el mateix material, una altra ubicació del temps fort.
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PERC_CH = 9
_BAIX_CH = 0
_ESCALA = (0, 2, 4, 7, 9)
# (nota GM, passos N, pulsacions K base, velocity)
_VEUS = ((36, 16, 5, 108),      # bombo
         (38, 12, 3, 88),       # caixa
         (42, 10, 7, 62),       # charles
         (75, 7, 3, 74))        # claves
_BAIX = (11, 4)                 # cicle del baix: N, K
_BAIX_GRAUS = (0, 2, 4, 3, 1, 4, 0, 2)
_GATE = 0.055


class ModePoliritmia(BaseMode):
    CANAL_PERC = 9
    PARAMS = ('Tempo', 'Densitat', 'Gir', 'Accent', 'Baix', 'Swing')
    POTS = ('Tempo', 'Densitat', 'Gir')


    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Polirítmia"
        self.bpm = 112.0
        self.step_dur = 60.0 / self.bpm / 4.0
        self.densitat = 1.0
        self.gir = 0
        self.accent = 0.12
        self.baix_on = True
        self.swing = 0.0
        self.pas = [0] * (len(_VEUS) + 1)
        self.pend = []
        self.baix_i = 0
        self.step = 0

    def setup(self):
        self.initialized = True
        self.pas = [0] * (len(_VEUS) + 1)
        self.pend = []
        self.step = 0
        self._polsos = {}
        self._panic()
        print("%s: %d BPM" % (self.name, int(self.bpm)))

    def _panic(self):
        for ch in (_PERC_CH, _BAIX_CH):
            try:
                m = ControlChange(123, 0)
                m.channel = ch
                self.midi_out.send(m)
            except Exception:
                pass

    def _pulsa(self, n, k, i, rot):
        """Bjorklund en una línia: el pas i porta pulsació si ((i·K) mod N) < K.
        Repartiment uniforme exacte, i el gir el desplaça."""
        if k <= 0:
            return False
        if k >= n:
            return True
        return ((((i + rot) % n) * k) % n) < k

    def _k(self, k_base, n):
        k = int(k_base * self.densitat + 0.5)
        return 1 if k < 1 else (n if k > n else k)

    def _allibera(self, now, totes=False):
        if not self.pend:
            return
        queden = []
        for p in self.pend:
            if totes or now >= p[2]:
                self.send_note_off(p[0], 0, p[1])
            else:
                queden.append(p)
        self.pend = queden

    def _cop(self, nota, vel, canal, dura, now):
        vel = 1 if vel < 1 else (127 if vel > 127 else int(vel))
        self.send_note_on(nota, vel, canal)
        self.pend.append([nota, canal, now + dura])

    def _pas(self, now):
        cops = 0
        toquen = []
        for v in range(len(_VEUS)):
            nota, n, kb, vel = _VEUS[v]
            rot = (self.gir * (v + 1)) % n           # cada veu gira diferent
            if self._pulsa(n, self._k(kb, n), self.pas[v], rot):
                toquen.append((nota, vel))
                cops += 1
            self.pas[v] = (self.pas[v] + 1) % n
        acc = 1.0 + self.accent * (cops - 1) if cops > 1 else 0.92
        for nota, vel in toquen:
            self._cop(nota, vel * acc, _PERC_CH, _GATE, now)
        # El baix: cicle d'onze, camina pels graus de la pentatònica
        n, kb = _BAIX
        if self.baix_on and self._pulsa(n, self._k(kb, n), self.pas[-1], self.gir % n):
            g = _BAIX_GRAUS[self.baix_i % len(_BAIX_GRAUS)]
            self.baix_i += 1
            nota = 36 + _ESCALA[g % 5] + 12 * (g // 5)
            self._cop(nota, 92 if cops > 1 else 78, _BAIX_CH, self.step_dur * 1.6, now)
        self.pas[-1] = (self.pas[-1] + 1) % n
        self.step += 1

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 80.0 + f * 80.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.step_dur = 60.0 / b / 4.0
        elif nom == 'Densitat':
            self.densitat = 0.4 + f * 1.2
        elif nom == 'Gir':
            g = int(f * 7.99)
            if g != self.gir:
                self.gir = g
                print("%s: gir %d" % (self.name, g))
        elif nom == 'Accent':
            self.accent = f * 0.3                 # quant s'accentuen les coincidències
        elif nom == 'Baix':
            self.baix_on = f >= 0.5
        elif nom == 'Swing':
            self.swing = f * 0.33
        else:
            return False
        return True

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self._allibera(now)
        self.potes(pot_values)
        k = 1.0 + (self.swing if (self.step % 2) == 0 else -self.swing)
        if self.toca('pas', self.step_dur * k):
            self._pas(now)
        return {'bpm': int(self.bpm), 'densitat': int(self.densitat * 100),
                'gir': self.gir, 'pas': self.step}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
        self._panic()
