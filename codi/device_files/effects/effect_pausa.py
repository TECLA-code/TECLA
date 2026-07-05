"""
EffectPausa - Atenua el so mentre es manté
"""
from adafruit_midi.control_change import ControlChange
from effects.base_effect import BaseEffect

class EffectPausa(BaseEffect):
    def on_activate(self):
        for ch in range(16):
            self.midi.send(ControlChange(7, 60, channel=ch))
            self.midi.send(ControlChange(11, 60, channel=ch))

    def on_deactivate(self):
        for ch in range(16):
            self.midi.send(ControlChange(7, 127, channel=ch))
            self.midi.send(ControlChange(11, 127, channel=ch))

    def update_params(self, x=0, y=0, z=0):
        vol = max(1, min(127, int(x)))
        expr = max(1, min(127, int(y)))
        for ch in range(16):
            self.midi.send(ControlChange(7, vol, channel=ch))
            self.midi.send(ControlChange(11, expr, channel=ch))
