"""
EffectModulation - Control simple de modulació via CC1
"""
from adafruit_midi.control_change import ControlChange
from effects.base_effect import BaseEffect

class EffectModulation(BaseEffect):
    def on_activate(self):
        # Començar amb un valor moderat
        for ch in range(16):
            self.midi.send(ControlChange(1, 64, channel=ch))

    def on_deactivate(self):
        # Desactivar modulació
        for ch in range(16):
            self.midi.send(ControlChange(1, 0, channel=ch))

    def update_params(self, x=0, y=0, z=0):
        mod = max(0, min(127, int(x)))
        for ch in range(16):
            self.midi.send(ControlChange(1, mod, channel=ch))
