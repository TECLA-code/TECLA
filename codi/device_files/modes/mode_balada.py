"""
Mode Balada - Cançó de piano: arpegis amb pedal, quatre acords i una melodia que recorda el seu motiu
X: Tempo  Y: Emoció (com creix la cançó: força, registre, arpegi)  Z: Registre
Configuració de Modes: Volum · Arpegi · Pedal | Frase · Acord de fons · Tonalitat
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (Z tria l'eix).

De la família de Cançó: un període de quatre frases (pregunta, resposta,
frase oberta i tancament) que es genera amb la gramàtica d'una cançó, i
aquí la cançó és una balada de piano. A sota, els quatre acords de mig
pop (I-V-vi-IV i les seves voltes) en arpegis de mà esquerra —blanques,
corxeres o semicorxeres— amb el PEDAL de debò: un CC64 que baixa a cada
acord i s'aixeca just abans del següent, perquè el sinte deixi ressonar
el que ha de ressonar.

El que aquesta cançó té de seu és la MEMÒRIA: la segona frase repeteix el
ritme i el dibuix de la primera (i canvia només el final, que ara tanca),
i la quarta repeteix els de la tercera. És el que fa que una melodia es
reconegui, i el que cap dels altres modes fa. El pot Y és l'EMOCIÓ: a
l'esquerra tot és íntim, notes llargues i poques; cap a la dreta la
cançó creix —la força, l'arpegi que dobla l'octava, la melodia que
s'omple— i cada frase té el seu arc, amb la tercera al cim. El generador
és determinista: cada període en canvia la llavor.
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_ESCALA = (0, 2, 4, 5, 7, 9, 11)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_PROGRESSIONS = (('I-V-vi-IV', (0, 4, 5, 3)), ('vi-IV-I-V', (5, 3, 0, 4)),
                 ('I-vi-IV-V', (0, 5, 3, 4)), ('IV-I-V-vi', (3, 0, 4, 5)))
_FINALS = (1, 0, 4, 0)
_ACORD = (0, 2, 4)
_ARC = (0.55, 0.7, 1.0, 0.8)              # la intensitat de cada frase
_COMPASSOS = (2, 4, 8)
# Arpegis: grau de l'acord a cada semicorxera del compàs (-1 = res)
_ARPEGIS = ((0, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1),
            (0, -1, 4, -1, 7, -1, 9, -1, 7, -1, 4, -1, 0, -1, 4, -1),
            (0, 4, 7, 9, 11, 9, 7, 4, 0, 4, 7, 9, 11, 9, 7, 4))
_NOMS_ARP = ('blanques', 'corxeres', 'semicorxeres')
# Cèl·lules d'un temps (semicorxeres amb atac); () manté la nota
_CELLES = ((0,), (), (0, 2), (2,), (3,))


class ModeBalada(BaseMode):
    PARAMS = ('Tempo', 'Emoció', 'Registre', 'Arpegi', 'Pedal', 'Frase',
              'Acord de fons', 'Tonalitat')
    POTS = ('Tempo', 'Emoció', 'Registre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Balada"
        self.key = 0
        self.octave = 4
        self.bpm = 72.0
        self.speed = 60.0 / self.bpm / 4.0
        self.emocio = 0.5
        self.arpegi = 1
        self.pedal = True
        self.pedal_baix = False
        self.llarg = 4
        self.prog = 0
        self.frase = 0
        self.compas = 0
        self.semi = 0
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.off_t = 0.0
        self.baix = -1
        self.acord_ant = -1
        self.arp = []                 # [nota, instant d'apagar] de l'arpegi
        self.mem_cel = []             # el motiu: cèl·lules i intervals de la frase recordada
        self.mem_int = []
        self.k_onset = 0
        self._llavor = 1975
        self._llavor0 = 1975
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.frase = 0
        self.compas = 0
        self.semi = 0
        self.cella = ()
        self.grau = 0
        self.sonant = -1
        self.baix = -1
        self.acord_ant = -1
        self.arp = []
        self.mem_cel = []
        self.mem_int = []
        self.k_onset = 0
        self.pedal_baix = False
        self._polsos = {}
        self._llavor = self._llavor0
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %d BPM" % (self.name, _KEYS[self.key], int(self.bpm)))

    # ── Comandaments ────────────────────────────────────────────────────────
    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 56.0 + f * 48.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.speed = 60.0 / b / 4.0
        elif nom == 'Emoció':
            self.emocio = f
        elif nom == 'Registre':
            if not self.neg_active:
                self.octave = 3 + int(f * 2.99)
        elif nom == 'Arpegi':
            a = min(2, int(f * 2.99))
            if a != self.arpegi:
                self.arpegi = a
                print("%s: arpegi de %s" % (self.name, _NOMS_ARP[a]))
        elif nom == 'Pedal':
            p = f >= 0.5
            if p != self.pedal:
                self.pedal = p
                if not p:
                    self._pedal(False)
        elif nom == 'Frase':
            l = _COMPASSOS[min(2, int(f * 2.99))]
            if l != self.llarg:
                self.llarg = l
                print("%s: frases de %d compassos" % (self.name, l))
        elif nom == 'Acord de fons':
            p = min(len(_PROGRESSIONS) - 1, int(f * len(_PROGRESSIONS)))
            if p != self.prog:
                self.prog = p
                print("%s: %s" % (self.name, _PROGRESSIONS[p][0]))
        elif nom == 'Tonalitat':
            k = min(11, int(f * 12))
            if k != self.key:
                self.key = k
                print("%s: %s" % (self.name, _KEYS[k]))
        else:
            return False
        return True

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _nota(self, grau, octava):
        return octava * 12 + self.key + _ESCALA[grau % 7] + 12 * (grau // 7)

    def _acord_g(self):
        p = (self.compas * 16 + self.semi) * 4 // (self.llarg * 16)
        return _PROGRESSIONS[self.prog][1][p]

    def _intensitat(self):
        return self.emocio * _ARC[self.frase]

    def _pedal(self, baix):
        if baix == self.pedal_baix:
            return
        self.pedal_baix = baix
        try:
            self.midi_out.send(ControlChange(64, 127 if baix else 0))
        except Exception:
            pass

    def _de_lacord(self, g):
        acord_g = self._acord_g()
        millor = g
        dist = 99
        for k in (-7, 0, 7):
            for a in _ACORD:
                cand = acord_g + a + k
                if abs(cand - g) < dist:
                    dist = abs(cand - g)
                    millor = cand
        return millor

    def _seguent_grau(self, resta):
        i = self._intensitat()
        lo = -2
        hi = 8 + int(4.0 * i)
        objectiu = _FINALS[self.frase] + (4 if self.frase == 2 else 0)
        if resta <= 4:
            return objectiu
        d = objectiu - self.grau
        cap = 1 if d > 0 else (-1 if d < 0 else 0)
        r = self._atzar(100)
        if r < 70 - int(20 * i):
            interval = 1
        elif r < 90:
            interval = 2 + self._atzar(2 + int(3 * i))
        else:
            interval = 0
        if abs(d) * 3 > resta or self._atzar(100) < 60:
            sentit = cap if cap != 0 else (1 if self._atzar(2) else -1)
        else:
            sentit = 1 if self._atzar(2) else -1
        g = self.grau + sentit * interval
        if self.semi % 4 == 0 and self._atzar(100) < 60:
            g = self._de_lacord(g)
        if g > hi:
            g = hi - self._atzar(3)
        if g < lo:
            g = lo + self._atzar(3)
        return g

    def _tria_cella(self, temps):
        """La cèl·lula del temps: nova a les frases 1 i 3, recordada a la 2 i la 4."""
        ultim = self.compas == self.llarg - 1 and self.semi >= 12
        if ultim:
            return (0,)
        if self.frase % 2 == 1 and temps < len(self.mem_cel):
            return self.mem_cel[temps]
        i = self._intensitat()
        r = self._atzar(100)
        a = 34
        b = a + 36 - int(30 * i)
        c = b + 10 + int(12 * i)
        d = c + 8 + int(10 * i)
        if r < a:
            cel = _CELLES[0]
        elif r < b:
            cel = _CELLES[1]
        elif r < c:
            cel = _CELLES[2]
        elif r < d:
            cel = _CELLES[3]
        else:
            cel = _CELLES[4]
        if self.frase % 2 == 0:
            self.mem_cel.append(cel)
        return cel

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def _apaga_baix(self):
        if self.baix >= 0:
            self.send_note_off(self.baix, 0)
            self.baix = -1

    def _apaga_arp(self, now=None):
        resta = []
        for par in self.arp:
            if now is None or now >= par[1]:
                self.send_note_off(par[0], 0)
            else:
                resta.append(par)
        self.arp = resta

    def _pas(self, now):
        s = self.semi
        pos = s % 4
        tonica = (self.octave * 12 + self.key) % 12
        acord_g = self._acord_g()
        i = self._intensitat()
        if acord_g != self.acord_ant:
            self.acord_ant = acord_g
            if self.pedal:
                self._pedal(False)                     # el pedal es canvia amb l'acord
            self._apaga_baix()
            n = self.negharm(self._nota(acord_g, self.octave - 1), tonica)
            if 12 <= n <= 96:
                self.send_note_on(n, int(52 + 30 * i))
                self.baix = n
            if self.pedal:
                self._pedal(True)
        rel = _ARPEGIS[self.arpegi][s]
        if rel >= 0:
            if self.arpegi == 0:
                graus = (0, 2, 4, 7)                   # l'acord en bloc
            else:
                graus = (rel,)
            vel = int(38 + 36 * i + (8 if s % 8 == 0 else 0))
            for a in graus:
                n = self.negharm(self._nota(acord_g + a, self.octave), tonica)
                if 24 <= n <= 108:
                    self.send_note_on(n, vel)
                    self.arp.append([n, now + self.speed * (8.0 if self.arpegi == 0 else 3.0)])
                    if i > 0.7 and s % 8 == 0 and n + 12 <= 108:
                        self.send_note_on(n + 12, vel - 10)   # l'octava, quan la cançó creix
                        self.arp.append([n + 12, now + self.speed * 3.0])
        if pos == 0:
            temps = self.compas * 4 + s // 4
            if temps == 0:
                self.k_onset = 0
                if self.frase % 2 == 0:
                    self.mem_cel = []
                    self.mem_int = []
            self.cella = self._tria_cella(temps)
        if pos not in self.cella:
            return
        resta = self.llarg * 16 - (self.compas * 16 + s)
        if self.frase % 2 == 1 and resta > 4 and self.k_onset < len(self.mem_int):
            g = self.grau + self.mem_int[self.k_onset]  # el motiu, recordat
            g = -2 if g < -2 else (12 if g > 12 else g)
        else:
            g = self._seguent_grau(resta)
            if self.frase % 2 == 0:
                self.mem_int.append(g - self.grau)
        self.k_onset += 1
        self.grau = g
        nota = self.negharm(self._nota(g, self.octave + 1), tonica)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        n = 0
        for p in self.cella:
            if p > pos:
                n = p - pos
                break
        tot = self.llarg * 16
        arc = 1.0 - abs(((self.compas * 16 + s) / float(tot - 1)) * 2.0 - 1.0)
        vel = int(56 + 46 * i + 14 * arc + (6 if pos == 0 else 0))
        vel = 30 if vel < 30 else (120 if vel > 120 else vel)
        self._apaga()
        self.send_note_on(nota, vel)
        self.sonant = nota
        durada = self.speed * n * 0.95 if n else self.speed * 16.0
        if self.compas == self.llarg - 1 and s >= 12:
            durada = self.speed * 12.0
        self.off_t = now + durada

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)

        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        if self.arp:
            self._apaga_arp(now)
        mult = 1.0
        if self.compas == self.llarg - 1 and self.semi >= 14:
            mult = 1.25                                # el final de frase respira
        if self.toca('semi', self.speed * mult):
            self._pas(now)
            self.semi += 1
            if self.semi >= 16:
                self.semi = 0
                self.compas += 1
                if self.compas >= self.llarg:
                    self.compas = 0
                    self.frase = (self.frase + 1) % 4
                    if self.frase == 0:
                        self._llavor0 = (self._llavor0 + 7919) & 0x7FFFFFFF
                        self._llavor = self._llavor0

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
        return {'key': _KEYS[self.key], 'frase': self.frase + 1, 'bpm': int(self.bpm),
                'emocio': int(self.emocio * 100)}

    def cleanup(self):
        self._apaga()
        self._apaga_baix()
        self._apaga_arp()
        self._pedal(False)
        self.stop_tracked_notes()
