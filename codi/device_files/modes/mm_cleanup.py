"""mm_cleanup.py - Aturada de notes, cleanup i emergency stop del ModeManager."""


def mm_stop_current_mode(mgr):
    """Atura el mode actual i neteja les seves notes actives."""
    if not mgr.current_mode:
        return
    try:
        if hasattr(mgr.current_mode, 'stop'):
            try:
                mgr.current_mode.stop()
            except Exception as e:
                print(f"Error stop() {mgr.current_mode_name}: {e}")

        from adafruit_midi.note_off import NoteOff

        # Tracking unificat (BaseMode.send_note_on): un sol punt de neteja.
        # Les comprovacions d'atributs següents es mantenen per als modes
        # antics que encara porten el seu propi tracking.
        if hasattr(mgr.current_mode, 'stop_tracked_notes'):
            try:
                mgr.current_mode.stop_tracked_notes()
            except Exception:
                pass

        if hasattr(mgr.current_mode, 'active_notes'):
            for note in list(mgr.current_mode.active_notes):
                try:
                    mgr.midi_out.send(NoteOff(note, 0))
                except Exception:
                    pass
            mgr.current_mode.active_notes.clear()

        if hasattr(mgr.current_mode, 'notes_playing'):
            for note in list(mgr.current_mode.notes_playing):
                try:
                    mgr.midi_out.send(NoteOff(note, 0))
                except Exception:
                    pass
            mgr.current_mode.notes_playing.clear()

        if hasattr(mgr.current_mode, 'current_chord'):
            for note in list(mgr.current_mode.current_chord):
                try:
                    mgr.midi_out.send(NoteOff(note, 0))
                except Exception:
                    pass
            mgr.current_mode.current_chord.clear()

        if hasattr(mgr.current_mode, 'background_notes'):
            for note_info in mgr.current_mode.background_notes.values():
                if isinstance(note_info, dict) and 'note' in note_info:
                    try:
                        mgr.midi_out.send(NoteOff(note_info['note'], 0))
                    except Exception:
                        pass

        if hasattr(mgr.current_mode, 'active_drones'):
            for drone_info in list(mgr.current_mode.active_drones):
                if isinstance(drone_info, tuple) and len(drone_info) >= 1:
                    try:
                        mgr.midi_out.send(NoteOff(drone_info[0], 0))
                    except Exception:
                        pass
            mgr.current_mode.active_drones.clear()

        if hasattr(mgr.current_mode, 'active_layers'):
            for layer_info in list(mgr.current_mode.active_layers):
                if isinstance(layer_info, tuple) and len(layer_info) >= 1:
                    try:
                        mgr.midi_out.send(NoteOff(layer_info[0], 0))
                    except Exception:
                        pass
            mgr.current_mode.active_layers.clear()

        if hasattr(mgr.current_mode, 'cleanup'):
            try:
                mgr.current_mode.cleanup()
            except Exception as e:
                print(f"Error cleanup {mgr.current_mode_name}: {e}")

    except Exception as e:
        print(f"Error aturant mode: {e}")



def mm_stop_all_sound(mgr):
    """PANIC: atura tot el so MIDI immediatament.

    UNA SOLA passada, mínima i sense al·locacions per missatge: CC64=0
    (sustain off), CC120 (All Sound Off) i CC123 (All Notes Off) per canal +
    pitch bend al centre. L'antiga versió enviava >500 missatges (2 passades,
    128 NoteOff individuals, i CC11=127 a tots els canals): més d'un segon de
    bloqueig i salts de volum — les "coses rares" del botó STOP."""
    if not mgr.midi_out:
        return
    try:
        from adafruit_midi.control_change import ControlChange
        from adafruit_midi.pitch_bend import PitchBend
        cc = ControlChange(64, 0, channel=0)
        pb = PitchBend(8192, channel=0)
        for channel in range(16):
            for ctrl in (64, 120, 123):
                cc.control = ctrl
                cc.value = 0
                cc.channel = channel
                mgr.midi_out.send(cc)
            pb.channel = channel
            mgr.midi_out.send(pb)
        # A més del CC120/123: NoteOff EXPLÍCIT per a les 128 notes al canal
        # de sortida configurat (on toquen el teclat i els modes). Molts
        # instruments de tercers (AUs dins un DAW) IGNOREN All Notes Off — amb
        # això STOP talla el so passi el que passi. Missatge únic reutilitzat;
        # ~120ms un sol cop en prémer STOP, mai al camí calent.
        from modes.base_mode import _note_off_msg
        off = _note_off_msg()
        off.velocity = 0
        off.channel = None   # None → out_channel
        for note in range(128):
            off.note = note
            off.channel = None
            mgr.midi_out.send(off)
    except Exception as e:
        print(f"Error panic: {e}")

    # Apagar el brunzidor PWM intern (mòdul mínim core/tone; abans es feia
    # via el mòdul-ombra 'main', vegeu mode_keyboard._update_pwm_for_note)
    try:
        from core import tone
        tone.off()
    except Exception:
        pass


def mm_emergency_stop(mgr):
    """Atura COMPLETAMENT el so i descarrega tots els modes de la memòria."""
    import gc
    import sys

    # 1. DESACTIVAR els efectes temporals DE VERITAT (amb el seu on_deactivate),
    # inclosos 'Config Modes' i 'Loop': STOP ho atura tot. L'antiga versió
    # només posava active=False sense cridar effect_manager.deactivate() — el
    # Sustain deixava el pedal CC64=127 latched al synth i TOTES les notes
    # posteriors quedaven enganxades (i el mateix STOP "no feia res").
    try:
        from modes.mm_update import mm_deactivate_efecte_temporal
        for _btn in list(mgr.efectes_temporals.keys()):
            try:
                mm_deactivate_efecte_temporal(mgr, _btn)
            except Exception:
                pass
    except Exception:
        pass
    try:
        mgr.effect_manager.deactivate()   # per si l'estat s'havia desincronitzat
    except Exception:
        pass

    mm_stop_all_sound(mgr)

    if mgr.current_mode:
        try:
            if hasattr(mgr.current_mode, 'cleanup'):
                mgr.current_mode.cleanup()
        except Exception:
            pass

    mm_stop_all_sound(mgr)

    modes_to_unload = [name for name in list(mgr.modes.keys()) if name != 'Teclat']
    from modes.mm_lifecycle import mm_unload_mode
    for mode_name in modes_to_unload:
        try:
            mm_unload_mode(mgr, mode_name)
        except Exception:
            pass

    mgr.current_mode = None
    mgr.current_mode_name = None
    mgr.previous_mode_name = None

    for btn in mgr.effect_buttons:
        mgr.efectes_temporals[btn]['active'] = False
        mgr.efectes_temporals[btn]['mode_instance'] = None
        mgr.efectes_temporals[btn]['pre_mode'] = None
        mgr.efectes_temporals[btn]['pre_mode_instance'] = None

    mgr.sustain_mode = None
    mgr.pre_sustain_mode = None
    mgr.pre_sustain_mode_instance = None
    mgr.pausa_mode = None
    mgr.pre_pausa_mode = None
    mgr.pre_pausa_mode_instance = None
    mgr.hold_mode = None

    modules_to_remove = []
    for module_name in list(sys.modules.keys()):
        if (module_name.startswith('modes.mode_') and
                module_name not in ['modes.mode_keyboard', 'modes.base_mode', 'modes.mode_manager']):
            modules_to_remove.append(module_name)
    for module_name in modules_to_remove:
        try:
            del sys.modules[module_name]
        except Exception:
            pass

    gc.collect()
    return True


def mm_cleanup(mgr):
    """Neteja tots els recursos dels modes."""
    from adafruit_midi.control_change import ControlChange

    if mgr.hold_active and mgr.hold_mode:
        if hasattr(mgr.hold_mode, 'cleanup'):
            mgr.hold_mode.cleanup()
        mgr.hold_active = False

    if mgr.sustain_active:
        mm_deactivate_sustain(mgr)
    if mgr.pausa_active:
        mm_deactivate_pausa(mgr)

    if mgr.midi_out:
        for channel in range(16):
            try:
                mgr.midi_out.send(ControlChange(123, 0, channel=channel))
            except Exception:
                pass

    for mode_name, mode_instance in mgr.modes.items():
        if hasattr(mode_instance, 'cleanup'):
            try:
                mode_instance.cleanup()
            except Exception as e:
                print(f"Error cleanup {mode_name}: {e}")
    return True


def mm_deactivate_sustain(mgr):
    try:
        mgr.effect_manager.deactivate()
    except Exception:
        pass
    mgr.sustain_active = False
    mgr.sustain_mode = None
    mgr.pre_sustain_mode_instance = None
    mgr.pre_sustain_mode = None


def mm_deactivate_pausa(mgr):
    try:
        mgr.effect_manager.deactivate()
    except Exception:
        pass
    mgr.pausa_active = False
    mgr.pausa_mode = None
    mgr.pre_pausa_mode_instance = None
    mgr.pre_pausa_mode = None


