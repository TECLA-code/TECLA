"""El rellotge del motor: passos exactes, iguals per a tothom.

Per què existeix
────────────────
Cada mode es feia el seu propi rellotge, i gairebé tots de la mateixa manera
equivocada:

    if ara - self.last_step >= self.step_dur:
        self.last_step = ara            # <- aquí es perd el tempo
        ...toca...

El bucle principal fa unes 500 voltes per segon, o sigui que la condició es
compleix fins a 2 ms TARD. Posant-hi `ara`, aquell retard es queda per sempre i
el següent pas surt encara més tard. Mesurat simulant el bucle real: demanant
120 BPM en surten **119,05**, i al cap d'un minut el pas va **475 ms** fora de
la graella. Gairebé quatre semicorxeres.

El looper, en canvi, sí que era exacte (`loop_t0 += durada`). Per això el que
es notava no era «va lent» sinó «no cau mai igual»: el loop anava a l'hora i el
mode se li n'anava.

La regla és sumar el PERÍODE, no llegir el rellotge:

    self.proper += self.periode

Així el retard d'una volta no es propaga a la següent i el tempo mitjà és
exacte.

Per què enters i no `time.monotonic()`
──────────────────────────────────────
CircuitPython es compila amb `MICROPY_FLOAT_IMPL_FLOAT`: els floats són de
PRECISIÓ SIMPLE, i `time.monotonic()` en retorna un. La resolució és el
tamany del bit menys significatiu del valor actual, i per tant es degrada com
més estona fa que el dispositiu està encès:

    1 hora    0,244 ms       2 hores    0,488 ms
    5 hores   1,953 ms       12 hores   3,906 ms
    1 dia     7,812 ms   ← el 6% d'una semicorxera a 120 BPM

`supervisor.ticks_ms()` retorna un ENTER de mil·lisegons i no es degrada mai.
A més cap dins d'un enter petit de MicroPython, o sigui que llegir-lo no
al·loca res —i al bucle principal, 500 al·locacions per segon acaben en
recollides de 10-40 ms enmig del que estàs tocant.

Enters també per a la FASE, i en microsegons. Un període de 109,48 ms
arrodonit a 109 ja no és el tempo que has demanat: és un 0,5% de desviació
constant, que sincronitzant amb un DAW se sent. Guardant el residu en
microsegons, cada pas cau al mil·lisegon més proper però el tempo MITJÀ és
exacte, que és el que fa un seqüenciador de debò.
"""

# ticks_ms dona la volta a 2**29 ms (uns 6,2 dies). Les comparacions han de ser
# a prova d'aquella volta o el dia que passi el dispositiu es quedaria clavat.
# (Sense `const()`: cal importar-lo de micropython i no s'usa enlloc més del
#  projecte. El guany seria d'uns pocs bytes en un mòdul que va congelat.)
_PERIODE = 1 << 29
_MAXIM = _PERIODE - 1
_MITJA = _PERIODE // 2

try:
    from supervisor import ticks_ms as _ticks
except ImportError:                     # escriptori, proves i simulador
    import time as _t

    def _ticks():
        return int(_t.monotonic() * 1000) & _MAXIM


def ara():
    """Mil·lisegons enters, sense degradació. La volta la resol `diferencia`."""
    return _ticks()


def diferencia(a, b):
    """`a - b` a prova de la volta de ticks_ms. Negatiu vol dir que `a` és
    abans que `b`."""
    return ((a - b + _MITJA) & _MAXIM) - _MITJA


def suma(t, ms):
    return (t + ms) & _MAXIM


class Pols:
    """Un pols regular que no perd el tempo.

    Ús, dins de l'update d'un mode:

        if self.pols.toca():
            ...un pas...

    UN pas per volta i prou. Si el bucle s'ha aturat 300 ms —una recollida de
    memòria, un fitxer llegit— hi hauria tres passos passats, i tocar-los tots
    tres alhora no és recuperar-los: és una ràfega, i sona pitjor que el
    silenci que l'ha causada. El que s'ha perdut, perdut està; el que no es pot
    perdre és LA GRAELLA, i per això la fase salta als punts que han passat en
    comptes de reprogramar-se des d'ara.

    (El looper no passa per aquí: reprodueix esdeveniments per índex i té la
    seva pròpia recuperació de fase.)
    """

    # Sostre de salts d'una tirada. Tornant d'una pausa llarga no cal recórrer
    # la graella punt per punt: es torna a arrencar i prou.
    MAX_SALT = 8

    def __init__(self, periode_s):
        self._us = 1000
        self._resta = 0
        self.periode(periode_s)
        self.resincronitza()

    def periode(self, periode_s):
        """Canvia el tempo SENSE moure la fase: el pas que ja estava programat
        cau on tocava i el canvi entra a partir del següent. Si es reprogramés
        la fase, cada retoc del pot de BPM faria un saltiró."""
        self._us = max(1, int(periode_s * 1000000))

    def resincronitza(self, t=None):
        """Torna a arrencar: el pas següent cau d'aquí un període.

        Per a l'entrada al mode, la represa d'una pausa i qualsevol cosa que
        hagi deixat el pols enrere. Un període i no zero perquè un pols de
        període P vol dir «cada P», i tornar d'una pausa disparant a l'instant
        seria justament el saltiró que això ha d'evitar."""
        self._proper = ara() if t is None else t
        self._resta = 0
        self._avanca()

    def toca(self, t=None):
        """Ja toca un pas? Un sol `True` per volta, i la graella es manté."""
        t = ara() if t is None else t
        retard = diferencia(t, self._proper)
        if retard < 0:
            return False
        ms = self._us // 1000 or 1
        if retard > ms * self.MAX_SALT:
            # Pausa, canvi de capa, primer dispar: no hi ha graella a mantenir.
            self.resincronitza(t)
        self._avanca()
        n = 0
        while diferencia(t, self._proper) >= 0 and n < self.MAX_SALT:
            self._avanca()
            n += 1
        return True

    def dispara_ja(self):
        """El pas següent cau a la pròxima volta, sense esperar el pols.

        Per als gestos que han de sonar A L'INSTANT —canviar d'acord, revocar
        en harmonia negativa— i no d'aquí mig compàs."""
        self._proper = ara()
        self._resta = 0

    def _avanca(self):
        """Un període exacte. El residu en microsegons és el que fa que un
        període de 109,489 ms doni 137 BPM i no 137,6."""
        self._resta += self._us
        salt = self._resta // 1000
        self._resta -= salt * 1000
        self._proper = suma(self._proper, salt)
