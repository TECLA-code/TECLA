"""
Mode Marea - Dues ones lentes que no coincideixen mai: una fa les notes, l'altra el timbre
X: Període  Y: Amplitud  Z: Onatge
Doble clic a qualsevol tecla: canvi de tonalitat.

Una ona sola és una sirena. Dues ones amb períodes que no tenen mesura comuna
(la segona va al ritme de la proporció àuria) donen una cosa que no es
repeteix mai i que, tanmateix, sempre és la mateixa: una marea. La primera
ona puja i baixa per l'escala, quantitzada de grau en grau, i cada canvi de
grau és una nota nova que se sosté fins a la següent. La segona ona no fa
notes: obre i tanca la brillantor (CC74) i l'expressió (CC11), com l'aigua
que arriba i es retira, i el punt on les dues coincideixen és el moment
que espera tothom que mira el mar. Per sota, una tercera ona molt més
lenta —minuts— desplaça el registre de tot plegat: la marea de debò.
"""
import time
import math
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_ESCALES = (('Major', (0, 2, 4, 5, 7, 9, 11)), ('Menor', (0, 2, 3, 5, 7, 8, 10)),
            ('Pentatònica', (0, 2, 4, 7, 9)), ('Lídia', (0, 2, 4, 6, 7, 9, 11)))
_AURI = 1.6180339


class ModeMarea(BaseMode):
    PARAMS = ('Període', 'Amplitud', 'Onatge', 'Escala', 'Registre', 'Marea', 'Tonalitat')
    POTS = ('Període', 'Amplitud', 'Onatge')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Marea"
        self.key = 0
        self.octave = 4
        self.periode = 12.0           # segons de l'ona de notes
        self.amplitud = 0.5           # fins a dues octaves
        self.onatge = 0.6             # profunditat de l'ona de timbre
        self.escala = 0
        self.marea = 0.5              # amplitud de la marea lenta (semitons)
        self.f1 = 0.0
        self.f2 = 0.0
        self.f3 = 0.0
        self.sonant = -1
        self.grau_ant = None
        self.cc74 = -1
        self.cc11 = -1
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.f1 = 0.0
        self.f2 = 0.25
        self.f3 = 0.0
        self.sonant = -1
        self.grau_ant = None
        self.cc74 = -1
        self.cc11 = -1
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %s" % (self.name, _KEYS[self.key], _ESCALES[self.escala][0]))

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Període':
            self.periode = 3.0 + f * f * 57.0        # de 3 s a un minut
        elif nom == 'Amplitud':
            self.amplitud = 0.1 + f * 0.9
        elif nom == 'Onatge':
            self.onatge = f
        elif nom == 'Escala':
            e = min(3, int(f * 4))
            if e != self.escala:
                self.escala = e
                print("%s: %s" % (self.name, _ESCALES[e][0]))
        elif nom == 'Registre':
            self.octave = 3 + int(f * 2.99)
        elif nom == 'Marea':
            self.marea = f
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _cc(self, cc, v):
        try:
            from adafruit_midi.control_change import ControlChange
            self.midi_out.send(ControlChange(cc, max(0, min(127, int(v)))))
        except Exception:
            pass

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.potes(pot_values)
        if self.toca('ona', 0.03):
            dt = 0.03
            self.f1 = (self.f1 + dt / self.periode) % 1.0
            self.f2 = (self.f2 + dt / (self.periode * _AURI)) % 1.0
            self.f3 = (self.f3 + dt / (self.periode * 11.0)) % 1.0
            # Ona 1: l'alçada, quantitzada a l'escala
            e = _ESCALES[self.escala][1]
            n_e = len(e)
            abast = self.amplitud * 2.0 * n_e          # graus d'amplitud (fins a 2 octaves)
            g = int(round(math.sin(self.f1 * 6.2832) * abast * 0.5))
            desp = math.sin(self.f3 * 6.2832) * self.marea * 7.0  # la marea lenta, en semitons
            if g != self.grau_ant:
                self.grau_ant = g
                nota = self.octave * 12 + self.key + e[g % n_e] + 12 * (g // n_e) + int(desp)
                nota = 24 if nota < 24 else (108 if nota > 108 else nota)
                # La força segueix l'ona de timbre: el cim de les dues ones alhora
                cresta = 0.5 + 0.5 * math.sin(self.f2 * 6.2832)
                self._apaga()
                self.send_note_on(nota, int(50 + 60 * cresta))
                self.sonant = nota
            # Ona 2: brillantor i expressió
            cresta = 0.5 + 0.5 * math.sin(self.f2 * 6.2832)
            c74 = int(40 + 87 * cresta * self.onatge + 87 * (1.0 - self.onatge) * 0.5)
            c11 = int(127 - self.onatge * 60 * (1.0 - cresta))
            if abs(c74 - self.cc74) >= 2:
                self.cc74 = c74
                self._cc(74, c74)
            if abs(c11 - self.cc11) >= 2:
                self.cc11 = c11
                self._cc(11, c11)
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
        return {'key': _KEYS[self.key], 'periode': int(self.periode), 'fase': int(self.f1 * 100)}

    def cleanup(self):
        self._apaga()
        self._cc(74, 64)
        self._cc(11, 127)
        self.stop_tracked_notes()
