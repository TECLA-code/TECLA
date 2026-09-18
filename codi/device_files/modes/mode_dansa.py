"""
Mode Dansa - Cançó de ball en sis per vuit: una tonada modal sobre un bordó, en forma AABB
X: Tempo  Y: Ornament (els mordents i els redoblaments de la gaita)  Z: Registre
Configuració de Modes: Volum · Mode · Bordó | Frase · Articulació · Tonalitat
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (Z tria l'eix).

De la família de Cançó, però amb la forma de les tonades de ball de tota
l'Europa atlàntica: la giga irlandesa, l'an-dro bretó, el ball de gaita.
A sota, un BORDÓ de fonamental i quinta que no es mou, i que a més
repica a cada temps si vols. A sobre, una tonada en sis per vuit feta de
tresets de corxeres, negra-corxera i alguna nota llarga, en un dels quatre
modes de la música de gaita: mixolidi, dòric, jònic i eòlic.

El que la fa tonada i no melodia és la FORMA: A A B B. La part A són dues
frases —pregunta i resposta— que es toquen dos cops iguals; la part B en
són dues més, una octava per damunt, també repetides. La segona vegada no
és mai ben bé la mateixa: els ORNAMENTS (el mordent de la nota de sobre a
l'atac, el redoblament a les notes llargues) cauen on volen, com ho
faria un gaiter. Cada tonada nova canvia la llavor.
"""
import time
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_MODES = (('Mixolidi', (0, 2, 4, 5, 7, 9, 10)), ('Dòric', (0, 2, 3, 5, 7, 9, 10)),
          ('Jònic', (0, 2, 4, 5, 7, 9, 11)), ('Eòlic', (0, 2, 3, 5, 7, 8, 10)))
_FINALS = (4, 0)                          # pregunta, resposta
_ACORD = (0, 2, 4)
_COMPASSOS = (2, 4, 8)
_CELLES = ((0, 1, 2), (0, 2), (0,))       # treset, negra-corxera, negra amb punt


class ModeDansa(BaseMode):
    PARAMS = ('Tempo', 'Ornament', 'Registre', 'Mode', 'Bordó', 'Frase',
              'Articulació', 'Tonalitat')
    POTS = ('Tempo', 'Ornament', 'Registre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Dansa"
        self.key = 2                  # re: el to de la gaita
        self.octave = 4
        self.bpm = 112.0              # negres amb punt per minut
        self.speed = 60.0 / self.bpm / 3.0
        self.ornament = 0.4
        self.modus = 0
        self.bordo = 2                # 0 res · 1 bordó · 2 bordó que repica
        self.artic = 0.85
        self.llarg = 4
        self.frase = 0                # 0-7: A A' A A' B B' B B'
        self.compas = 0
        self.cx = 0
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.off_t = 0.0
        self.pend_nota = -1           # la nota real, després del mordent
        self.pend_t = 0.0
        self.pend_vel = 0
        self.redobla = False
        self.drone = []
        self.repic = -1
        self.off_repic = 0.0
        self.mem = ([], [], [], [])   # les quatre frases de la tonada: (corxera, grau)
        self.mem_i = 0
        self._llavor = 1798
        self._llavor0 = 1798
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
        self.pend_nota = -1
        self.redobla = False
        self.drone = []
        self.repic = -1
        self.mem = ([], [], [], [])
        self.mem_i = 0
        self._polsos = {}
        self._llavor = self._llavor0
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %s %d BPM" % (self.name, _KEYS[self.key], _MODES[self.modus][0], int(self.bpm)))

    # ── Comandaments ────────────────────────────────────────────────────────
    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 80.0 + f * 60.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.speed = 60.0 / b / 3.0
        elif nom == 'Ornament':
            self.ornament = f
        elif nom == 'Registre':
            if not self.neg_active:
                self.octave = 3 + int(f * 2.99)
        elif nom == 'Mode':
            m = min(3, int(f * 3.99))
            if m != self.modus:
                self.modus = m
                print("%s: %s" % (self.name, _MODES[m][0]))
        elif nom == 'Bordó':
            b = min(2, int(f * 2.99))
            if b != self.bordo:
                self.bordo = b
                self._apaga_drone()
                self._apaga_repic()
        elif nom == 'Frase':
            l = _COMPASSOS[min(2, int(f * 2.99))]
            if l != self.llarg:
                self.llarg = l
                print("%s: frases de %d compassos" % (self.name, l))
        elif nom == 'Articulació':
            self.artic = 0.45 + f * 0.55
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                self._apaga_drone()
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _nota(self, grau, octava):
        e = _MODES[self.modus][1]
        return octava * 12 + self.key + e[grau % 7] + 12 * (grau // 7)

    def _part_b(self):
        return self.frase >= 4

    def _seguent_grau(self):
        alt = 7 if self._part_b() else 0
        lo = -2 + alt
        hi = 8 + alt
        objectiu = _FINALS[self.frase % 2] + alt
        resta = self.llarg * 6 - (self.compas * 6 + self.cx)
        if resta <= 3:
            return objectiu
        d = objectiu - self.grau
        cap = 1 if d > 0 else (-1 if d < 0 else 0)
        r = self._atzar(100)
        if r < 62:
            interval = 1
        elif r < 88:
            interval = 2                              # l'arpegi de la tonada
        else:
            interval = 0
        if abs(d) * 2 > resta or self._atzar(100) < 55:
            sentit = cap if cap != 0 else (1 if self._atzar(2) else -1)
        else:
            sentit = 1 if self._atzar(2) else -1
        g = self.grau + sentit * interval
        if self.cx % 3 == 0 and self._atzar(100) < 50:
            millor = g
            dist = 99
            for k in (-7, 0, 7, 14):
                for a in _ACORD:
                    if abs(a + k - g) < dist:
                        dist = abs(a + k - g)
                        millor = a + k
            g = millor
        if g > hi:
            g = hi - self._atzar(3)
        if g < lo:
            g = lo + self._atzar(3)
        return g

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1
        self.pend_nota = -1

    def _apaga_drone(self):
        for n in self.drone:
            self.send_note_off(n, 0)
        self.drone = []

    def _apaga_repic(self):
        if self.repic >= 0:
            self.send_note_off(self.repic, 0)
            self.repic = -1

    def _engega_drone(self):
        self._apaga_drone()
        if self.bordo == 0:
            return
        tonica = (self.octave * 12 + self.key) % 12
        for n in ((self.octave - 1) * 12 + self.key, (self.octave - 1) * 12 + self.key + 7):
            n = self.negharm(n, tonica)
            if 12 <= n <= 96:
                self.send_note_on(n, 54)
                self.drone.append(n)

    def _ataca(self, now, nota, vel, durada, gracia):
        """Una nota, amb mordent o sense: el mordent sona ara i la nota just després."""
        self._apaga()
        if gracia >= 0 and gracia != nota:
            self.send_note_on(gracia, max(20, vel - 12))
            self.sonant = gracia
            self.pend_nota = nota
            self.pend_vel = vel
            self.pend_t = now + min(0.07, self.speed * 0.3)
            self.off_t = self.pend_t + durada
        else:
            self.send_note_on(nota, vel)
            self.sonant = nota
            self.off_t = now + durada

    def _pas(self, now):
        cx = self.cx
        pos = cx % 3
        tonica = (self.octave * 12 + self.key) % 12
        rep = (self.frase % 4) >= 2                    # segona volta de la part
        slot = (2 if self._part_b() else 0) + self.frase % 2
        abs_cx = self.compas * 6 + cx
        if abs_cx == 0:
            self.mem_i = 0
            if not rep:
                self.mem[slot].clear()
            if self.frase == 0 or self.frase == 4:
                print("%s: part %s" % (self.name, 'B' if self._part_b() else 'A'))
                if not self.drone:
                    self._engega_drone()
        if self.bordo == 2 and pos == 0:
            self._apaga_repic()
            n = self.negharm(self.octave * 12 + self.key, tonica)
            if 12 <= n <= 108:
                self.send_note_on(n, 60 if cx == 0 else 48)
                self.repic = n
                self.off_repic = now + self.speed * 0.6
        # Redoblament: a mig d'una nota llarga, la nota de sota i tornar
        if pos == 1 and self.redobla and self.sonant >= 0:
            self.redobla = False
            nota = self.sonant
            self._ataca(now, nota, self.pend_vel, self.off_t - now, self._nota(self.grau - 1, self.octave + 1))
            return
        if rep:
            m = self.mem[slot]
            if self.mem_i >= len(m) or m[self.mem_i][0] != abs_cx:
                return
            g = m[self.mem_i][1]
            self.mem_i += 1
            n = (m[self.mem_i][0] - abs_cx) if self.mem_i < len(m) else (self.llarg * 6 - abs_cx)
        else:
            if pos == 0:
                if self.compas == self.llarg - 1 and cx == 3:
                    self.cella = (0,)
                else:
                    r = self._atzar(100)
                    self.cella = _CELLES[0 if r < 60 else (1 if r < 85 else 2)]
            if pos not in self.cella:
                return
            g = self._seguent_grau()
            self.mem[slot].append((abs_cx, g))
            n = 3 - pos
            for p in self.cella:
                if p > pos:
                    n = p - pos
                    break
        self.grau = g
        nota = self.negharm(self._nota(g, self.octave + 1), tonica)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        tot = self.llarg * 6
        arc = 1.0 - abs((abs_cx / float(tot - 1)) * 2.0 - 1.0)
        vel = int(68 + 26 * arc + (10 if pos == 0 else 0) + (6 if self._part_b() else 0))
        vel = 30 if vel < 30 else (120 if vel > 120 else vel)
        durada = self.speed * n * self.artic
        if self.compas == self.llarg - 1 and cx >= 3:
            durada = self.speed * (5.0 if rep and self.frase % 2 else 3.5)
        gracia = -1
        if pos == 0 and self._atzar(100) < int(70 * self.ornament):
            gracia = self.negharm(self._nota(g + 1, self.octave + 1), tonica)   # el mordent
            gracia = 24 if gracia < 24 else (108 if gracia > 108 else gracia)
        self.redobla = n >= 3 and self._atzar(100) < int(60 * self.ornament)
        self.pend_vel = vel
        self._ataca(now, nota, vel, durada, gracia)

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)

        if self.pend_nota >= 0 and now >= self.pend_t:
            if self.sonant >= 0:
                self.send_note_off(self.sonant, 0)
            self.send_note_on(self.pend_nota, self.pend_vel)
            self.sonant = self.pend_nota
            self.pend_nota = -1
        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        if self.repic >= 0 and now >= self.off_repic:
            self._apaga_repic()
        if self.bordo and not self.drone and self.cx == 0:
            self._engega_drone()
        mult = 1.0
        if self.compas == self.llarg - 1 and self.cx >= 4 and self.frase % 2 == 1:
            mult = 1.3                                 # la resposta respira abans de tornar-hi
        if self.toca('cx', self.speed * mult):
            self._pas(now)
            self.cx += 1
            if self.cx >= 6:
                self.cx = 0
                self.compas += 1
                if self.compas >= self.llarg:
                    self.compas = 0
                    self.frase = (self.frase + 1) % 8
                    if self.frase == 0:
                        self._llavor0 = (self._llavor0 + 7919) & 0x7FFFFFFF
                        self._llavor = self._llavor0

        for i in range(min(len(button_states), 15)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                if 0.05 < (now - self.last_rel[i]) < 0.4:
                    self.last_rel[i] = 0.0
                    self.key = (self.key + 1) % 12
                    self._apaga_drone()
                    print("%s: %s" % (self.name, _KEYS[self.key]))
                else:
                    self.last_rel[i] = now
            self.last_btn[i] = cur
        return {'key': _KEYS[self.key], 'part': 'B' if self._part_b() else 'A',
                'frase': self.frase % 4 + 1, 'bpm': int(self.bpm)}

    def cleanup(self):
        self._apaga()
        self._apaga_drone()
        self._apaga_repic()
        self.stop_tracked_notes()
