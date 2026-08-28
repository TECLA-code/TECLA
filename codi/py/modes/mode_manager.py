"""
ModeManager - Classe prima. Logica repartida en mm_lifecycle, mm_update, mm_cleanup.
"""
import time


def _get_mode_info_from_registry(mode_name):
    from modes.mm_lifecycle import _get_mode_info_from_registry as _f
    return _f(mode_name)


# ATENCIÓ: duplicat de MODE_CLASSES a mm_lifecycle.py (la còpia funcional).
# Aquesta còpia la llegeix la web (tecla-modes.js) via regex sobre aquest
# fitxer font. Si en modifiques una, modifica també l'altra.
MODE_CLASSES = {'Teclat': ('mode_keyboard', 'KeyboardMode')}


class ModeManager:
    MAX_LOADED_MODES = 3

    def __init__(self, midi_out=None, config_manager=None):
        import gc; gc.collect()
        self.midi_out = midi_out
        self.modes = {}
        self.current_mode = None
        self.current_mode_name = None
        self.banks = {}
        self.current_bank = None
        self.button_mappings = {}
        self.loaded_modes_history = []

        # Tecles d'efecte FLEXIBLES: qualsevol tecla (idx 0-14, excepte 12=canvi de
        # capa) pot tenir una funció/efecte. Es deriven de la config (efectos_temporales,
        # claus = índex de tecla). Fallback a [13, 14] per compatibilitat.
        _efectos = {}
        try:
            if config_manager:
                _efectos = config_manager.config.get('efectos_temporales', {}) or {}
        except Exception:
            _efectos = {}
        self.effect_buttons = []
        for _k in _efectos:
            try:
                _i = int(_k)
            except Exception:
                continue
            if 0 <= _i <= 14 and _i != 12 and _i not in self.effect_buttons:
                self.effect_buttons.append(_i)
        self.effect_buttons.sort()
        if not self.effect_buttons:
            self.effect_buttons = [13, 14]
        self.efectes_temporals = {}
        for btn in self.effect_buttons:
            self.efectes_temporals[btn] = {
                'active': False, 'last_state': False, 'press_time': 0,
                'last_release_time': 0, 'mode_instance': None,
                'pre_mode': None, 'pre_mode_instance': None,
                'tipus': _efectos.get(str(btn), 'Sustain')
            }
        self.effect_hold_threshold = 0.35
        self.double_click_threshold = 0.3
        self.effect_long_press = 0.5   # botons 14/15: >= => cicla l'efecte; tap => latch
        self.available_effects = []
        self.mode_octave = 0
        self.sustain_active = False
        self.sustain_press_time = 0
        self.sustain_last_state = False
        self.pre_sustain_mode = None
        self.pre_sustain_mode_instance = None
        self.sustain_mode = None
        self.pausa_active = False
        self.pausa_press_time = 0
        self.pausa_last_state = False
        self.pre_pausa_mode = None
        self.pre_pausa_mode_instance = None
        self.pausa_mode = None
        self.debounce_time = 0.2
        self.last_mode_error = None
        self.hold_active = False
        self.hold_mode = None
        self.last_mode_change = time.monotonic()
        self.previous_mode_name = None
        self.mode_info_cache = {}

        if config_manager is not None:
            self.config_manager = config_manager
        else:
            from core.config_manager import ConfigManager
            self.config_manager = ConfigManager()
        self._layer_manager = None
        self._effect_manager = None

        gc.collect()
        self._load_all_modes()
        self.load_config()
        try:
            import modes.mm_cleanup
        except Exception:
            pass
        gc.collect()
        print("ModeManager inicialitzat")

    # ── Stubs lifecycle ──────────────────────────────────────────────────────

    def load_config(self):
        from modes.mm_lifecycle import mm_load_config
        return mm_load_config(self)

    def _load_all_modes(self):
        from modes.mm_lifecycle import mm_load_all_modes
        mm_load_all_modes(self)

    def _load_mode(self, mode_name):
        from modes.mm_lifecycle import mm_load_mode
        return mm_load_mode(self, mode_name)

    def _unload_mode(self, mode_name):
        from modes.mm_lifecycle import mm_unload_mode
        return mm_unload_mode(self, mode_name)

    def set_mode(self, mode_name, force_reload=False, capture_state=True):
        from modes.mm_lifecycle import mm_set_mode
        return mm_set_mode(self, mode_name, force_reload, capture_state)

    def reload_current_mode(self):
        from modes.mm_lifecycle import mm_reload_current_mode
        return mm_reload_current_mode(self)

    def get_available_modes(self):
        from modes.mm_lifecycle import mm_get_available_modes
        return mm_get_available_modes(self)

    # ── Stubs update ─────────────────────────────────────────────────────────

    def update(self, pot_values, button_states):
        from modes.mm_update import mm_update
        return mm_update(self, pot_values, button_states)

    def _deactivate_efecte_temporal(self, efecte_button):
        from modes.mm_update import mm_deactivate_efecte_temporal
        mm_deactivate_efecte_temporal(self, efecte_button)

    def _cycle_effect(self, button_index):
        from modes.mm_update import mm_cycle_effect
        mm_cycle_effect(self, button_index)

    def _change_mode_octave(self, delta):
        from modes.mm_update import mm_change_mode_octave
        mm_change_mode_octave(self, delta)

    def _activate_mode(self, mode_name, captured_state=None):
        from modes.mm_update import mm_activate_mode
        return mm_activate_mode(self, mode_name, captured_state)

    # ── Stubs cleanup ────────────────────────────────────────────────────────

    def _stop_current_mode(self):
        from modes.mm_cleanup import mm_stop_current_mode
        mm_stop_current_mode(self)

    def stop_all_sound(self):
        from modes.mm_cleanup import mm_stop_all_sound
        mm_stop_all_sound(self)

    def emergency_stop_and_cleanup(self):
        from modes.mm_cleanup import mm_emergency_stop
        return mm_emergency_stop(self)

    def cleanup(self):
        from modes.mm_cleanup import mm_cleanup
        return mm_cleanup(self)

    def _deactivate_sustain(self):
        from modes.mm_cleanup import mm_deactivate_sustain
        mm_deactivate_sustain(self)

    def _deactivate_pausa(self):
        from modes.mm_cleanup import mm_deactivate_pausa
        mm_deactivate_pausa(self)

    # ── Metodes petits mantinguts inline ─────────────────────────────────────

    @property
    def layer_manager(self):
        if self._layer_manager is None:
            from core.layer_manager import LayerManager
            self._layer_manager = LayerManager(self)
        return self._layer_manager

    @property
    def effect_manager(self):
        if self._effect_manager is None:
            from effects.effect_manager import EffectManager
            self._effect_manager = EffectManager(self.midi_out)
        return self._effect_manager

    def change_layer(self, layer_name):
        return self.layer_manager.change_layer(layer_name)

    def _get_memory_info(self):
        try:
            import gc; gc.collect()
            import micropython
            return micropython.mem_info()
        except Exception:
            return None

    def note_on(self, note, velocity=127, channel=0):
        from adafruit_midi.note_on import NoteOn
        msg = NoteOn(note & 0x7F, velocity & 0x7F)
        msg.channel = channel
        return msg

    def note_off(self, note, velocity=0, channel=0):
        from adafruit_midi.note_off import NoteOff
        msg = NoteOff(note & 0x7F, velocity & 0x7F)
        msg.channel = channel
        return msg

    def control_change(self, control, value, channel=0):
        from adafruit_midi.control_change import ControlChange
        return ControlChange(control, value, channel=channel)
