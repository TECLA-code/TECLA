"""llum.py — el LED RGB del TECLA.

Maquinari: LL-509RGBC2E-002, un RGB de 5 mm amb TRES XIPS dins d'una càpsula.
No és un LED adreçable: no hi ha protocol de dades, hi ha tres terminals de
color i un de comú. Per tant vol TRES PINS PWM, no un.

    R  1,6–2,6 V
    G  2,8–3,8 V     ← el vermell demana bastant menys que els altres dos,
    B  2,8–3,8 V       i per això vol una resistència de limitació diferent

El pin de l'àudio va desaparèixer
────────────────────────────────
Fins a la v3.16 GP22 era la sortida de minijack i `core/tone.py` hi feia un to
PWM a cada nota del teclat. El to intern s'ha retirat sencer i GP22 va quedar
lliure. El LED, però, no hi va anar a parar: al muntatge real està soldat a
GP19, GP20 i GP21, i GP22 no fa res. Cap altre mòdul toca aquests tres pins —
dos amos al mateix pin volia dir soroll al LED a cada tecla.

Dues coses que fan que els colors surtin bé
───────────────────────────────────────────
1. GAMMA. El PWM és lineal i l'ull no: al 50% de cicle de treball no veus la
   meitat de llum, en veus molta més. Sense corregir-ho tots els colors tiren
   a clar i els tons mitjans s'aplanen.
2. CALIBRAT. Els tres xips no tenen ni el mateix voltatge ni el mateix
   rendiment, i les resistències que els posis tampoc seran iguals. Si el
   blanc surt rosat o verdós, es corregeix AQUÍ i no retocant color per color.

Tot és best-effort: sense maquinari (tests, simulador) queda en no-op.
"""

# ── El que s'ha d'ajustar al muntatge ──────────────────────────────────────
PINS = ('GP20', 'GP19', 'GP21')   # R, G, B — ORDRE MESURAT AL DISPOSITIU.
                                  # No és consecutiu i no segueix la numeració:
                                  # el VERD va a GP19 i el VERMELL a GP20. Es va
                                  # comprovar encenent els pins d'un en un pel
                                  # REPL i mirant el LED. Si algun dia es torna a
                                  # soldar, refés la prova abans de tocar això.
                                  # Els lliures del Pico són GP16-GP22 (els
                                  # botons ocupen GP0-GP15, els potes A0-A2);
                                  # GP22 ha quedat sense connectar.
CATODE_COMU = True                # LL-509RGB(C)2E → càtode comú. Amb ànode
                                  # comú, posa-ho a False: el cicle s'inverteix.
CALIBRAT = (1.0, 1.0, 1.0)        # trim per canal si el blanc surt tenyit
BRILLANTOR = 0.35                 # 0..1 — a tota canya enlluerna, i s'hi grava
GAMMA = 2.2
FREQ = 1000                       # Hz: prou per no veure parpelleig ni a càmera

# Un color per personalitat. Triats pel to, no per la marca: han de ser
# distingibles d'un cop d'ull i també per algú que confongui vermell i verd.
COLORS = (
    (0, 90, 255),      # 0 Instrument — blau
    (255, 80, 0),      # 1 Macropad   — taronja
    (0, 210, 120),     # 2 Blocks     — verd
)

_canals = None          # [PWMOut, PWMOut, PWMOut]
_taula = None           # corba de gamma, 256 entrades


def _gamma():
    global _taula
    if _taula is None:
        t = []
        for v in range(256):
            t.append(int(((v / 255.0) ** GAMMA) * 65535 + 0.5))
        _taula = t
    return _taula


def _prepara():
    """Agafa els tres pins. Un sol cop; si en falla un, no hi ha LED."""
    global _canals
    if _canals is not None:
        return _canals
    try:
        import board
        import pwmio
        _canals = [pwmio.PWMOut(getattr(board, nom), frequency=FREQ, duty_cycle=0)
                   for nom in PINS]
    except Exception:
        _canals = None
    return _canals


def color(r, g, b):
    """Pinta el LED. Mai llança: un testimoni no pot trencar el so."""
    try:
        c = _prepara()
        if c is None:
            return
        taula = _gamma()
        for i, v in enumerate((r, g, b)):
            # L'ORDRE IMPORTA: primer la gamma sobre el color, i la brillantor
            # DESPRÉS, sobre el cicle de treball. Al revés, la brillantor entra
            # a la corba i queda comprimida ella també (0.35 ** 2.2 ≈ 0.098):
            # un color apagat com (102, 125, 169) baixava a l'1-4% de cicle i
            # no es veia. La brillantor és una escala lineal de sortida, no un
            # color.
            v = int(max(0, min(255, v)) * CALIBRAT[i])
            duty = int(taula[max(0, min(255, v))] * BRILLANTOR)
            c[i].duty_cycle = duty if CATODE_COMU else 65535 - duty
    except Exception:
        pass


def apaga():
    color(0, 0, 0)


# ── El LED reactiu al so ────────────────────────────────────────────────────
# Cada capa tria com va el LED (`bank['led']`):
#   'fix'   el color de la capa, quiet (el de sempre)
#   'pols'  el color de la capa, que batega amb cada nota: puja amb la força
#           de la nota i cau en un quart de segon fins a un repòs tènue
#   'to'    a més, la nota li dona el color: dotze tons pel cercle cromàtic,
#           blanc per a la percussió; en repòs torna al color de la capa
# Totes les notes passen per aquí (main embolcalla el port MIDI), també les
# del looper, l'acompanyament i el mode de fons. Costa el que costa: en
# repòs `tick` surt a la primera línia i no escriu res al PWM; mentre cau,
# només escriu quan el color quantitzat a 8 bits canvia.
MODES_LED = ('fix', 'pols', 'to')
_REPOS = 0.22           # fracció del color de capa que queda en repòs
_TAU = 0.22             # segons: la caiguda de cada nota
_TONS = ((255, 40, 40), (255, 120, 0), (255, 200, 0), (170, 255, 0),
         (40, 255, 60), (0, 230, 160), (0, 200, 255), (40, 110, 255),
         (110, 60, 255), (190, 40, 255), (255, 40, 190), (255, 60, 110))
_capa = (0, 90, 255)
_mode = 'fix'
_nivell = 0.0
_t = 0.0
_to = None
_ultim = None


def capa(rgb, mode='fix'):
    """El color de la capa activa i com s'hi comporta el LED."""
    global _capa, _mode, _nivell, _to, _ultim
    try:
        _capa = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
    except Exception:
        _capa = COLORS[0]
    _mode = mode if mode in MODES_LED else 'fix'
    _nivell = 0.0
    _to = None
    _ultim = None
    if _mode == 'fix':
        color(*_capa)
    else:
        _pinta(0.0)


def nota(note, velocity, channel=0):
    """Una nota acaba de sonar: el LED puja (i, amb 'to', pren el seu color)."""
    global _nivell, _t, _to
    if _mode == 'fix' or velocity <= 0:
        return
    n = 0.35 + 0.65 * (velocity if velocity < 127 else 127) / 127.0
    if n > _nivell:
        _nivell = n
    try:
        import time
        _t = time.monotonic()
    except Exception:
        _t = 0.0
    if _mode == 'to':
        _to = (255, 255, 255) if channel == 9 else _TONS[int(note) % 12]
    _pinta(_nivell)


def tick(now):
    """Cada volta del bucle: la caiguda. En repòs no fa res."""
    global _nivell, _t
    if _mode == 'fix' or _nivell <= 0.0:
        return
    dt = now - _t
    if dt < 0.004:
        return                  # sense moure _t: si no, un bucle ràpid no cau mai
    _t = now
    _nivell -= _nivell * (dt / _TAU if dt < _TAU else 1.0)
    if _nivell < 0.04:
        _nivell = 0.0
    _pinta(_nivell)


class PortAmbLlum:
    """El port MIDI de sortida embolcallat: a cada NoteOn amb força avisa el
    LED i passa el missatge tal qual. Llegir o escriure qualsevol altra cosa
    (out_channel…) va a parar al port de debò."""

    # Res de __setattr__ ni de object.__setattr__: a CircuitPython no hi són.
    # El canal de sortida, que main i el canvi de config escriuen, és una
    # propietat que va al port de debò; la resta de lectures, per __getattr__.

    def __init__(self, port):
        self._port = port

    @property
    def out_channel(self):
        return self._port.out_channel

    @out_channel.setter
    def out_channel(self, v):
        self._port.out_channel = v

    def send(self, msg, channel=None):
        try:
            if type(msg).__name__.endswith('NoteOn') and msg.velocity > 0:
                c = channel if channel is not None else msg.channel
                if c is None:
                    c = self._port.out_channel
                nota(msg.note, msg.velocity, c)
        except Exception:
            pass
        return self._port.send(msg, channel)

    def __getattr__(self, nom):
        return getattr(self._port, nom)


def _pinta(n):
    """El color de la capa (o el de la nota) a la fracció n, quantitzat: només
    escriu al PWM si el color de 8 bits ha canviat."""
    global _ultim
    base = _capa
    if _mode == 'to' and _to is not None:
        base = (int(_capa[0] + (_to[0] - _capa[0]) * n),
                int(_capa[1] + (_to[1] - _capa[1]) * n),
                int(_capa[2] + (_to[2] - _capa[2]) * n))
    k = _REPOS + (1.0 - _REPOS) * n
    rgb = (int(base[0] * k), int(base[1] * k), int(base[2] * k))
    if rgb == _ultim:
        return
    _ultim = rgb
    color(*rgb)


def personalitat(i):
    """El color de la personalitat i (0..2)."""
    try:
        color(*COLORS[int(i) % len(COLORS)])
    except Exception:
        pass


def pampallugues(n, rgb=(255, 255, 255), encesa=0.12, apagada=0.1):
    """N parpelleigs. El retorn de "ha passat una cosa, i són N".

    Mai llança i mai deixa el LED encès a mitges.
    """
    try:
        import time
        for _ in range(max(1, int(n))):
            color(*rgb)
            time.sleep(encesa)
            apaga()
            time.sleep(apagada)
    except Exception:
        try:
            apaga()
        except Exception:
            pass
