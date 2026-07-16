"""Tests del Looper harmònic (kbd_looper.py) — timing lliure.

Es testegen les funcions del mòdul amb timestamps sintètics (deterministes,
sense sleeps): gravació, reproducció amb el timing original, wrap del bucle,
pausa/represa, esborrat i integració amb stop_all_notes().
"""
import pytest

from conftest import FakeMidiOut

from modes.mode_keyboard import KeyboardMode
from modes.kbd_buttons import build_fn_mappings
from modes.kbd_pots import apply_pot_function
from modes import kbd_looper as lp


@pytest.fixture
def kbd():
    k = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)
    k.available_scales = [0]
    k.btn_functions = ['note'] * 8 + ['scale', 'looper', 'chord', 'arp',
                                      'modes_layer', 'octave_down', 'octave_up', 'stop']
    build_fn_mappings(k)
    return k


def _noms(missatges):
    return [type(m).__name__ for m in missatges]


def _grava_dos_acords(kbd):
    """Arma, grava 2 'acords' sintètics i arrenca el loop a t=10.
    Acord A: t=0-0.4 (notes 60,64,67) | Acord B: t=1.0-1.4 (nota 55)
    Llargada del loop: 2.0s. El loop comença a sonar a now=12.0."""
    lp.handle_button(kbd, 0.1, 9.9)        # IDLE -> ARMED
    kbd.button_notes[0] = {60, 64, 67}
    lp.record_press(kbd, 0, 10.0)          # ARMED -> RECORDING, t0=10
    lp.record_release(kbd, 0, 10.4)
    kbd.button_notes[1] = {55}
    lp.record_press(kbd, 1, 11.0)
    lp.record_release(kbd, 1, 11.4)
    lp.handle_button(kbd, 0.1, 12.0)       # RECORDING -> PLAYING (llargada 2.0)
    kbd.midi_out_sent_baseline = len(kbd.midi.sent)


def test_armar_i_cancellar(kbd):
    lp.handle_button(kbd, 0.1, 0.0)
    assert kbd.loop_state == lp.ARMED
    lp.handle_button(kbd, 0.1, 0.5)
    assert kbd.loop_state == lp.IDLE


def test_gravacio_comenca_amb_la_primera_nota(kbd):
    lp.handle_button(kbd, 0.1, 5.0)
    assert kbd.loop_state == lp.ARMED
    kbd.button_notes[0] = {60}
    lp.record_press(kbd, 0, 7.5)
    assert kbd.loop_state == lp.RECORDING
    assert kbd.loop_t0 == 7.5              # t0 és el moment de la primera nota
    assert kbd.loop_events[0][0] == 0.0    # primer esdeveniment a offset 0


def test_loop_buit_no_arrenca(kbd):
    lp.handle_button(kbd, 0.1, 0.0)        # ARMED
    kbd.loop_state = lp.RECORDING          # gravant però sense esdeveniments
    kbd.loop_t0 = 0.0
    lp.handle_button(kbd, 0.1, 3.0)
    assert kbd.loop_state == lp.IDLE


def test_reproduccio_respecta_el_timing(kbd):
    _grava_dos_acords(kbd)
    assert kbd.loop_state == lp.PLAYING
    assert kbd.loop_length == pytest.approx(2.0)

    kbd.midi.sent.clear()
    lp.tick(kbd, 12.0)                     # t=0 -> acord A (3 NoteOn)
    assert _noms(kbd.midi.sent).count('_NoteOn') == 3
    lp.tick(kbd, 12.2)                     # res nou encara
    assert _noms(kbd.midi.sent).count('_NoteOn') == 3
    lp.tick(kbd, 12.5)                     # t=0.5 -> NoteOff de l'acord A (dur 0.4)
    assert _noms(kbd.midi.sent).count('_NoteOff') == 3
    lp.tick(kbd, 13.05)                    # t=1.05 -> acord B (1 NoteOn)
    assert _noms(kbd.midi.sent).count('_NoteOn') == 4


def test_wrap_repeteix_sense_deriva(kbd):
    _grava_dos_acords(kbd)
    kbd.midi.sent.clear()
    lp.tick(kbd, 12.0)                     # passada 1: acord A
    lp.tick(kbd, 13.0)                     # acord B
    lp.tick(kbd, 14.05)                    # wrap (t>=2.0) -> acord A una altra vegada
    ons = _noms(kbd.midi.sent).count('_NoteOn')
    assert ons == 3 + 1 + 3
    assert kbd.loop_t0 == pytest.approx(14.0)  # fase exacta, sense deriva


def test_pausa_silencia_i_conserva(kbd):
    _grava_dos_acords(kbd)
    kbd.midi.sent.clear()
    lp.tick(kbd, 12.0)                     # acord A sonant
    lp.handle_button(kbd, 0.1, 12.1)       # PLAYING -> PAUSED
    assert kbd.loop_state == lp.PAUSED
    # les notes pendents s'han silenciat
    assert _noms(kbd.midi.sent).count('_NoteOff') == 3
    assert len(kbd.loop_events) == 2       # el loop es conserva
    lp.handle_button(kbd, 0.1, 20.0)       # PAUSED -> PLAYING des del principi
    assert kbd.loop_state == lp.PLAYING
    assert kbd.loop_t0 == 20.0


def test_toc_llarg_esborra(kbd):
    _grava_dos_acords(kbd)
    lp.handle_button(kbd, 1.0, 13.0)       # toc llarg
    assert kbd.loop_state == lp.IDLE
    assert kbd.loop_events == []


def test_stop_all_notes_NO_pausa_el_loop(kbd):
    """REGRESSIÓ: l'arpegiador crida stop_all_notes() a CADA pas — si pausés
    el loop, activar l'arp aturaria el loop a l'instant (bug reportat)."""
    _grava_dos_acords(kbd)
    kbd.stop_all_notes()
    assert kbd.loop_state == lp.PLAYING    # el loop continua


def test_pause_looper_si_que_pausa(kbd):
    """L'STOP general (botó 16) pausa el loop via pause_looper()."""
    _grava_dos_acords(kbd)
    lp.tick(kbd, 12.0)                     # acord A sonant
    kbd.midi.sent.clear()
    kbd.pause_looper()
    assert kbd.loop_state == lp.PAUSED
    assert len(kbd.loop_events) == 2       # es conserva per reprendre
    # i silencia les notes del loop que sonaven
    assert _noms(kbd.midi.sent).count('_NoteOff') == 3


def test_limit_esdeveniments(kbd):
    lp.handle_button(kbd, 0.1, 0.0)
    kbd.button_notes[0] = {60}
    for i in range(80):
        lp.record_press(kbd, 0, float(i) * 0.01)
    assert len(kbd.loop_events) <= lp.MAX_EVENTS


# ── Variant quantitzada ('looper_q') ─────────────────────────────────────────

def _grava_quantitzat(kbd):
    """Grava 2 notes amb timing imperfecte i tanca amb quantized=True.
    arp_speed=0.5 → graella de 0.5s. Notes a t=0 i t=1.05 (≈2 passos)."""
    kbd.arp_speed = 0.5
    lp.handle_button(kbd, 0.1, 9.9, quantized=True)   # ARMED
    kbd.button_notes[0] = {60}
    lp.record_press(kbd, 0, 10.0)
    lp.record_release(kbd, 0, 10.4)
    kbd.button_notes[1] = {55}
    lp.record_press(kbd, 1, 11.05)                    # 1.05s ≈ pas 2
    lp.record_release(kbd, 1, 11.45)
    lp.handle_button(kbd, 0.1, 12.1, quantized=True)  # llargada 2.1s ≈ 4 passos


def test_quantitzacio_converteix_a_passos(kbd):
    _grava_quantitzat(kbd)
    assert kbd.loop_quantized
    assert kbd.loop_length == 4                       # 2.1s / 0.5 = 4 passos
    offsets = [ev[0] for ev in kbd.loop_events]
    assert offsets == [0, 2]                          # el timing imperfecte s'ajusta
    assert all(isinstance(ev[1], int) and ev[1] >= 1 for ev in kbd.loop_events)


def test_variant_lliure_no_quantitza(kbd):
    _grava_dos_acords(kbd)                            # tancat amb quantized=False
    assert not kbd.loop_quantized
    assert kbd.loop_length == pytest.approx(2.0)      # segueix en segons


def test_quantitzat_reprodueix_a_la_graella(kbd):
    _grava_quantitzat(kbd)
    kbd.midi.sent.clear()
    lp.tick(kbd, 12.1)                                # pas 0 → nota 60
    assert _noms(kbd.midi.sent).count('_NoteOn') == 1
    lp.tick(kbd, 12.9)                                # pas 1.6: encara no (ev1 al pas 2 = 1.0s)
    assert _noms(kbd.midi.sent).count('_NoteOn') == 1
    lp.tick(kbd, 13.15)                               # t=1.05 ≥ pas 2 (1.0s) → nota 55
    assert _noms(kbd.midi.sent).count('_NoteOn') == 2


def test_quantitzat_tempo_fixat_mentre_sona(kbd):
    """REGRESSIÓ: el tempo del loop NO segueix arp_speed en viu — si no,
    activar la capa arp (que reescriu arp_speed amb el pot a cada cicle)
    segrestaria el tempo del loop (bug reportat)."""
    _grava_quantitzat(kbd)
    kbd.midi.sent.clear()
    kbd.arp_speed = 0.02                              # el pot es mou (capa arp activa)
    lp.tick(kbd, 12.1)                                # pas 0 → nota 60
    lp.tick(kbd, 12.9)                                # ev1 segueix al pas 2×0.5=1.0s: encara no
    assert _noms(kbd.midi.sent).count('_NoteOn') == 1
    lp.tick(kbd, 13.15)                               # t=1.05 ≥ 1.0 → nota 55 (graella intacta)
    assert _noms(kbd.midi.sent).count('_NoteOn') == 2


def test_quantitzat_la_represa_adopta_el_tempo_nou(kbd):
    """Per canviar el tempo del loop: pausa → ajustar BPM → represa."""
    _grava_quantitzat(kbd)
    lp.handle_button(kbd, 0.1, 13.0)                  # PAUSED
    kbd.arp_speed = 0.25                              # nou tempo ABANS de reprendre
    lp.handle_button(kbd, 0.1, 20.0)                  # PLAYING, adopta graella 0.25
    kbd.midi.sent.clear()
    lp.tick(kbd, 20.0)                                # pas 0 → nota 60
    assert _noms(kbd.midi.sent).count('_NoteOn') == 1
    lp.tick(kbd, 20.4)                                # ev1 ara cau a 2×0.25=0.5s: encara no
    assert _noms(kbd.midi.sent).count('_NoteOn') == 1
    lp.tick(kbd, 20.55)                               # t=0.55 ≥ 0.5 → nota 55
    assert _noms(kbd.midi.sent).count('_NoteOn') == 2


# ── Captura de l'arpegiador (record_live_note) ───────────────────────────────

def test_arp_es_pot_loopejar(kbd):
    """Les notes que emet l'arp (button_index=-1) es graven al loop i, com que
    l'arp ha intervingut, la presa s'AUTO-QUANTITZA a la graella de l'arp (captura
    fina sense desfasament). El looper únic integra el comportament del quantitzat:
    no cal un botó 'looper_q' separat."""
    kbd.arp_speed = 0.2
    lp.handle_button(kbd, 0.1, 9.9)                   # ARMED
    lp.record_live_note(kbd, 60, 100, 10.0)           # 1a nota arp → comença gravació
    assert kbd.loop_state == lp.RECORDING
    assert kbd._loop_had_arp is True                  # marca de presència d'arp
    lp.record_live_note(kbd, 64, 100, 10.2)
    lp.record_live_note(kbd, 67, 100, 10.4)
    lp.handle_button(kbd, 0.1, 10.8)                  # PLAYING (llargada 0.8s → 4 passos)
    assert kbd.loop_state == lp.PLAYING
    assert kbd.loop_quantized is True                 # auto-quantitzat per l'arp
    assert len(kbd.loop_events) == 3
    assert all(len(ev[2]) == 1 for ev in kbd.loop_events)  # notes soles
    assert [ev[0] for ev in kbd.loop_events] == [0, 1, 2]  # offsets en passos
    assert kbd.loop_events[0][1] == 1                       # durada en passos (no segons)
    assert kbd.loop_length == 4                             # 0.8s / 0.2 = 4 passos


def test_acords_manuals_no_es_quantitzen(kbd):
    """Sense arp, el mateix botó looper conserva el timing LLIURE (el que agrada):
    l'auto-quantització NOMÉS s'activa si l'arp intervé durant la presa."""
    _grava_dos_acords(kbd)                            # només acords manuals
    assert kbd.loop_state == lp.PLAYING
    assert kbd._loop_had_arp is False
    assert kbd.loop_quantized is False                # timing lliure intacte
    assert kbd.loop_length == pytest.approx(2.0)      # segons, no passos


# ── Independència del loop respecte al sustain en directe ─────────────────────

def test_loop_gravat_amb_sustain_es_independent(kbd):
    """Gravar amb sustain (CC64) FIXA el sustain a les durades: cada acord se sosté
    fins al següent (lligat), de manera que el loop sona sostingut per si mateix i
    NO depèn del pedal en directe. Modificar el sustain després no altera el loop."""
    kbd.sustain_level = 100                           # sustain (CC64) actiu
    lp.handle_button(kbd, 0.1, 0.0)                   # ARMED
    kbd.button_notes[0] = {60, 64, 67}
    lp.record_press(kbd, 0, 0.0)
    lp.record_release(kbd, 0, 0.3)                    # tecla amunt aviat (staccato)
    kbd.button_notes[1] = {62, 65, 69}
    lp.record_press(kbd, 1, 1.0)
    lp.record_release(kbd, 1, 1.3)
    lp.handle_button(kbd, 0.1, 2.0)                   # PLAYING (llargada 2.0)
    assert kbd._loop_had_sustain is True
    # durades "lligades" malgrat el staccato: acord 1 fins ~acord 2, acord 2 fins ~final
    assert kbd.loop_events[0][1] > 0.9
    assert kbd.loop_events[1][1] > 0.9


def test_loop_sense_sustain_conserva_durades(kbd):
    """Sense sustain, les durades es conserven tal com es toquen (no es fixa res)."""
    kbd.sustain_level = 0
    _grava_dos_acords(kbd)
    assert kbd._loop_had_sustain is False
    assert kbd.loop_events[0][1] == pytest.approx(0.4)   # durada real (release - press)


# ── Sustain progressiu (el pot fixa el temps de release; sense CC64) ─────────

def test_sustain_progressiu(kbd):
    """El pot de sustain fixa el release TECLA-side: zona morta baixa (release
    immediat), corba creixent fins a SUSTAIN_MAX_S, i hold indefinit només prop
    del màxim (>=125)."""
    kbd.pot_z_function = 'Sustain (CC64)'
    apply_pot_function(kbd, 'pot_z', 4, force_update=True)
    assert kbd.sustain_release_time == 0.0
    assert kbd.sustain_hold_enabled is False
    prev = 0.0
    for v in (40, 70, 100, 124):
        apply_pot_function(kbd, 'pot_z', v, force_update=True)
        assert 0 < kbd.sustain_release_time <= kbd.SUSTAIN_MAX_S, f"pot={v}"
        assert kbd.sustain_release_time > prev, f"pot={v}: corba creixent"
        assert kbd.sustain_hold_enabled is False
        prev = kbd.sustain_release_time
    for v in (125, 127):
        apply_pot_function(kbd, 'pot_z', v, force_update=True)
        assert kbd.sustain_release_time == -1.0, f"pot={v}: hold indefinit"
        assert kbd.sustain_hold_enabled is True


def test_loop_gravat_amb_pot_baix_no_es_lliga(kbd):
    """Gravar amb el pot de sustain a la zona baixa (<64) NO activa el baking:
    el loop conserva les durades tal com s'han tocat."""
    kbd.pot_z_function = 'Sustain (CC64)'
    apply_pot_function(kbd, 'pot_z', 40, force_update=True)
    _grava_dos_acords(kbd)
    assert kbd._loop_had_sustain is False
    assert kbd.loop_events[0][1] == pytest.approx(0.4)       # durada intacta


def test_loop_gravat_amb_pot_alt_es_lliga(kbd):
    """Gravar amb el pot de sustain a la zona alta (>=64) marca la presa i el
    baking lliga les durades: el loop queda independent del pot en directe."""
    kbd.pot_z_function = 'Sustain (CC64)'
    apply_pot_function(kbd, 'pot_z', 70, force_update=True)
    _grava_dos_acords(kbd)
    assert kbd._loop_had_sustain is True
    assert kbd.loop_events[0][1] > 0.9                       # lligat fins al següent


def test_arp_capturat_via_note_on(kbd):
    """El ganxo real: _note_on amb button_index=-1 grava al loop."""
    lp.handle_button(kbd, 0.1, 0.0)                   # ARMED
    kbd._note_on(60, -1)                              # nota d'arp
    assert kbd.loop_state == lp.RECORDING
    assert len(kbd.loop_events) == 1
    kbd._note_on(64, 0)                               # nota de botó: NO la grava aquest ganxo
    assert len(kbd.loop_events) == 1
