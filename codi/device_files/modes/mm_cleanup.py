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


def mm_stop_notes(mgr, notes_info):
    """Atura les notes especificades."""
    from adafruit_midi.note_off import NoteOff
    for note_info in notes_info:
        try:
            if len(note_info) >= 2:
                note, velocity = note_info[0], note_info[1]
                channel = note_info[2] if len(note_info) > 2 else 0
                note_off_msg = NoteOff(note & 0x7F, velocity & 0x7F)
                note_off_msg.channel = channel
                mgr.midi_out.send(note_off_msg)
        except Exception as e:
            print(f"Error aturant nota {note_info}: {e}")


def mm_stop_all_sound(mgr):
    """PANIC: atura tot el so MIDI immediatament."""
    if not mgr.midi_out:
        return
    from adafruit_midi.control_change import ControlChange
    from adafruit_midi.note_off import NoteOff

    for iteration in range(2):
        try:
            for channel in range(3):
                mgr.midi_out.send(ControlChange(64, 0, channel=channel))
                mgr.midi_out.send(ControlChange(120, 0, channel=channel))
                mgr.midi_out.send(ControlChange(123, 0, channel=channel))
            for note in range(128):
                try:
                    mgr.midi_out.send(NoteOff(note, 0, channel=0))
                except Exception:
                    pass
            for channel in range(16):
                mgr.midi_out.send(ControlChange(64, 0, channel=channel))
                mgr.midi_out.send(ControlChange(120, 0, channel=channel))
                mgr.midi_out.send(ControlChange(123, 0, channel=channel))
                try:
                    from adafruit_midi.pitch_bend import PitchBend
                    mgr.midi_out.send(PitchBend(8192, channel=channel))
                except Exception:
                    pass
                mgr.midi_out.send(ControlChange(1, 0, channel=channel))
                mgr.midi_out.send(ControlChange(11, 127, channel=channel))
                mgr.midi_out.send(ControlChange(91, 0, channel=channel))
                mgr.midi_out.send(ControlChange(93, 0, channel=channel))
        except Exception as e:
            print(f"Error panic iter {iteration}: {e}")
        if iteration == 0:
            try:
                import time; time.sleep(0.01)
            except Exception:
                pass

    # Apagar el brunzidor PWM si existeix. Es consulta sys.modules en lloc de
    # fer `import main`: si 'main' encara no s'ha importat com a mòdul, el pwm
    # no pot existir, i l'import re-executaria tot main.py (pic de RAM en ple
    # pànic, el pitjor moment possible).
    try:
        import sys
        _main = sys.modules.get('main')
        if _main is not None and getattr(_main, 'pwm', None) is not None:
            _main.pwm.duty_cycle = 0
    except Exception:
        pass


def mm_emergency_stop(mgr):
    """Atura COMPLETAMENT el so i descarrega tots els modes de la memòria."""
    import gc
    import sys

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
    gc.collect()
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


def mm_silent_controls(mgr):
    """Silencia controls MIDI del mode actual."""
    try:
        from adafruit_midi.control_change import ControlChange
        for channel in range(16):
            mgr.midi_out.send(ControlChange(11, 127, channel=channel))
            mgr.midi_out.send(ControlChange(1, 0, channel=channel))
    except Exception as e:
        print(f"Error silenciant controls: {e}")
