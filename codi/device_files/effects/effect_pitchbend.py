"""
EffectPitchBend - Vibrato simple via Pitch Bend (si el dispositiu ho suporta)
"""
try:
    from adafruit_midi.pitch_bend import PitchBend
except Exception:
    PitchBend = None
from effects.base_effect import BaseEffect

_CENTER = 8192   # centre del pitch bend MIDI (0 = bend a fons AVALL!)


class EffectPitchBend(BaseEffect):
    def __init__(self, midi_out):
        super().__init__(midi_out)
        self._last_val = None

    def on_activate(self):
        self._last_val = None

    def _bend_all(self, val):
        """Pitch bend (0..16383, 8192 centre) a tots els canals, missatge únic."""
        if not PitchBend:
            return
        val = max(0, min(16383, int(val)))
        if val == self._last_val:
            return
        self._last_val = val
        try:
            msg = PitchBend(val, channel=0)
        except Exception:
            return
        for ch in range(16):
            msg.channel = ch
            try:
                self.midi.send(msg)
            except Exception:
                pass

    def on_deactivate(self):
        # ABANS enviava PitchBend(0): això és bend a fons AVALL, no el centre —
        # deixava el synth desafinat en desactivar l'efecte ("so estrany").
        self._bend_all(_CENTER)

    def update_params(self, x=0, y=0, z=0):
        # Map X 0..127 al voltant del CENTRE: rang suau ±2048 (~±2 semitons)
        self._bend_all(_CENTER + int((x - 64) * 32))
