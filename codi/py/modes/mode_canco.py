"""
Mode Cançó - Melodia generativa amb frases que pregunten i responen
X: Tempo  Y: Caràcter (de diatònic i per graus a cromàtic i a salts)  Z: Registre
Configuració de Modes: Volum · Silencis · Rubato | Articulació · Frase · Acord de fons | Tonalitat…
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa (Z tria l'eix).

Els dotze compositors que hi havia abans compartien una cosa: totes eren
seqüències escrites, i al cap de dues voltes ja les sabies. Aquí la melodia
no està escrita: es GENERA amb la gramàtica d'una cançó. Quatre frases
formen un període: la primera PREGUNTA (acaba lluny de la tònica), la
segona RESPON (hi torna), la tercera puja de registre i queda oberta sobre
la dominant, i la quarta tanca. Cada frase té un acord de fons que sona al
baix, i la melodia s'hi dirigeix: els passos van per graus conjunts amb
algun salt, i tendeixen cap a la nota que la frase ha d'assolir. La
dinàmica dibuixa un arc a cada frase, els finals s'allarguen i respiren, i
un rubato lleu fa que cap frase caigui clavada.

El pot Y és el CARÀCTER: a l'esquerra tot són graus conjunts i notes de
l'acord (Satie); cap a la dreta entren els salts, les notes de pas
cromàtiques i els silencis sobtats (Debussy, Beethoven). El generador és
determinista (un congruencial lineal): la mateixa tonalitat i el mateix
caràcter donen la mateixa cançó, i cada període en canvia la llavor.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 5, 7, 9, 11)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
# Acords de fons de les quatre frases (grau de l'escala), per progressió
_PROGRESSIONS = (('I-IV-V-I', (0, 3, 4, 0)), ('I-vi-IV-V', (0, 5, 3, 4)),
                 ('I-V-vi-IV', (0, 4, 5, 3)), ('vi-IV-I-V', (5, 3, 0, 4)))
# On acaba la melodia a cada frase (grau): pregunta, resposta, oberta, tanca
_FINALS = (1, 0, 4, 0)
_ACORD = (0, 2, 4)           # graus de l'acord (tríada)
_FRASES_LLARG = (4, 8, 16)   # corxeres per frase, segons el comandament 'Frase'


class ModeCanco(BaseMode):
    PARAMS = ('Tempo', 'Caràcter', 'Registre', 'Silencis', 'Rubato', 'Articulació',
              'Frase', 'Acord de fons', 'Tonalitat')
    POTS = ('Tempo', 'Caràcter', 'Registre')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Cançó"
        self.key = 0
        self.octave = 4
        self.bpm = 84.0
        self.speed = 60.0 / self.bpm / 2.0
        self.caracter = 0.3
        self.silencis = 0.0           # probabilitat afegida de silenci (0-0,4)
        self.rubato = 0.08            # fracció del pas que s'endarrereix al mig de la frase
        self.artic = 0.92             # fracció del pas que dura la nota
        self.llarg = 8                # corxeres per frase
        self.prog = 0
        self.frase = 0
        self.pas = 0
        self.grau = 0                 # grau actual de la melodia (pot passar de 7)
        self.sonant = -1
        self.off_t = 0.0
        self.baix = -1
        self.retard = 0.0
        self.t_pas = 0.0
        self.pendent = False
        self._llavor = 4242
        self._llavor0 = 4242
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16

    def setup(self):
        self.initialized = True
        self.frase = 0
        self.pas = 0
        self.grau = 0
        self.sonant = -1
        self.baix = -1
        self.pendent = False
        self._polsos = {}
        self._llavor = self._llavor0
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        print("%s: %s %d BPM" % (self.name, _KEYS[self.key], int(self.bpm)))

    # ── Comandaments ────────────────────────────────────────────────────────
    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            b = 50.0 + f * 90.0
            if b < self.bpm - 0.3 or b > self.bpm + 0.3:
                self.bpm = b
                self.speed = 60.0 / b / 2.0
        elif nom == 'Caràcter':
            self.caracter = f
        elif nom == 'Registre':
            if not self.neg_active:
                self.octave = 3 + int(f * 2.99)
        elif nom == 'Silencis':
            self.silencis = f * 0.4
        elif nom == 'Rubato':
            self.rubato = f * 0.25
        elif nom == 'Articulació':
            self.artic = 0.35 + f * 0.65
        elif nom == 'Frase':
            l = _FRASES_LLARG[min(2, int(f * 2.99))]
            if l != self.llarg:
                self.llarg = l
                print("%s: frases de %d" % (self.name, l))
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

    def _nota(self, grau):
        n = len(_ESCALA)
        return self.octave * 12 + self.key + _ESCALA[grau % n] + 12 * (grau // n)

    def _acord_g(self):
        return _PROGRESSIONS[self.prog][1][self.frase]

    def _seguent_grau(self):
        """El pas següent de la melodia: conjunt, salt o cromàtic, segons el
        caràcter, i sempre atret cap a la nota final de la frase."""
        c = self.caracter
        acord_g = self._acord_g()
        # A la tercera frase la melodia viu una quarta més amunt
        objectiu = _FINALS[self.frase] + (7 if self.frase == 2 else 0)
        resta = self.llarg - self.pas                # passos fins al final
        if resta <= 1:
            return objectiu                          # l'última nota és la del final
        d = objectiu - self.grau
        cap = 1 if d > 0 else (-1 if d < 0 else 0)
        r = self._atzar(1000) / 1000.0
        p_salt = 0.08 + 0.45 * c
        p_conj = 0.85 - 0.45 * c
        if r < p_conj:
            interval = 1
        elif r < p_conj + p_salt:
            interval = 2 + self._atzar(3)            # tercera, quarta o quinta
        else:
            interval = 0                             # repetició
        if abs(d) > resta or self._atzar(100) < 60 + int(20 * c):
            sentit = cap if cap != 0 else (1 if self._atzar(2) else -1)
        else:
            sentit = 1 if self._atzar(2) else -1
        g = self.grau + sentit * interval
        # Els temps forts prefereixen notes de l'acord de fons
        if self.pas % 2 == 0 and self._atzar(100) < 55 - int(35 * c):
            g = self._mes_proper_de_lacord(g, acord_g)
        if g > 10:
            g = 10 - self._atzar(3)
        if g < -3:
            g = -3 + self._atzar(3)
        return g

    def _mes_proper_de_lacord(self, g, acord_g):
        millor = g
        dist = 99
        for k in (-7, 0, 7):
            for a in _ACORD:
                cand = acord_g + a + k
                if abs(cand - g) < dist:
                    dist = abs(cand - g)
                    millor = cand
        return millor

    def _apaga(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def _baix(self, acord_g):
        if self.baix >= 0:
            self.send_note_off(self.baix, 0)
            self.baix = -1
        n = (self.octave - 1) * 12 + self.key + _ESCALA[acord_g % 7]
        n = self.negharm(n, (self.octave * 12 + self.key) % 12)
        if 12 <= n <= 96:
            self.send_note_on(n, 58)
            self.baix = n

    def _pas_melodia(self, now):
        c = self.caracter
        if self.pas == 0:
            self._baix(self._acord_g())
        g = self._seguent_grau()
        self.grau = g
        # Silenci: amb caràcter o amb el comandament, i mai al final de frase
        p_sil = self.silencis + (max(0.0, c - 0.5) * 0.24)
        if p_sil > 0.0 and self.pas < self.llarg - 2 and self._atzar(1000) < int(p_sil * 1000):
            self._apaga()
            self.pas += 1
            return
        nota = self._nota(g)
        # Nota de pas cromàtica: entre dos graus conjunts, amb caràcter alt
        if c > 0.6 and self.pas % 2 == 1 and self._atzar(100) < int((c - 0.6) * 60):
            nota -= 1
        nota = self.negharm(nota, (self.octave * 12 + self.key) % 12)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        # Arc dinàmic de la frase: creix fins al mig i cau; accent al temps fort
        arc = 1.0 - abs((self.pas / float(self.llarg - 1)) * 2.0 - 1.0)
        vel = int(62 + 40 * arc + (10 if self.pas % 4 == 0 else 0))
        if self.frase == 2:
            vel += 8                                  # la frase alta és la més intensa
        vel = 30 if vel < 30 else (120 if vel > 120 else vel)
        self._apaga()
        self.send_note_on(nota, vel)
        self.sonant = nota
        durada = self.speed * self.artic
        if self.pas == self.llarg - 1:
            durada = self.speed * 1.6                 # el final de frase respira
        self.off_t = now + durada
        self.pas += 1

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self.poll_negharm(button_states, pot_values[2])
        self.potes(pot_values)

        if self.sonant >= 0 and now >= self.off_t:
            self._apaga()
        # El final de frase dura el doble: el pols del pas següent s'allarga
        periode = self.speed * (2.0 if self.pas >= self.llarg else 1.0)
        if self.toca('pas', periode):
            if self.pas >= self.llarg:
                self.pas = 0
                self.frase = (self.frase + 1) % 4
                if self.frase == 0:
                    self._llavor0 = (self._llavor0 + 7919) & 0x7FFFFFFF
                    self._llavor = self._llavor0        # cada període, una variació
            # Rubato: al mig de la frase el pas s'endarrereix una mica
            self.t_pas = now
            mig = 1.0 - abs((self.pas / float(self.llarg - 1)) * 2.0 - 1.0)
            self.retard = self.speed * self.rubato * mig
            self.pendent = True
        if self.pendent and now - self.t_pas >= self.retard:
            self.pendent = False
            self._pas_melodia(now)

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
                'caracter': int(self.caracter * 100)}

    def cleanup(self):
        self._apaga()
        if self.baix >= 0:
            self.send_note_off(self.baix, 0)
            self.baix = -1
        self.stop_tracked_notes()
