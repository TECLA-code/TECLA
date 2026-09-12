"""
Mode Ràdio - Buscar emissora: estàtica, xiulet d'heterodí i cinc programes
X: Dial  Y: Estàtica (densitat del soroll entre emissores)  Z: Escombrat automàtic

El TECLA no té generador de soroll: té setze tecles i un port MIDI. El soroll
es fa com s'ha fet sempre, amb massa esdeveniments alhora, i aquí es fa
servir per a la cosa més radiofònica que hi ha: buscar emissora. Al dial hi
ha cinc emissores. Entre dues, se sent l'ESTÀTICA —grans de soroll amb
espectre rosa, els greus més presents que els aguts— i el XIULET d'heterodí,
el batec entre la portadora i el receptor, que com més desintonitzat més
agut és i que baixa fins a desaparèixer quan hi entres. I quan hi ets, sona
el PROGRAMA de l'emissora, net: un bordó de quinta, un arpegi lent, un pols
de percussió, un fragment de melodia o el morse d'una balisa. Cada emissora
és un mode en miniatura.

X és la rodeta del dial. Y és quant soroll hi ha entre emissores (de quasi
res a paret). Z engega l'escombrat automàtic: el dial es mou sol, cada cop
més de pressa, i la ràdio va passant emissores com un cotxe de nit.
"""
import time
from modes.base_mode import BaseMode

_ESTACIONS = 5
_PROGRAMES = ('bordo', 'arpegi', 'pols', 'melodia', 'morse')
_PERC_CH = 9
_MAX_VEUS = 14
_MAX_PER_TICK = 6
_ARPEGI = (0, 7, 12, 16, 19, 16, 12, 7)
_MELODIA = (0, 2, 4, 7, 4, 2, 0, -3, -1, 0, 4, 2)
_MORSE = (1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0)


class ModeRadio(BaseMode):
    CANAL_PERC = 9
    PARAMS = ('Dial (emissora)', 'Estàtica', 'Escombrat', 'Xiulet del dial', 'Amplada', 'Intensitat', 'Programa')
    POTS = ('Dial (emissora)', 'Estàtica', 'Escombrat')


    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Ràdio"
        self.dial = 0.5
        self.estatica = 40.0          # grans per segon quan no hi ha emissora
        self.escombrat = 0.0          # velocitat de l'escombrat automàtic
        self.deute = 0.0
        self.t_ant = 0.0
        self.pend = []
        self.xiulet = -1
        self.emissora = -1            # a quina emissora estem sintonitzats (−1 = cap)
        self.prog_i = 0
        self.prog_notes = []
        self.rosa = [0.0, 0.0, 0.0]
        self.xiulet_k = 0.7
        self.amplada = 28
        self.intensitat = 1.0
        self.prog_vel = 0.22
        self._llavor = 2718

    def setup(self):
        self.initialized = True
        self.t_ant = time.monotonic()
        self.deute = 0.0
        self.pend = []
        self.xiulet = -1
        self.emissora = -1
        self.prog_notes = []
        self._polsos = {}
        print("%s: dial %d" % (self.name, int(self.dial * 100)))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _soroll_rosa(self):
        """Tres octaves de soroll blanc sumades a ritmes diferents (Voss):
        més greus que aguts, espectre aproximadament 1/f. Entre −1 i 1."""
        r = self.rosa
        r[0] = self._atzar(2001) / 1000.0 - 1.0
        if self._atzar(2) == 0:
            r[1] = self._atzar(2001) / 1000.0 - 1.0
        if self._atzar(4) == 0:
            r[2] = self._atzar(2001) / 1000.0 - 1.0
        return (r[0] + r[1] + r[2]) / 3.0

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

    def _cop(self, nota, vel, dura, now, canal=0):
        if nota < 12 or nota > 120:
            return
        vel = 1 if vel < 1 else (127 if vel > 127 else int(vel))
        self.send_note_on(nota, vel, canal)
        if dura <= 0.003:
            self.send_note_off(nota, 0, canal)
            return
        self.pend.append([nota, canal, now + dura])
        if len(self.pend) > _MAX_VEUS:
            v = self.pend.pop(0)
            self.send_note_off(v[0], 0, v[1])

    def _calla_programa(self):
        for n in self.prog_notes:
            self.send_note_off(n, 0)
        self.prog_notes = []

    def _programa(self, k, now):
        """El programa de l'emissora k, a cada pols de programa."""
        p = _PROGRAMES[k % len(_PROGRAMES)]
        base = 48 + k * 5
        if p == 'bordo':
            if not self.prog_notes:
                for iv in (0, 7, 12):
                    self.send_note_on(base + iv, 64)
                    self.prog_notes.append(base + iv)
        elif p == 'arpegi':
            self._cop(base + _ARPEGI[self.prog_i % 8], 72, 0.9, now)
        elif p == 'pols':
            i = self.prog_i % 8
            if i % 2 == 0:
                self._cop(36, 100, 0.05, now, _PERC_CH)
            if i == 4:
                self._cop(38, 90, 0.05, now, _PERC_CH)
            self._cop(42, 60, 0.05, now, _PERC_CH)
        elif p == 'melodia':
            g = _MELODIA[self.prog_i % len(_MELODIA)]
            self._cop(base + 12 + g, 80, 0.3, now)
        else:                                          # morse
            if _MORSE[self.prog_i % len(_MORSE)]:
                self._cop(base + 31, 90, 0.11, now)
        self.prog_i += 1

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Dial (emissora)':
            self.dial = f
        elif nom == 'Estàtica':
            self.estatica = 2.0 + f * 160.0
        elif nom == 'Escombrat':
            self.escombrat = 0.0 if v < 6 else 0.01 + f * 0.25
        elif nom == 'Xiulet del dial':
            self.xiulet_k = f
        elif nom == 'Amplada':
            self.amplada = 6 + int(f * 42)             # semitons de dispersió de l'estàtica
        elif nom == 'Intensitat':
            self.intensitat = 0.3 + f * 0.7
        elif nom == 'Programa':
            self.prog_vel = 0.08 + f * 0.6             # segons entre polsos del programa
        else:
            return False
        return True

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self._allibera(now)
        dt = now - self.t_ant
        if dt > 0.25:
            dt = 0.25
        self.t_ant = now
        self.potes(pot_values)
        if self.escombrat > 0.0:
            self.dial = (self.dial + self.escombrat * dt) % 1.0

        pos = self.dial * (_ESTACIONS - 1)
        k = int(pos + 0.5)
        des = pos - k                                  # −0,5 … 0,5
        prop = 1.0 - abs(des) * 2.0                    # 1 sintonitzat, 0 entremig
        sintonitzat = prop > 0.84

        if sintonitzat:
            if self.emissora != k:
                self._calla_programa()
                self.emissora = k
                self.prog_i = 0
                self.xiulet = -1
                print("%s: emissora %d (%s)" % (self.name, k + 1, _PROGRAMES[k % 5]))
            if self.toca('programa', self.prog_vel):
                self._programa(k, now)
        else:
            if self.emissora >= 0:
                self._calla_programa()
                self.emissora = -1
            # El xiulet: l'altura segueix la desintonització; s'atura en entrar
            xn = 84 + int(abs(des) * 2.0 * 30.0)
            if xn != self.xiulet:
                if self.xiulet >= 0:
                    self.send_note_off(self.xiulet, 0)
                self.xiulet = xn
                self.send_note_on(xn, int((30 + (1.0 - prop) * 50) * self.xiulet_k) if self.xiulet_k > 0.03 else 1)
            # L'estàtica: grans de soroll rosa, més densos com més lluny
            self.deute += self.estatica * (0.35 + 0.65 * (1.0 - prop)) * dt
            n = int(self.deute)
            if n > 0:
                self.deute -= n
                if n > _MAX_PER_TICK:
                    n = _MAX_PER_TICK
                for _ in range(n):
                    nota = 60 + int(self._soroll_rosa() * self.amplada)
                    self._cop(nota, int((30 + self._atzar(50)) * self.intensitat), 0.0, now)
        if sintonitzat and self.xiulet >= 0:
            self.send_note_off(self.xiulet, 0)
            self.xiulet = -1
        return {'dial': round(self.dial, 3), 'emissora': self.emissora + 1,
                'estatica': int(self.estatica), 'escombrat': round(self.escombrat, 3)}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self._calla_programa()
        if self.xiulet >= 0:
            self.send_note_off(self.xiulet, 0)
            self.xiulet = -1
        self.stop_tracked_notes()
