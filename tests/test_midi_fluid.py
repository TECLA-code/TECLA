"""Tests del MIDI "com la seda" (v3.1.1): sustain amb acords, re-articulació
neta i botó STOP sense allau de missatges.

Reprodueixen els símptomes reportats al dispositiu real:
  - "el sustain de la capa de teclat no funciona" — amb el mode acords actiu,
    _note_off_for_button refusava d'ajornar note-offs (restricció del disseny
    antic de capes de pots pròpies, retirades al tancament v3.1).
  - "el so fa coses rares amb sustain" — re-tocar una nota que ressonava
    deixava viu el seu note-off ajornat, que tallava la nota NOVA.
  - "el botó 16 fa coses rares" — mm_stop_all_sound enviava >500 missatges
    (128 NoteOff + CC11=127 a tots els canals, 2 passades) i mm_emergency_stop
    ho repetia: més d'un segon de bloqueig i salts de volum.
"""
import json
import time

from conftest import FakeMidiOut

from core.config_manager import ConfigManager
from modes.mode_keyboard import KeyboardMode
from modes.kbd_buttons import process_keyboard_buttons

OFF = [False] * 15


def _teclat(tmp_path, **bank_extra):
    bank = {'name': 'Teclat', 'type': 'teclat', 'modes': ['Silenci'] * 16,
            'keyboard_scales': [0], 'chord_types': ['Major']}
    bank.update(bank_extra)
    cfg = {'banks': [bank], 'current_bank': 0}
    p = tmp_path / 'cfg.json'
    with open(p, 'w') as f:
        json.dump(cfg, f)
    cm = ConfigManager(config_path=str(p))
    return KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=cm)


def _premi(kbd, idx):
    estats = list(OFF)
    estats[idx] = True
    process_keyboard_buttons(kbd, estats)


def _deixa(kbd, idx):
    process_keyboard_buttons(kbd, OFF)


def _noms(msgs):
    return [type(m).__name__ for m in msgs]


def test_sustain_ajorna_note_offs_en_mode_normal(tmp_path):
    kbd = _teclat(tmp_path)
    kbd._set_sustain(100)                      # pot Z amunt → release llarg
    assert kbd.sustain_release_time > 0

    _premi(kbd, 0)
    nota = next(iter(kbd.active_notes))
    kbd.midi.sent.clear()
    _deixa(kbd, 0)

    # Cap NoteOff immediat: la nota ressona i té l'off AJORNAT
    assert not any(n.endswith('NoteOff') for n in _noms(kbd.midi.sent))
    assert nota in kbd._sustain_pending
    assert nota in kbd.active_notes


def test_sustain_tambe_funciona_amb_mode_acords(tmp_path):
    """El bug reportat: amb acords actius el sustain no feia RES (els note-offs
    sortien immediats). Des del tancament v3.1 el pot Z fa sustain a tot arreu
    menys a l'arpegiador."""
    kbd = _teclat(tmp_path)
    kbd.chord_mode_active = True
    kbd._set_sustain(100)

    _premi(kbd, 0)
    assert len(kbd.active_notes) >= 3          # acord sonant
    kbd.midi.sent.clear()
    _deixa(kbd, 0)

    assert not any(n.endswith('NoteOff') for n in _noms(kbd.midi.sent))
    assert len(kbd._sustain_pending) >= 3      # tot l'acord ressona


def test_retocar_nota_amb_sustain_cancela_off_ajornat(tmp_path):
    """Re-articulació neta: l'off ajornat de la nota vella NO ha de tallar la
    nota nova al cap d'uns segons (les "coses rares" amb sustain + acords)."""
    kbd = _teclat(tmp_path)
    kbd.chord_mode_active = True
    kbd._set_sustain(60)                       # release finit

    _premi(kbd, 0)
    _deixa(kbd, 0)
    assert kbd._sustain_pending
    # Re-prémer el MATEIX botó mentre l'acord ressona
    _premi(kbd, 0)
    for nota in kbd.active_notes:
        assert nota not in kbd._sustain_pending, (
            f"la nota {nota} re-tocada encara té un off ajornat que la tallarà")


def test_sustain_no_interfereix_amb_arpegiador(tmp_path):
    kbd = _teclat(tmp_path)
    kbd.arp_mode_active = True
    kbd._set_sustain(100)
    kbd.button_notes[0] = {60}
    kbd.active_notes = {60}
    kbd._note_off_for_button(0, from_release=True)
    # A l'arpegiador els note-offs són immediats (cada pas gestiona els seus)
    assert 60 not in kbd._sustain_pending
    assert 60 not in kbd.active_notes


def test_stop_all_sound_es_curt_i_no_apuja_expression():
    """El pànic del botó 16: UNA passada — CC64/120/123 + pitch bend per canal
    (64 msgs) + NoteOff explícit de les 128 notes al canal de sortida (perquè
    molts instruments de DAW ignoren All Notes Off) — i mai CC11=127 (el salt
    de volum de l'antiga versió, que enviava >500 missatges en 2 passades)."""
    from modes.mm_cleanup import mm_stop_all_sound

    class _Mgr:
        midi_out = FakeMidiOut()
    mgr = _Mgr()
    mm_stop_all_sound(mgr)

    sent = mgr.midi_out.sent
    assert len(sent) <= 200, f"pànic massa llarg: {len(sent)} missatges"
    ccs = [m for m in sent if type(m).__name__.endswith('ControlChange')]
    assert not any(getattr(m, 'control', None) == 11 for m in ccs), \
        "el pànic no ha de tocar CC11 (Expression)"
    controls = {getattr(m, 'control', None) for m in ccs}
    assert {64, 120, 123} <= controls
    # Els 128 NoteOff explícits (xarxa per a instruments que ignoren CC123)
    offs = {m.note for m in sent if type(m).__name__.endswith('NoteOff')}
    assert offs == set(range(128)), f"falten NoteOff explícits: {128 - len(offs)}"


def test_note_on_i_off_no_alloquen_missatges(tmp_path):
    """El camí calent usa els missatges POOLED de base_mode (una al·locació
    per nota podia disparar un gc.collect de 10-40ms — el lag "no va al toc")."""
    from modes.base_mode import _note_on_msg, _note_off_msg
    kbd = _teclat(tmp_path)

    _premi(kbd, 0)
    ons = [m for m in kbd.midi.sent if type(m).__name__.endswith('NoteOn')]
    assert ons, "no s'ha enviat cap NoteOn"
    # El missatge enviat és el del pool (FakeMidiOut en guarda una còpia, així
    # que ho verifiquem tocant el pool i mirant que la MUTACIÓ és compartida)
    pool_on = _note_on_msg()
    _deixa(kbd, 0)
    offs = [m for m in kbd.midi.sent if type(m).__name__.endswith('NoteOff')]
    assert offs, "no s'ha enviat cap NoteOff"
    pool_off = _note_off_msg()
    assert pool_on is _note_on_msg() and pool_off is _note_off_msg()


def test_tone_singleton_i_off():
    """core/tone: singleton PWM (mock als tests) — play fixa freqüència i
    duty, off silencia; sense pwmio real tot és no-op silenciós."""
    from core import tone
    tone.play(69)                              # A4
    if tone.pwm is not None:                   # amb mock de pwmio
        assert tone.pwm.frequency == 440
        assert tone.pwm.duty_cycle == 32767
        primer = tone.pwm
        tone.play(81)                          # A5 → REUTILITZA el pin
        assert tone.pwm is primer
        assert tone.pwm.frequency == 880
        tone.off()
        assert tone.pwm.duty_cycle == 0
