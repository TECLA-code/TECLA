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

        if hasattr(mgr.current_mode, 'cleanup'):
            try:
                mgr.current_mode.cleanup()
            except Exception as e:
                print(f"Error cleanup {mgr.current_mode_name}: {e}")

    except Exception as e:
        print(f"Error aturant mode: {e}")



def mm_all_notes_off(mgr):
    """Xarxa de seguretat BARATA per al canvi de mode: CC120 (All Sound Off) +
    CC123 (All Notes Off) als 16 canals, amb UN missatge reutilitzat.

    32 missatges, no 192. mm_stop_all_sound() —que hi afegeix CC64, el pitch
    bend i 128 NoteOff explícits— porta escrit al seu docstring que és per al
    botó STOP i "mai al camí calent", i era exactament on estava: a CADA canvi
    de mode. Els 128 NoteOff hi són per als AU que ignoren l'All Notes Off, i
    aquest és un problema del pànic, no de passar de Dub a Grana.
    """
    if not mgr.midi_out:
        return
    try:
        from adafruit_midi.control_change import ControlChange
        cc = ControlChange(120, 0, channel=0)
        for channel in range(16):
            for ctrl in (120, 123):
                cc.control = ctrl
                cc.value = 0
                cc.channel = channel
                mgr.midi_out.send(cc)
    except Exception as e:
        print(f"Error all notes off: {e}")


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
        # PRIMER el pedal i el pitch bend, DESPRÉS l'all-notes-off. L'ordre no
        # és estètic: amb el sustain premut, un sinte que només faci cas del
        # CC123 es queda les notes sonant fins que el pedal s'aixequi. Aixecar-lo
        # abans és el que fa que el STOP talli de debò.
        cc = ControlChange(64, 0, channel=0)
        pb = PitchBend(8192, channel=0)
        for channel in range(16):
            cc.channel = channel
            mgr.midi_out.send(cc)
            pb.channel = channel
            mgr.midi_out.send(pb)
        # I el CC120/123 dels 16 canals és el mateix bucle de mm_all_notes_off:
        # no se'n tenen dues còpies.
        mm_all_notes_off(mgr)
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



def mm_unload_all_modes(mgr):
    """Descarrega TOTS els modes carregats (instància i bytecode). Retorna quants.

    El ModeManager en manté fins a MAX_LOADED_MODES de vius alhora perquè
    tornar a un mode recent sigui instantani. Això està bé mentre segueixes a
    la capa de modes, però en SORTIR-NE és RAM retinguda per a res: passar a
    una capa de teclat ha d'al·locar el KeyboardMode i els seus set mòduls
    —vora 46 KB de bytecode— i fer-ho amb dos modes que ja no tornaràs a tocar
    encara al heap és la diferència entre que hi càpiga i que no.

    Es notava poc mentre hi havia tecles mortes: un mode que no es podia
    carregar no ocupava res. En arreglar-les, `mgr.modes` s'omple de debò.
    """
    from modes.mm_lifecycle import mm_unload_mode
    n = 0
    for mode_name in [x for x in list(mgr.modes.keys()) if x != 'Teclat']:
        try:
            if mm_unload_mode(mgr, mode_name):
                n += 1
        except Exception:
            pass
    return n


# Mòduls que NOMÉS serveixen a una capa de TECLAT. Mentre ets en una capa de
# modes no els pot cridar ningú i són 44 KB de bytecode al heap per a res —
# amb 17 KB lliures al dispositiu, són la diferència entre que hi càpiga el
# proper mode i que no.
#
# `negharm` NO hi és: l'importa `base_mode`, o sigui TOTS els modes.
# `modeloop` tampoc: és l'efecte 'Loop' de la capa de MODES (mm_update).
#
# Tots s'importen de forma lazy dins de funcions, així que treure'ls de
# sys.modules només vol dir que el proper ús els torna a llegir del flash.
# Cap d'ells té estat de mòdul mutable: només taules constants.
MODULS_DEL_TECLAT = (
    'modes.mode_keyboard', 'modes.kbd_notes', 'modes.kbd_buttons',
    'modes.kbd_looper', 'modes.kbd_pots', 'modes.kbd_arp',
    'modes.kbd_voicelead', 'modes.accompaniment',
)


def _oblida_modul(nom_complet):
    """Treu un mòdul de sys.modules I del seu paquet.

    Les dues coses, sempre. L'import penja el submòdul com a ATRIBUT del
    paquet (`modes.kbd_notes` → `modes.kbd_notes`), i amb l'atribut viu el
    bytecode queda referenciat encara que sys.modules ja no el tingui: el
    `del sys.modules[...]` tot sol no allibera ni un byte. És la mateixa
    trampa que documenta mm_unload_mode com a «CLAU DE RAM».
    """
    import sys
    tret = False
    if nom_complet in sys.modules:
        try:
            del sys.modules[nom_complet]
            tret = True
        except Exception:
            pass
    paquet, _, fill = nom_complet.rpartition('.')
    if paquet and fill:
        try:
            pkg = sys.modules.get(paquet)
            if pkg is not None and hasattr(pkg, fill):
                delattr(pkg, fill)
                tret = True
        except Exception:
            pass
    return tret


def mm_purga_modules_teclat():
    """Allibera el bytecode de la capa de teclat. Retorna quants n'ha tret."""
    return sum(1 for m in MODULS_DEL_TECLAT if _oblida_modul(m))


def mm_enter_modes_layer(mgr):
    """Entra en una capa de MODES: atura el que sonava, allibera la capa que
    deixes i carrega la config del banc nou. Retorna quants modes ha alliberat.

    Per què existeix: `main._activate_modes_layer` posava `current_mode = None`
    i prou. `mm_set_mode` només descarrega l'anterior si `mgr.current_mode` és
    cert, o sigui que aquell mode ja no el descarregava NINGÚ: es quedava viu a
    `mgr.modes` i el seu bytecode penjat de `sys.modules` i del paquet `modes`
    fins que no passaves per una capa de teclat.

    La branca del teclat (`_activate_keyboard_layer`) ja feia
    `unload_all_modes()` amb aquest mateix argument escrit al docstring de
    `mm_unload_all_modes`. Això és la mateixa regla per a l'altra branca: els
    modes de la capa que deixes no els pot disparar cap tecla de la capa nova,
    o sigui que retenir-los és RAM regalada, i justament al moment en què n'hi
    ha menys.
    """
    if mgr.current_mode is not None:
        try:
            mm_stop_current_mode(mgr)
        except Exception:
            pass
    mgr.current_mode = None
    mgr.current_mode_name = None
    alliberats = mm_unload_all_modes(mgr)
    try:
        mgr.load_config()
    except Exception as e:
        print("Error carregant config de modes: %s" % e)
    # L'ORDRE amaga RAM: mentre corre l'unload, un efecte actiu encara pot
    # referenciar la instància del mode per `pre_mode_instance`, i una
    # instància viva manté viva la seva classe i, amb ella, el MÒDUL sencer —
    # o sigui que el bytecode no es pot alliberar per més que el traguem de
    # sys.modules. Qui deixa anar aquella referència és el `load_config` d'aquí
    # sobre, que reconstrueix els botons d'efecte amb `pre_mode_instance` a
    # None. Sense aquest collect final, ningú no escombra el que acaba
    # d'alliberar-se i el heap se'l queda fins al proper cicle de 30 s.
    # I els 44 KB de la capa de teclat, que aquí no els pot fer servir ningú.
    mm_purga_modules_teclat()
    import gc
    gc.collect()
    return alliberats


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

    mm_unload_all_modes(mgr)

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


