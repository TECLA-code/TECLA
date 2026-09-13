"""
Mode Clave - La clau afrocubana: clave, càscara, congues i tumbao de baix
X: Tempo  Y: Clave (son 3-2, son 2-3, rumba 3-2, rumba 2-3)  Z: Densitat
Doble clic a qualsevol tecla: canvi de tonalitat del baix.

Tota la música afrocubana penja d'un patró de dues barres que no sona fort
però mana sobre tot: la CLAVE. Aquí sona a la percussió (canal 10, com la
bateria General MIDI) i les altres veus s'hi encaixen: la càscara a la vora
del timbal, les congues amb el cop obert al final de cada compàs, i al baix
el TUMBAO, que no toca el temps fort sinó que s'hi anticipa (l'«i» de 2 i el
4), que és el que fa que balli. El pot Y tria la clave —son o rumba, i en
quina direcció, 3-2 o 2-3— i tota la secció es gira amb ella. La densitat
afegeix veus: només clave i baix a l'esquerra; a la dreta, tot el conjunt.
"""
import time
from modes.base_mode import BaseMode

CANAL_PERC = 9                # la percussió, com la bateria General MIDI (canal 10)

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
# 16 semicorxeres per compàs, dos compassos = 32 passos. 1 = cop.
_SON32 = (1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0,
          0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0)
_RUMBA32 = (1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0,
            0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1)
_CLAVES = (('Son 3-2', _SON32, 0), ('Son 2-3', _SON32, 16),
           ('Rumba 3-2', _RUMBA32, 0), ('Rumba 2-3', _RUMBA32, 16))
_CASCARA = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0)   # un compàs
_CONGA = (0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2, 2, 0, 0)     # 1 tap, 2 obert
_TUMBAO = (0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0)    # baix: «i» de 2 i el 4
_CLAVE_N, _CASCARA_N, _CONGA_T, _CONGA_O = 75, 56, 63, 64     # notes GM de percussió


class ModeClave(BaseMode):
    PARAMS = ('Tempo', 'Clave', 'Densitat', 'Baix', 'Força', 'Tonalitat')
    POTS = ('Tempo', 'Clave', 'Densitat')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Clave"
        self.key = 0
        self.bpm = 100.0
        self.clave = 0
        self.densitat = 0.6
        self.baix_on = True
        self.forca = 1.0
        self.pas = 0
        self.perc = []                # (nota, off_t)
        self.baix = -1
        self.baix_off = 0.0
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.pas = 0
        self.perc = []
        self.baix = -1
        self._polsos = {}
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %d BPM" % (self.name, _CLAVES[self.clave][0], int(self.bpm)))

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            self.bpm = 70.0 + f * 90.0
        elif nom == 'Clave':
            c = min(3, int(f * 4))
            if c != self.clave:
                self.clave = c
                print("%s: %s" % (self.name, _CLAVES[c][0]))
        elif nom == 'Densitat':
            self.densitat = f
        elif nom == 'Baix':
            self.baix_on = f >= 0.5
            if not self.baix_on:
                self._apaga_baix()
        elif nom == 'Força':
            self.forca = 0.3 + f * 0.7
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _cop(self, nota, vel, now, durada=0.08):
        vel = int(vel * self.forca)
        self.send_note_on(nota, max(1, min(127, vel)), CANAL_PERC)
        self.perc.append((nota, now + durada))

    def _apaga_baix(self):
        if self.baix >= 0:
            self.send_note_off(self.baix, 0)
            self.baix = -1

    def _pas_tot(self, now, semi):
        nom, patro, gir = _CLAVES[self.clave]
        p = self.pas
        d = self.densitat
        if patro[(p + gir) % 32]:
            self._cop(_CLAVE_N, 108, now)
        if d > 0.25 and _CASCARA[p % 16]:
            self._cop(_CASCARA_N, 64 if p % 4 else 80, now)
        if d > 0.5:
            c = _CONGA[p % 16]
            if c == 1:
                self._cop(_CONGA_T, 58, now)
            elif c == 2:
                self._cop(_CONGA_O, 96, now, 0.2)
        if d > 0.8 and p % 4 == 0:
            self._cop(42, 40 + (30 if p % 16 == 0 else 0), now)      # charles, la marca del temps
        t = _TUMBAO[p % 16]
        if t and self.baix_on:
            self._apaga_baix()
            arrel = 36 + self.key
            n = arrel + (7 if t == 1 else 0) + (12 if (p // 16) % 2 and t == 2 else 0)
            if 0 <= n <= 127:
                self.send_note_on(n, int(92 * self.forca))
                self.baix = n
                self.baix_off = now + semi * (5 if t == 1 else 3)

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.potes(pot_values)
        semi = 60.0 / self.bpm / 4.0
        if self.perc:
            queden = []
            for nota, off in self.perc:
                if now >= off:
                    self.send_note_off(nota, 0, CANAL_PERC)
                else:
                    queden.append((nota, off))
            self.perc = queden
        if self.baix >= 0 and now >= self.baix_off:
            self._apaga_baix()
        if self.toca('semi', semi):
            self._pas_tot(now, semi)
            self.pas = (self.pas + 1) % 32
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
        return {'clave': _CLAVES[self.clave][0], 'bpm': int(self.bpm), 'pas': self.pas}

    def cleanup(self):
        for nota, _ in self.perc:
            self.send_note_off(nota, 0, CANAL_PERC)
        self.perc = []
        self._apaga_baix()
        self.stop_tracked_notes()
