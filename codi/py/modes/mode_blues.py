"""
Mode Blues - Dotze compassos amb shuffle, baix caminant i una veu que respon
X: Tempo  Y: Swing  Z: Densitat
Doble clic a qualsevol tecla: canvi de tonalitat.

El blues és una FORMA abans que una escala: dotze compassos que tothom sap
(I I I I · IV IV I I · V IV I I) i que per això es poden tocar a sobre sense
haver-se posat d'acord. Aquí la forma la porta el baix, que camina per les
notes de cada acord (fonamental, tercera, quinta, sisena, setena menor…) i
marca el canvi. Per sobre, una veu improvisa amb l'escala de blues (amb la
nota blava, la quinta disminuïda) en FRASES de pregunta i resposta: dos
compassos de pregunta, dos de resposta que tornen a la fonamental, i un
silenci entre frase i frase, que en el blues és tan important com les notes.
El swing és el de debò: les corxeres van a parells desiguals, del recte
(pot a l'esquerra) al tresillo (a la dreta). La densitat diu quantes notes
té cada frase, de dues o tres a un reguitzell.
"""
import time
from modes.base_mode import BaseMode

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_FORMA = (0, 0, 0, 0, 5, 5, 0, 0, 7, 5, 0, 0)         # grau (semitons) de cada compàs
_BLUES = (0, 3, 5, 6, 7, 10)                          # escala de blues
_CAMI = (0, 4, 7, 9, 10, 9, 7, 4)                     # el baix, per corxeres


class ModeBlues(BaseMode):
    PARAMS = ('Tempo', 'Swing', 'Densitat', 'Registre', 'Baix', 'Tonalitat')
    POTS = ('Tempo', 'Swing', 'Densitat')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Blues"
        self.key = 0
        self.octave = 4
        self.bpm = 96.0
        self.swing = 0.62             # fracció de la negra que dura la primera corxera
        self.densitat = 0.5
        self.baix_on = True
        self.compas = 0
        self.corxera = 0              # 0..7 dins del compàs (4/4)
        self.sonant = -1
        self.off_t = 0.0
        self.baix = -1
        self.grau = 0
        self.frase_notes = 0
        self._llavor = 1234
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.compas = 0
        self.corxera = 0
        self.sonant = -1
        self.baix = -1
        self.grau = 0
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %d BPM" % (self.name, _KEYS[self.key], int(self.bpm)))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 60.0 + f * 100.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
        elif nom == 'Swing':
            self.swing = 0.5 + f * 0.22
        elif nom == 'Densitat':
            self.densitat = f
        elif nom == 'Registre':
            self.octave = 3 + int(f * 2.99)
        elif nom == 'Baix':
            b = f >= 0.5
            if b != self.baix_on:
                self.baix_on = b
                self._apaga_baix()
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def _apaga_baix(self):
        if self.baix >= 0:
            self.send_note_off(self.baix, 0)
            self.baix = -1

    def _pas_baix(self):
        self._apaga_baix()
        if not self.baix_on:
            return
        arrel = (self.octave - 2) * 12 + self.key + _FORMA[self.compas]
        n = arrel + _CAMI[self.corxera]
        if self.corxera == 7 and self.compas in (3, 7, 11):
            n = arrel + 11 if _FORMA[(self.compas + 1) % 12] == 0 else arrel + 12   # sensible cap al següent
        if 0 <= n <= 127:
            self.send_note_on(n, 78 if self.corxera % 2 == 0 else 62)
            self.baix = n

    def _pas_veu(self, now, durada):
        """Pregunta als compassos parells del parell, resposta als senars."""
        c = self.compas % 4
        if self.corxera == 0:
            self.frase_notes = 0
        # Silenci entre frases: l'últim compàs de cada resposta calla més
        maxim = 2 + int(self.densitat * 6)
        if self.frase_notes >= maxim or (c == 3 and self.corxera >= 4):
            self._apaga()
            return
        if self._atzar(100) > 35 + int(self.densitat * 55):
            return
        # La veu es mou per l'escala de blues; la resposta cau cap a la tònica
        salt = self._atzar(3) - 1
        if c >= 2 and self.grau > 0 and self._atzar(100) < 60:
            salt = -1
        self.grau = max(-2, min(9, self.grau + salt))
        if c == 3 and self.corxera >= 2:
            self.grau = 0                              # la resposta acaba a casa
        e = _BLUES
        nota = self.octave * 12 + self.key + e[self.grau % 6] + 12 * (self.grau // 6)
        nota = self.negharm(nota, self.key)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        vel = 84 if self.corxera % 2 == 0 else 66
        if self.grau % 6 == 3:
            vel += 14                                  # la nota blava, marcada
        self._apaga()
        self.send_note_on(nota, min(127, vel))
        self.sonant = nota
        self.off_t = now + durada * 0.8
        self.frase_notes += 1

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)
        negra = 60.0 / self.bpm
        # Shuffle: la corxera del temps dura swing·negra i la del contratemps la resta
        durada = negra * (self.swing if self.corxera % 2 == 0 else 1.0 - self.swing)
        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        if self.toca('corxera', durada):
            self._pas_baix()
            self._pas_veu(now, durada)
            self.corxera += 1
            if self.corxera >= 8:
                self.corxera = 0
                self.compas = (self.compas + 1) % 12
                if self.compas == 0:
                    print("%s: torna a l'I" % self.name)
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
        return {'key': _KEYS[self.key], 'compas': self.compas + 1, 'bpm': int(self.bpm)}

    def cleanup(self):
        self._apaga()
        self._apaga_baix()
        self.stop_tracked_notes()
