"""Generacio de notes i acords per al Mode Teclat - modul separat per estalviar RAM"""

try:
    from music_constants import SCALES, get_chord, note_offset
except ImportError:
    SCALES = ((0, 2, 4, 5, 7, 9, 11),)
    _CN = ('Major','m','7','maj7','m7','dim','aug','sus4','sus2','m7b5','add9','6','add11','add13','9','9#5','9b5','9#11','11','13','13b9','13#9','7b9','7#9','7sus4','7b13','69','m9','m11','m13','m69')
    _CI = ((0,4,7),(0,3,7),(0,4,7,10),(0,4,7,11),(0,3,7,10),(0,3,6),(0,4,8),(0,5,7),(0,2,7),(0,3,6,10),(0,4,7,14),(0,4,7,9),(0,4,7,17),(0,4,7,21),(0,4,7,10,14),(0,4,8,10,14),(0,4,6,10,14),(0,4,7,10,14,18),(0,4,7,10,14,17),(0,4,7,10,14,21),(0,4,7,10,13,21),(0,4,7,10,15,21),(0,4,7,10,13),(0,4,7,10,15),(0,5,7,10),(0,4,7,10,20),(0,4,7,9,14),(0,3,7,10,14),(0,3,7,10,14,17),(0,3,7,10,14,21),(0,3,7,9,14))
    def get_chord(n):
        try: return _CI[_CN.index(n)]
        except: return (0, 4, 7)
    def note_offset(n):
        _N = ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')
        try: return _N.index(n)
        except: return 0

from adafruit_midi.note_on import NoteOn

_KEY_OFFSET = {'C':0,'C#':1,'D':2,'Eb':3,'E':4,'F':5,'F#':6,'G':7,'Ab':8,'A':9,'Bb':10,'B':11}
_NEG_HARM_AXES = (3.5, 0.0, 2.0, 1.5, 6.0, 2.5, 4.5, 5.5)


def cycle_neg_harm_type(kbd, step):
    ids = kbd.available_neg_harm_ids
    if not ids:
        return (kbd.neg_harmony_type + step) % len(_NEG_HARM_AXES)
    n = len(ids)
    ci = 0
    for j in range(n):
        if ids[j] == kbd.neg_harmony_type:
            ci = j
            break
    return ids[(ci + step) % n]


def reflect_note(kbd, note):
    key_offset = _KEY_OFFSET.get(
        kbd.available_keys[kbd.key_index] if kbd.key_index < len(kbd.available_keys) else 'C', 0)
    axis = key_offset + _NEG_HARM_AXES[kbd.neg_harmony_type % len(_NEG_HARM_AXES)]
    note_pc = note % 12
    reflected_pc = int(round(2.0 * axis - note_pc)) % 12
    new_note = (note // 12) * 12 + reflected_pc
    if new_note - note > 6:
        new_note -= 12
    elif note - new_note > 6:
        new_note += 12
    return max(0, min(127, new_note))


def generate_notes_for_button(kbd, slot, btn_idx):
    if len(kbd.available_scales) == 0:
        return
    if getattr(kbd, 'diatonic_fn_idx', -1) >= 0:
        generate_chord_for_button(kbd, slot, btn_idx)
        return
    current_scale_id = kbd.available_scales[kbd.scale_mode_index]
    if current_scale_id >= 2000:
        custom_scale = kbd.config_manager.get_custom_scale_by_scale_id(current_scale_id) if kbd.config_manager else None
        if custom_scale:
            generate_note_from_custom_scale(kbd, slot, btn_idx, custom_scale)
        else:
            print(f"Error: Escala {current_scale_id} no trobada")
    elif current_scale_id >= 1000:
        progression = kbd.config_manager.get_progression_by_scale_id(current_scale_id) if kbd.config_manager else None
        if progression:
            generate_chord_from_progression(kbd, slot, btn_idx, progression)
        else:
            print(f"Error: Progressio {current_scale_id} no trobada")
    else:
        scale_intervals = SCALES[current_scale_id]
        key_offset = _KEY_OFFSET.get(kbd.available_keys[kbd.key_index], 0)
        scale_degree = slot % len(scale_intervals)
        octave_offset = slot // len(scale_intervals)
        base_note = (kbd.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
        base_note = max(0, min(127, base_note))
        kbd._note_on(base_note, btn_idx)


def generate_chord_from_progression(kbd, slot, btn_idx, progression):
    if not progression:
        return
    kbd._note_off_for_button(btn_idx)
    chords = progression.get('chords', [])
    chord_config = None
    for chord in chords:
        if chord.get('button') == slot:
            chord_config = chord
            break
    if not chord_config:
        return
    root_note_name = chord_config.get('root_note', 'C')
    chord_type = chord_config.get('chord_type', 'Major')
    config_octave = chord_config.get('octave', 4)
    root_offset_val = note_offset(root_note_name)
    base_note = (kbd.octave + config_octave - 4) * 12 + root_offset_val
    chord_intervals = get_chord(chord_type)
    _send_chord(kbd, [base_note + i for i in chord_intervals], btn_idx)


def generate_note_from_custom_scale(kbd, slot, btn_idx, custom_scale):
    if not custom_scale:
        return
    kbd._note_off_for_button(btn_idx)
    notes = custom_scale.get('notes', [])
    note_config = None
    for note in notes:
        if note.get('button') == slot:
            note_config = note
            break
    if not note_config:
        return
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
    kbd._note_on(midi_note, btn_idx)


def generate_chord_from_custom_scale(kbd, slot, btn_idx, custom_scale):
    if not custom_scale:
        return
    kbd._note_off_for_button(btn_idx)
    notes = custom_scale.get('notes', [])
    note_config = None
    for note in notes:
        if note.get('button') == slot:
            note_config = note
            break
    if not note_config:
        return
    midi_note = note_config.get('midi_note')
    if midi_note is None:
        note_name = note_config.get('note_name', 'C')
        octave = note_config.get('octave', 4)
        note_offset_val = note_offset(note_name)
        midi_note = (octave + 1) * 12 + note_offset_val
    midi_note = max(0, min(127, midi_note))
    _send_chord(kbd, [midi_note, midi_note + 4, midi_note + 7], btn_idx)


def _send_chord(kbd, chord_notes, btn_idx):
    """Camí únic d'enviament d'acords: clamp + harmonia negativa +
    conducció de veus (si està activa) + NoteOn amb tracking."""
    final_notes = []
    for note in chord_notes:
        note = max(0, min(127, note))
        if kbd.neg_harmony_active:
            note = reflect_note(kbd, note)
        final_notes.append(note)

    if getattr(kbd, 'voice_lead_active', False):
        from modes.kbd_voicelead import apply_voice_leading
        final_notes = apply_voice_leading(kbd, final_notes)

    for i, note in enumerate(final_notes):
        try:
            kbd.midi.send(NoteOn(note, kbd.velocity))
            kbd.active_notes.add(note)
            kbd.button_notes[btn_idx].add(note)
            if i == 0:
                kbd._update_pwm_for_note(note)
        except Exception as e:
            print(f"Error tocant acord: {e}")


_MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)
_MINOR_QUALITIES = ('m', 'dim', 'Major', 'm', 'm', 'Major', 'Major')

# Qualitats diatòniques per a cada ID d'escala (7 modes + altres 7-notes)
_DIATONIC_QUALITIES = {
    0:  ('Major', 'm',     'm',     'Major', 'Major', 'm',     'dim'),    # Jònica
    1:  ('m',     'm',     'Major', 'Major', 'm',     'dim',   'Major'),  # Dòrica
    2:  ('m',     'Major', 'Major', 'm',     'dim',   'Major', 'm'),      # Frígia
    3:  ('Major', 'Major', 'm',     'dim',   'Major', 'm',     'm'),      # Lídia
    4:  ('Major', 'm',     'dim',   'Major', 'm',     'm',     'Major'),  # Mixolídia
    5:  ('m',     'dim',   'Major', 'm',     'm',     'Major', 'Major'),  # Eòlica
    6:  ('dim',   'Major', 'm',     'm',     'Major', 'Major', 'm'),      # Lòcria
    11: ('Major', 'dim',   'aug',   'm',     'Major', 'Major', 'dim'),    # H. Harmònica
    15: ('m',     'dim',   'Major', 'Major', 'Major', 'dim',   'dim'),    # Mel. Menor
    23: ('Major', 'm',     'aug',   'Major', 'm',     'dim',   'Major'),  # Harm. Major
}


def _diatonic_chord_type(scale_intervals, degree, scale_id=None):
    d = degree % len(scale_intervals)
    if scale_id is not None and scale_id in _DIATONIC_QUALITIES:
        q = _DIATONIC_QUALITIES[scale_id]
        return q[d % len(q)]
    n = len(scale_intervals)
    if n < 3:
        return 'Major'
    root = scale_intervals[d]
    third = scale_intervals[(d + 2) % n]
    fifth = scale_intervals[(d + 4) % n]
    third_iv = (third - root) % 12
    fifth_iv = (fifth - root) % 12
    if third_iv == 4 and fifth_iv == 7:
        return 'Major'
    elif third_iv == 3 and fifth_iv == 7:
        return 'm'
    elif third_iv == 3 and fifth_iv == 6:
        return 'dim'
    elif third_iv == 4 and fifth_iv == 8:
        return 'aug'
    return 'Major'


_DIATONIC_7TH = {
    0: ('maj7', 'm7',    'm7',    'maj7', '7',    'm7',    'm7b5'),  # Jònica
    1: ('m7',   'm7',    'maj7',  '7',    'm7',   'm7b5',  'maj7'),  # Dòrica
    2: ('m7',   'maj7',  '7',     'm7',   'm7b5', 'maj7',  'm7'),    # Frígia
    3: ('maj7', '7',     'm7',    'm7b5', 'maj7', 'm7',    'm7'),    # Lídia
    4: ('7',    'm7',    'm7b5',  'maj7', 'm7',   'm7',    'maj7'),  # Mixolídia
    5: ('m7',   'm7b5',  'maj7',  'm7',   'm7',   'maj7',  '7'),     # Eòlica
    6: ('m7b5', 'maj7',  'm7',    'm7',   'maj7', '7',     'm7'),    # Lòcria
}


def _diatonic_7th_type(scale_intervals, degree, scale_id=None):
    n = len(scale_intervals)
    d = degree % n
    if scale_id is not None and scale_id in _DIATONIC_7TH:
        q = _DIATONIC_7TH[scale_id]
        return q[d % len(q)]
    if n < 7:
        return _diatonic_chord_type(scale_intervals, d, scale_id)
    root    = scale_intervals[d]
    third   = scale_intervals[(d + 2) % n]
    fifth   = scale_intervals[(d + 4) % n]
    seventh = scale_intervals[(d + 6) % n]
    t = (third   - root) % 12
    f = (fifth   - root) % 12
    s = (seventh - root) % 12
    if t == 4 and f == 7 and s == 11: return 'maj7'
    if t == 4 and f == 7 and s == 10: return '7'
    if t == 3 and f == 7 and s == 10: return 'm7'
    if t == 3 and f == 6 and s == 10: return 'm7b5'
    return _diatonic_chord_type(scale_intervals, d, scale_id)


def _apply_harmonic_fn(scale_intervals, scale_degree, fn, scale_id=None):
    """Retorna (root_semitone_offset, chord_type_or_tuple) per a la funcio harmonica fn."""
    n = len(scale_intervals)
    d = scale_degree % n

    if fn == 'diatonic' or not fn:
        return 0, _diatonic_chord_type(scale_intervals, d, scale_id)

    elif fn == 'sec_dominant':
        return 7, '7'

    elif fn == 'sec_leading':
        return -1, 'dim'

    elif fn == 'borrowed':
        d7 = d % 7
        if n >= 7:
            borrowed_root = _MINOR_SCALE[d7]
            current_root = scale_intervals[d] % 12
            offset = (borrowed_root - current_root) % 12
            if offset > 6:
                offset -= 12
            return offset, _MINOR_QUALITIES[d7]
        return 0, 'm'

    elif fn == 'subdominant_m':
        d7 = d % 7
        if d7 == 3:
            return 0, 'm'
        return 0, _diatonic_chord_type(scale_intervals, d)

    elif fn == 'tritone_sub':
        return 6, '7'

    elif fn == 'dominant_chain':
        return 0, '7'

    elif fn == 'dim_passing':
        next_d = (d + 1) % n
        curr_root = scale_intervals[d]
        next_root = scale_intervals[next_d]
        if next_d == 0:
            next_root += 12
        offset = (next_root - curr_root) - 1
        return offset, 'dim'

    elif fn == 'neapolitan':
        return -1, 'Major'

    elif fn == 'aug6_ger':
        return -4, '7'

    elif fn == 'aug6_it':
        return -4, (0, 4, 10)

    elif fn == 'aug6_fr':
        return -4, (0, 4, 6, 10)

    elif fn == 'tonics':
        return 0, _diatonic_7th_type(scale_intervals, d, scale_id)

    elif fn == 'modulation':
        next_d = (d + 1) % n
        curr_root = scale_intervals[d]
        next_root = scale_intervals[next_d]
        if next_d == 0:
            next_root += 12
        offset = (next_root - curr_root) + 7
        if offset > 12:
            offset -= 12
        return offset, '7'

    return 0, _diatonic_chord_type(scale_intervals, d, scale_id)


def generate_chord_for_button(kbd, slot, btn_idx):
    if len(kbd.available_scales) == 0:
        return
    current_scale_id = kbd.available_scales[kbd.scale_mode_index]
    if current_scale_id >= 2000:
        custom_scale = kbd.config_manager.get_custom_scale_by_scale_id(current_scale_id) if kbd.config_manager else None
        if custom_scale:
            generate_chord_from_custom_scale(kbd, slot, btn_idx, custom_scale)
        return
    if current_scale_id >= 1000:
        progression = kbd.config_manager.get_progression_by_scale_id(current_scale_id) if kbd.config_manager else None
        if progression:
            generate_chord_from_progression(kbd, slot, btn_idx, progression)
        return
    scale_intervals = SCALES[current_scale_id]
    key_offset = _KEY_OFFSET.get(kbd.available_keys[kbd.key_index], 0)
    kbd._note_off_for_button(btn_idx)
    scale_degree = slot % len(scale_intervals)
    octave_offset = slot // len(scale_intervals)
    root_note = (kbd.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
    fn_idx = getattr(kbd, 'diatonic_fn_idx', -1)
    if fn_idx >= 0:
        fns = getattr(kbd, 'available_diatonic_fns', [])
        fn = fns[fn_idx] if fns and fn_idx < len(fns) else 'diatonic'
        root_offset, chord_type = _apply_harmonic_fn(scale_intervals, scale_degree, fn, current_scale_id)
        root_note += root_offset
        print(f"Δ grau {scale_degree}: {fn} → {chord_type}")
    else:
        chord_type = kbd.available_chord_types[kbd.chord_type_index] if kbd.available_chord_types else 'Major'
    if isinstance(chord_type, tuple):
        chord_intervals = chord_type
    else:
        chord_intervals = get_chord(chord_type)
    chord_notes = [root_note + interval for interval in chord_intervals]
    _send_chord(kbd, chord_notes, btn_idx)
