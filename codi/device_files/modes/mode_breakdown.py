"""
Mode Breakdown - Techno: quatre per quatre, baix àcid i el recurs de retirar capes
X: Tempo  Y: Àcid (obertura del filtre i variació del baix)  Z: Breakdown (capes)

Set modes de techno, groove i acid feien variacions del mateix gest, i el
gest és aquest: un bombo a cada pulsació, la caixa al dos i al quatre, el
charles a contratemps amb un d'obert al final del compàs, i un baix de
setze passos amb accents i salts d'octava que és el que va fer la TB-303.
Sobre això, l'únic recurs que importa en directe: el BREAKDOWN. El pot Z
retira capes d'una en una —primer el charles obert i les claves, després la
caixa, després el charles, i al final només queda el bombo, o només el baix
sense bombo— i en tornar-les a posar la pista esclata. El pot Y és l'àcid:
obre el filtre (CC74) i la ressonància (CC71) i, a la meitat superior,
muta el patró del baix a una variació més nerviosa. La percussió surt pel
canal 10 i el baix pel canal 1.
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PERC_CH = 9
_BAIX_CH = 0
_BOMBO, _CAIXA, _CHARLES, _OBERT, _CLAVES = 36, 38, 42, 46, 75
_GATE = 0.05
# Baix: graus cromàtics sobre la tònica (−1 = silenci), accent (1) i octava (+12)
_BAIX_A = ((0, 1, 0), (-1, 0, 0), (0, 0, 0), (12, 0, 0), (0, 0, 0), (-1, 0, 0), (3, 1, 0), (0, 0, 0),
           (0, 1, 0), (-1, 0, 0), (0, 0, 0), (7, 0, 0), (0, 0, 0), (10, 1, 0), (0, 0, 0), (12, 0, 0))
_BAIX_B = ((0, 1, 0), (0, 0, 0), (12, 0, 0), (0, 0, 0), (3, 1, 0), (0, 0, 0), (12, 0, 0), (0, 0, 0),
           (0, 1, 0), (7, 0, 0), (0, 0, 0), (12, 1, 0), (0, 0, 0), (10, 0, 0), (12, 0, 0), (0, 1, 0))
_CAPES_NOMS = ('nomes baix', 'nomes bombo', 'bombo+baix', '+charles', '+caixa', 'tot')


class ModeBreakdown(BaseMode):
    CANAL_PERC = 9
    PARAMS = ('Tempo', 'Àcid', 'Capes (breakdown)', 'Swing', 'Accent', 'Octava del baix', 'Repicons')
    POTS = ('Tempo', 'Àcid', 'Capes (breakdown)')


    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Breakdown"
        self.bpm = 132.0
        self.step_dur = 60.0 / self.bpm / 4.0
        self.acid = 0.4
        self.capa = 5
        self.step = 0
        self.pend = []
        self.arrel = 36
        self.swing = 0.0
        self.accent = 0.5
        self.repic = 0.0
        self.repic_ara = False
        self._llavor = 777
        self._cc_cache = {}

    def setup(self):
        self.initialized = True
        self.step = 0
        self.pend = []
        self._cc_cache = {}
        self._polsos = {}
        self._panic()
        print("%s: %d BPM" % (self.name, int(self.bpm)))

    def _cc(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if abs(self._cc_cache.get(cc, -99) - v) < 2:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _panic(self):
        for ch in (_PERC_CH, _BAIX_CH):
            try:
                m = ControlChange(123, 0)
                m.channel = ch
                self.midi_out.send(m)
            except Exception:
                pass

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
        i = self.step % 16
        c = self.capa
        if c >= 1 and c != 0 and i % 4 == 0:
            self._cop(_BOMBO, 112, _PERC_CH, _GATE, now)
        if c >= 4 and (i == 4 or i == 12):
            self._cop(_CAIXA, 96, _PERC_CH, _GATE, now)
            self.repic_ara = self.repic > 0.0 and self._atzar(1000) < int(self.repic * 1000)
        elif c >= 4 and (i == 5 or i == 13) and self.repic_ara:
            self._cop(_CAIXA, 62, _PERC_CH, _GATE, now)           # el repicó
            self.repic_ara = False
        if c >= 3 and i % 2 == 1:
            self._cop(_CHARLES, int(40 + 30 * self.accent) if i % 4 == 1 else 70, _PERC_CH, _GATE, now)
        if c >= 5:
            if i == 14:
                self._cop(_OBERT, 84, _PERC_CH, self.step_dur * 1.5, now)
            if i in (3, 6, 11):
                self._cop(_CLAVES, 66, _PERC_CH, _GATE, now)
        if c == 0 or c >= 2:
            patro = _BAIX_B if self.acid > 0.5 else _BAIX_A
            semi, accent, _ = patro[i]
            if semi >= 0:
                nota = self.arrel + semi
                vel = 118 if accent else 84
                dura = self.step_dur * (0.85 if accent else 0.5)
                self._cop(nota, vel, _BAIX_CH, dura, now)
                # L'àcid: cada accent obre el filtre i el pot decideix fins on
                self._cc(74, 30 + int(self.acid * 90) + (20 if accent else 0))
        self.step += 1

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 118.0 + f * 32.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.step_dur = 60.0 / b / 4.0
        elif nom == 'Àcid':
            self.acid = f
            self._cc(71, int(20 + self.acid * 100))
        elif nom == 'Capes (breakdown)':
            c = int(f * 5.99)
            if c != self.capa:
                self.capa = c
                print("%s: %s" % (self.name, _CAPES_NOMS[c]))
        elif nom == 'Swing':
            self.swing = f * 0.33
        elif nom == 'Accent':
            self.accent = f
        elif nom == 'Octava del baix':
            self.arrel = 24 + 12 * min(2, int(f * 3))
        elif nom == 'Repicons':
            self.repic = f * 0.5
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
        return {'bpm': int(self.bpm), 'acid': int(self.acid * 100),
                'capa': _CAPES_NOMS[self.capa], 'pas': self.step % 16}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
        self._cc(74, 64)
        self._cc(71, 40)
        self._panic()
