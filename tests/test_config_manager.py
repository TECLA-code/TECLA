"""Tests del ConfigManager (codi/device_files/core/config_manager.py)."""
import json
import os

import pytest

from core.config_manager import ConfigManager


@pytest.fixture
def config_path(tmp_path):
    return str(tmp_path / 'tecla_config.json')


@pytest.fixture
def manager(config_path):
    return ConfigManager(config_path=config_path)


# ── Càrrega i valors per defecte ─────────────────────────────────────────────

def test_crea_config_per_defecte_si_no_existeix(config_path):
    cm = ConfigManager(config_path=config_path)
    assert os.path.exists(config_path)
    banks = cm.config['banks']
    assert len(banks) == 5
    assert banks[0]['type'] == 'teclat'          # arrenca al teclat
    assert all(b['type'] == 'modes' for b in banks[1:])
    for bank in banks:
        assert len(bank['modes']) == 16


def test_json_corrupte_cau_a_defecte(config_path):
    with open(config_path, 'w') as f:
        f.write('{trencat]]]')
    cm = ConfigManager(config_path=config_path)
    assert 'banks' in cm.config


def test_config_sense_banks_cau_a_defecte(config_path):
    with open(config_path, 'w') as f:
        json.dump({'una_altra_cosa': 1}, f)
    cm = ConfigManager(config_path=config_path)
    assert len(cm.config['banks']) == 5


def test_mode_teclat_es_substitueix_per_silenci(config_path):
    cfg = {'banks': [{'name': 'X', 'modes': ['Teclat'] * 4}], 'current_bank': 0}
    with open(config_path, 'w') as f:
        json.dump(cfg, f)
    cm = ConfigManager(config_path=config_path)
    modes = cm.config['banks'][0]['modes']
    assert 'Teclat' not in modes
    assert len(modes) == 16  # s'amplia fins a 16


def test_migracio_camps_nivell_superior_cap_als_bancs(config_path):
    pot_fns = {'pot_x': 'A', 'pot_y': 'B', 'pot_z': 'C'}
    cfg = {
        'banks': [{'name': 'X', 'modes': ['Silenci'] * 16}],
        'potentiometer_functions': pot_fns,
    }
    with open(config_path, 'w') as f:
        json.dump(cfg, f)
    cm = ConfigManager(config_path=config_path)
    assert cm.config['banks'][0]['potentiometer_functions'] == pot_fns


# ── Bancs ────────────────────────────────────────────────────────────────────

def test_next_bank_es_ciclic(manager):
    n = len(manager.config['banks'])
    inicial = manager.current_bank_index
    for _ in range(n):
        manager.next_bank()
    assert manager.current_bank_index == inicial


def test_get_current_bank_index_invalid_retorna_none(manager):
    manager.current_bank_index = 99
    assert manager.get_current_bank() is None


# ── Hash de configuració ─────────────────────────────────────────────────────

def test_hash_independent_del_banc_actiu(manager):
    """CRÍTIC: si el hash depengués del banc actiu, el bucle principal
    recarregaria la config a cada canvi de capa i el revertiria."""
    h0 = manager.get_config_hash()
    manager.next_bank()
    assert manager.get_config_hash() == h0


def test_hash_canvia_si_canvia_un_mode(manager):
    h0 = manager.get_config_hash()
    manager.config['banks'][0]['modes'][0] = 'UnModeNou'
    assert manager.get_config_hash() != h0


# ── Progressions ─────────────────────────────────────────────────────────────

def test_ids_progressions_unics_i_sequencials(manager):
    id1 = manager.create_progression('Una', [{'button': 0}])
    id2 = manager.create_progression('Dues', [{'button': 1}])
    assert id1 != id2
    assert id1 == 'prog_1'
    assert id2 == 'prog_2'


def test_ids_progressions_no_es_reutilitzen_apres_esborrar(manager):
    id1 = manager.create_progression('Una', [])
    id2 = manager.create_progression('Dues', [])
    manager.delete_progression(id1)
    id3 = manager.create_progression('Tres', [])
    # id2 encara existeix: id3 no pot col·lidir-hi
    assert id3 != id2


def test_ids_progressions_compatibles_amb_format_antic(manager):
    # IDs antics derivats de time.monotonic (números grans)
    manager.config['custom_chord_progressions'] = [{'id': 'prog_173456', 'name': 'Antiga', 'chords': []}]
    nou = manager.create_progression('Nova', [])
    assert nou == 'prog_173457'


def test_progression_crud(manager):
    pid = manager.create_progression('Prova', [{'button': 0, 'root_note': 60}])
    assert manager.get_progression_by_id(pid)['name'] == 'Prova'
    assert manager.update_progression(pid, name='Canviada')
    assert manager.get_progression_by_id(pid)['name'] == 'Canviada'
    assert manager.delete_progression(pid)
    assert manager.get_progression_by_id(pid) is None


# ── Robustesa amb config corrupta ────────────────────────────────────────────

def test_neg_harmony_type_robust(manager):
    manager.config['neg_harmony_type'] = 'porqueria'
    assert manager.get_neg_harmony_type() == 0
    manager.config['neg_harmony_type'] = 12
    assert manager.get_neg_harmony_type() == 0
    manager.config['neg_harmony_type'] = '5'
    assert manager.get_neg_harmony_type() == 5


def test_neg_harmony_axes_robust(manager):
    manager.config['neg_harmony_axes'] = ['2', 'x', 9, 3]
    assert manager.get_neg_harmony_axes() == [2, 3]
    manager.config['neg_harmony_axes'] = ['x']  # cap de vàlid → tots
    assert manager.get_neg_harmony_axes() == list(range(8))


def test_keyboard_scales_llista_buida_cau_a_defecte(manager):
    manager.config['banks'][0]['keyboard_scales'] = []
    scales = manager.get_keyboard_scales(0)
    assert scales == [0, 1, 4, 5, 7, 8, 13, 15, 18, 19]


def test_midi_channel_validacio(manager):
    assert not manager.set_midi_channel(0)
    assert not manager.set_midi_channel(17)
    assert manager.set_midi_channel(10)
    assert manager.get_midi_channel() == 10


# ── Capes tipades (v3): tipus per banc i config de teclat PER-CAPA ───────────

def test_migracio_tipa_les_capes_i_garanteix_teclat(config_path):
    """Configs antigues sense 'type': tots els bancs passen a 'modes' i
    s'afegeix una capa de teclat al final (la tecla 13 cicla les capes i el
    teclat ha de ser sempre accessible)."""
    cfg = {'banks': [{'name': 'A', 'modes': ['Silenci'] * 16},
                     {'name': 'B', 'modes': ['Silenci'] * 16}], 'current_bank': 0}
    with open(config_path, 'w') as f:
        json.dump(cfg, f)
    cm = ConfigManager(config_path=config_path)
    banks = cm.config['banks']
    assert [b['type'] for b in banks[:2]] == ['modes', 'modes']
    assert banks[-1]['type'] == 'teclat'


def test_config_teclat_es_llegeix_per_capa(config_path):
    """Dues capes de teclat amb configs diferents: els getters han de retornar
    la config de la capa ACTIVA (el bug del dispositiu: la segona capa de
    teclat repetia la primera)."""
    cfg = {
        'banks': [
            {'name': 'Teclat A', 'type': 'teclat', 'modes': ['Silenci'] * 16,
             'keyboard_button_functions': ['note'] * 8 + ['scale', 'tonality', 'chord', 'arp',
                                                          'modes_layer', 'octave_down', 'octave_up', 'stop'],
             'voice_lead_types': ['proximitat'],
             'neg_harmony_type': 0,
             'keyboard_scales': [0]},
            {'name': 'Acords', 'type': 'teclat', 'modes': ['Silenci'] * 16,
             'keyboard_button_functions': ['note'] * 8 + ['chord', 'voice_lead', 'diatonic', 'latch',
                                                          'modes_layer', 'octave_down', 'octave_up', 'stop'],
             'voice_lead_types': ['obert', 'baix'],
             'neg_harmony_type': 4,
             'keyboard_scales': [5, 7]},
        ],
        'current_bank': 0,
    }
    with open(config_path, 'w') as f:
        json.dump(cfg, f)
    cm = ConfigManager(config_path=config_path)

    assert cm.get_keyboard_button_functions()[8] == 'scale'
    assert cm.get_voice_lead_types() == ['proximitat']
    assert cm.get_neg_harmony_type() == 0
    assert cm.get_keyboard_scales() == [0]

    cm.set_current_bank(1)   # la tecla 13 cicla cap a la segona capa de teclat
    assert cm.get_keyboard_button_functions()[8] == 'chord'
    assert cm.get_keyboard_button_functions()[9] == 'voice_lead'
    assert cm.get_voice_lead_types() == ['obert', 'baix']
    assert cm.get_neg_harmony_type() == 4
    assert cm.get_keyboard_scales() == [5, 7]


def test_config_teclat_cau_a_global_si_la_capa_no_en_te(config_path):
    """Capa de teclat sense config pròpia: fallback a la config global."""
    cfg = {
        'banks': [{'name': 'T', 'type': 'teclat', 'modes': ['Silenci'] * 16}],
        'current_bank': 0,
        'keyboard_button_functions': ['note'] * 8 + ['latch', 'looper', 'chord', 'arp',
                                                     'modes_layer', 'octave_down', 'octave_up', 'stop'],
        'voice_lead_types': ['comu'],
    }
    with open(config_path, 'w') as f:
        json.dump(cfg, f)
    cm = ConfigManager(config_path=config_path)
    assert cm.get_keyboard_button_functions()[8] == 'latch'
    assert cm.get_voice_lead_types() == ['comu']
