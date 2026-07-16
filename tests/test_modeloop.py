"""Tests del loop MIDI de la capa de modes (modes/modeloop.py)."""
from conftest import FakeMidiOut

from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from modes.modeloop import ModeLoop, MAX_LEN_S, IDLE, RECORDING, PLAYING


def _notes(out):
    # endswith: els mocks anomenen les classes '_NoteOn'/'_NoteOff'
    res = []
    for m in out.sent:
        n = type(m).__name__
        if n.endswith('NoteOn'):
            res.append(('NoteOn', m.note))
        elif n.endswith('NoteOff'):
            res.append(('NoteOff', m.note))
    return res


def _make(now=0.0):
    out = FakeMidiOut()
    lp = ModeLoop()
    lp.attach(out)
    return out, lp


def test_tap_cicla_estats():
    out, lp = _make()
    assert lp.state == IDLE
    assert lp.tap(0.0) == RECORDING
    out.send(NoteOn(60, 100)); out.send(NoteOff(60, 0))
    assert lp.tap(1.0) == PLAYING
    assert lp.tap(2.0) == IDLE                 # tap sobre SONANT = esborra
    assert lp.events == []


def test_gravacio_buida_no_sona():
    out, lp = _make()
    lp.tap(0.0)
    assert lp.tap(1.0) == IDLE                 # res gravat → torna a IDLE


def test_reprodueix_el_que_ha_gravat():
    out, lp = _make()
    lp.tap(10.0)
    lp._t0 = 10.0                              # temps determinista
    out.send(NoteOn(60, 100))
    lp.events[-1][0] = 0.1                     # fixa t_rel exacte
    out.send(NoteOff(60, 0))
    lp.events[-1][0] = 0.4
    lp.tap(11.0)                               # tanca (len 1.0) i sona
    out.sent.clear()
    lp.tick(out, 11.05)                        # abans del primer event: res
    assert _notes(out) == []
    lp.tick(out, 11.15)                        # 0.15 dins el cicle → NoteOn
    assert ('NoteOn', 60) in _notes(out)
    lp.tick(out, 11.5)                         # 0.5 → NoteOff
    assert ('NoteOff', 60) in _notes(out)


def test_el_loop_dona_la_volta():
    out, lp = _make()
    lp.tap(0.0); lp._t0 = 0.0
    out.send(NoteOn(64, 90)); lp.events[-1][0] = 0.1
    out.send(NoteOff(64, 0)); lp.events[-1][0] = 0.3
    lp.tap(1.0)                                # loop d'1s
    out.sent.clear()
    lp.tick(out, 1.2)                          # volta 1: NoteOn
    lp.tick(out, 2.05)                         # wrap → reinicia
    lp.tick(out, 2.2)                          # volta 2: NoteOn una altra vegada
    ons = [n for n in _notes(out) if n[0] == 'NoteOn']
    assert len(ons) == 2


def test_no_es_grava_a_si_mateix():
    out, lp = _make()
    lp.tap(0.0); lp._t0 = 0.0
    out.send(NoteOn(60, 100)); lp.events[-1][0] = 0.1
    out.send(NoteOff(60, 0)); lp.events[-1][0] = 0.2
    lp.tap(0.5)
    n_events = len(lp.events)
    lp.tick(out, 0.65)                         # replay (via el send embolcallat)
    assert len(lp.events) == n_events          # el replay no s'ha capturat


def test_autotancament_al_limit():
    out, lp = _make()
    lp.tap(0.0); lp._t0 = 0.0
    out.send(NoteOn(60, 100)); lp.events[-1][0] = 0.1
    lp.tick(out, MAX_LEN_S + 0.5)              # la presa supera el límit
    assert lp.state == PLAYING                 # s'ha tancat sola
    assert lp.loop_len <= MAX_LEN_S


def test_clear_envia_noteoffs_de_les_notes_del_loop():
    out, lp = _make()
    lp.tap(0.0); lp._t0 = 0.0
    out.send(NoteOn(72, 100)); lp.events[-1][0] = 0.05
    out.send(NoteOff(72, 0)); lp.events[-1][0] = 0.9
    lp.tap(1.0)
    out.sent.clear()
    lp.tick(out, 1.1)                          # NoteOn sonant pel loop
    lp.clear(out)
    assert ('NoteOff', 72) in _notes(out)
    assert lp.state == IDLE
