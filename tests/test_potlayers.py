"""Tests de 'Config Modes' (modes/potlayers.py): capes de potes per al mode actiu."""
from conftest import FakeMidiOut

from modes.potlayers import PotLayers, potfn_to_cc, DEFAULT_MODE_POT_LAYERS


def _ccs(out):
    return [(m.control, m.value) for m in out.sent if 'ControlChange' in type(m).__name__]


# ── potfn_to_cc ───────────────────────────────────────────────────────────────

def test_potfn_to_cc_digits_manen():
    assert potfn_to_cc('Reverb (CC91)') == 91
    assert potfn_to_cc('CC Lliure (CC74)') == 74


def test_potfn_to_cc_noms_pelats():
    assert potfn_to_cc('Volum') == 7
    assert potfn_to_cc('Filtre') == 74
    assert potfn_to_cc('inexistent') is None
    assert potfn_to_cc(None) is None


# ── Cicle de capes ────────────────────────────────────────────────────────────

def test_cicle_off_capes_off():
    lay = PotLayers()
    assert not lay.active
    noms = []
    for _ in range(len(DEFAULT_MODE_POT_LAYERS)):
        lay.cycle([0, 0, 0])
        noms.append(lay.name())
    assert noms == ['Mescla', 'Timbre', 'Expressio']
    lay.cycle([0, 0, 0])                      # després de l'última → OFF
    assert not lay.active


def test_capes_custom_de_la_config():
    lay = PotLayers([{'name': 'Meva', 'x': 'Volum', 'y': 'Pan (CC10)', 'z': 'Reverb (CC91)'}])
    lay.cycle([0, 0, 0])
    assert lay.name() == 'Meva'
    lay.cycle([0, 0, 0])
    assert not lay.active


# ── Pickup i enviament de CCs ─────────────────────────────────────────────────

def test_pickup_no_envia_fins_que_el_pot_es_mou():
    out = FakeMidiOut()
    lay = PotLayers()
    lay.cycle([64, 64, 64])                   # activa Mescla; base = 64
    lay.apply(out, [64, 64, 64])              # cap moviment → res
    assert _ccs(out) == []
    lay.apply(out, [80, 64, 64])              # pot X es mou → CC7 (Volum)
    assert (7, 80) in _ccs(out)
    assert all(cc == 7 for cc, _v in _ccs(out))   # els altres continuen dormits


def test_cache_no_repeteix_valors():
    out = FakeMidiOut()
    lay = PotLayers()
    lay.cycle([0, 0, 0])
    lay.apply(out, [90, 0, 0])
    n = len(_ccs(out))
    lay.apply(out, [90, 0, 0])                # mateix valor → cap enviament nou
    assert len(_ccs(out)) == n


def test_off_atura_l_enviament():
    out = FakeMidiOut()
    lay = PotLayers()
    lay.cycle([0, 0, 0])
    lay.off()
    lay.apply(out, [90, 90, 90])
    assert _ccs(out) == []
