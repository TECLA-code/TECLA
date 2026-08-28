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
