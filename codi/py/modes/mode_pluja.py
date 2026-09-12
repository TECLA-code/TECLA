"""
Mode Pluja - De les primeres gotes al núvol: una textura amb densitat, zona i gra
X: Densitat (una gota cada tres segons → quaranta per segon)  Y: Zona (registre)
Z: Gra (de l'espurna de 8 ms al núvol d'un segon)

La família de les textures té una sola idea: esdeveniments curts a l'atzar
dins d'una zona, i el que mana és la DENSITAT i la seva irregularitat. Aquí
la densitat va de la gota solitària a la pluja batent, i mai no és regular:
cada gota cau a un temps una mica diferent (jitter del 70 %), que és el que
separa una textura d'un metrònom. Les altures són de la pentatònica, així
que qualsevol densitat sona a música; el pot Y mou la zona del greu a
l'agut; i el pot Z és el gra: curt són espurnes i clics, llarg són notes que
s'apilen fins a fer un núvol.

Dues coses que fan la diferència. El FONS: a partir d'un cert cabal apareix
un baix sostingut de tònica i quinta que puja de volum amb la densitat, i
que és el que fa que la pluja tingui terra i no floti. I les RÀFEGUES: a
densitats altes les gotes ja no cauen d'una en una sinó en grups de tres a
sis amb una pausa entremig, com fa la pluja de debò contra un vidre.
"""
import time
from modes.base_mode import BaseMode

_ESCALA = (0, 2, 4, 7, 9)
_MAX_VEUS = 16
_MAX_PER_TICK = 6
_JITTER = 0.7
_FONS_INTERVALS = (0, 7)


class ModePluja(BaseMode):
    PARAMS = ('Densitat', 'Zona de notes', 'Durada del gra', 'Irregularitat', 'Dispersió', 'Fons greu', 'Ràfegues', 'Atenuació')
    POTS = ('Densitat', 'Zona de notes', 'Durada del gra')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Pluja"
        self.dens = 4.0              # gotes per segon
        self.centre = 72
        self.gra = 0.06              # segons
        self.pend = []
        self.seguent = 0.0           # quan cau la gota següent
        self.rafega = 0              # gotes que queden de la ràfega en curs
        self.fons = []               # notes del fons sonant
        self.fons_vel = 0
        self.fons_t = 0.0
        self.jitter = _JITTER
        self.dispersio = 12
        self.fons_k = 0.7
        self.rafegues_k = 0.5
        self.atenuacio = 0.3
        self._llavor = 8642

    def setup(self):
        self.initialized = True
        self.pend = []
        self.fons = []
        self.fons_vel = 0
        self.seguent = 0.0
        self.rafega = 0
        self._polsos = {}
        print("%s: %.1f gotes/s" % (self.name, self.dens))

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _quantitza(self, nota):
        """La nota més propera de la pentatònica."""
        base = (nota // 12) * 12
        millor = nota
        dist = 99
        for o in (-12, 0, 12):
            for iv in _ESCALA:
                c = base + o + iv
                if abs(c - nota) < dist:
                    dist = abs(c - nota)
                    millor = c
        return millor

    def _allibera(self, now, totes=False):
        if not self.pend:
            return
        queden = []
        for p in self.pend:
            if totes or now >= p[1]:
                self.send_note_off(p[0], 0)
            else:
                queden.append(p)
        self.pend = queden

    def _gota(self, now):
        # Dispersió de ±12 al voltant del centre, amb més pes al mig
        d = (self._atzar(2 * self.dispersio + 1) + self._atzar(2 * self.dispersio + 1)) // 2 - self.dispersio
        nota = self._quantitza(self.centre + d)
        if nota < 24 or nota > 108:
            return
        vel = 40 + self._atzar(60)
        if nota > self.centre:
            vel = int(vel * (1.0 - self.atenuacio * (nota - self.centre) / 24.0))
        vel = 10 if vel < 10 else vel
        for p in self.pend:
            if p[0] == nota:
                self.send_note_off(nota, 0)
                self.pend.remove(p)
                break
        self.send_note_on(nota, vel)
        if self.gra <= 0.01:
            self.send_note_off(nota, 0)      # espurna: el clic
            return
        self.pend.append([nota, now + self.gra * (0.6 + self._atzar(80) / 100.0)])
        if len(self.pend) > _MAX_VEUS:
            vella = self.pend.pop(0)
            self.send_note_off(vella[0], 0)

    def _programa(self, now):
        """Quan cau la gota següent: interval mitjà 1/densitat, amb jitter."""
        mitja = 1.0 / self.dens
        k = 1.0 + self.jitter * ((self._atzar(2000) / 1000.0) - 1.0)
        if self.rafega > 0:
            self.rafega -= 1
            k *= 0.25                          # dins la ràfega, molt seguides
        elif self.rafegues_k > 0.0 and self.dens > 12.0 * (1.0 - 0.6 * self.rafegues_k) and self._atzar(100) < int(35 * self.rafegues_k * 2):
            self.rafega = 2 + self._atzar(4)   # una ràfega de 3 a 6
            k *= 2.5                           # ...després d'una pausa
        self.seguent = now + mitja * (k if k > 0.05 else 0.05)

    def _fons_actualitza(self, now):
        objectiu = 0 if (self.dens < 2.0 or self.fons_k <= 0.02) else int(min(64, 10 + self.dens * 2.2) * self.fons_k)
        if now - self.fons_t < 1.5:
            return
        self.fons_t = now
        if abs(objectiu - self.fons_vel) < 8 and (self.fons or objectiu == 0):
            return
        for n in self.fons:
            self.send_note_off(n, 0)
        self.fons = []
        self.fons_vel = objectiu
        if objectiu > 0:
            arrel = 36 + (self.centre - 72) // 12 * 12
            for iv in _FONS_INTERVALS:
                n = arrel + iv
                if 12 <= n <= 96:
                    self.send_note_on(n, objectiu)
                    self.fons.append(n)

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Densitat':
            self.dens = 0.3 * (133.0 ** f)             # logarítmic: 0,3 → 40 gotes/s
        elif nom == 'Zona de notes':
            self.centre = 48 + int(f * 48)
        elif nom == 'Durada del gra':
            self.gra = 0.008 * (150.0 ** f)            # 8 ms → 1,2 s
        elif nom == 'Irregularitat':
            self.jitter = f
        elif nom == 'Dispersió':
            self.dispersio = 2 + int(f * 22)           # ±2 … ±24 semitons
        elif nom == 'Fons greu':
            self.fons_k = f                            # 0 = sense fons · 1 = ple
        elif nom == 'Ràfegues':
            self.rafegues_k = f
        elif nom == 'Atenuació':
            self.atenuacio = f                         # les gotes agudes, més fluixes
        else:
            return False
        return True

    def update(self, pot_values, button_states):
        now = time.monotonic()
        self._allibera(now)
        self.potes(pot_values)
        # El pols del fons i de la neteja de gotes vives va a 10 Hz
        if self.toca('fons', 0.1):
            self._fons_actualitza(now)
        n = 0
        while now >= self.seguent and n < _MAX_PER_TICK:
            self._gota(now)
            self._programa(now)
            n += 1
        return {'dens': round(self.dens, 1), 'centre': self.centre,
                'gra': int(self.gra * 1000), 'vives': len(self.pend)}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        for n in self.fons:
            self.send_note_off(n, 0)
        self.fons = []
        self.stop_tracked_notes()
