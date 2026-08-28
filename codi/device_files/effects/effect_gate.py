"""
EffectGate - Gating simple d'expressió via CC11 amb control de velocitat i profunditat
Premut = activa gating; Alliberar = desactiva i restaura

X: Velocitat (més alt = més ràpid)
Y: Profunditat (0..127) valor mínim d'expressió
Z: Duty cycle (0..127) proporció de temps en 'alt'
"""
import time
from effects.base_effect import BaseEffect

class EffectGate(BaseEffect):
    def __init__(self, midi_out):
        super().__init__(midi_out)
        self._last_toggle = 0.0
        self._high = True

    def on_activate(self):
        self._last_toggle = time.monotonic()
        self._high = True
        self._cc_all(11, 127, force=True)

    def on_deactivate(self):
        self._cc_all(11, 127, force=True)

    def update_params(self, x=0, y=0, z=0):
        now = time.monotonic()
        # Map X a període: 0..127 -> 0.5s..0.05s
        speed = max(0, min(127, int(x)))
        period = 0.5 - (speed / 127.0) * 0.45  # 0.5 .. 0.05
        # Profunditat (expressió mínima)
        min_expr = max(0, min(127, int(y)))
        # Duty cycle
        duty = max(0.05, min(0.95, (z / 127.0)))

        elapsed = now - self._last_toggle
        target = period * (duty if self._high else (1.0 - duty))
        if elapsed >= target:
            self._high = not self._high
            self._last_toggle = now

        # _cc_all només envia quan el valor CANVIA (toggle o gir de pot):
        # el gate sona igual però sense inundar l'USB a cada cicle.
        self._cc_all(11, 127 if self._high else min_expr)
