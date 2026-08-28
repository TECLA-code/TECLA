"""Processament de botons per al Mode Teclat - modul separat per estalviar RAM"""
import time

_NEG_HARM_AXES = (3.5, 0.0, 2.0, 1.5, 6.0, 2.5, 4.5, 5.5)
_NEG_HARM_NAMES = ('Quinta', 'Unisonant', 'Tercera M', 'Tercera m', 'Trito', 'Quarta', 'Sexta M', 'Septima m')
_DIATONIC_FN_NAMES = {
    'diatonic': 'Diatonic',
    'sec_dominant': 'Dom.Sec.',
    'sec_leading': 'Sensible',
    'borrowed': 'Prestat',
    'subdominant_m': 'Sub.Men.',
    'tritone_sub': 'Triton',
    'dominant_chain': 'Cadena',
    'dim_passing': 'Dism.Pas',
    'neapolitan': 'Napol.',
}
_SCALE_NAMES = (
    'Major', 'Doric', 'Frigi', 'Lidi', 'Mixolidi', 'Menor', 'Locri',
    'Pentat.Maj', 'Pentat.Men', 'Japonesa', 'Egipcia', 'Arabiga', 'Hongaresa',
    'Lidia Dom', 'Alterada', 'Men.Melod', 'Bhairav', 'Todi',
    'Flamenca', 'Catalana', 'Frigia', 'Balcanica', 'Tons Senc', 'Harm.Maj')


def build_fn_mappings(kbd):
    fns = kbd.btn_functions
    kbd._fn_scale_btn = -1
    kbd._fn_ton_btn = -1
    kbd._fn_chord_btn = -1
    kbd._fn_arp_btn = -1
    kbd._fn_oct_dn_btn = -1
    kbd._fn_oct_up_btn = -1
    kbd._fn_neg_harm_btn = -1
    kbd._fn_diatonic_btn = -1
    kbd._fn_latch_btn = -1
    kbd._fn_looper_btn = -1
    kbd._fn_looper_q_btn = -1
    kbd._fn_looper_dub_btn = -1
    kbd._fn_voice_lead_btn = -1
    kbd._fn_synth_wave_btn = -1
    kbd._fn_accomp_btn = -1
    kbd._note_buttons = []
    kbd._note_btn_to_slot = {}
    slot = 0
    for i in range(min(len(fns), 15)):
        f = fns[i]
        if f == 'note':
            kbd._note_btn_to_slot[i] = slot
            kbd._note_buttons.append(i)
            slot += 1
        elif f == 'scale' and kbd._fn_scale_btn < 0:
            kbd._fn_scale_btn = i
        elif f == 'tonality' and kbd._fn_ton_btn < 0:
            kbd._fn_ton_btn = i
        elif f == 'chord' and kbd._fn_chord_btn < 0:
            kbd._fn_chord_btn = i
        elif f == 'arp' and kbd._fn_arp_btn < 0:
            kbd._fn_arp_btn = i
        elif f == 'octave_down' and kbd._fn_oct_dn_btn < 0:
            kbd._fn_oct_dn_btn = i
        elif f == 'octave_up' and kbd._fn_oct_up_btn < 0:
            kbd._fn_oct_up_btn = i
        elif f == 'neg_harmony' and kbd._fn_neg_harm_btn < 0:
            kbd._fn_neg_harm_btn = i
        elif f == 'diatonic' and kbd._fn_diatonic_btn < 0:
            kbd._fn_diatonic_btn = i
        elif f == 'latch' and kbd._fn_latch_btn < 0:
            kbd._fn_latch_btn = i
        elif f == 'looper' and kbd._fn_looper_btn < 0:
            kbd._fn_looper_btn = i
        elif f == 'looper_q' and kbd._fn_looper_q_btn < 0:
            kbd._fn_looper_q_btn = i
        elif f == 'looper_dub' and kbd._fn_looper_dub_btn < 0:
            kbd._fn_looper_dub_btn = i
        elif f == 'voice_lead' and kbd._fn_voice_lead_btn < 0:
            kbd._fn_voice_lead_btn = i
        elif f == 'synth_wave' and kbd._fn_synth_wave_btn < 0:
            kbd._fn_synth_wave_btn = i
        elif f == 'accomp' and kbd._fn_accomp_btn < 0:
            kbd._fn_accomp_btn = i


def process_keyboard_buttons(kbd, button_states):
    current_time = time.monotonic()
    n = min(len(button_states), 15)

    for btn_idx in range(n):
        if btn_idx == 12:
            continue
        cur = button_states[btn_idx] if btn_idx < len(button_states) else False
        prv = kbd.last_button_states[btn_idx] if btn_idx < len(kbd.last_button_states) else False
        if not (cur or prv):
            continue

        if cur and not prv:
            if btn_idx == kbd._fn_scale_btn:
                kbd._scale_btn_press_time = current_time
            elif btn_idx == kbd._fn_ton_btn:
                kbd._key_btn_press_time = current_time
            elif btn_idx == kbd._fn_chord_btn:
                kbd.chord_btn_press_time = current_time
            elif btn_idx == kbd._fn_arp_btn:
                kbd.arp_btn_press_time = current_time
            elif btn_idx == kbd._fn_oct_dn_btn:
                kbd.change_octave(-1)
            elif btn_idx == kbd._fn_oct_up_btn:
                kbd.change_octave(1)
            elif btn_idx == kbd._fn_neg_harm_btn:
                kbd._neg_harm_btn_press_time = current_time
            elif btn_idx == kbd._fn_diatonic_btn:
                kbd._diatonic_btn_press_time = current_time
            elif btn_idx == kbd._fn_latch_btn:
                # Toggle latch al moment de prémer (resposta immediata en directe)
                kbd.latch_active = not kbd.latch_active
                if kbd.latch_active:
                    print("∞ Latch ACTIVAT (les notes es mantenen en deixar anar)")
                else:
                    kbd.stop_all_notes()
                    print("∞ Latch DESACTIVAT")
            elif btn_idx == kbd._fn_looper_btn or btn_idx == kbd._fn_looper_q_btn:
                kbd._looper_btn_press_time = current_time
            elif btn_idx == kbd._fn_looper_dub_btn:
                kbd._dub_btn_press_time = current_time
            elif btn_idx == kbd._fn_voice_lead_btn:
                # Gest al deixar anar: tap = activa/cicla forma · llarga = desactiva
                kbd._voice_lead_press_time = current_time
            elif btn_idx == kbd._fn_accomp_btn:
                # Gest al deixar anar: tap = activa/cicla patró · llarga = desactiva
                kbd._accomp_btn_press_time = current_time
            elif btn_idx == kbd._fn_synth_wave_btn:
                # Cada clic cicla la forma d'ona del sinte (CC70 → motor d'àudio)
                idx = (getattr(kbd, '_synth_wave_idx', 0) + 1) % 4
                kbd._synth_wave_idx = idx
                kbd._send_cc(70, idx * 32)
                _wn = ('Sinus', 'Dent de serra', 'Triangle', 'Quadrada')
                print(f"∿ Forma d'ona: {_wn[idx]}")
            elif btn_idx < len(kbd.btn_functions) and kbd.btn_functions[btn_idx] == 'synth_cfg':
                # Config àudio (DUPLICABLE: cada tecla és un preset). Commuta: mentre
                # activa, els 3 potes editen el so segons el mapatge d'aquesta tecla.
                if getattr(kbd, '_audio_cfg_key', -1) == btn_idx:
                    kbd._audio_cfg_key = -1
                    print("🎛 Config àudio OFF")
                else:
                    kbd._audio_cfg_key = btn_idx
                    m = kbd.audio_pot_functions.get(str(btn_idx)) or {'x': 'Filtre', 'y': 'Ressonància', 'z': "Forma d'ona"}
                    print("🎛 Config àudio K%d: X=%s Y=%s Z=%s" % (btn_idx + 1, m.get('x'), m.get('y'), m.get('z')))

        elif not cur and prv:
            if btn_idx == kbd._fn_scale_btn:
                elapsed = current_time - kbd._scale_btn_press_time
                backward = elapsed >= 0.6
                if len(kbd.available_scales) > 0:
                    if backward:
                        kbd.scale_mode_index = (kbd.scale_mode_index - 1) % len(kbd.available_scales)
                    else:
                        kbd.scale_mode_index = (kbd.scale_mode_index + 1) % len(kbd.available_scales)
                    actual_scale_id = kbd.available_scales[kbd.scale_mode_index]
                    d = '◀' if backward else '▶'
                    if actual_scale_id >= 2000:
                        cs = kbd.config_manager.get_custom_scale_by_scale_id(actual_scale_id) if kbd.config_manager else None
                        sname = cs.get('name', 'Sense nom') if cs else f'#{actual_scale_id - 2000}'
                        print(f"🎼{d} Escala: {sname} ({kbd.scale_mode_index + 1}/{len(kbd.available_scales)})")
                    elif actual_scale_id >= 1000:
                        pg = kbd.config_manager.get_progression_by_scale_id(actual_scale_id) if kbd.config_manager else None
                        pname = pg.get('name', 'Sense nom') if pg else f'#{actual_scale_id - 1000}'
                        print(f"♪{d} Progressió: {pname} ({kbd.scale_mode_index + 1}/{len(kbd.available_scales)})")
                    else:
                        sname = _SCALE_NAMES[actual_scale_id] if actual_scale_id < len(_SCALE_NAMES) else f'#{actual_scale_id}'
                        print(f"🎼{d} {sname} ({kbd.scale_mode_index + 1}/{len(kbd.available_scales)})")
                    if getattr(kbd, '_accomp_active', False):
                        from modes.accompaniment import sync_context
                        sync_context(kbd)

            elif btn_idx == kbd._fn_ton_btn:
                elapsed = current_time - kbd._key_btn_press_time
                backward = elapsed >= 0.6
                nk = len(kbd.available_keys)
                if nk > 0:
                    kbd.key_index = (kbd.key_index + (-1 if backward else 1)) % nk
                    d = '◀' if backward else '▶'
                    print(f"🎵{d} Tonalitat: {kbd.available_keys[kbd.key_index]}")
                    if getattr(kbd, '_accomp_active', False):
                        from modes.accompaniment import sync_context
                        sync_context(kbd)

            elif btn_idx == kbd._fn_arp_btn:
                elapsed = current_time - kbd.arp_btn_press_time
                since_last = current_time - kbd._arp_last_release
                kbd._arp_last_release = current_time
                if elapsed >= 0.5:
                    kbd.stop_all_notes()
                    kbd.arp_mode_active = False
                    kbd.arp_notes = []
                    kbd.arp_button_order = []
                    kbd._arp_just_activated = False
                    print("🎶 Arpeggiador DESACTIVAT")
                elif not kbd.arp_mode_active:
                    kbd.arp_mode_active = True
                    kbd.arp_notes = []
                    kbd.arp_button_order = []
                    kbd._arp_pat_sel_last_val = None
                    kbd._arp_just_activated = True
                    if kbd.arp_mode_index not in kbd.available_arp_modes:
                        kbd.arp_mode_index = kbd.available_arp_modes[0] if kbd.available_arp_modes else 2
                    print(f"🎶 Arpeggiador: {kbd._get_arp_name(kbd.arp_mode_index)}")
                elif since_last < 0.4 and not kbd._arp_just_activated:
                    kbd._arp_just_activated = False
                    if kbd.available_arp_modes:
                        try:
                            ci = kbd.available_arp_modes.index(kbd.arp_mode_index)
                            kbd.arp_mode_index = kbd.available_arp_modes[(ci - 2) % len(kbd.available_arp_modes)]
                        except ValueError:
                            kbd.arp_mode_index = kbd.available_arp_modes[-1]
                        kbd.arp_index = 0; kbd.arp_direction = 1
                        kbd.arp_button_order = []; kbd._arp_pat_sel_last_val = None
                        print(f"🎶◀ Arpeggiador: {kbd._get_arp_name(kbd.arp_mode_index)}")
                else:
                    kbd._arp_just_activated = False
                    if kbd.available_arp_modes:
                        try:
                            ci = kbd.available_arp_modes.index(kbd.arp_mode_index)
                            kbd.arp_mode_index = kbd.available_arp_modes[(ci + 1) % len(kbd.available_arp_modes)]
                        except ValueError:
                            kbd.arp_mode_index = kbd.available_arp_modes[0]
                        kbd.arp_index = 0; kbd.arp_direction = 1
                        kbd.arp_button_order = []; kbd._arp_pat_sel_last_val = None
                        print(f"🎶▶ Arpeggiador: {kbd._get_arp_name(kbd.arp_mode_index)}")
                kbd._reapply_active_ccs()

            elif btn_idx == kbd._fn_neg_harm_btn:
                elapsed = current_time - kbd._neg_harm_btn_press_time
                since_last = current_time - kbd._neg_harm_last_release
                kbd._neg_harm_last_release = current_time
                if elapsed >= 0.5:
                    # NO tallar el so: les notes que sonen es deixen anar de forma
                    # natural en alliberar el botó (evita el tall brusc en directe).
                    kbd.neg_harmony_active = False
                    kbd._neg_harm_just_activated = False
                    print("↕ Harmonia Negativa DESACTIVADA")
                elif not kbd.neg_harmony_active:
                    kbd.neg_harmony_active = True
                    kbd._neg_harm_just_activated = True
                    print(f"↕ Harmonia Negativa: {_NEG_HARM_NAMES[kbd.neg_harmony_type % len(_NEG_HARM_AXES)]}")
                elif since_last < 0.4 and not kbd._neg_harm_just_activated:
                    kbd._neg_harm_just_activated = False
                    kbd.neg_harmony_type = kbd._cycle_neg_harm_type(-2)
                    print(f"↕◀ H.Neg: {_NEG_HARM_NAMES[kbd.neg_harmony_type % len(_NEG_HARM_AXES)]}")
                else:
                    kbd._neg_harm_just_activated = False
                    kbd.neg_harmony_type = kbd._cycle_neg_harm_type(1)
                    print(f"↕▶ H.Neg: {_NEG_HARM_NAMES[kbd.neg_harmony_type % len(_NEG_HARM_AXES)]}")

            elif btn_idx == kbd._fn_voice_lead_btn:
                # Tap = activa / cicla la forma de conducció · llarga = desactiva
                elapsed = current_time - getattr(kbd, '_voice_lead_press_time', current_time)
                vl_ids = getattr(kbd, 'available_vl_types', None) or ('proximitat',)
                if elapsed >= 0.5 and getattr(kbd, 'voice_lead_active', False):
                    kbd.voice_lead_active = False
                    print("Conduccio de veus DESACTIVADA")
                elif not getattr(kbd, 'voice_lead_active', False):
                    kbd.voice_lead_active = True
                    kbd._vl_prev_chord = None
                    kbd._vl_type_idx = 0
                    kbd._vl_type = vl_ids[0]
                    print("Conduccio: %s" % kbd._vl_type)
                else:
                    kbd._vl_type_idx = (getattr(kbd, '_vl_type_idx', 0) + 1) % len(vl_ids)
                    kbd._vl_type = vl_ids[kbd._vl_type_idx]
                    print("Conduccio: %s" % kbd._vl_type)

            elif btn_idx == kbd._fn_accomp_btn:
                # Base d'acompanyament (mòdul lazy: només s'importa si s'usa)
                from modes.accompaniment import handle_button as _accomp_gesture
                held = current_time - getattr(kbd, '_accomp_btn_press_time', current_time)
                _accomp_gesture(kbd, held, current_time)

            elif btn_idx == kbd._fn_looper_btn or btn_idx == kbd._fn_looper_q_btn:
                from modes.kbd_looper import handle_button
                held = current_time - getattr(kbd, '_looper_btn_press_time', current_time)
                handle_button(kbd, held, current_time,
                              quantized=(btn_idx == kbd._fn_looper_q_btn))

            elif btn_idx == kbd._fn_looper_dub_btn:
                from modes.kbd_looper import handle_dub_button
                held = current_time - getattr(kbd, '_dub_btn_press_time', current_time)
                handle_dub_button(kbd, held, current_time)

            elif btn_idx == kbd._fn_diatonic_btn:
                elapsed = current_time - kbd._diatonic_btn_press_time
                fns = kbd.available_diatonic_fns
                if not fns:
                    fns = ['diatonic']
                if elapsed >= 0.5:
                    # NO tallar el so: les notes sonant es deixen anar en alliberar el botó.
                    kbd.diatonic_fn_idx = -1
                    print("Δ Funcions Harmòniques DESACTIVAT")
                else:
                    kbd.diatonic_fn_idx = (kbd.diatonic_fn_idx + 1) % len(fns)
                    fn_name = _DIATONIC_FN_NAMES.get(fns[kbd.diatonic_fn_idx], fns[kbd.diatonic_fn_idx])
                    print(f"Δ {fn_name} ({kbd.diatonic_fn_idx + 1}/{len(fns)})")

            elif btn_idx == kbd._fn_chord_btn:
                elapsed = current_time - kbd.chord_btn_press_time
                since_last = current_time - kbd._chord_last_release
                kbd._chord_last_release = current_time
                if elapsed >= 0.5:
                    kbd.stop_all_notes()
                    kbd.chord_mode_active = False
                    kbd.chord_type_index = 0
                    kbd._chord_just_activated = False
                    print("Mode Acords DESACTIVAT")
                elif not kbd.chord_mode_active:
                    kbd.chord_mode_active = True
                    kbd._chord_just_activated = True
                    ct = kbd.available_chord_types[kbd.chord_type_index] if kbd.available_chord_types else 'Major'
                    print(f"Mode Acords ACTIVAT ({ct})")
                elif since_last < 0.4 and not kbd._chord_just_activated:
                    kbd._chord_just_activated = False
                    if kbd.available_chord_types:
                        nct = len(kbd.available_chord_types)
                        kbd.chord_type_index = (kbd.chord_type_index - 2) % nct
                        print(f"Acord: {kbd.available_chord_types[kbd.chord_type_index]}")
                else:
                    kbd._chord_just_activated = False
                    if kbd.available_chord_types:
                        kbd.chord_type_index = (kbd.chord_type_index + 1) % len(kbd.available_chord_types)
                        print(f"Acord: {kbd.available_chord_types[kbd.chord_type_index]}")
                kbd._reapply_active_ccs()

    if kbd.arp_mode_active:
        note_states = [button_states[i] if i < len(button_states) else False
                       for i in kbd._note_buttons]
        kbd._process_arpeggiator(note_states, current_time)
    else:
        for slot, btn_idx in enumerate(kbd._note_buttons):
            cur = button_states[btn_idx] if btn_idx < len(button_states) else False
            prv = kbd.last_button_states[btn_idx] if btn_idx < len(kbd.last_button_states) else False
            if cur and not prv:
                if kbd.latch_active and kbd.button_notes.get(btn_idx):
                    # Latch: re-prémer un botó que ja sona el commuta a OFF
                    kbd._note_off_for_button(btn_idx)
                elif kbd.chord_mode_active:
                    kbd._generate_chord_for_button(slot, btn_idx)
                else:
                    kbd._generate_notes_for_button(slot, btn_idx)
                if kbd.loop_state:  # ARMED/RECORDING: capturar l'acord generat
                    from modes.kbd_looper import record_press
                    record_press(kbd, btn_idx, current_time)
            elif not cur and prv:
                if kbd.loop_state:
                    from modes.kbd_looper import record_release
                    record_release(kbd, btn_idx, current_time)
                # Latch: en deixar anar, les notes es mantenen sonant
                if not kbd.latch_active:
                    kbd._note_off_for_button(btn_idx, from_release=True)
        if kbd.gate_enabled:
            kbd._process_gate(current_time)

    kbd.last_button_states = list(button_states[:15])
