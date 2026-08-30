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
    # Ni una línia més: BaseEffect ja té on_activate/on_deactivate/update_params
    # buits, i reescriure'ls amb `pass` només afegia bytecode.
    pass
