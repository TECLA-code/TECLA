"""
EffectPausa - Atenua el so mentre es manté
"""
from effects.base_effect import BaseEffect

class EffectPausa(BaseEffect):
    def on_activate(self):
        self._cc_all(7, 60, force=True)
        self._cc_all(11, 60, force=True)

    def on_deactivate(self):
        self._cc_all(7, 127, force=True)
        self._cc_all(11, 127, force=True)

    def update_params(self, x=0, y=0, z=0):
        self._cc_all(7, max(1, min(127, int(x))))
        self._cc_all(11, max(1, min(127, int(y))))
