"""Tests d'integració del CANVI DE CAPES (tancament v3.1).

Reprodueixen el flux real del dispositiu: config amb diverses capes tipades,
la tecla 13 cicla i cada capa de teclat es RECREA amb la seva pròpia config
(el bug reportat: la segona capa de teclat repetia la primera).
"""
import json

import pytest
from conftest import FakeMidiOut

from core.config_manager import ConfigManager
from modes.mode_keyboard import KeyboardMode
from modes.kbd_buttons import process_keyboard_buttons

OFF = [False] * 15


def _cfg_dues_capes_teclat(path):
    cfg = {
        'banks': [
            {'name': 'Teclat', 'type': 'teclat', 'modes': ['Silenci'] * 16,
             'keyboard_scales': [0],
             'keyboard_button_functions': ['note'] * 8 + ['scale', 'tonality', 'chord', 'arp',
                                                          'modes_layer', 'octave_down', 'octave_up', 'stop'],
             'chord_types': ['Major']},
            {'name': 'Acords', 'type': 'teclat', 'modes': ['Silenci'] * 16,
             'keyboard_scales': [5],
             'keyboard_button_functions': ['note'] * 8 + ['chord', 'voice_lead', 'latch', 'diatonic',
                                                          'modes_layer', 'octave_down', 'octave_up', 'stop'],
             'chord_types': ['m7', '9']},
            {'name': 'Ritmes', 'type': 'modes', 'modes': ['Silenci'] * 16},
        ],
        'current_bank': 0,
    }
    with open(path, 'w') as f:
        json.dump(cfg, f)
    return ConfigManager(config_path=str(path))


def _nou_teclat(cm):
    """Mirall de main._activate_keyboard_layer: recrea el KeyboardMode."""
    k = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=cm)
    return k


def test_cada_capa_de_teclat_sona_amb_la_seva_config(tmp_path):
    cm = _cfg_dues_capes_teclat(tmp_path / 'cfg.json')

    kbd = _nou_teclat(cm)                       # capa 0: 'Teclat'
    assert kbd.available_scales == [0]
    assert kbd.btn_functions[8] == 'scale'
    assert kbd.available_chord_types == ['Major']

    cm.next_bank()                              # tecla 13 → capa 1: 'Acords'
    kbd = _nou_teclat(cm)
    assert kbd.available_scales == [5]
    assert kbd.btn_functions[8] == 'chord'
    assert kbd.btn_functions[9] == 'voice_lead'
    assert kbd.available_chord_types == ['m7', '9']

    cm.next_bank()                              # capa 2: modes
    assert cm.get_current_bank()['type'] == 'modes'
    cm.next_bank()                              # torna a la capa 0 (cicle complet)
    assert cm.get_current_bank()['name'] == 'Teclat'
    kbd = _nou_teclat(cm)
    assert kbd.available_scales == [0]


def test_el_cicle_passa_per_totes_les_capes(tmp_path):
    cm = _cfg_dues_capes_teclat(tmp_path / 'cfg.json')
    noms = []
    for _ in range(3):
        cm.next_bank()
        noms.append(cm.get_current_bank()['name'])
    assert noms == ['Acords', 'Ritmes', 'Teclat']


def test_limit_de_capes_es_retalla(tmp_path):
    banks = [{'name': f'C{i}', 'type': 'modes', 'modes': ['Silenci'] * 16} for i in range(9)]
    banks[0]['type'] = 'teclat'
    cfg = {'banks': banks, 'current_bank': 8}
    p = tmp_path / 'cfg.json'
    with open(p, 'w') as f:
        json.dump(cfg, f)
    cm = ConfigManager(config_path=str(p))
    assert len(cm.config['banks']) == ConfigManager.MAX_BANKS
    assert cm.config['current_bank'] == 0       # l'índex fora de rang es reinicia


def test_acord_surt_amb_notes_consecutives(tmp_path):
    """Les 3 notes d'un acord han de sortir SEGUIDES (cap missatge entremig):
    és el que garanteix que sonin alhora al DAW."""
    cm = _cfg_dues_capes_teclat(tmp_path / 'cfg.json')
    cm.next_bank()                              # capa 'Acords'
    kbd = _nou_teclat(cm)
    s = list(OFF); s[8] = True                  # tap al botó 'chord' (tecla 9)
    process_keyboard_buttons(kbd, s)
    process_keyboard_buttons(kbd, OFF)          # release → activa mode acords
    assert kbd.chord_mode_active

    kbd.midi.sent.clear()
    s = list(OFF); s[0] = True                  # tecla 1 → acord
    process_keyboard_buttons(kbd, s)
    noms = [type(m).__name__ for m in kbd.midi.sent]
    ons = [i for i, n in enumerate(noms) if n.endswith('NoteOn')]
    assert len(ons) >= 3                        # m7 = 4 notes; mínim 3
    # Consecutius: cap altre missatge entre el primer i l'últim NoteOn
    assert ons == list(range(ons[0], ons[0] + len(ons)))
    process_keyboard_buttons(kbd, OFF)
