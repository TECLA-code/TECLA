"""
EffectSustain - Manté les notes actives (CC64)
"""
from effects.base_effect import BaseEffect

class EffectSustain(BaseEffect):
    def on_activate(self):
        self._cc_all(64, 127, force=True)

    def on_deactivate(self):
        # CRÍTIC: si això no s'executa (p. ex. STOP que no desactivava
        # l'efecte), el synth queda amb el pedal premut i TOTES les notes
        # posteriors queden enganxades — vegeu mm_emergency_stop.
        self._cc_all(64, 0, force=True)
        self._cc_all(1, 0, force=True)     # mod off
        self._cc_all(11, 127, force=True)  # expr reset

    def update_params(self, x=0, y=0, z=0):
        self._cc_all(11, x)
