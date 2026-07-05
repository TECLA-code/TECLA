"""Tests de l'Overdub (kbd_looper.handle_dub_button i captura en PLAYING)."""
import pytest

from conftest import FakeMidiOut

from modes.mode_keyboard import KeyboardMode
from modes.kbd_buttons import build_fn_mappings
from modes import kbd_looper as lp

OFF = [False] * 15


@pytest.fixture
def kbd():
    k = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)
    k.available_scales = [0]
    k.btn_functions = ['note'] * 8 + ['looper', 'looper_dub', 'chord', 'arp',
                                      'modes_layer', 'octave_down', 'octave_up', 'stop']
    build_fn_mappings(k)
    return k


def _noms(missatges):
    return [type(m).__name__ for m in missatges]


def _loop_en_marxa(kbd):
    """Loop lliure de 2.0s amb 2 acords (offsets 0 i 1.0), PLAYING des de t=12."""
    lp.handle_button(kbd, 0.1, 9.9)
    kbd.button_notes[0] = {60, 64, 67}
    lp.record_press(kbd, 0, 10.0)
    lp.record_release(kbd, 0, 10.4)
    kbd.button_notes[1] = {55}
    lp.record_press(kbd, 1, 11.0)
    lp.record_release(kbd, 1, 11.4)
    lp.handle_button(kbd, 0.1, 12.0)
    assert kbd.loop_state == lp.PLAYING


def test_overdub_nomes_amb_loop(kbd):
    lp.handle_dub_button(kbd, 0.1, 0.0)     # sense loop: missatge i res més
    assert kbd.loop_state == lp.IDLE
    assert not kbd.loop_overdub


def test_entrar_i_sortir(kbd):
    _loop_en_marxa(kbd)
    lp.handle_dub_button(kbd, 0.1, 12.2)
    assert kbd.loop_overdub
    assert kbd.loop_state == lp.PLAYING     # el loop NO s'atura
    lp.handle_dub_button(kbd, 0.1, 12.5)
    assert not kbd.loop_overdub


def test_afegir_acord_al_loop(kbd):
    _loop_en_marxa(kbd)
    lp.tick(kbd, 12.0)                      # passi en marxa
    lp.handle_dub_button(kbd, 0.1, 12.2)    # overdub ON
    kbd.button_notes[2] = {70}
    lp.record_press(kbd, 2, 12.5)           # offset 0.5 dins del loop
    lp.record_release(kbd, 2, 12.8)
    assert len(kbd.loop_events) == 3
    # inserit ordenat entre offset 0 i 1.0
    offsets = [ev[0] for ev in kbd.loop_events]
    assert offsets == sorted(offsets)
    assert kbd.loop_events[1][0] == pytest.approx(0.5)
    assert kbd.loop_events[1][1] == pytest.approx(0.3)


def test_no_es_redispara_al_mateix_passi_pero_si_al_seguent(kbd):
    _loop_en_marxa(kbd)
    lp.tick(kbd, 12.0)                      # acord A sona
    lp.handle_dub_button(kbd, 0.1, 12.2)
    kbd.button_notes[2] = {70}
    lp.record_press(kbd, 2, 12.5)
    kbd.midi.sent.clear()
    lp.tick(kbd, 12.6)                      # mateix passi: la nota nova NO es redispara
    assert _noms(kbd.midi.sent).count('_NoteOn') == 0
    lp.tick(kbd, 13.05)                     # acord B (offset 1.0) sí
    assert _noms(kbd.midi.sent).count('_NoteOn') == 1
    lp.tick(kbd, 14.05)                     # wrap → passi següent
    lp.tick(kbd, 14.55)                     # offset 0.5: ara la capa nova SÍ que sona
    ons = [m for m in kbd.midi.sent if type(m).__name__ == '_NoteOn']
    assert any(m.note == 70 for m in ons)


def _afegir_capa(kbd, btn, nota, t_press, t_release, t_obre, t_tanca):
    """Obre overdub, afegeix una nota i tanca la capa."""
    lp.handle_dub_button(kbd, 0.1, t_obre)
    kbd.button_notes[btn] = {nota}
    lp.record_press(kbd, btn, t_press)
    lp.record_release(kbd, btn, t_release)
    lp.handle_dub_button(kbd, 0.1, t_tanca)


def test_desfer_ultima_capa(kbd):
    _loop_en_marxa(kbd)
    _afegir_capa(kbd, 2, 70, 12.5, 12.8, 12.2, 13.0)
    assert len(kbd.loop_events) == 3
    lp.handle_dub_button(kbd, 1.0, 13.5)    # toc llarg → desfer
    assert len(kbd.loop_events) == 2
    assert kbd._dub_layers == []


def test_pelar_capes_una_a_una(kbd):
    """Premuda llarga repetida: va traient capes de la més nova a la més vella."""
    _loop_en_marxa(kbd)
    _afegir_capa(kbd, 2, 70, 12.5, 12.8, 12.2, 13.0)   # capa 1: nota 70
    _afegir_capa(kbd, 3, 75, 13.4, 13.6, 13.2, 13.8)   # capa 2: nota 75
    assert len(kbd.loop_events) == 4
    assert len(kbd._dub_layers) == 2
    lp.handle_dub_button(kbd, 1.0, 14.0)    # fora capa 2
    assert len(kbd.loop_events) == 3
    assert not any(75 in ev[2] for ev in kbd.loop_events)
    assert any(70 in ev[2] for ev in kbd.loop_events)   # la capa 1 segueix
    lp.handle_dub_button(kbd, 1.0, 14.5)    # fora capa 1
    assert len(kbd.loop_events) == 2        # només el loop base
    lp.handle_dub_button(kbd, 1.0, 15.0)    # res més a desfer: no peta
    assert len(kbd.loop_events) == 2


def test_esborrar_totes_les_capes_de_cop(kbd):
    """Premuda molt llarga (1.6s): fora TOTES les capes, el loop base es manté."""
    _loop_en_marxa(kbd)
    _afegir_capa(kbd, 2, 70, 12.5, 12.8, 12.2, 13.0)
    _afegir_capa(kbd, 3, 75, 13.4, 13.6, 13.2, 13.8)
    _afegir_capa(kbd, 4, 80, 14.2, 14.4, 14.0, 14.6)
    assert len(kbd.loop_events) == 5
    lp.handle_dub_button(kbd, 1.7, 15.0)    # molt llarg
    assert len(kbd.loop_events) == 2        # només el loop base
    assert kbd._dub_layers == [] and kbd._dub_current == []
    assert kbd.loop_state == lp.PLAYING     # el loop segueix sonant


def test_esborrar_totes_inclou_la_capa_en_curs(kbd):
    _loop_en_marxa(kbd)
    _afegir_capa(kbd, 2, 70, 12.5, 12.8, 12.2, 13.0)
    lp.handle_dub_button(kbd, 0.1, 13.2)    # obrir una capa nova
    kbd.button_notes[3] = {75}
    lp.record_press(kbd, 3, 13.4)
    lp.record_release(kbd, 3, 13.6)         # capa en curs (sense tancar)
    lp.handle_dub_button(kbd, 1.7, 14.0)    # molt llarg en plena gravació
    assert len(kbd.loop_events) == 2
    assert not kbd.loop_overdub


def test_desfer_durant_overdub(kbd):
    _loop_en_marxa(kbd)
    lp.handle_dub_button(kbd, 0.1, 12.2)
    kbd.button_notes[2] = {70}
    lp.record_press(kbd, 2, 12.5)
    lp.record_release(kbd, 2, 12.8)
    lp.handle_dub_button(kbd, 1.0, 13.0)    # toc llarg en plena capa
    assert not kbd.loop_overdub
    assert len(kbd.loop_events) == 2        # capa en curs eliminada


def test_pausar_el_loop_tanca_overdub(kbd):
    _loop_en_marxa(kbd)
    lp.handle_dub_button(kbd, 0.1, 12.2)
    kbd.button_notes[2] = {70}
    lp.record_press(kbd, 2, 12.5)
    lp.record_release(kbd, 2, 12.8)
    lp.handle_button(kbd, 0.1, 13.0)        # botó looper: pausa
    assert kbd.loop_state == lp.PAUSED
    assert not kbd.loop_overdub
    assert len(kbd._dub_layers) == 1        # la capa queda tancada i desfable


def test_repren_des_de_pausa_amb_overdub(kbd):
    _loop_en_marxa(kbd)
    lp.handle_button(kbd, 0.1, 13.0)        # pausa
    lp.handle_dub_button(kbd, 0.1, 20.0)    # botó overdub des de pausa
    assert kbd.loop_state == lp.PLAYING
    assert kbd.loop_overdub


def test_esborrar_el_loop_neteja_overdub(kbd):
    _loop_en_marxa(kbd)
    lp.handle_dub_button(kbd, 0.1, 12.2)
    kbd.button_notes[2] = {70}
    lp.record_press(kbd, 2, 12.5)
    lp.handle_button(kbd, 1.0, 13.0)        # toc llarg looper: esborrar-ho tot
    assert kbd.loop_state == lp.IDLE
    assert not kbd.loop_overdub
    assert kbd.loop_events == []
    assert kbd._dub_current == [] and kbd._dub_layers == []


def test_overdub_quantitzat_en_passos(kbd):
    kbd.arp_speed = 0.5
    lp.handle_button(kbd, 0.1, 9.9, quantized=True)
    kbd.button_notes[0] = {60}
    lp.record_press(kbd, 0, 10.0)
    lp.record_release(kbd, 0, 10.4)
    lp.handle_button(kbd, 0.1, 12.1, quantized=True)  # 4 passos de 0.5s
    lp.handle_dub_button(kbd, 0.1, 12.2)
    kbd.button_notes[2] = {70}
    lp.record_press(kbd, 2, 13.15)          # t=1.05 → pas 2
    lp.record_release(kbd, 2, 13.4)
    ev = kbd._dub_current[0]
    assert ev[0] == 2                        # offset enter (passos)
    assert isinstance(ev[1], int) and ev[1] >= 1


def test_arp_es_grava_durant_overdub(kbd):
    _loop_en_marxa(kbd)
    lp.handle_dub_button(kbd, 0.1, 12.2)
    lp.record_live_note(kbd, 72, 100, 12.4)  # nota d'arp en plena reproducció
    lp.record_live_note(kbd, 76, 100, 12.6)
    assert len(kbd._dub_current) == 2
    assert all(len(ev[2]) == 1 for ev in kbd._dub_current)