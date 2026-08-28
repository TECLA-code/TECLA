"""personalitat.py — quina de les tres TECLA és avui aquest dispositiu.

El mateix maquinari pot ser INSTRUMENT, MACROPAD o BLOCKS. Quina de les tres
arrenca ho diu un byte de la NVM, i el gest de l'usuari el fa rotar.

Per què la NVM i no un fitxer
────────────────────────────
Sobreviu el reset, i sobretot NO toca el sistema de fitxers: el disc del Pico
és d'1 MB i ja hem vist com de fàcil és omplir-lo i deixar un fitxer a mitges.
Un byte a la NVM no es pot corrompre a mitja escriptura.

Mapa de la NVM (el crashguard ja n'ocupa una part; vegeu core/crashguard.py):
    [0]        MAGIC del crashguard
    [1]        comptador de fallades
    [2..65]    últim error
    [66]       MAGIC d'aquest mòdul      ← a partir d'aquí, nosaltres
    [67]       personalitat (0, 1 o 2)
    [68]       marca de "el reinici que ve el demano jo" (vegeu més avall)

Per què cal un REINICI DUR
──────────────────────────
Les tres personalitats necessiten descriptors USB diferents (MIDI, HID, canal
de dades), i això NOMÉS es pot configurar al boot.py. El boot.py corre en
arrencada freda i prou: `supervisor.reload()` —que és el que fa servir la
resta del firmware— NO hi torna a passar. Per això canviar de personalitat
demana `microcontroller.reset()`, i per això el dispositiu es desconnecta i es
torna a connectar per USB. No és un defecte: els descriptors USB no es poden
canviar amb el cable posat.

Tot és best-effort: sense NVM (tests, simulador) queda a la personalitat 0.
"""

MAGIC = 0x5A
BASE = 66                     # primer byte lliure després del crashguard
REINICI = BASE + 2            # marca: el reinici que ve el demana el gest
NOMS = ('instrument', 'macropad', 'blocks')
ETIQUETES = ('Instrument', 'Macropad', 'Blocks')

try:
    import microcontroller
    _nvm = microcontroller.nvm
except Exception:
    _nvm = None


def _set_nvm(nvm):
    """Injecció per a tests."""
    global _nvm
    _nvm = nvm


def actual():
    """Índex de la personalitat activa (0..2). Per defecte, l'Instrument."""
    if _nvm is None:
        return 0
    try:
        if _nvm[BASE] != MAGIC:
            return 0
        i = _nvm[BASE + 1]
        return i if 0 <= i < len(NOMS) else 0
    except Exception:
        return 0


def posa(i):
    """Fixa la personalitat. Retorna l'índex que ha quedat."""
    i = int(i) % len(NOMS)
    if _nvm is None:
        return i
    try:
        _nvm[BASE:BASE + 2] = bytes((MAGIC, i))
    except Exception:
        pass
    return i


def seguent():
    """Fa rotar a la següent i la desa. Retorna el nou índex."""
    return posa(actual() + 1)


PETICIO = '/config/personalitat.txt'


def aplica_peticio():
    """Una app ha demanat una personalitat escrivint un fitxer? Aplica-la.

    Les apps no poden escriure a la NVM: només veuen el disc. Quan el Macropad
    o el Blocks instal·len la seva personalitat, deixen el seu nom a
    /config/personalitat.txt; aquí es converteix en el byte de la NVM i el
    fitxer s'esborra, perquè la petició valgui UN COP i no a cada arrencada
    (si no, el gest de les cantonades no podria treure't d'allà mai).

    Retorna l'índex demanat, o None si no hi havia petició.
    """
    try:
        with open(PETICIO, 'r') as f:
            volgut = f.read().strip().lower()
    except Exception:
        return None
    i = None
    for k, n in enumerate(NOMS):
        if volgut == n:
            i = k
            break
    try:
        import os
        os.remove(PETICIO)
    except Exception:
        pass
    if i is None:
        return None
    posa(i)
    return i


def nom(i=None):
    return NOMS[actual() if i is None else int(i) % len(NOMS)]


def etiqueta(i=None):
    return ETIQUETES[actual() if i is None else int(i) % len(ETIQUETES)]


def reinicia():
    """Reinici DUR: torna a passar per boot.py i re-enumera l'USB.

    supervisor.reload() NO serveix aquí — no torna a executar boot.py, o sigui
    que l'USB es quedaria configurat per a la personalitat anterior.
    """
    try:
        import microcontroller
        microcontroller.reset()
    except Exception:
        pass


# ── «Aquest reinici el demano jo» ──────────────────────────────────────────
# El gest en marxa rota la personalitat i reinicia en DUR ~mig segon després.
# Mig segon no és res: encara tens els dits a les cantonades quan el boot.py
# les torna a llegir, i el seu rescat les veu premudes i ROTA UNA ALTRA VEGADA.
# Des de l'Instrument no arribaves al Macropad: te'l saltaves i queies al
# Blocks.
#
# No es pot resoldre per temps (quanta estona triga algú a treure els dits?),
# així que es resol per intenció: qui demana el reinici deixa una marca, i el
# boot, si la troba, sap que aquestes tecles premudes són les MATEIXES d'un
# gest ja atès i no un endoll nou.
#
# La marca es consumeix sempre, passi el que passi. Si es perd el corrent
# entremig es queda posada i es menja el primer rescat següent; és un
# inconvenient petit i acotat, i l'alternativa —no marcar res— és una rotació
# doble cada vegada.

def marca_reinici_propi():
    """Deixa dit que el reinici que ve el demana el firmware, no un endoll."""
    if _nvm is None:
        return
    try:
        _nvm[REINICI:REINICI + 1] = bytes((MAGIC,))
    except Exception:
        pass


def consumeix_reinici_propi():
    """El reinici l'ha demanat el firmware? Ho diu i esborra la marca."""
    if _nvm is None:
        return False
    try:
        hi_es = _nvm[REINICI] == MAGIC
        if hi_es:
            _nvm[REINICI:REINICI + 1] = bytes((0,))
        return hi_es
    except Exception:
        return False


# ── El rescat d'arrencada ──────────────────────────────────────────────────
# Les quatre cantonades premudes MENTRE S'ENDOLLA. És l'única sortida que no
# depèn de codi generat per cap app, i per això és la que ha de funcionar
# sempre: el Macropad i el Blocks els escriuen les seves apps, i una generació
# que peta o un bucle que no hi és et deixen amb un dispositiu que no respon a
# res. Ho crida el boot.py, l'únic lloc on encara es pot triar.
#
# Dues sortides, no una:
#   · endollar aguantant-les          → la personalitat SEGÜENT
#   · seguir aguantant-les LLARG s    → l'INSTRUMENT, directe
# La segona és el que fa que no es pugui perdre un dispositiu. Sortir d'una
# personalitat morta rotant a cegues no és cap interfície: ningú no hauria
# d'endevinar quantes vegades li toca tornar a endollar.
#
# I es MOSTREGEN, no es llegeixen un cop. Abans era una sola lectura, a pèl,
# l'instant just després de configurar els pins: si el pull-down encara no
# havia assentat o una tecla rebotava, no hi havia rescat — i no hi havia cap
# manera de saber per què.

FINESTRA = 0.35   # s: temps per trobar-les. El preu que paga cada arrencada.
MINIM = 0.15      # s: menys que això és rebot, no pas un gest
LLARG = 5.0       # s: aguantant-les tant, cap a l'Instrument


def rescat(premudes, ara, dorm, sentit=None):
    """Mostreja les cantonades en arrencar. Retorna None, 'seguent' o
    'instrument'.

    Tot el maquinari entra per paràmetre —`premudes()` diu si les quatre hi
    són, `ara()` és el rellotge, `dorm(s)` espera— perquè això es pugui provar
    sencer sense dispositiu. És l'últim recurs que hi ha entre una persona i un
    TECLA que no respon: no pot ser l'únic tros de codi que ningú no prova.

    `sentit()` es crida un sol cop, en reconèixer el gest: el parpelleig de
    «t'he sentit». Sense ell, aguantar cinc segons a cegues no és un gest, és fe.
    """
    ini = ara()
    des_de = None
    estona = 0.0
    avisat = False
    while True:
        t = ara()
        if premudes():
            if des_de is None:
                des_de = t
            estona = t - des_de
            if not avisat and estona >= MINIM:
                avisat = True
                if sentit is not None:
                    try:
                        sentit()
                    except Exception:
                        pass
            if estona >= LLARG:
                return 'instrument'
        else:
            if estona >= MINIM:
                return 'seguent'      # deixades anar: rotació simple
            des_de = None             # rebot: torna a començar
            if t - ini >= FINESTRA:
                return None           # no hi ha ningú: arrencada normal
        dorm(0.005)


# ── El gest ────────────────────────────────────────────────────────────────
# Aquesta classe és PURA: no llegeix pins ni toca maquinari, només rep l'estat
# de les dues tecles i l'hora. Així es pot provar sense dispositiu i la poden
# fer servir les tres personalitats amb el mateix comportament exacte.

# LES QUATRE CANTONADES de la graella de 4×4: tecles 1, 4, 13 i 16.
#
#     [1]  2   3  [4]      Amb dues no n'hi havia prou: al Macropad es poden
#      5   6   7   8       configurar combinacions de dues tecles, i el gest
#      9  10  11  12       li hauria robat una funció. Quatre cantonades
#    [13] 14  15 [16]      alhora no les fa ningú sense voler, i cap
#                          configuració raonable les demana juntes.
CANTONADES = (0, 3, 12, 15)
AVIS = 1.0        # segons: un parpelleig de "t'he sentit"
CANVI = 3.0       # segons: es confirma el canvi


class Gest:
    """Detecta les quatre cantonades mantingudes.

    actualitza(tecles, ara) — `tecles` és la llista d'estats dels 16 botons,
    tal com la retorna hardware.read_buttons(). Retorna:
        None      no passa res
        'avis'    s'acaba de creuar el segon 1 (parpelleig curt)
        'canvi'   s'han complert els 3 s (rota i reinicia)
    'canvi' es dona UN SOL COP per premuda: mantenir-les més estona no
    encadena canvis.
    """

    def __init__(self, avis=AVIS, canvi=CANVI, cantonades=CANTONADES):
        self.avis = avis
        self.canvi = canvi
        self.cantonades = cantonades
        self._des_de = None
        self._avisat = False
        self._fet = False

    def _totes(self, tecles):
        try:
            for i in self.cantonades:
                if not tecles[i]:
                    return False
            return True
        except Exception:
            return False

    def actualitza(self, tecles, ara):
        if not self._totes(tecles):
            self._des_de = None
            self._avisat = False
            self._fet = False
            return None
        if self._des_de is None:
            self._des_de = ara
            return None
        estona = ara - self._des_de
        if not self._avisat and estona >= self.avis:
            self._avisat = True
            return 'avis'
        if not self._fet and estona >= self.canvi:
            self._fet = True
            return 'canvi'
        return None


def avisa(n=None):
    """Retorn visual. Sense n, un parpelleig blanc curt ("t\'he sentit");
    amb n, el LED es queda del COLOR de la personalitat cap a on vas, després
    de parpellejar-hi n vegades.

    Abans això eren xiulets per un brunzidor a GP22; ara allà hi ha un LED
    multicolor. Es veu de lluny i no fa soroll enmig d'una actuació.
    """
    try:
        from core import llum
        if n is None:
            llum.pampallugues(1, (255, 255, 255))
            return
        rgb = llum.COLORS[int(n) % len(llum.COLORS)]
        llum.pampallugues(int(n) + 1, rgb)
        llum.personalitat(n)
    except Exception:
        pass


# ── El gest sencer, en una sola crida ──────────────────────────────────────
# El Macropad i el Blocks NO són fitxers d'aquest repositori: els escriuen les
# seves apps a personalitats/*.py. Tot el que hagin d'emetre és codi que es pot
# emetre malament, i durant tota la v3.15 i la v3.16 senzillament no en van
# emetre gens: el gest existia, estava ben provat, i no el cridava ningú més
# que l'Instrument — l'única personalitat de la qual sempre se'n pot sortir.
#
# Per això la lògica viu AQUÍ i allà només hi va la crida. Com menys hagin
# d'escriure els generadors, menys se'n poden deixar.

_vigilant = None


def vigila(tecles, ara, silencia=None):
    """Detecta el gest, avisa, rota i reinicia. Retorna el que ha passat.

    `tecles`  llista d'estats dels 16 botons (True = premut).
    `ara`     time.monotonic().
    `silencia`  crida opcional per deixar-ho tot callat abans del reinici dur:
                deixar anar les tecles del HID, apagar les notes MIDI. Sense
                això, el que sonés o estigués premut es queda així a l'altra
                banda del cable, perquè el dispositiu marxa sense acomiadar-se.
    """
    global _vigilant
    if _vigilant is None:
        _vigilant = Gest()
    que = _vigilant.actualitza(tecles, ara)
    if que == 'avis':
        avisa()
    elif que == 'canvi':
        if silencia is not None:
            try:
                silencia()
            except Exception:
                pass
        nova = seguent()
        try:
            print('Canviant a la personalitat %d (%s)' % (nova, etiqueta(nova)))
        except Exception:
            pass
        avisa(nova)
        marca_reinici_propi()
        reinicia()
    return que
