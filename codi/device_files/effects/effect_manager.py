"""
EffectManager - Gestor centralitzat d'efectes temporals per TECLA
Carrega els efectes sota demanda per reduir l'ús de memòria.
"""
from effects.base_effect import BaseEffect

# Índex d'efectes: nom -> (mòdul, classe)
EFFECT_INDEX = {
    'Sustain': ('effects.effect_sustain', 'EffectSustain'),
    'Pausa': ('effects.effect_pausa', 'EffectPausa'),
    # Efectes simples i robustos
    'Gate': ('effects.effect_gate', 'EffectGate'),
    'Expression': ('effects.effect_expression', 'EffectExpression'),
    'Modulation': ('effects.effect_modulation', 'EffectModulation'),
    'PitchBend': ('effects.effect_pitchbend', 'EffectPitchBend'),
    # Config àudio (presets duplicables): els potes editen el so, el mode segueix.
    # El mapatge dels potes és configurable per preset (routing a mm_update).
    'Àudio 1': ('effects.effect_synth', 'EffectAudioCfg'),
    'Àudio 2': ('effects.effect_synth', 'EffectAudioCfg'),
    'Àudio 3': ('effects.effect_synth', 'EffectAudioCfg'),
    'Àudio 4': ('effects.effect_synth', 'EffectAudioCfg'),
    'Àudio 5': ('effects.effect_synth', 'EffectAudioCfg'),
    'Àudio 6': ('effects.effect_synth', 'EffectAudioCfg'),
}

class EffectManager:
    def __init__(self, midi_out):
        self.midi = midi_out
        self.effects = {}
        self.active_name = None

    def _get_or_create(self, name):
        if name in self.effects:
            return self.effects[name]
        if name not in EFFECT_INDEX:
            return None
        module_name, class_name = EFFECT_INDEX[name]
        try:
            # CircuitPython/MicroPython no accepten paraules clau a __import__
            # Ús posicional: __import__(name, globals, locals, fromlist)
            module = __import__(module_name, None, None, [class_name])
            effect_cls = getattr(module, class_name)
            instance = effect_cls(self.midi)
            self.effects[name] = instance
            return instance
        except Exception as e:
            print("EffectManager: error carregant efecte:")
            print(f"  nom={name} modul={module_name} classe={class_name} err={e}")
            return None

    def activate(self, name):
        """Activa un efecte pel seu nom (desactiva qualsevol altre)."""
        if self.active_name == name:
            return True
        # Deactivate current
        self.deactivate()
        # Activate new
        eff = self._get_or_create(name)
        if not eff:
            print(f"EffectManager: no s'ha pogut crear l'efecte {name}")
            return False
        try:
            eff.on_activate()
            self.active_name = name
            return True
        except Exception as e:
            print(f"EffectManager: error a on_activate de {name}: {e}")
            return False

    def deactivate(self):
        """Desactiva l'efecte actiu (si n'hi ha)."""
        if not self.active_name:
            return
        eff = self.effects.get(self.active_name)
        if eff:
            try:
                eff.on_deactivate()
            except Exception:
                pass
        self.active_name = None

    def update_active_params(self, pot_values):
        """Actualitza els paràmetres de l'efecte actiu amb X/Y/Z."""
        if not self.active_name:
            return
        x = pot_values[0] if len(pot_values) > 0 else 0
        y = pot_values[1] if len(pot_values) > 1 else 0
        z = pot_values[2] if len(pot_values) > 2 else 0
        eff = self.effects.get(self.active_name)
        if eff:
            try:
                eff.update_params(x, y, z)
            except Exception:
                pass
