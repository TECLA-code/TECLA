"""Config Modes — capes ciclables de funcions de potes per modificar el MODE
mentre sona (port de mix_runner.PotLayers de la v2, adaptat a l'arquitectura
v3 d'un sol mode actiu: els CCs s'envien pel canal MIDI per defecte).

Gest (tecla d'efecte 'Config Modes' a 14/15): TAP = capa següent
(OFF → Mescla → Timbre → Expressió → OFF). El click llarg continua ciclant
l'EFECTE assignat a la tecla, com la resta d'efectes.

Pickup: en entrar a una capa cap pot envia res fins que es mou una mica —
evita salts de volum per la posició física del pot. Mòdul amb càrrega lazy:
només s'importa si l'efecte s'usa.
"""
from adafruit_midi.control_change import ControlChange

# Vocabulari de funcions → CC (subset del de kbd_pots + mescla estàndard MIDI)
MODE_POT_CC = {
    'Volum': 7, 'Volume': 7, 'Modulació': 1, 'Modulation': 1,
    'Expressió': 11, 'Expression': 11, 'Pan': 10, 'Reverb': 91, 'Chorus': 93,
    'Filtre': 74, 'Ressonància': 71, 'Atac': 73, 'Release': 72,
    'Decay': 75, "Forma d'ona": 70, 'Detune': 85,
}

# Capes per defecte si la config no en defineix (funcionen out-of-the-box).
# Es poden personalitzar amb 'mode_pot_layers' a la config (per banc o global).
# NOMÉS CCs MIDI estàndard (funcionen amb qualsevol DAW, sense sinte intern).
DEFAULT_MODE_POT_LAYERS = (
    {'name': 'Mescla', 'x': 'Volum', 'y': 'Reverb (CC91)', 'z': 'Pan (CC10)'},
    {'name': 'Timbre', 'x': 'Brillantor (CC74)', 'y': 'Timbre (CC71)', 'z': 'Release (CC72)'},
    {'name': 'Expressio', 'x': 'Expressió', 'y': 'Modulació', 'z': 'Chorus (CC93)'},
)


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
    """Capes ciclables de funcions de potes per al mode actiu (efecte 'Config
    Modes'). Límit MAX_LAYERS (l'UX del cicle mana: més capes = més clics per
    sortir). Pickup: en activar una capa cap pot envia res fins que es mou
    PICKUP passos — evita salts de volum per la posició física del pot."""

    MAX_LAYERS = 4
    PICKUP = 3

    def __init__(self, layers=None):
        self.index = -1
        self._cc_cache = {}
        self._base = [0, 0, 0]
        self._live = [False, False, False]
        self.set_layers(layers)

    def set_layers(self, layers):
        """Fixa les capes des de la config (o les per defecte). Desactiva."""
        src = layers if layers else DEFAULT_MODE_POT_LAYERS
        self.layers = [l for l in src if isinstance(l, dict)][:self.MAX_LAYERS]
        self.index = -1

    @property
    def active(self):
        return self.index >= 0

    def name(self):
        if not self.active:
            return ''
        return str(self.layers[self.index].get('name') or 'Capa %d' % (self.index + 1))

    def off(self):
        self.index = -1

    def cycle(self, pot_values):
        """Tap a la tecla: capa següent (OFF → 1a → … → última → OFF).
        Retorna l'índex nou (-1 = OFF)."""
        if not self.layers:
            self.index = -1
            return -1
        self.index += 1
        if self.index >= len(self.layers):
            self.index = -1
        else:
            # Pickup: memoritza la posició física actual de cada pot
            for ax in range(3):
                self._live[ax] = False
                self._base[ax] = pot_values[ax] if ax < len(pot_values) else 0
        return self.index

    def apply(self, midi_out, pot_values):
        """Aplica la capa activa: cada pot 'viu' envia el seu CC pel canal per
        defecte (el del mode actiu; arquitectura v3 d'un sol mode)."""
        if self.index < 0 or len(pot_values) < 3:
            return
        layer = self.layers[self.index]
        for ax, axis_key in ((0, 'x'), (1, 'y'), (2, 'z')):
            v = int(pot_values[ax])
            if not self._live[ax]:
                if abs(v - self._base[ax]) < self.PICKUP:
                    continue
                self._live[ax] = True
            cc = potfn_to_cc(layer.get(axis_key))
            if cc is None:
                continue
            if abs(self._cc_cache.get(cc, -99) - v) < 2:
                continue
            self._cc_cache[cc] = v
            try:
                midi_out.send(ControlChange(cc, max(0, min(127, v))))
            except Exception:
                pass
