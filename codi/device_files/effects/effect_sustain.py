"""
EffectSustain - Manté les notes actives (CC64)
"""
from adafruit_midi.control_change import ControlChange
from effects.base_effect import BaseEffect

class EffectSustain(BaseEffect):
    def on_activate(self):
        for ch in range(16):
            self.midi.send(ControlChange(64, 127, channel=ch))

    def on_deactivate(self):
        for ch in range(16):
            self.midi.send(ControlChange(64, 0, channel=ch))
            self.midi.send(ControlChange(1, 0, channel=ch))  # mod off
            self.midi.send(ControlChange(11, 127, channel=ch))  # expr reset

    def update_params(self, x=0, y=0, z=0):
        expr = max(0, min(127, int(x)))
        for ch in range(16):
            self.midi.send(ControlChange(11, expr, channel=ch))
