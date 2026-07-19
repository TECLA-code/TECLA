"""Tests del motor d'acompanyament Python (modes/accompaniment.py).

Mirall dels asserts de tools/test_accompaniment.mjs: patrons que segueixen la
tonalitat, motor amb rellotge injectat, canals independents i note-offs.
"""
from conftest import FakeMidiOut
from modes.accompaniment import Accompaniment, PATTERNS

CTX = {'root': 60, 'scale': (0, 2, 4, 5, 7, 9, 11)}   # C major


def _ons(out):
    return [(m.note, getattr(m, 'channel', 0)) for m in out.sent if 'NoteOn' in type(m).__name__]


def _offs(out):
    return [(m.note, getattr(m, 'channel', 0)) for m in out.sent if 'NoteOff' in type(m).__name__]


# ── Patrons (segueixen la tonalitat) ─────────────────────────────────────────

def test_pols_tonica_greu_a_la_negra():
    assert PATTERNS['pols'](0, CTX, None)[0][0] == 36   # tònica greu
    assert PATTERNS['pols'](1, CTX, None) == ()          # res fora de la negra


def test_baix_tonica_quinta_octava():
    assert PATTERNS['baix'](0, CTX, None)[0][0] == 48
    assert PATTERNS['baix'](4, CTX, None)[0][0] == 55
    assert PATTERNS['baix'](12, CTX, None)[0][0] == 60


def test_baix_segueix_la_tonica():
    ctx_d = {'root': 62, 'scale': CTX['scale']}
    assert PATTERNS['baix'](0, ctx_d, None)[0][0] == 50   # D → 50


def test_arpegi_triada_diatonica():
    notes = [PATTERNS['arpegi'](n, CTX, None)[0][0] for n in (0, 2, 4)]
    assert notes == [60, 64, 67]


def test_sequencia_dins_l_escala():
    in_scale = {60 + 12 + i for i in CTX['scale']}
    ev = PATTERNS['sequencia'](0, CTX, lambda: 0.5)
    assert len(ev) == 1 and ev[0][0] in in_scale


# ── Motor (rellotge injectat + canals + note-offs) ───────────────────────────

def test_motor_baix_canal_i_sequencia():
    out = FakeMidiOut()
    acc = Accompaniment(out)
    acc.set_tempo(120)                    # step_s = 0.125
    acc.set_context(60, CTX['scale'])
    acc.add_pattern('baix', 8, now=0.0)
    for s in range(17):
        acc.tick(s * acc.step_s)
    ons = _ons(out)
    assert len(ons) >= 4                                  # un compàs de baix
    assert all(ch == 8 for _n, ch in ons)                 # tot pel canal 8
    assert [n for n, _c in ons[:4]] == [48, 55, 48, 60]   # tònica/quinta/tònica/octava
    assert len(_offs(out)) > 0                            # note-offs programats


def test_patrons_independents_per_canal():
    out = FakeMidiOut()
    acc = Accompaniment(out)
    acc.set_tempo(120)
    acc.add_pattern('baix', 8, now=0.0)
    acc.add_pattern('pols', 9, now=0.0)
    for s in range(9):
        acc.tick(s * acc.step_s)
    ons = _ons(out)
    assert any(ch == 9 and n == 36 for n, ch in ons)      # pols pel canal 9
    assert any(ch == 8 for _n, ch in ons)                 # baix pel canal 8


def test_clear_envia_offs_pendents():
    out = FakeMidiOut()
    acc = Accompaniment(out)
    acc.add_pattern('arpegi', 10, now=0.0)
    acc.tick(0.0)
    n_offs_abans = len(_offs(out))
    acc.clear()
    assert not acc.patterns
    assert len(_offs(out)) > n_offs_abans                 # offs pendents enviats


def test_remove_pattern_atura_el_seu_canal():
    out = FakeMidiOut()
    acc = Accompaniment(out)
    acc.add_pattern('baix', 8, now=0.0)
    acc.add_pattern('pols', 9, now=0.0)
    acc.tick(0.0)
    acc.remove_pattern(8)
    assert all(p['channel'] != 8 for p in acc.patterns)
    assert any(ch == 8 for _n, ch in _offs(out))          # offs del canal 8 enviats
    assert acc._running                                   # el pols continua


def test_catchup_guard_no_allau():
    out = FakeMidiOut()
    acc = Accompaniment(out)
    acc.set_tempo(120)
    acc.add_pattern('pols', 8, now=0.0)
    acc.tick(0.0)
    n0 = len(_ons(out))
    acc.tick(100.0)                                       # "parón" de 100s
    assert len(_ons(out)) - n0 <= 2                       # no dispara centenars de passos


# ── Integració amb el Mode Teclat (base de la capa teclat v3) ────────────────

import pytest
from modes.mode_keyboard import KeyboardMode
from modes.kbd_buttons import build_fn_mappings, process_keyboard_buttons
from modes import accompaniment as acc_mod

OFF = [False] * 15


@pytest.fixture
def kbd():
    k = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)
    k.available_scales = [0]
    k.available_keys = ['C', 'G']
    k.key_index = 0
    k.btn_functions = ['note'] * 8 + ['scale', 'accomp', 'chord', 'arp',
                                      'modes_layer', 'octave_down', 'octave_up', 'stop']
    build_fn_mappings(k)
    return k


def _press_release(kbd, i):
    s = list(OFF); s[i] = True
    process_keyboard_buttons(kbd, s)
    process_keyboard_buttons(kbd, OFF)


def test_tap_activa_i_cicla_llarga_desactiva(kbd):
    assert not kbd._accomp_active
    _press_release(kbd, 9)                                # tap → activa (primer patró)
    assert kbd._accomp_active
    assert kbd._accomp is not None
    assert kbd._accomp.patterns[0]['type'] == 'pols'
    _press_release(kbd, 9)                                # tap → cicla patró
    assert kbd._accomp_active
    assert kbd._accomp.patterns[0]['type'] == 'baix'
    s = list(OFF); s[9] = True                            # premuda llarga → desactiva
    process_keyboard_buttons(kbd, s)
    kbd._accomp_btn_press_time -= 1.0
    process_keyboard_buttons(kbd, OFF)
    assert not kbd._accomp_active
    assert not kbd._accomp.patterns


def test_la_base_sona_pel_seu_canal(kbd):
    _press_release(kbd, 9)
    kbd._accomp.tick(kbd._accomp._next_t + 0.001)
    ons = [(m.note, getattr(m, 'channel', 0)) for m in kbd.midi.sent
           if 'NoteOn' in type(m).__name__ and m.velocity > 0]
    assert ons, "la base ha d'emetre notes"
    assert all(ch == acc_mod.ACCOMP_CHANNEL for _n, ch in ons)


def test_el_context_segueix_la_tonalitat(kbd):
    _press_release(kbd, 9)                                # activa (root C4 = 48)
    assert kbd._accomp.ctx['root'] == 48
    _press_release(kbd, 8)                                # el canvi d'escala re-sincronitza
    assert kbd._accomp.ctx['root'] == 48
    kbd.key_index = 1                                     # G
    acc_mod.sync_context(kbd)
    assert kbd._accomp.ctx['root'] == 55


def test_octava_resincronitza_el_context(kbd):
    _press_release(kbd, 9)
    kbd.change_octave(1)
    assert kbd._accomp.ctx['root'] == 60


def test_cleanup_atura_la_base(kbd):
    _press_release(kbd, 9)
    assert kbd._accomp_active
    kbd.cleanup()
    assert not kbd._accomp_active
    assert not kbd._accomp.patterns


# ── Acompanyaments CUSTOM (editor "Acompanyaments" de l'app, v3.2) ───────────

def test_custom_toca_la_sequencia_amb_octava_i_velocitat():
    from modes.accompaniment import _make_custom
    spec = {'sequence': [0, 2, 4, -1], 'octave': 1, 'velocity': 77, 'gate': 50}
    pat = _make_custom(spec)
    # passos: cada element de la seqüència dura 2 setzens (n parell dispara)
    n0 = pat(0, CTX, None); n1 = pat(2, CTX, None); n2 = pat(4, CTX, None); n3 = pat(6, CTX, None)
    assert n0[0][0] == 60 + 12 + 0      # grau 0, +1 octava
    assert n1[0][0] == 60 + 12 + 4      # grau 2 (3a de l'escala major = E)
    assert n2[0][0] == 60 + 12 + 7      # grau 4 (5a = G)
    assert n3 == ()                     # silenci
    assert n0[0][2] == 77               # brillantor = velocitat MIDI
    assert abs(n0[0][1] - 1.0) < 1e-6   # gate 50% de 2 setzens = 1 pas
    assert pat(1, CTX, None) == ()      # els setzens senars no disparen


def test_custom_grau_alt_puja_d_octava():
    from modes.accompaniment import _make_custom
    pat = _make_custom({'sequence': [7], 'octave': 0, 'velocity': 90, 'gate': 90})
    assert pat(0, CTX, None)[0][0] == 60 + 12   # grau 7 = tònica una octava amunt


def test_add_custom_aplica_el_seu_bpm_i_sona():
    out = FakeMidiOut()
    eng = Accompaniment(out)
    ok = eng.add_custom({'sequence': [0, 4], 'octave': 0, 'velocity': 90,
                         'gate': 90, 'bpm': 200}, 1, now=0.0)
    assert ok and eng.bpm == 200
    eng.tick(0.0)
    assert (60, 1) in _ons(out)
    # el note-off arriba quan venç la durada
    eng.tick(10.0)
    assert (60, 1) in _offs(out)


def test_cicle_inclou_els_customs_despres_dels_integrats(tmp_path):
    import json
    from core.config_manager import ConfigManager
    from modes.mode_keyboard import KeyboardMode
    from modes.accompaniment import handle_button, ACCOMP_PATTERN_IDS
    cfg = {'banks': [{'name': 'T', 'type': 'teclat', 'modes': [''] * 16,
                      'keyboard_scales': [0],
                      'custom_accompaniments': [
                          {'name': 'Meva Base', 'sequence': [0, 4], 'octave': 0,
                           'velocity': 90, 'gate': 90, 'bpm': 140}]}],
           'current_bank': 0}
    p = tmp_path / 'cfg.json'
    p.write_text(json.dumps(cfg))
    kbd = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=ConfigManager(config_path=str(p)))
    # tap: activa (idx 0) i cicla fins a l'últim integrat...
    for _ in range(len(ACCOMP_PATTERN_IDS)):
        handle_button(kbd, 0.1, 0.0)
    # ...el següent tap ha de ser el custom
    handle_button(kbd, 0.1, 0.0)
    assert kbd._accomp_pat_idx == len(ACCOMP_PATTERN_IDS)
    assert kbd._accomp.bpm == 140
    assert kbd._accomp.patterns and kbd._accomp.patterns[0]['type'] == 'custom'
    # i el tap següent torna al primer integrat (volta completa)
    handle_button(kbd, 0.1, 0.0)
    assert kbd._accomp_pat_idx == 0
    assert kbd._accomp.bpm == 110
