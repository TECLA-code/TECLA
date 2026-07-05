"""
Efecte "Config àudio" de la capa de modes (presets 'Àudio 1'…'Àudio 6').

NO pren el control del mode: mentre està actiu, els 3 potes editen el so segons
un mapatge CONFIGURABLE per preset. El routing real (llegir el mapatge de config i
enviar els CCs) el fa mm_update._route_audio_pots, perquè és qui té accés a
mgr.config_manager. Aquesta classe és només un placeholder perquè
EffectManager.activate() funcioni (cicle/latch dels botons 14/15).
"""
from effects.base_effect import BaseEffect


class EffectAudioCfg(BaseEffect):
    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    def update_params(self, x=0, y=0, z=0):
        pass  # el routing es fa a mm_update segons el mapatge del preset
