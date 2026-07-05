"""Funcions d'arpegiador per al Mode Teclat - mòdul separat per estalviar RAM"""

import random

try:
    from music_constants import SCALES, ARP_DIRS, get_chord, note_offset
except ImportError:
    SCALES = ((0, 2, 4, 5, 7, 9, 11),)
    ARP_DIRS = ('up', 'down', 'pingpong', 'random', 'order',
                'alberti', 'alberti_alt', 'waltz', 'broken', 'tremolo',
                'zigzag', 'block', 'rolled', 'octaves', 'contrary', 'spread', 'custom')
    def get_chord(n): return (0, 4, 7)
    def note_offset(n): return 0

KEY_OFFSETS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


def _arp_notes_for_button(kbd, btn_idx, scale_intervals, key_offset, scale_id):
    """Notes que ha de generar un botó en mode arpegiador.

    Respecta, en aquest ordre de prioritat:
      - Funcions harmòniques (diatonic_fn_idx >= 0) -> acord de la funció
      - Mode acords (chord_mode_active) -> acord del tipus seleccionat
      - Per defecte -> nota simple de l'escala
    L'harmonia negativa s'aplica més tard, a _note_on (reflect_note).
    """
    n = len(scale_intervals)
    scale_degree = btn_idx % n
    octave_offset = btn_idx // n
    root_note = (kbd.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]

    fn_idx = getattr(kbd, 'diatonic_fn_idx', -1)
    if fn_idx >= 0:
        try:
            from modes.kbd_notes import _apply_harmonic_fn
            fns = getattr(kbd, 'available_diatonic_fns', [])
            fn = fns[fn_idx] if fns and fn_idx < len(fns) else 'diatonic'
            root_offset, chord_type = _apply_harmonic_fn(scale_intervals, scale_degree, fn, scale_id)
            root_note += root_offset
            intervals = chord_type if isinstance(chord_type, tuple) else get_chord(chord_type)
            return [max(0, min(127, root_note + iv)) for iv in intervals]
        except Exception:
            return [max(0, min(127, root_note))]
    elif kbd.chord_mode_active:
        chord_type = kbd.available_chord_types[kbd.chord_type_index] if kbd.available_chord_types else 'Major'
        return [max(0, min(127, root_note + iv)) for iv in get_chord(chord_type)]
    else:
        return [max(0, min(127, root_note))]


def get_arp_name(kbd, mode_index):
    if mode_index >= 2000:
        custom = kbd.config_manager.get_custom_arp_by_id(mode_index) if kbd.config_manager else None
        return custom.get('name', 'Custom') if custom else 'Custom'
    arp_names = {
        0: 'Amunt', 1: 'Avall', 2: 'Ping-Pong', 3: 'Aleatori', 4: 'Ordre',
        5: 'Alberti', 6: 'Alberti Alt', 7: 'Vals', 8: 'Trencat', 9: 'Tr\u00e8molo',
        10: 'Zig-Zag', 11: 'Block', 12: 'Rolled', 13: 'Octaves', 14: 'Contrari', 15: 'Spread'
    }
    return arp_names.get(mode_index, f'Mode {mode_index}')


def process_arpeggiator(kbd, button_states, current_time):
    pressed_buttons = [i for i in range(len(button_states)) if button_states[i]]

    if not pressed_buttons:
        kbd.stop_all_notes()
        kbd.arp_index = 0
        kbd.arp_notes = []
        kbd.arp_button_order = []
        return

    _arp_dir_check = 'custom' if kbd.arp_mode_index >= 2000 else ARP_DIRS[kbd.arp_mode_index]
    if _arp_dir_check == 'order':
        for btn in pressed_buttons:
            if btn not in kbd.arp_button_order:
                kbd.arp_button_order.append(btn)
        kbd.arp_button_order = [btn for btn in kbd.arp_button_order if btn in pressed_buttons]

    all_notes = []

    if len(kbd.available_scales) == 0:
        return

    current_scale_id = kbd.available_scales[kbd.scale_mode_index]

    if current_scale_id >= 2000:
        custom_scale = kbd.config_manager.get_custom_scale_by_scale_id(current_scale_id) if kbd.config_manager else None
        if not custom_scale:
            return

        notes_data = custom_scale.get('notes', [])
        for btn_idx in pressed_buttons:
            note_config = None
            for note in notes_data:
                if note.get('button') == btn_idx:
                    note_config = note
                    break

            if note_config:
                midi_note = note_config.get('midi_note')
                if midi_note is None:
                    note_name = note_config.get('note_name', 'C')
                    config_octave = note_config.get('octave', 4)
                    note_offset_val = note_offset(note_name)
                    midi_note = (kbd.octave + config_octave - 4 + 1) * 12 + note_offset_val
                else:
                    config_octave = midi_note // 12
                    note_in_octave = midi_note % 12
                    midi_note = (config_octave + kbd.octave - 4) * 12 + note_in_octave

                midi_note = max(0, min(127, midi_note))
                all_notes.append(midi_note)

    elif current_scale_id >= 1000:
        progression = kbd.config_manager.get_progression_by_scale_id(current_scale_id) if kbd.config_manager else None
        if not progression:
            return

        chords_data = progression.get('chords', [])
        for btn_idx in pressed_buttons:
            chord_config = None
            for chord in chords_data:
                if chord.get('button') == btn_idx:
                    chord_config = chord
                    break

            if chord_config:
                root_note_name = chord_config.get('root_note', 'C')
                chord_type = chord_config.get('chord_type', 'Major')
                config_octave = chord_config.get('octave', 4)

                root_offset = note_offset(root_note_name)
                base_note = (kbd.octave + config_octave - 4) * 12 + root_offset

                chord_intervals = get_chord(chord_type)
                for interval in chord_intervals:
                    note = base_note + interval
                    note = max(0, min(127, note))
                    all_notes.append(note)

    else:
        scale_intervals = SCALES[current_scale_id]
        key_offset = KEY_OFFSETS[kbd.key_index]
        for btn_idx in pressed_buttons:
            all_notes.extend(_arp_notes_for_button(kbd, btn_idx, scale_intervals, key_offset, current_scale_id))

    arp_direction = 'custom' if kbd.arp_mode_index >= 2000 else ARP_DIRS[kbd.arp_mode_index]

    if arp_direction == 'order' and current_scale_id < 1000:
        scale_intervals = SCALES[current_scale_id]
        key_offset = KEY_OFFSETS[kbd.key_index]
        ordered_notes = []
        for btn_idx in kbd.arp_button_order:
            ordered_notes.extend(_arp_notes_for_button(kbd, btn_idx, scale_intervals, key_offset, current_scale_id))
        kbd.arp_notes = ordered_notes
    else:
        all_notes = sorted(set(max(0, min(127, n)) for n in all_notes))
        kbd.arp_notes = all_notes

    if current_time - kbd.last_arp_time >= kbd.arp_speed:
        kbd.stop_all_notes()

        if kbd.arp_notes:
            play_arp_pattern(kbd, arp_direction)
            # Avança el rellotge per PASSOS EXACTES d'arp_speed (no 'now'): si es fa
            # servir 'now', la granularitat del bucle acumula error i els passos cauen
            # a múltiples desiguals d'arp_speed → el loop gravat surt amb SWING.
            kbd.last_arp_time += kbd.arp_speed
            if current_time - kbd.last_arp_time >= kbd.arp_speed:
                kbd.last_arp_time = current_time  # resync (1r dispar, canvi de tempo, pausa…)

    if kbd.gate_enabled:
        kbd._process_gate(current_time)


def play_arp_pattern(kbd, direction):
    if not kbd.arp_notes:
        return

    num_notes = len(kbd.arp_notes)

    if direction == 'random':
        current_note = kbd.arp_notes[random.randint(0, num_notes - 1)]
        kbd._note_on(current_note, -1)

    elif direction == 'up':
        current_note = kbd.arp_notes[kbd.arp_index % num_notes]
        kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'down':
        current_note = kbd.arp_notes[kbd.arp_index % num_notes]
        kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index - 1) % num_notes

    elif direction == 'pingpong':
        current_note = kbd.arp_notes[kbd.arp_index % num_notes]
        kbd._note_on(current_note, -1)
        kbd.arp_index += kbd.arp_direction
        if kbd.arp_index >= num_notes:
            kbd.arp_index = num_notes - 2
            kbd.arp_direction = -1
        elif kbd.arp_index < 0:
            kbd.arp_index = 1
            kbd.arp_direction = 1

    elif direction == 'order':
        current_note = kbd.arp_notes[kbd.arp_index % num_notes]
        kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'alberti':
        if num_notes >= 3:
            alberti_pattern = [0, 2, 1, 2]
            idx = alberti_pattern[kbd.arp_index % 4]
            current_note = kbd.arp_notes[min(idx, num_notes - 1)]
            kbd._note_on(current_note, -1)
            kbd.arp_index = (kbd.arp_index + 1) % 4
        else:
            current_note = kbd.arp_notes[kbd.arp_index % num_notes]
            kbd._note_on(current_note, -1)
            kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'alberti_alt':
        if num_notes >= 3:
            alberti_alt_pattern = [0, 1, 2, 1]
            idx = alberti_alt_pattern[kbd.arp_index % 4]
            current_note = kbd.arp_notes[min(idx, num_notes - 1)]
            kbd._note_on(current_note, -1)
            kbd.arp_index = (kbd.arp_index + 1) % 4
        else:
            current_note = kbd.arp_notes[kbd.arp_index % num_notes]
            kbd._note_on(current_note, -1)
            kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'waltz':
        if num_notes >= 3:
            if kbd.arp_index % 3 == 0:
                kbd._note_on(kbd.arp_notes[0], -1)
            else:
                for i in range(1, min(num_notes, 4)):
                    kbd._note_on(kbd.arp_notes[i], -1)
            kbd.arp_index = (kbd.arp_index + 1) % 3
        else:
            current_note = kbd.arp_notes[kbd.arp_index % num_notes]
            kbd._note_on(current_note, -1)
            kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'broken':
        if num_notes >= 3:
            broken_pattern = [0, 1, 2, 0, 2, 1]
            idx = broken_pattern[kbd.arp_index % 6]
            current_note = kbd.arp_notes[min(idx, num_notes - 1)]
            kbd._note_on(current_note, -1)
            kbd.arp_index = (kbd.arp_index + 1) % 6
        else:
            current_note = kbd.arp_notes[kbd.arp_index % num_notes]
            kbd._note_on(current_note, -1)
            kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'tremolo':
        if num_notes >= 2:
            tremolo_pattern = [0, 1]
            idx = tremolo_pattern[kbd.arp_index % 2]
            current_note = kbd.arp_notes[idx]
            kbd._note_on(current_note, -1)
            kbd.arp_index = (kbd.arp_index + 1) % 2
        else:
            kbd._note_on(kbd.arp_notes[0], -1)

    elif direction == 'zigzag':
        if kbd.arp_index % 2 == 0:
            idx = kbd.arp_index // 2
        else:
            idx = (kbd.arp_index // 2) + 1
        current_note = kbd.arp_notes[idx % num_notes]
        kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index + 1) % (num_notes * 2)

    elif direction == 'block':
        for note in kbd.arp_notes:
            kbd._note_on(note, -1)
        kbd.arp_index = 0

    elif direction == 'rolled':
        current_note = kbd.arp_notes[kbd.arp_index % num_notes]
        kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'octaves':
        current_note = kbd.arp_notes[kbd.arp_index % num_notes]
        kbd._note_on(current_note, -1)
        if current_note + 12 <= 127:
            kbd._note_on(current_note + 12, -1)
        kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'contrary':
        mid_point = num_notes // 2
        if kbd.arp_index < mid_point:
            current_note = kbd.arp_notes[kbd.arp_index]
        else:
            idx = num_notes - 1 - (kbd.arp_index - mid_point)
            current_note = kbd.arp_notes[idx]
        kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index + 1) % num_notes

    elif direction == 'spread':
        jump = max(2, num_notes // 3)
        current_note = kbd.arp_notes[kbd.arp_index % num_notes]
        kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index + jump) % num_notes

    elif direction == 'custom':
        custom_pattern = kbd.config_manager.get_custom_arp_by_id(kbd.arp_mode_index) if kbd.config_manager else None
        sequence = custom_pattern.get('sequence', [0]) if custom_pattern else [0]
        if not sequence:
            sequence = [0]
        idx = sequence[kbd.arp_index % len(sequence)]
        if idx != -1 and idx is not None:
            current_note = kbd.arp_notes[min(idx, num_notes - 1)]
            kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index + 1) % len(sequence)

    else:
        current_note = kbd.arp_notes[kbd.arp_index % num_notes]
        kbd._note_on(current_note, -1)
        kbd.arp_index = (kbd.arp_index + 1) % num_notes
