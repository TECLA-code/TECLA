"""mm_lifecycle.py - Gestió del cicle de vida dels modes: càrrega, descàrrega, canvi."""
import time
import os
import json
import sys

# Registre estàtic: únic mode permanent (KeyboardMode es gestiona per separat)
MODE_CLASSES = {
    'Teclat': ('mode_keyboard', 'KeyboardMode'),
}


def _get_mode_info_from_registry(mode_name):
    try:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            registry_path = os.path.join(current_dir, 'custom_modes_registry.json')
        except Exception:
            registry_path = 'modes/custom_modes_registry.json'
        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            modes_data = registry.get('custom_modes', {})
            if mode_name in modes_data:
                mode_info = modes_data[mode_name]
                return (mode_info['file_name'], mode_info['class_name'])
        except OSError:
            pass
    except Exception as e:
        print(f"Error consultant registre per {mode_name}: {e}")
    return None


def _count_registered_modes():
    try:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            registry_path = os.path.join(current_dir, 'custom_modes_registry.json')
        except Exception:
            registry_path = 'modes/custom_modes_registry.json'
        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            return len(registry.get('custom_modes', {}))
        except OSError:
            return 0
    except Exception:
        return 0


def _build_mode_info_cache(mgr, configured_modes):
    """Llegeix el registre UNA SOLA VEGADA i crea un cache per als modes del banc."""
    import gc
    try:
        registry_path = 'modes/custom_modes_registry.json'
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        modes_data = registry.get('custom_modes', {})
        mgr.mode_info_cache = {}
        for mode_name in configured_modes:
            if mode_name and mode_name not in MODE_CLASSES:
                if mode_name in modes_data:
                    info = modes_data[mode_name]
                    mgr.mode_info_cache[mode_name] = (info['file_name'], info['class_name'])
                else:
                    print(f"Mode '{mode_name}' no al registre")
        del registry, modes_data
        gc.collect()
    except Exception as e:
        print(f"Error llegint registre: {e}")


def mm_load_config(mgr):
    """Carrega la configuració de bancs i modes."""
    efectes_preservats = {}
    for btn in mgr.effect_buttons:
        if mgr.efectes_temporals[btn]['active']:
            # NOMÉS el nom, no la instància: preservar pre_mode_instance
            # mantenia viva una instància que tot just es descarrega per
            # alliberar RAM (i no es llegeix enlloc del codi)
            efectes_preservats[btn] = {
                'tipus': mgr.efectes_temporals[btn]['tipus'],
                'pre_mode': mgr.efectes_temporals[btn]['pre_mode']
            }

    if mgr.current_mode and mgr.current_mode_name and mgr.current_mode_name != 'Teclat':
        from modes.mm_cleanup import mm_stop_current_mode, mm_stop_all_sound
        previous_mode_name = mgr.current_mode_name
        mm_stop_all_sound(mgr)
        mm_stop_current_mode(mgr)
        if previous_mode_name and previous_mode_name != 'Teclat':
            mm_unload_mode(mgr, previous_mode_name)
        mgr.current_mode = None
        mgr.current_mode_name = None
        import gc; gc.collect()

    try:
        current_bank = mgr.config_manager.get_current_bank()
        if not current_bank:
            return False

        disabled_modes = current_bank.get('disabled_modes', []) if isinstance(current_bank, dict) else []
        configured_modes = current_bank.get('modes', []) if isinstance(current_bank, dict) else []

        # Pre-cache les dades del registre per als modes del banc (1 sola lectura JSON)
        import gc; gc.collect()
        _build_mode_info_cache(mgr, configured_modes)
        gc.collect()

        # Netejar les assignacions del banc anterior (botons 0-11): si el nou
        # banc té menys modes vàlids, no han de quedar mapejos residuals
        for button_idx in range(12):
            mgr.button_mappings.pop(button_idx, None)

        for button_idx in range(12):
            mode_name = configured_modes[button_idx] if button_idx < len(configured_modes) else None
            if mode_name and mode_name not in disabled_modes:
                if mode_name in MODE_CLASSES or mode_name in mgr.mode_info_cache:
                    mgr.button_mappings[button_idx] = mode_name
                else:
                    print(f"Botó {button_idx+1}: mode '{mode_name}' no trobat")

        mgr.button_mappings[12] = 'RESERVADO_BANCS'

        global_efectos = mgr.config_manager.config.get('efectos_temporales', {})
        if global_efectos:
            for btn in mgr.effect_buttons:
                key = str(btn)
                if key in global_efectos:
                    efecte_tipus_nou = global_efectos[key]
                    if efecte_tipus_nou != mgr.efectes_temporals[btn]['tipus']:
                        if mgr.efectes_temporals[btn]['active']:
                            from modes.mm_update import mm_deactivate_efecte_temporal
                            mm_deactivate_efecte_temporal(mgr, btn)
                        mgr.efectes_temporals[btn]['tipus'] = efecte_tipus_nou

        if efectes_preservats:
            for btn, efecte_data in efectes_preservats.items():
                if mgr.efectes_temporals[btn]['tipus'] == efecte_data['tipus']:
                    activat = mgr.effect_manager.activate(efecte_data['tipus'])
                    if activat:
                        mgr.efectes_temporals[btn]['active'] = True
                        mgr.efectes_temporals[btn]['pre_mode'] = efecte_data['pre_mode']
                        mgr.efectes_temporals[btn]['pre_mode_instance'] = None

        if mgr.config_manager:
            mgr.available_effects = mgr.config_manager.get_available_effects()

        for btn in mgr.effect_buttons:
            mgr.button_mappings[btn] = f"RESERVADO_EFECTO_{mgr.efectes_temporals[btn]['tipus']}"
        mgr.button_mappings[15] = 'RESERVADO_TORNAR'

        return True
    except Exception as e:
        print(f"Error carregant configuració: {e}")
        return False


def mm_load_all_modes(mgr):
    """Inicialitza els modes (lazy loading - no crea instàncies innecessàries)."""
    print("✓ ModeManager: lazy loading activat")
    # No precarregar Teclat: ja gestionat per hardware.keyboard_mode


def mm_load_mode(mgr, mode_name):
    """Carrega un mode individual sota demanda."""
    if mode_name in MODE_CLASSES:
        module_name, class_name = MODE_CLASSES[mode_name]
    elif hasattr(mgr, 'mode_info_cache') and mode_name in mgr.mode_info_cache:
        module_name, class_name = mgr.mode_info_cache[mode_name]
    else:
        mode_info = _get_mode_info_from_registry(mode_name)
        if mode_info:
            module_name, class_name = mode_info
        else:
            return False

    if mode_name in mgr.modes:
        if mode_name in mgr.loaded_modes_history:
            mgr.loaded_modes_history.remove(mode_name)
        mgr.loaded_modes_history.append(mode_name)
        return True

    try:
        if len(mgr.modes) >= mgr.MAX_LOADED_MODES:
            for old_mode in mgr.loaded_modes_history:
                if (old_mode in mgr.modes and
                        old_mode != 'Teclat' and
                        old_mode != mgr.current_mode_name and
                        old_mode != mode_name):
                    print(f"[MEMÒRIA] Descarregant: {old_mode}")
                    mm_unload_mode(mgr, old_mode)
                    break

        import gc; gc.collect()
        print(f"[CÀRREGA] Carregant mode: {mode_name}...")

        module = __import__(f'modes.{module_name}')
        module = getattr(module, module_name)
        mode_class = getattr(module, class_name)
        mgr.modes[mode_name] = mode_class(mgr.midi_out, {})
        mgr.loaded_modes_history.append(mode_name)
        gc.collect()
        print(f"✓ Mode {mode_name} carregat")
        return True

    except Exception as e:
        print(f"✗ Error carregant {mode_name}: {e}")
        return False


def mm_unload_mode(mgr, mode_name):
    """Descarrega un mode de la memòria."""
    if mode_name not in mgr.modes:
        return False
    try:
        import gc
        module_name = None
        if mode_name in MODE_CLASSES:
            module_name, _ = MODE_CLASSES[mode_name]
        elif hasattr(mgr, 'mode_info_cache') and mode_name in mgr.mode_info_cache:
            module_name, _ = mgr.mode_info_cache[mode_name]
        else:
            mode_info = _get_mode_info_from_registry(mode_name)
            if mode_info:
                module_name, _ = mode_info

        del mgr.modes[mode_name]

        full_module_name = f'modes.{module_name}' if module_name else None
        if full_module_name and full_module_name in sys.modules:
            del sys.modules[full_module_name]

        if mode_name in mgr.loaded_modes_history:
            mgr.loaded_modes_history.remove(mode_name)

        gc.collect()
        return True
    except Exception as e:
        print(f"Error descarregant {mode_name}: {e}")
        return False


def mm_set_mode(mgr, mode_name, force_reload=False, capture_state=True):
    """Canvia al mode especificat: PARA l'actual primer, CARREGA el nou despres."""
    try:
        import gc

        # 1. PRIMER: aturar i descarregar el mode actual per alliberar RAM
        if mgr.current_mode and (mgr.current_mode_name != mode_name or force_reload):
            previous_mode = mgr.current_mode_name
            print(f"Aturant: {previous_mode}")
            from modes.mm_cleanup import mm_stop_current_mode, mm_stop_all_sound
            mm_stop_current_mode(mgr)
            mm_stop_all_sound(mgr)
            mgr.current_mode = None
            mgr.current_mode_name = None
            if previous_mode and previous_mode != 'Teclat':
                mm_unload_mode(mgr, previous_mode)
            gc.collect()

        if mgr.current_mode_name == mode_name and not force_reload:
            return True

        # 2. DESPRES: carregar el nou mode amb la RAM alliberada
        if mode_name not in mgr.modes:
            mm_load_mode(mgr, mode_name)
            if mode_name not in mgr.modes:
                print(f"No s'ha pogut carregar '{mode_name}'")
                return False

        print(f"Mode: {mode_name}")
        mgr.current_mode = mgr.modes[mode_name]
        mgr.current_mode_name = mode_name
        mgr.last_mode_change = time.monotonic()
        mgr.previous_mode_name = mode_name

        if hasattr(mgr.current_mode, 'setup'):
            try:
                mgr.current_mode.setup()
            except Exception as e:
                print(f"Error setup {mode_name}: {e}")

        return True

    except Exception as e:
        print(f"Error canviant a {mode_name}: {e}")
        mgr.last_mode_error = str(e)
        return False


def mm_reload_current_mode(mgr):
    if mgr.current_mode_name:
        return mm_set_mode(mgr, mgr.current_mode_name, force_reload=True)
    return False


def mm_get_available_modes(mgr):
    """Retorna els modes del banc actual (des de button_mappings, NO tot el registre)."""
    modes = []
    for btn_idx in sorted(mgr.button_mappings.keys()):
        name = mgr.button_mappings.get(btn_idx, '')
        if name and not name.startswith('RESERVADO_') and name not in modes:
            modes.append(name)
    return modes
