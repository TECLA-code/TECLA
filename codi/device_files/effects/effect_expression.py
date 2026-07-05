"""
EffectExpression - Control simple d'expressió via CC11
"""
from adafruit_midi.control_change import ControlChange
from effects.base_effect import BaseEffect

class EffectExpression(BaseEffect):
    def on_activate(self):
        # No cal forçar, però deixem un valor alt per defecte
        for ch in range(16):
            self.midi.send(ControlChange(11, 127, channel=ch))

    def on_deactivate(self):
        # Restaurar expressió a nivell alt
        for ch in range(16):
            self.midi.send(ControlChange(11, 127, channel=ch))

    def update_params(self, x=0, y=0, z=0):
        expr = max(0, min(127, int(x)))
        for ch in range(16):
            self.midi.send(ControlChange(11, expr, channel=ch))
