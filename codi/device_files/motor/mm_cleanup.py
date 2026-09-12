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

        # Els noms de sota són DUCK-TYPING sobre modes que no controlem: els
        # de fàbrica antics i els del Laboratori (i els que escrigui qualsevol).
        # Un mode pot fer servir un d'aquests noms per a una altra cosa —la
        # plantilla melòdica del Laboratori té `self.playing = -1`, la nota
        # que sona— i `list(-1)` petava i s'enduia TOTA la resta de l'aturada,
        # `cleanup()` inclòs: la nota es quedava sonant. Cada bloc s'aïlla i
        # només s'escombra el que és de debò una col·lecció.
        _m = mgr.current_mode
        for _attr in ('active_notes', 'playing', 'notes_playing', 'current_chord'):
            _col = getattr(_m, _attr, None)
            if not isinstance(_col, (list, set, tuple)):
                continue
            for note in list(_col):
                try:
                    mgr.midi_out.send(NoteOff(note, 0))
                except Exception:
                    pass
            try:
                _col.clear()
            except Exception:
                pass

        _bg = getattr(_m, 'background_notes', None)
        if isinstance(_bg, dict):
            for note_info in list(_bg.values()):
                if isinstance(note_info, dict) and 'note' in note_info:
                    try:
                        mgr.midi_out.send(NoteOff(note_info['note'], 0))
                    except Exception:
                        pass

        _dr = getattr(_m, 'active_drones', None)
        if isinstance(_dr, (list, set, tuple)):
            for drone_info in list(_dr):
                if isinstance(drone_info, tuple) and len(drone_info) >= 1:
                    try:
                        mgr.midi_out.send(NoteOff(drone_info[0], 0))
                    except Exception:
                        pass
            try:
                _dr.clear()
            except Exception:
                pass

        # PERCUSSIÓ: quatre modes (groove, hardgroove, hardtechno, techno)
        # toquen pel canal 9 enviant el NoteOn DIRECTAMENT al port, o sigui
        # que no són a `tracked_notes`, i tanquen la nota amb un gate. Aturats
        # a mig gate, el note-off no arriba mai i el CC123 no basta: molts AU
        # l'ignoren. S'escombra el rang GM, però NOMÉS si el mode que deixes
        # declara que hi toca — un canvi de mode no és un STOP, i encarir-lo
        # per a tots seria tornar el pànic al camí calent.
        _perc = getattr(mgr.current_mode, 'CANAL_PERC', None)
        if _perc is not None:
            for note in range(_PERC[0], _PERC[1]):
                try:
                    off_p = NoteOff(note, 0)
                    off_p.channel = _perc
                    mgr.midi_out.send(off_p)
                except Exception:
                    pass

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


# Què escombra el pànic de l'STOP, canal per canal i amb el RANG que de debò
# hi pot sonar. L'escombrat explícit de NoteOff hi és per als instruments que
# IGNOREN l'All Notes Off (molts AU dins d'un DAW): és l'única cosa que
# garanteix silenci, i s'enviava NOMÉS al canal de sortida.
#
# Deu modes envien NoteOn directament al port amb `msg.channel = c`, sense
# passar per `BaseMode.send_note_on`: `tracked_notes` no en sap res i el seu
# note-off depèn d'un gate que, si atures a mig camí, no arriba mai. En un
# sinte que ignori el CC123 es quedaven sonant per sempre. Reportat: «alguns
# modes deixen remanent de so mort fins i tot després de l'stop».
#
# Per rang, no 128 per canal: el pànic ha de seguir sent CURT. Aquesta és la
# regla que va matar la versió antiga de >500 missatges i més d'un segon de
# bloqueig, i no la pot desfer un arranjament de fuites.
_PERC = (35, 82)       # percussió GM: Acoustic Bass Drum … Open Triangle

_ESCOMBRAT = (
    (None, 0, 128),    # canal de sortida: teclat i modes melòdics, tot el rang
    (9, _PERC[0], _PERC[1]),
    (1, 24, 121),      # ACCOMP_CHANNEL: l'acompanyament (24-96) i el MODE DE FONS (kbd_fons)
)


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
        from motor.base_mode import _note_off_msg
        off = _note_off_msg()
        off.velocity = 0
        # ELS CANALS QUE FEM SERVIR, no només el de sortida. Aquest escombrat
        # explícit hi és precisament per als instruments que IGNOREN l'All
        # Notes Off, i s'enviava només a `out_channel` (channel=None): les
        # notes que un mode de percussió havia deixat obertes al canal 9 no
        # les apagava ningú, ni amb STOP. Reportat: «alguns modes deixen
        # remanent de so mort en alguns moments fins i tot després de l'stop».
        #
        #   None → out_channel   (teclat i modes melòdics)
        #      9 → bateria GM    (mode_groove, techno, hardtechno, tormenta…)
        #      1 → ACCOMP_CHANNEL (accompaniment.py)
        #
        # 3×128 missatges, ~360 ms un sol cop en prémer STOP. La versió antiga
        # d'aquest pànic n'enviava més de 500 i bloquejava més d'un segon; la
        # diferència és que ara cada missatge serveix per a alguna cosa.
        for canal, primera, ultima in _ESCOMBRAT:
            for note in range(primera, ultima):
                off.note = note
                off.channel = canal
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
    from motor.mm_lifecycle import mm_unload_mode
    n = 0
    for mode_name in [x for x in list(mgr.modes.keys()) if x != 'Teclat']:
        try:
            if mm_unload_mode(mgr, mode_name):
                n += 1
        except Exception:
            pass
    return n


def _oblida_modul(nom_complet):
    """Treu un mòdul de sys.modules I del seu paquet.

    Les dues coses, sempre. L'import penja el submòdul com a ATRIBUT del
    paquet (`modes.mode_bit` → `modes.mode_bit`), i amb l'atribut viu el
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
        from motor.mm_update import mm_deactivate_efecte_temporal
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

    # Amb _oblida_modul, no amb `del sys.modules[...]` a seques: l'import penja
    # el submòdul com a ATRIBUT del paquet `modes`, i amb l'atribut viu el
    # bytecode queda referenciat encara que sys.modules ja no el tingui. Fins
    # ara aquesta purga no alliberava ni un byte, i és el botó d'emergència
    # justament per quan no queda RAM. Mesurat al dispositiu: un mòdul ocupa
    # al heap ~1,4 vegades la mida del seu .mpy (kbd_looper, 4,8 KB → 6.720 B).
    # Qui es purga i qui no ho decideix ara el NOM DEL PAQUET, no una llista
    # de noms a mà. Des que el motor viu a `motor/`, dins de `modes.` només hi
    # queden modes: el teclat, el gestor i la classe base són `motor.*` i no
    # entren aquí ni que es vulgui. Abans calia excloure'ls un per un, i una
    # llista així només es queda enrere.
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('modes.mode_'):
            _oblida_modul(module_name)

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


