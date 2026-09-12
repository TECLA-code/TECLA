"""
Mode Caos - El mapa logístic, del punt fix al caos, quantitzat a l'escala
X: Paràmetre r (2,8 → 4,0)  Y: Velocitat  Z: Amplitud (quantes notes abasta)
Doble clic a qualsevol tecla: canvi de tonalitat.

De la família de les ones, la que no és cap ona: x = r·x·(1−x). El pot X
recorre el camí sencer cap al caos, i se sent: amb r sota 3 la nota es
queda quieta (punt fix); a 3 comença a alternar dues notes (període 2);
cap a 3,45 en són quatre, després vuit, cada cop més de pressa (la cascada
de Feigenbaum); a partir de 3,57 ja no es repeteix mai; i a 3,83 s'obre una
finestra on de sobte torna un període de tres, enmig del caos. Tot això no
és una il·lustració: és exactament la fórmula que corre a cada nota.

La peça clau és la QUANTITZACIÓ: el valor 0-1 es mapa a graus d'una escala,
no a semitons, i el caos deixa de sonar a sirena i sona a música. Y és la
velocitat de les notes, Z quantes n'abasta (d'una quinta a tres octaves), i
la força de cada nota segueix el salt que ha fet: els salts grans piquen.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 7, 9)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_BASE_OCT = 3


class ModeCaos(BaseMode):
    PARAMS = ('Paràmetre del caos', 'Velocitat', 'Amplitud', 'Força', 'Octava', 'Tonalitat')
    POTS = ('Paràmetre del caos', 'Velocitat', 'Amplitud')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Caos"
        self.key = 0
        self.r = 3.7
        self.x = 0.31
        self.speed = 0.25            # segons per nota
        self.abast = 12              # graus de l'escala que abasta
        self.sonant = -1
        self.grau_ant = 0
        self.r_dit = 0.0
        self.forca = 1.0
        self.octava = _BASE_OCT
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.x = 0.31
        self.sonant = -1
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: r=%.2f" % (self.name, self.r))

    def _nota(self, grau):
        n = len(_ESCALA)
        return self.octava * 12 + self.key + _ESCALA[grau % n] + 12 * (grau // n)

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def _pas(self):
        # Un pas del mapa. Es protegeix dels extrems: a 0 o 1 s'hi quedaria.
        x = self.r * self.x * (1.0 - self.x)
        if x < 0.0005:
            x = 0.0005
        elif x > 0.9995:
            x = 0.9995
        self.x = x
        grau = int(x * self.abast)
        salt = abs(grau - self.grau_ant)
        self.grau_ant = grau
        nota = self._nota(grau)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        vel = int((58 + min(60, salt * 9)) * self.forca)
        if nota == self.sonant:
            return                    # punt fix: la nota es queda sonant, no es repica
        self._apaga()
        self.send_note_on(nota, vel)
        self.sonant = nota

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Paràmetre del caos':
            r = 2.8 + f * 1.2
            self.r = r
            if abs(r - self.r_dit) >= 0.05:
                self.r_dit = r
                print("%s: r=%.2f" % (self.name, r))
        elif nom == 'Velocitat':
            self.speed = 0.6 - f * 0.52               # 1,7 a 12,5 notes/s
        elif nom == 'Amplitud':
            self.abast = 4 + int(f * 12.99)            # de 4 a 16 graus
        elif nom == 'Força':
            self.forca = 0.3 + f * 0.7
        elif nom == 'Octava':
            self.octava = 2 + int(f * 2.99)
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
        self.potes(pot_values)
        if self.toca('nota', self.speed):
            self._pas()
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
        return {'r': round(self.r, 3), 'x': round(self.x, 3), 'key': _KEYS[self.key]}

    def cleanup(self):
        self._apaga()
        self.stop_tracked_notes()
