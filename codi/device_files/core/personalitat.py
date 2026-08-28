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
