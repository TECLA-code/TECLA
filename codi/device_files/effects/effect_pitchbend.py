"""
EffectPitchBend - Vibrato simple via Pitch Bend (si el dispositiu ho suporta)
"""
try:
    from adafruit_midi.pitch_bend import PitchBend
except Exception:
    PitchBend = None
from effects.base_effect import BaseEffect

class EffectPitchBend(BaseEffect):
    def on_activate(self):
        # No cal inicialització
        pass

    def on_deactivate(self):
        if not PitchBend:
            return
        # Reset pitch bend al centre (8192)
        for ch in range(16):
            try:
                self.midi.send(PitchBend(0))  # Alguns dispositius interpreten 0 com a centre
            except Exception:
                pass

    def update_params(self, x=0, y=0, z=0):
        if not PitchBend:
            return
        # Map X 0..127 a rang suau -2000..+2000 approx.
        val = int((x - 64) * 32)  # curt, suau
        for ch in range(16):
            try:
                self.midi.send(PitchBend(val))
            except Exception:
                pass
