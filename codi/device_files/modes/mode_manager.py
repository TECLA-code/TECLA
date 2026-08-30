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
    # Sostre de modes instanciats alhora. AVUI no s'arriba a disparar mai:
    # mm_set_mode descarrega l'anterior a cada canvi, així que n'hi ha com a
    # molt un de viu. Es queda com a xarxa per a qui carregui un mode sense
    # passar per set_mode (mm_load_mode és pública), però no esperis que el
    # dispositiu en tingui tres a la RAM: no n'hi té cap més d'un.
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
        # capa) pot tenir una funció/efecte. Surten de la config del BANC
        # (`efectos_temporales`, claus = índex de tecla), amb el mapa global com
        # a segona opció; ho resol config_manager.get_temporal_effects(). Es
        # tornen a construir a cada canvi de capa des de mm_load_config.
        self.effect_buttons = []
        self.efectes_temporals = {}
        self.effect_long_press = 0.5   # botons 14/15: >= => cicla l'efecte; tap => latch
        self.available_effects = []
        self.mode_octave = 0
        # (fora: effect_hold_threshold i double_click_threshold, que no llegia
        #  ningú — cada mode que fa doble clic es defineix el seu propi llindar—,
        #  i els quatre sustain_/pausa_press_time i _last_state, restes del
        #  gest antic de «mantenir premut» que va substituir el latch.)
        self.sustain_active = False
        self.pre_sustain_mode = None
        self.pre_sustain_mode_instance = None
        self.sustain_mode = None
        self.pausa_active = False
        self.pre_pausa_mode = None
        self.pre_pausa_mode_instance = None
        self.pausa_mode = None
        # Filtre de rebots dels botons d'efecte. 20 ms és el temps que triga un
        # contacte mecànic a assentar-se; els 200 ms d'abans no filtraven
        # rebots, es menjaven els tocs (vegeu mm_update).
        self.debounce_time = 0.02
        self.last_mode_error = None
        self.last_mode_change = time.monotonic()
        self.previous_mode_name = None
        self.mode_info_cache = {}

        if config_manager is not None:
            self.config_manager = config_manager
        else:
            from core.config_manager import ConfigManager
            self.config_manager = ConfigManager()
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





    def _stop_current_mode(self):
        from modes.mm_cleanup import mm_stop_current_mode
        mm_stop_current_mode(self)

    def unload_all_modes(self):
        from modes.mm_cleanup import mm_unload_all_modes
        return mm_unload_all_modes(self)

    def stop_all_sound(self):
        from modes.mm_cleanup import mm_stop_all_sound
        mm_stop_all_sound(self)

    def emergency_stop_and_cleanup(self):
        from modes.mm_cleanup import mm_emergency_stop
        return mm_emergency_stop(self)

    def cleanup(self):
        from modes.mm_cleanup import mm_cleanup
        return mm_cleanup(self)




    @property
    def effect_manager(self):
        if self._effect_manager is None:
            from effects.effect_manager import EffectManager
            self._effect_manager = EffectManager(self.midi_out)
        return self._effect_manager

