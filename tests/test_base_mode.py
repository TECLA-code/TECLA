"""Tests del tracking unificat de notes a BaseMode."""
from conftest import FakeMidiOut

from modes.base_mode import BaseMode


def _noms(missatges):
    return [type(m).__name__ for m in missatges]


def test_send_note_on_registra_la_nota():
    mode = BaseMode(FakeMidiOut())
    mode.send_note_on(60)
    mode.send_note_on(64, velocity=100, channel=2)
    assert mode.tracked_notes == {(60, 0), (64, 2)}
    assert len(mode.midi_out.sent) == 2


def test_send_note_off_desregistra():
    mode = BaseMode(FakeMidiOut())
    mode.send_note_on(60)
    mode.send_note_off(60)
    assert mode.tracked_notes == set()


def test_stop_tracked_notes_envia_noteoff_i_buida():
    out = FakeMidiOut()
    mode = BaseMode(out)
    mode.send_note_on(60)
    mode.send_note_on(64)
    mode.send_note_on(67, channel=3)
    out.sent.clear()

    mode.stop_tracked_notes()

    assert mode.tracked_notes == set()
    assert len(out.sent) == 3
    assert all('NoteOff' in n for n in _noms(out.sent))
    # els canals es conserven
    assert sorted(getattr(m, 'channel', 0) for m in out.sent) == [0, 0, 3]


def test_cleanup_atura_les_notes():
    out = FakeMidiOut()
    mode = BaseMode(out)
    mode.send_note_on(72)
    out.sent.clear()
    mode.cleanup()
    assert mode.tracked_notes == set()
    assert len(out.sent) == 1


def test_stop_tracked_notes_segur_sense_tracking():
    """Un mode antic que no crida super().__init__() no ha de petar."""
    mode = BaseMode.__new__(BaseMode)  # sense __init__
    mode.stop_tracked_notes()  # no ha de llançar


def test_nota_fora_de_rang_es_normalitza():
    mode = BaseMode(FakeMidiOut())
    mode.send_note_on(200)  # 200 & 0x7F = 72
    assert (72, 0) in mode.tracked_notes
    mode.send_note_off(200)
    assert mode.tracked_notes == set()
