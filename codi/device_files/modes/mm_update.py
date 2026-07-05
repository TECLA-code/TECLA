"""mm_update.py - Bucle d'actualització del ModeManager i gestió d'efectes temporals."""
import time
from adafruit_midi.control_change import ControlChange

# Presets de "Config àudio" (capa modes, tecles 14/15): NO prenen el control del
# mode (segueix sonant), només redirigeixen els 3 potes segons un mapatge
# configurable per preset. Mirall de AUDIO_FX_PRESETS / AUDIO_FX_DEFAULTS a
# tecla-music-data.js.
_AUDIO_FX = ('Àudio 1', 'Àudio 2', 'Àudio 3', 'Àudio 4', 'Àudio 5', 'Àudio 6')
_AUDIO_DEFAULTS = {
    'Àudio 1': {'x': 'Filtre', 'y': 'Ressonància', 'z': 'Env Filtre'},
    'Àudio 2': {'x': 'Atac', 'y': 'Release', 'z': 'Env Decay'},
    'Àudio 3': {'x': 'LFO Vel.', 'y': 'LFO Prof.', 'z': 'LFO→Filtre'},
    'Àudio 4': {'x': "Forma d'ona", 'y': 'Volum', 'z': 'Filtre'},
    'Àudio 5': {'x': 'Filtre', 'y': 'Env Filtre', 'z': 'Env Decay'},
    'Àudio 6': {'x': 'Ressonància', 'y': 'LFO→Filtre', 'z': 'LFO Vel.'},
}
_AUDIO_FN_CC = {
    'Filtre': 74, 'Ressonància': 71, 'Atac': 73, 'Decay': 75, 'Release': 72,
    'LFO Vel.': 76, 'LFO Prof.': 77, 'Env Filtre': 78, 'Env Decay': 79,
    'LFO→Filtre': 80, "Forma d'ona": 70, 'Volum': 7,
    'Env Sustain': 81, 'Trèmol': 82, 'Trèmol vel.': 83, 'Detune': 85,
    'Filtre tipus': 86, 'Pitch env': 87,
}


def _audio_fn_cc(fn):
    """Resol una funció de pot d'àudio (o 'CC Lliure (CCnn)') al seu CC, o None."""
    if fn in _AUDIO_FN_CC:
        return _AUDIO_FN_CC[fn]
    if isinstance(fn, str) and fn.startswith('CC Lliure'):
        d = ''.join(c for c in fn if '0' <= c <= '9')
        if d:
            return min(127, int(d))
    return None


def _route_audio_pots(mgr, preset, pot_values):
    """Envia els CCs dels 3 potes segons el mapatge del preset (config o defaults).
    X=pot[0], Y=pot[1], Z=pot[2]. Threshold simple: només si el valor canvia."""
    maps = {}
    if mgr.config_manager:
        try:
            maps = mgr.config_manager.get_modes_audio_pot_functions()
        except Exception:
            maps = {}
    m = maps.get(preset) or _AUDIO_DEFAULTS.get(preset) or {}
    midi = mgr.effect_manager.midi
    cache = mgr.__dict__.setdefault('_audio_cc_cache', {})
    for axis, val in (('x', pot_values[0]), ('y', pot_values[1]), ('z', pot_values[2])):
        cc = _audio_fn_cc(m.get(axis))
        if cc is None:
            continue
        v = max(0, min(127, int(val)))
        if cache.get(cc) != v:
            cache[cc] = v
            try:
                midi.send(ControlChange(cc, v))
            except Exception:
                pass


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
        # Gest: TAP curt = commuta el latch (l'efecte es queda actiu sense mantenir
        # premut; un altre tap el desactiva). CLICK LLARG (>= effect_long_press) = cicla
        # a l'efecte següent. (Substitueix l'antic 'mantenir per activar' + 'doble clic'.)
        if isinstance(button_states, list) and len(button_states) > 14:
            for efecte_button in mgr.effect_buttons:
                if len(button_states) <= efecte_button:
                    continue
                efecte_info = mgr.efectes_temporals[efecte_button]
                current_state = bool(button_states[efecte_button])

                if current_state != efecte_info['last_state']:
                    # Debounce: ignora rebots massa ràpids
                    if (current_time - efecte_info.get('last_change_time', 0)) < mgr.debounce_time:
                        continue
                    efecte_info['last_change_time'] = current_time
                    efecte_info['last_state'] = current_state
                    if current_state:
                        efecte_info['press_time'] = current_time
                    else:
                        held = (current_time - efecte_info['press_time']
                                if efecte_info['press_time'] > 0 else 0)
                        if held >= mgr.effect_long_press:
                            # CLICK LLARG: cicla l'efecte (desactiva el latch si calia)
                            if efecte_info['active']:
                                mm_deactivate_efecte_temporal(mgr, efecte_button)
                                _clear_susp_flags(mgr, efecte_info['tipus'])
                            mm_cycle_effect(mgr, efecte_button)
                        elif efecte_info['active']:
                            # TAP amb latch actiu: desactiva
                            print(f"{efecte_info['tipus']} OFF")
                            mm_deactivate_efecte_temporal(mgr, efecte_button)
                            _clear_susp_flags(mgr, efecte_info['tipus'])
                        else:
                            # TAP: activa el latch (es queda sense mantenir premut)
                            mm_activate_efecte_temporal(mgr, efecte_button)

        # === PRIORITAT 3: Actualitzar mode actual ===
        # 'Harmonia Negativa' és un efecte de TRANSFORMACIÓ (no de presa de control):
        # encara que estigui actiu (latch), NO atura el mode — només reflecteix les notes.
        algun_efecte_actiu = False
        efecte_actiu_nom = None
        audio_cfg_active = False
        for efecte_button, efecte_info in mgr.efectes_temporals.items():
            if efecte_info['active'] and efecte_info['tipus'] != 'Harmonia Negativa':
                tipus = efecte_info['tipus']
                if tipus in _AUDIO_FX:
                    # Config d'àudio (preset): els potes editen el sinte segons el
                    # mapatge configurable; el mode NO es congela (segueix tocant).
                    audio_cfg_active = True
                    try:
                        _route_audio_pots(mgr, tipus, pot_values)
                    except Exception:
                        pass
                else:
                    try:
                        mgr.effect_manager.update_active_params(pot_values)
                    except Exception as e:
                        print(f"Error params efecte: {e}")
                    algun_efecte_actiu = True
                    efecte_actiu_nom = tipus
                break

        if not audio_cfg_active and mgr.__dict__.get('_audio_cc_cache'):
            mgr._audio_cc_cache = {}   # reset perquè la propera activació reenviï

        if not algun_efecte_actiu and (mgr.sustain_active or mgr.pausa_active):
            algun_efecte_actiu = True
            efecte_actiu_nom = 'sustain' if mgr.sustain_active else 'pausa'

        # Harmonia negativa: efecte de transformació amb LATCH. Si està actiu (un tap
        # l'ha activat), el mode segueix sonant però reflecteix les notes, fins que un
        # altre tap el desactivi. No marca algun_efecte_actiu (no pren el control).
        negharm_held = False
        for efecte_button, efecte_info in mgr.efectes_temporals.items():
            if efecte_info['tipus'] == 'Harmonia Negativa' and efecte_info['active']:
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
                # Config d'àudio activa: passa al mode un snapshot congelat dels
                # potes (els girs en viu només afecten el sinte, no el mode).
                if audio_cfg_active:
                    if getattr(mgr, '_frozen_pots', None) is None:
                        mgr._frozen_pots = list(pot_values)
                    pots_for_mode = mgr._frozen_pots
                else:
                    mgr._frozen_pots = None
                    pots_for_mode = pot_values
                mode_status = mgr.current_mode.update(pots_for_mode, filtered)
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


def _clear_susp_flags(mgr, efecte_tipus):
    """Neteja els flags globals sustain/pausa segons el tipus d'efecte."""
    if efecte_tipus == 'Sustain':
        mgr.sustain_active = False
    elif efecte_tipus == 'Pausa':
        mgr.pausa_active = False


def mm_activate_efecte_temporal(mgr, efecte_button):
    """Activa (latch) l'efecte d'un botó 14/15. Es queda actiu fins a un altre tap.
    Exclusió mútua: només un efecte actiu alhora entre els dos botons."""
    efecte_info = mgr.efectes_temporals[efecte_button]
    efecte_tipus = efecte_info['tipus']
    for altre_button, altre_info in mgr.efectes_temporals.items():
        if altre_button != efecte_button and altre_info['active']:
            mm_deactivate_efecte_temporal(mgr, altre_button)
            _clear_susp_flags(mgr, altre_info['tipus'])
    if efecte_tipus == 'Harmonia Negativa':
        # Transformació: no pren el control (s'injecta a filtered[15]). El mode segueix.
        efecte_info['active'] = True
        print("Harmonia Negativa ON (latch)")
        return
    if mgr.current_mode_name in ['Sustain', 'Pausa']:
        return
    efecte_info['pre_mode'] = mgr.current_mode_name
    efecte_info['pre_mode_instance'] = mgr.current_mode
    if mgr.effect_manager.activate(efecte_tipus):
        efecte_info['active'] = True
        efecte_info['mode_instance'] = None
        print(f"{efecte_tipus} ON (latch)")
        if efecte_tipus == 'Sustain':
            mgr.sustain_active = True
        elif efecte_tipus == 'Pausa':
            mgr.pausa_active = True


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
