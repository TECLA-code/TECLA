"""Config Modes — les capes de comandaments del mode que sona.

Cada mode té UNA llista ordenada de comandaments (BaseMode.comandaments()):
els tres primers són els potes físics X, Y i Z, i la resta es reparteix de
tres en tres a cada TAP de la tecla d'efecte 'Config Modes':

    OFF → capa 1 (comandaments 4-6) → capa 2 (7-9) → … → OFF

Un comandament és una VARIABLE del mode (la família del Laboratori: 'Tempo',
'Caràcter', 'Densitat'…, aplicada amb mode.set_param) o un CC COMÚ ('Volum',
'Reverb (CC91)'…, enviat pel canal per defecte). No hi ha variables
genèriques: cada mode exposa les de la seva família, i per això sempre
funcionen. Vegeu SPEC_VARIABLES_FAMILIA.md.

Un mode sense comandaments (del Laboratori, desat abans d'aquest canvi) cau
a les capes de CC de sempre (Mescla · Timbre · Expressió, o les que l'app
hagi desat a 'mode_pot_layers'): res es trenca.

Pickup: en entrar a una capa cap pot envia res fins que es mou una mica —
evita salts per la posició física del pot. La capa activa SOBREVIU al canvi
de mode (l'efecte és persistent): al mode nou s'hi aplica la capa del
mateix número, reresolta contra la seva llista. Mòdul amb càrrega lazy:
només s'importa si l'efecte s'usa.
"""
from adafruit_midi.control_change import ControlChange
try:
    from core.pantalla import diu
except Exception:                       # simulador i proves sense core/
    def diu(text):
        print(text)
        return True

# Vocabulari de funcions → CC (subset del de kbd_pots + mescla estàndard MIDI)
MODE_POT_CC = {
    'Volum': 7, 'Volume': 7, 'Modulació': 1, 'Modulation': 1,
    'Expressió': 11, 'Expression': 11, 'Pan': 10, 'Reverb': 91, 'Chorus': 93,
    'Filtre': 74, 'Ressonància': 71, 'Atac': 73, 'Release': 72,
    'Decay': 75, "Forma d'ona": 70, 'Detune': 85,
}

# Capes de CC de reserva: per als modes sense comandaments propis. Es poden
# personalitzar amb 'mode_pot_layers' a la config (per banc o global).
# NOMÉS CCs MIDI estàndard (funcionen amb qualsevol DAW, sense sinte intern).
DEFAULT_MODE_POT_LAYERS = (
    {'name': 'Mescla', 'x': 'Volum', 'y': 'Reverb (CC91)', 'z': 'Pan (CC10)'},
    {'name': 'Timbre', 'x': 'Brillantor (CC74)', 'y': 'Timbre (CC71)', 'z': 'Release (CC72)'},
    {'name': 'Expressio', 'x': 'Expressió', 'y': 'Modulació', 'z': 'Chorus (CC93)'},
)

# Potes físics: la capa diu X, Y, Z i el maquinari els porta com pots[1],
# pots[0], pots[2] (els mateixos noms que la capa de teclat i la Pantalla).
_EIXOS = ((0, 'x', 1), (1, 'y', 0), (2, 'z', 2))


def potfn_to_cc(function):
    """Nom de funció de pot → número de CC. Els dígits després de 'CC' manen
    ('CC Lliure (CC74)' → 74, 'Reverb (CC91)' → 91); si no n'hi ha, el mapa de
    noms pelats. Retorna None si no resol."""
    if not function:
        return None
    i = function.find('CC')
    if i >= 0:
        digits = ''
        for ch in function[i + 2:]:
            if '0' <= ch <= '9':
                digits += ch
            elif digits:
                break
        if digits:
            return min(127, int(digits))
    return MODE_POT_CC.get(function)


class PotLayers:
    """Capes ciclables de comandaments per al mode actiu (efecte 'Config
    Modes'). Límit MAX_LAYERS (l'UX del cicle mana: més capes = més clics per
    sortir). Pickup: en activar una capa cap pot envia res fins que es mou
    PICKUP passos."""

    MAX_LAYERS = 4
    PICKUP = 3

    def __init__(self, layers=None):
        self.index = -1
        self._cc_cache = {}
        self._base = [0, 0, 0]
        self._live = [False, False, False]
        self._last = [-1, -1, -1]      # últim valor aplicat per eix: no es repeteix
        self.mode = None
        self.propies = False           # les capes són del mode (True) o de CC (False)
        self._dit = None               # testimoni per a la Pantalla (motor/potdit), lazy
        self.set_layers(layers)

    def set_layers(self, layers):
        """Les capes de CC de reserva, des de la config (o les per defecte).
        No toca la capa activa: si hi ha mode amb comandaments, manen elles."""
        src = layers if layers else DEFAULT_MODE_POT_LAYERS
        self.cc_layers = [l for l in src if isinstance(l, dict)][:self.MAX_LAYERS]
        if not self.propies:
            self.layers = self.cc_layers
            self.index = -1

    def set_mode(self, mode):
        """El mode que sona ha canviat: les capes es tornen a resoldre contra
        la seva llista de comandaments. La capa activa es conserva (mateix
        número) si el mode nou hi arriba; si no, es retalla a l'última."""
        self.mode = mode
        cmds = None
        try:
            # Només els modes amb comandaments PROPIS (PARAMS o POTS) tenen
            # capes pròpies; a la resta els queda la Mescla de sempre.
            if mode is not None and hasattr(mode, 'comandaments') and (
                    getattr(mode, 'PARAMS', ()) or getattr(mode, 'POTS', ())
                    or getattr(mode, '_cmds', None)):
                cmds = mode.comandaments()
        except Exception:
            cmds = None
        if cmds and len(cmds) > 3:
            capes = []
            k = 1
            for i in range(3, len(cmds), 3):
                tros = cmds[i:i + 3]
                capes.append({'name': 'Capa %d' % k,
                              'x': tros[0] if len(tros) > 0 else '',
                              'y': tros[1] if len(tros) > 1 else '',
                              'z': tros[2] if len(tros) > 2 else ''})
                k += 1
                if len(capes) >= self.MAX_LAYERS:
                    break
            self.layers = capes
            self.propies = True
        else:
            self.layers = self.cc_layers
            self.propies = False
        if self.index >= len(self.layers):
            self.index = len(self.layers) - 1
        if self.index >= 0:
            self._reprendre()

    @property
    def active(self):
        return self.index >= 0

    def name(self):
        """Els tres comandaments de la capa activa: 'Volum · Silencis · Rubato'."""
        if not self.active:
            return ''
        l = self.layers[self.index]
        noms = [str(l.get(k) or '—') for k in ('x', 'y', 'z')]
        return ' · '.join(noms)

    def off(self):
        self.index = -1
        if self.mode is not None and hasattr(self.mode, 'repren_potes'):
            try:
                self.mode.repren_potes()
            except Exception:
                pass

    def _reprendre(self, pot_values=None):
        """Pickup: memoritza la posició física actual de cada pot."""
        for ax in range(3):
            self._live[ax] = False
            self._last[ax] = -1
            self._base[ax] = (pot_values[_EIXOS[ax][2]]
                              if pot_values is not None and len(pot_values) > 2 else -999)

    def cycle(self, pot_values):
        """Tap a la tecla: capa següent (OFF → 1a → … → última → OFF).
        Retorna l'índex nou (-1 = OFF)."""
        if not self.layers:
            self.off()
            return -1
        self.index += 1
        if self.index >= len(self.layers):
            self.off()
        else:
            self._reprendre(pot_values)
        return self.index

    def apply(self, midi_out, pot_values):
        """Aplica la capa activa: cada pot 'viu' mana sobre el seu comandament
        (variable del mode via set_param, o CC comú pel canal per defecte)."""
        dit = self._dit
        if dit is not None:
            dit.tick()                              # el pot aturat diu on ha quedat
        if self.index < 0 or len(pot_values) < 3:
            return
        layer = self.layers[self.index]
        for ax, axis_key, idx in _EIXOS:
            v = int(pot_values[idx])
            if not self._live[ax]:
                if self._base[ax] == -999:
                    self._base[ax] = v                  # primera lectura d'aquesta capa
                    continue
                if abs(v - self._base[ax]) < self.PICKUP:
                    continue
                self._live[ax] = True
            if v == self._last[ax]:
                continue                                # el pot no s'ha mogut
            self._last[ax] = v
            nom = layer.get(axis_key)
            if not nom or nom == '—':
                continue
            fet = False
            if self.mode is not None and hasattr(self.mode, 'set_param'):
                try:
                    fet = bool(self.mode.set_param(nom, v))
                except Exception:
                    fet = False
            if not fet:
                cc = potfn_to_cc(nom)
                if cc is None:
                    continue
                if abs(self._cc_cache.get(cc, -99) - v) < 2:
                    continue
                self._cc_cache[cc] = v
                try:
                    midi_out.send(ControlChange(cc, max(0, min(127, v))))
                except Exception:
                    pass
            # Testimoni per a la PANTALLA amb el nom de la VARIABLE (motor/potdit:
            # sense inundar, sense soroll, mai es deixa l'últim valor). Mai llança.
            try:
                if dit is None:
                    from motor.potdit import PotDit
                    dit = self._dit = PotDit()
                dit.mou(nom, v)
            except Exception:
                pass
