"""mm_update.py - Bucle d'actualització del ModeManager i gestió d'efectes temporals."""
import time


def mm_update(mgr, pot_values, button_states):
    """Actualitza el mode actual i processa botons d'efecte."""
    change_mode = None
    try:
        status = {'change_mode': None}
        current_time = time.monotonic()

        # === PRIORITAT 1: Canvis de capa (botons 13 i 16) ===
        if isinstance(button_states, list) and len(button_states) > 15:
            layer_changed = mgr.layer_manager.process_layer_buttons(button_states)
            if layer_changed:
                status['layer'] = mgr.layer_manager.current_layer

        # === PRIORITAT 2: Botons d'efecte (14 i 15) ===
        if isinstance(button_states, list) and len(button_states) > 14:
            button_states_modified = False
            button_states_list = list(button_states)

            for efecte_button in mgr.effect_buttons:
                if len(button_states) <= efecte_button:
                    continue
                efecte_info = mgr.efectes_temporals[efecte_button]
                efecte_tipus = efecte_info['tipus']
                current_state = bool(button_states[efecte_button])

                elapsed = (current_time - efecte_info['press_time']
                           if efecte_info['press_time'] > 0 else 0)
                time_since_press = (current_time - efecte_info['press_time']
                                    if efecte_info['press_time'] > 0 else 999)

                if time_since_press > mgr.debounce_time or efecte_info['press_time'] == 0:
                    if current_state != efecte_info['last_state']:
                        efecte_info['last_state'] = current_state
                        if current_state:
                            efecte_info['press_time'] = current_time
                        else:
                            release_time = current_time
                            time_since_last_release = release_time - efecte_info.get('last_release_time', 0)
                            is_double_click = (time_since_last_release < mgr.double_click_threshold and
                                               time_since_last_release > 0.05)
                            if is_double_click:
                                print(f"Doble clic botó {efecte_button+1}")
                                if efecte_info['active']:
                                    mm_deactivate_efecte_temporal(mgr, efecte_button)
                                mm_cycle_effect(mgr, efecte_button)
                                efecte_info['last_release_time'] = 0
                                button_states_list[efecte_button] = False
                                button_states_modified = True
                            else:
                                if efecte_info['active']:
                                    print(f"{efecte_tipus} OFF")
                                    mm_deactivate_efecte_temporal(mgr, efecte_button)
                                    if efecte_tipus == 'Sustain':
                                        mgr.sustain_active = False
                                    elif efecte_tipus == 'Pausa':
                                        mgr.pausa_active = False
                                efecte_info['last_release_time'] = release_time
                    else:
                        # 'Harmonia Negativa' és un efecte de transformació, no de
                        # presa de control: no s'activa via effect_manager (manté el
                        # mode sonant). Es processa més avall injectant negharm_held.
                        if (current_state and not efecte_info['active'] and
                                elapsed >= mgr.effect_hold_threshold and
                                efecte_tipus != 'Harmonia Negativa'):
                            if mgr.current_mode_name not in ['Sustain', 'Pausa']:
                                print(f"{efecte_tipus} ON")
                                for altre_button, altre_info in mgr.efectes_temporals.items():
                                    if altre_button != efecte_button and altre_info['active']:
                                        mm_deactivate_efecte_temporal(mgr, altre_button)
                                efecte_info['pre_mode'] = mgr.current_mode_name
                                efecte_info['pre_mode_instance'] = mgr.current_mode
                                activat = mgr.effect_manager.activate(efecte_tipus)
                                if activat:
                                    efecte_info['active'] = True
                                    efecte_info['mode_instance'] = None
                                    if efecte_tipus == 'Sustain':
                                        mgr.sustain_active = True
                                    elif efecte_tipus == 'Pausa':
                                        mgr.pausa_active = True

            if button_states_modified:
                button_states = button_states_list

        # === PRIORITAT 3: Actualitzar mode actual ===
        algun_efecte_actiu = False
        efecte_actiu_nom = None
        for efecte_button, efecte_info in mgr.efectes_temporals.items():
            if efecte_info['active']:
                try:
                    mgr.effect_manager.update_active_params(pot_values)
                except Exception as e:
                    print(f"Error params efecte: {e}")
                algun_efecte_actiu = True
                efecte_actiu_nom = efecte_info['tipus']
                break

        if not algun_efecte_actiu and (mgr.sustain_active or mgr.pausa_active):
            algun_efecte_actiu = True
            efecte_actiu_nom = 'sustain' if mgr.sustain_active else 'pausa'

        # Harmonia negativa: efecte de transformació. Mentre es manté premut un botó
        # 14/15 amb aquest efecte assignat, el mode segueix sonant però reflecteix les
        # notes. No marca algun_efecte_actiu (no pren el control de la sortida).
        negharm_held = False
        for efecte_button, efecte_info in mgr.efectes_temporals.items():
            if (efecte_info['tipus'] == 'Harmonia Negativa'
                    and len(button_states) > efecte_button
                    and bool(button_states[efecte_button])):
                negharm_held = True
                break

        if not algun_efecte_actiu:
            if mgr.current_mode:
                filtered = list(button_states) if isinstance(button_states, (list, tuple)) else button_states
                if isinstance(filtered, list) and len(filtered) > 14:
                    filtered[13] = False
                    filtered[14] = False
                # Injecta l'estat d'harmonia negativa al botó 16 (índex 15), el canal
                # que els modes melòdics consulten via poll_negharm(). Substitueix
                # l'estat real de la tecla 16 (STOP, gestionada a main.py).
                if isinstance(filtered, list) and len(filtered) > 15:
                    filtered[15] = negharm_held
                mode_status = mgr.current_mode.update(pot_values, filtered)
                if isinstance(mode_status, dict):
                    status.update(mode_status)
                    if mode_status.get('change_mode'):
                        change_mode = mode_status['change_mode']
                else:
                    status = {'status': str(mode_status)}
        else:
            status['effect_active'] = efecte_actiu_nom

        # === PRIORITAT 4: Canvi de mode ===
        if change_mode and change_mode in mgr.modes:
            mgr.set_mode(change_mode)

        status['mode'] = mgr.current_mode_name
        status['layer'] = mgr.layer_manager.current_layer
        status['pausa_active'] = mgr.pausa_active
        status['sustain_active'] = mgr.sustain_active
        status['mode_octave'] = mgr.mode_octave
        return status

    except Exception as e:
        print(f"Error update mode '{mgr.current_mode_name}': {e}")
        import sys; sys.print_exception(e)
        return {'mode': 'Error'}


def mm_deactivate_efecte_temporal(mgr, efecte_button):
    """Desactiva un efecte temporal i restaura l'estat anterior."""
    if efecte_button not in mgr.efectes_temporals or not mgr.efectes_temporals[efecte_button]['active']:
        return
    efecte_info = mgr.efectes_temporals[efecte_button]
    print(f"Desactivant efecte {efecte_info['tipus']}")
    try:
        mgr.effect_manager.deactivate()
    except Exception as e:
        print(f"Error desactivant efecte: {e}")
    efecte_info['active'] = False
    efecte_info['mode_instance'] = None
    efecte_info['pre_mode_instance'] = None
    efecte_info['pre_mode'] = None


def mm_cycle_effect(mgr, button_index):
    """Cicla l'efecte assignat a un botó."""
    efecte_info = mgr.efectes_temporals[button_index]
    current_effect = efecte_info['tipus']
    if not mgr.available_effects:
        return
    if efecte_info['active']:
        mm_deactivate_efecte_temporal(mgr, button_index)
    try:
        current_index = mgr.available_effects.index(current_effect)
    except ValueError:
        current_index = -1
    next_index = (current_index + 1) % len(mgr.available_effects)
    new_effect = mgr.available_effects[next_index]
    efecte_info['tipus'] = new_effect
    if mgr.config_manager:
        try:
            if 'efectos_temporales' not in mgr.config_manager.config:
                mgr.config_manager.config['efectos_temporales'] = {}
            mgr.config_manager.config['efectos_temporales'][str(button_index)] = new_effect
        except Exception as e:
            print(f"Error guardant efecte: {e}")
    print(f"[EFECTE] Botó {button_index+1}: {current_effect} -> {new_effect}")


def mm_change_mode_octave(mgr, delta):
    """Canvia l'octava global dels modes."""
    try:
        mgr.mode_octave = max(-4, min(4, mgr.mode_octave + (1 if delta > 0 else -1)))
        print(f"Octava modes: {mgr.mode_octave}")
        if mgr.current_mode:
            if hasattr(mgr.current_mode, 'set_octave_shift'):
                try:
                    mgr.current_mode.set_octave_shift(mgr.mode_octave)
                except Exception:
                    pass
            elif hasattr(mgr.current_mode, 'set_octave'):
                try:
                    mgr.current_mode.set_octave(mgr.mode_octave)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error octava: {e}")


def mm_activate_mode(mgr, mode_name, captured_state=None):
    """Activa un mode sense netejar el mode anterior."""
    if mode_name not in mgr.modes:
        print(f"No es pot activar {mode_name}: no trobat")
        return False
    mgr.current_mode = mgr.modes[mode_name]
    mgr.current_mode_name = mode_name
    if hasattr(mgr.current_mode, 'cleanup'):
        try:
            mgr.current_mode.cleanup()
        except Exception:
            pass
    if hasattr(mgr.current_mode, 'setup'):
        try:
            mgr.current_mode.setup()
        except Exception as e:
            print(f"Error setup {mode_name}: {e}")
    return True
