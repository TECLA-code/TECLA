"""Tests del Latch i del CC Lliure del Mode Teclat."""
import pytest

from conftest import FakeMidiOut

from modes.mode_keyboard import KeyboardMode
from modes.kbd_buttons import build_fn_mappings, process_keyboard_buttons
from modes import kbd_pots

OFF = [False] * 15


@pytest.fixture
def kbd():
    k = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)
    k.available_scales = [0]  # escala major (normalment ho fa setup() amb config)
    # Botó 9 = latch; botons 0-7 = notes
    k.btn_functions = ['note'] * 8 + ['scale', 'latch', 'chord', 'arp',
                                      'modes_layer', 'octave_down', 'octave_up', 'stop']
    build_fn_mappings(k)
    return k


def _press_release(kbd, i):
    s = list(OFF); s[i] = True
    process_keyboard_buttons(kbd, s)
    process_keyboard_buttons(kbd, OFF)


def test_sense_latch_la_nota_para_en_deixar_anar(kbd):
    _press_release(kbd, 0)
    assert len(kbd.active_notes) == 0


def test_latch_mante_la_nota_apres_deixar_anar(kbd):
    _press_release(kbd, 9)
    assert kbd.latch_active
    _press_release(kbd, 0)
    assert len(kbd.active_notes) == 1


def test_latch_apila_notes_de_botons_diferents(kbd):
    _press_release(kbd, 9)
    _press_release(kbd, 0)
    _press_release(kbd, 1)
    assert len(kbd.active_notes) == 2


def test_latch_repremer_commuta_a_off(kbd):
    _press_release(kbd, 9)
    _press_release(kbd, 0)
    _press_release(kbd, 0)
    assert len(kbd.active_notes) == 0


def test_desactivar_latch_neteja_tot(kbd):
    _press_release(kbd, 9)
    _press_release(kbd, 0)
    _press_release(kbd, 1)
    _press_release(kbd, 9)  # latch OFF
    assert not kbd.latch_active
    assert len(kbd.active_notes) == 0


def test_free_cc_parseja_i_envia(kbd):
    sent = []
    kbd._send_cc_if_changed = lambda cc, v, threshold=2: sent.append((cc, v))
    assert kbd_pots._try_free_cc(kbd, 'CC Lliure (CC74)', 99, 2)
    assert sent == [(74, 99)]


def test_free_cc_clampa_a_127(kbd):
    sent = []
    kbd._send_cc_if_changed = lambda cc, v, threshold=2: sent.append((cc, v))
    kbd_pots._try_free_cc(kbd, 'CC Lliure (CC200)', 50, 2)
    assert sent == [(127, 50)]


def test_free_cc_ignora_funcions_normals(kbd):
    assert not kbd_pots._try_free_cc(kbd, 'Modulació', 10, 2)
    assert not kbd_pots._try_free_cc(kbd, 'Sustain (CC64)', 10, 2)
