"""
EffectModulation - Control simple de modulació via CC1
"""
from effects.base_effect import BaseEffect

class EffectModulation(BaseEffect):
    def on_activate(self):
        self._cc_all(1, 64, force=True)

    def on_deactivate(self):
        self._cc_all(1, 0, force=True)

    def update_params(self, x=0, y=0, z=0):
        self._cc_all(1, x)
