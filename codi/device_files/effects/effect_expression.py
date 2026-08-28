"""
EffectExpression - Control simple d'expressió via CC11
"""
from effects.base_effect import BaseEffect

class EffectExpression(BaseEffect):
    def on_activate(self):
        self._cc_all(11, 127, force=True)

    def on_deactivate(self):
        self._cc_all(11, 127, force=True)

    def update_params(self, x=0, y=0, z=0):
        self._cc_all(11, x)
