"""
Mode Contrapunt - Dues veus que es persegueixen: cànon, inversió i desfasament
X: Tempo  Y: Relació entre veus  Z: Octava
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (Z tria l'eix).

L'essència de la família melòdica no és la melodia sinó el que passa quan
n'hi ha dues. Un sol subjecte de dotze notes, i la segona veu el repeteix
d'una de cinc maneres: a l'octava, a la quinta, invertit (el mirall de Bach),
retrògrad (de darrere cap endavant) o en FASE —la veu segona va un 9/8 més
lenta i les dues es desfasen a poc a poc fins a tornar a coincidir, que és
el mecanisme de Reich a "Piano Phase". El pot Y recorre les cinc relacions;
X és el tempo i Z l'octava. Quan les dues veus ataquen alhora i formen una
consonància (tercera, sexta, octava), l'atac és més fort: el contrapunt es
sent, no només se sap.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 5, 7, 9, 11)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
# El subjecte, en graus de l'escala (−1 = silenci). Puja, respira, torna.
_SUBJECTE = (0, 2, 4, 5, 4, 2, 1, 3, 2, 0, -1, 4)
_RELACIONS = ('Octava', 'Quinta', 'Inversio', 'Retrograd', 'Fase')
_OCT = 4
_VEL1 = 96
_VEL2 = 76
_CONSONANTS = (0, 3, 4, 7, 8, 9, 12)   # semitons: unísons, terceres, quinta, sextes, octava


class ModeContrapunt(BaseMode):
    PARAMS = ('Tempo', 'Relació', 'Octava', 'Articulació', 'Contrast', 'Tonalitat')
    POTS = ('Tempo', 'Relació', 'Octava')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Contrapunt"
        self.key = 0
        self.octave = _OCT
        self.relacio = 0
        self.bpm = 96.0
        self.speed = 60.0 / self.bpm / 2.0     # corxeres
        self.pas = [0, 0]                      # índex de cada veu dins del subjecte
        self.sonant = [-1, -1]                 # nota que sona a cada veu
        self.off_t = [0.0, 0.0]
        self.artic = 1.0
        self.contrast = 20
        self.atac_t = [0.0, 0.0]               # quan ha atacat cada veu (coincidència)
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.pas = [0, 0]
        self.sonant = [-1, -1]
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %s" % (self.name, _KEYS[self.key], _RELACIONS[self.relacio]))

    def _nota(self, grau):
        n = len(_ESCALA)
        return self.octave * 12 + self.key + _ESCALA[grau % n] + 12 * (grau // n)

    def _grau_veu(self, veu, i):
        """Grau del subjecte per a la veu `veu` al pas `i`, segons la relació."""
        n = len(_SUBJECTE)
        if veu == 0:
            g = _SUBJECTE[i % n]
            return None if g < 0 else g
        r = self.relacio
        if r == 3:                              # retrògrad
            g = _SUBJECTE[(n - 1 - i) % n]
            return None if g < 0 else g - 7     # una octava avall
        g = _SUBJECTE[(i - 2) % n]              # cànon: entra dos passos després
        if g < 0:
            return None
        if r == 0:
            return g - 7                        # a l'octava inferior
        if r == 1:
            return g - 3                        # a la quinta inferior (grau IV avall)
        if r == 2:
            return 4 - g - 7                    # inversió al voltant del III, una octava avall
        return g - 7                            # fase: mateix subjecte, altre període

    def _apaga(self, veu):
        if self.sonant[veu] >= 0:
            self.send_note_off(self.sonant[veu], 0)
            self.sonant[veu] = -1

    def _ataca(self, veu, now):
        g = self._grau_veu(veu, self.pas[veu])
        self.pas[veu] += 1
        self._apaga(veu)
        if g is None:
            return
        nota = self.negharm(self._nota(g), (self.octave * 12 + self.key) % 12)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        vel = _VEL1 if veu == 0 else _VEL1 - self.contrast
        altra = 1 - veu
        # Coincidència consonant: les dues veus ataquen alhora i s'entenen
        if self.sonant[altra] >= 0 and now - self.atac_t[altra] < 0.02:
            if abs(nota - self.sonant[altra]) % 12 in _CONSONANTS:
                vel += 14
        self.send_note_on(nota, vel)
        self.sonant[veu] = nota
        self.atac_t[veu] = now
        self.off_t[veu] = now + self.speed * self.artic * (1.7 if veu == 0 else 1.4)

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 60.0 + f * 120.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.speed = 60.0 / b / 2.0
        elif nom == 'Relació':
            r = min(4, int(f * 5))
            if r != self.relacio:
                self.relacio = r
                self.pas = [0, 0]
                print("%s: %s" % (self.name, _RELACIONS[r]))
        elif nom == 'Octava':
            if not self.neg_active:
                self.octave = 3 + int(f * 2.99)
        elif nom == 'Articulació':
            self.artic = 0.5 + f * 1.5            # de picada a molt lligada
        elif nom == 'Contrast':
            self.contrast = int(f * 40)           # quant més fluixa va la segona veu
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])

        self.potes(pot_values)

        for v in (0, 1):
            if self.sonant[v] >= 0 and now >= self.off_t[v]:
                self._apaga(v)
        if self.toca('v1', self.speed):
            self._ataca(0, now)
        k2 = 1.125 if self.relacio == 4 else 1.0     # fase: 9/8 del període
        if self.toca('v2', self.speed * k2):
            self._ataca(1, now)

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
        return {'key': _KEYS[self.key], 'relacio': _RELACIONS[self.relacio],
                'bpm': int(self.bpm), 'oct': self.octave}

    def cleanup(self):
        self._apaga(0)
        self._apaga(1)
        self.stop_tracked_notes()
