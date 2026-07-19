"""Tests de la conducció de veus (kbd_voicelead.py)."""
import pytest

from conftest import FakeMidiOut

from modes.mode_keyboard import KeyboardMode
from modes.kbd_buttons import build_fn_mappings, process_keyboard_buttons
from modes.kbd_voicelead import apply_voice_leading

OFF = [False] * 15


@pytest.fixture
def kbd():
    k = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)
    k.available_scales = [0]            # escala major
    k.available_keys = ['C']
    k.key_index = 0
    k.available_chord_types = ['Major']
    k.chord_type_index = 0
    k.octave = 4
    k.btn_functions = ['note'] * 8 + ['scale', 'voice_lead', 'chord', 'arp',
                                      'modes_layer', 'octave_down', 'octave_up', 'stop']
    build_fn_mappings(k)
    return k


def _press_release(kbd, i):
    s = list(OFF); s[i] = True
    process_keyboard_buttons(kbd, s)
    process_keyboard_buttons(kbd, OFF)


# ── Unitat: l'algorisme ──────────────────────────────────────────────────────

def test_primer_acord_no_es_modifica(kbd):
    notes = apply_voice_leading(kbd, [48, 52, 55])  # Do M
    assert notes == [48, 52, 55]
    assert kbd._vl_prev_chord == [48, 52, 55]


def test_c_a_g_tria_la_inversio_propera(kbd):
    """El cas de manual: C (do-mi-sol) → G no salta a sol-si-re;
    es queda a si-re-sol (2a inversió), moviment total de 3 semitons."""
    apply_voice_leading(kbd, [48, 52, 55])          # C: do3-mi3-sol3
    result = apply_voice_leading(kbd, [55, 59, 62])  # G en posició fonamental
    assert result == [47, 50, 55]                    # si2-re3-sol3


def test_acord_repetit_es_identic(kbd):
    apply_voice_leading(kbd, [48, 52, 55])
    assert apply_voice_leading(kbd, [48, 52, 55]) == [48, 52, 55]


def test_conserva_les_classes_de_altura(kbd):
    apply_voice_leading(kbd, [48, 52, 55])
    result = apply_voice_leading(kbd, [53, 57, 60])  # F M
    assert sorted(n % 12 for n in result) == sorted(n % 12 for n in [53, 57, 60])


def test_progressio_completa_es_mante_compacta(kbd):
    """I-V-vi-IV: cap acord no s'ha de moure més d'una octava del primer."""
    apply_voice_leading(kbd, [48, 52, 55])           # C
    for chord in ([55, 59, 62], [57, 60, 64], [53, 57, 60]):  # G, Am, F
        result = apply_voice_leading(kbd, chord)
        assert all(36 <= n <= 67 for n in result), result


# ── Funció de botó i integració ──────────────────────────────────────────────

def test_tap_activa_i_cicla_llarga_desactiva(kbd):
    """Gest del botó: tap = activa / cicla la forma · premuda llarga = desactiva."""
    kbd.available_vl_types = ['proximitat', 'comu']
    assert not kbd.voice_lead_active
    _press_release(kbd, 9)                    # tap → activa (primera forma)
    assert kbd.voice_lead_active
    assert kbd._vl_type == 'proximitat'
    _press_release(kbd, 9)                    # tap → cicla forma, segueix activa
    assert kbd.voice_lead_active
    assert kbd._vl_type == 'comu'
    s = list(OFF); s[9] = True                # premuda llarga → desactiva
    process_keyboard_buttons(kbd, s)
    kbd._voice_lead_press_time -= 1.0
    process_keyboard_buttons(kbd, OFF)
    assert not kbd.voice_lead_active


def test_activar_reseteja_la_referencia(kbd):
    kbd._vl_prev_chord = [48, 52, 55]
    _press_release(kbd, 9)
    assert kbd._vl_prev_chord is None


def test_integracio_mode_acords(kbd):
    """Amb chord mode + conducció de veus, el segon acord surt re-voicejat."""
    kbd.chord_mode_active = True
    _press_release(kbd, 9)                 # voice_lead ON
    _press_release(kbd, 0)                 # C major: 48-52-55
    assert kbd._vl_prev_chord == [48, 52, 55]
    s = list(OFF); s[4] = True             # grau 5 (sol) → G major
    process_keyboard_buttons(kbd, s)
    assert kbd.button_notes[4] == {47, 50, 55}  # 2a inversió, no 55-59-62
    process_keyboard_buttons(kbd, OFF)


def test_desactivat_no_toca_res(kbd):
    kbd.chord_mode_active = True
    _press_release(kbd, 0)
    s = list(OFF); s[4] = True
    process_keyboard_buttons(kbd, s)
    assert kbd.button_notes[4] == {55, 59, 62}  # posició fonamental intacta
    process_keyboard_buttons(kbd, OFF)

# ── Formes NOVES (v3.2): inversions integrades + patrons addicionals ─────────

def _vl(kbd, tipus, seq):
    """Aplica la forma `tipus` a una seqüència d'acords; retorna els voicings."""
    kbd.voice_lead_active = True
    kbd._vl_type = tipus
    kbd._vl_prev_chord = None
    if hasattr(kbd, '_vl_pendol_up'):
        del kbd._vl_pendol_up
    return [apply_voice_leading(kbd, list(ch)) for ch in seq]


def test_fonamental_posa_el_baix_a_la_fonamental(kbd):
    # C M → F M (notes en ordre d'intervals: fonamental primer)
    out = _vl(kbd, 'fonamental', [[48, 52, 55], [53, 57, 60]])
    assert min(out[1]) % 12 == 5, f"el baix hauria de ser F: {out[1]}"


def test_inv1_posa_el_baix_a_la_tercera(kbd):
    # F M després de C M: 1a inversió → baix = A (la 3a de F)
    out = _vl(kbd, 'inv1', [[48, 52, 55], [53, 57, 60]])
    assert min(out[1]) % 12 == 9, f"el baix hauria de ser A (3a de F): {out[1]}"


def test_inv2_posa_el_baix_a_la_quinta(kbd):
    # F M després de C M: 2a inversió → baix = C (la 5a de F)
    out = _vl(kbd, 'inv2', [[48, 52, 55], [53, 57, 60]])
    assert min(out[1]) % 12 == 0, f"el baix hauria de ser C (5a de F): {out[1]}"


def test_descendent_les_veus_baixen(kbd):
    out = _vl(kbd, 'descendent', [[60, 64, 67], [62, 66, 69]])
    assert min(out[1]) < min(out[0]), f"el baix hauria de baixar: {out}"


def test_tancat_es_mes_compacte_que_obert(kbd):
    seq = [[48, 52, 55], [53, 57, 60]]
    tancat = _vl(kbd, 'tancat', seq)[1]
    obert = _vl(kbd, 'obert', seq)[1]
    assert (max(tancat) - min(tancat)) <= (max(obert) - min(obert))


def test_drop2_baixa_una_veu_una_octava(kbd):
    # Amb 4 veus el drop2 té un span > que el voicing tancat de les mateixes pc
    out = _vl(kbd, 'drop2', [[48, 52, 55, 59], [53, 57, 60, 64]])
    span = max(out[1]) - min(out[1])
    assert span >= 12, f"un drop2 de 4 veus ha de superar l'octava: {out[1]}"
    # les classes d'altura es conserven
    assert sorted(n % 12 for n in out[1]) == sorted(n % 12 for n in [53, 57, 60, 64])


def test_pendol_alterna_pujar_i_baixar(kbd):
    seq = [[60, 64, 67]] + [[60, 64, 67], [62, 65, 69], [60, 64, 67], [62, 65, 69]]
    out = _vl(kbd, 'pendol', seq)
    baixos = [min(v) for v in out]
    dirs = [1 if baixos[i+1] >= baixos[i] else -1 for i in range(len(baixos)-1)]
    assert 1 in dirs and -1 in dirs, f"el pèndol ha d'alternar direccions: {baixos}"


def test_totes_les_formes_conserven_les_classes_daltura(kbd):
    from modes.kbd_voicelead import VL_TYPE_IDS
    for tipus in VL_TYPE_IDS:
        out = _vl(kbd, tipus, [[48, 52, 55], [50, 53, 57], [55, 59, 62]])
        for orig, veu in zip([[48, 52, 55], [50, 53, 57], [55, 59, 62]], out):
            assert sorted(n % 12 for n in veu) == sorted(n % 12 for n in orig), \
                f"{tipus}: classes d'altura canviades ({orig} → {veu})"
