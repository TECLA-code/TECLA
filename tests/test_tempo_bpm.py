"""Tempo en BPM per a la PANTALLA virtual.

El pols que es veu a la pantalla ha de ser el que SONA, en BPM, per poder
sincronitzar-lo amb la peça que s'està tocant. Tres famílies de modes:
  · patró (techno, acid, euclid…) → self.bpm, ja en negres per minut
  · melòdics (Bach, Glass, Satie…) → self.speed, segons per nota
  · directe (live_*) → self.interval, segons per pas
"""
import importlib

import pytest

from conftest import FakeMidiOut

from modes.mm_update import mode_bpm, _report_mode_bpm
from modes.kbd_pots import _report_bpm, apply_arp_pot_function
from modes.mode_keyboard import KeyboardMode


@pytest.fixture
def console(monkeypatch):
    """Consola connectada: els testimonis de la pantalla només s'emeten
    quan algú els llegeix (en directe no costen res)."""
    import supervisor

    class _Runtime:
        serial_connected = True

    monkeypatch.setattr(supervisor, 'runtime', _Runtime(), raising=False)


class _Fake:
    pass


# ── mode_bpm: les tres famílies ────────────────────────────────────────────

def test_mode_de_patro_diu_el_seu_bpm_musical():
    m = _Fake(); m.bpm = 128.0
    assert mode_bpm(m) == 128


def test_mode_melodic_converteix_segons_per_nota_a_bpm():
    m = _Fake(); m.speed = 0.5          # una nota cada mig segon
    assert mode_bpm(m) == 120


def test_mode_de_directe_converteix_l_interval_a_bpm():
    m = _Fake(); m.interval = 0.25      # un pas cada quart de segon
    assert mode_bpm(m) == 240


def test_mode_sense_pols_no_diu_res():
    assert mode_bpm(_Fake()) is None
    m = _Fake(); m.speed = 0            # cap divisió per zero
    assert mode_bpm(m) is None


def test_bpm_al_mode_es_prioritari_sobre_els_segons():
    """Els modes de patró tenen tots dos (bpm musical + step_dur): manen les
    negres per minut, que és el número amb què l'usuari sincronitza."""
    m = _Fake(); m.bpm = 135.0; m.speed = 0.11
    assert mode_bpm(m) == 135


# ── Modes REALS: el BPM existeix i puja amb el pot de velocitat ────────────

@pytest.mark.parametrize('modul,classe', [
    ('mode_bach', 'ModeBach'),
    ('mode_glass', 'ModeGlass'),
    ('mode_satie', 'ModeSatie'),
    ('mode_part', 'ModePart'),
    ('mode_live_pols', 'ModeLivePols'),
    ('mode_techno', 'ModeTechno'),
])
def test_els_modes_reals_donen_bpm_i_puja_amb_el_pot(modul, classe):
    mod = importlib.import_module('modes.' + modul)
    mode = getattr(mod, classe)(FakeMidiOut())
    mode.setup()
    # El pot de velocitat és pot_values[0] (el pot FÍSIC Y) a tots els modes
    mode.update([10, 64, 64], [False] * 16)
    lent = mode_bpm(mode)
    mode.update([120, 64, 64], [False] * 16)
    rapid = mode_bpm(mode)
    assert lent is not None and rapid is not None
    assert rapid > lent, f'{classe}: el pot de velocitat no accelera el pols'


# ── Testimoni del mode: només quan el tempo canvia de debò ────────────────

def _mgr(nom='Bach', bpm=120.0):
    mgr = _Fake()
    mgr.current_mode_name = nom
    mgr.current_mode = _Fake()
    mgr.current_mode.bpm = bpm
    return mgr


def test_el_primer_tempo_d_un_mode_no_tapa_el_nom_del_mode(console, capsys):
    mgr = _mgr()
    _report_mode_bpm(mgr)
    assert capsys.readouterr().out == ''


def test_el_canvi_de_tempo_es_diu_en_bpm(console, capsys):
    mgr = _mgr()
    _report_mode_bpm(mgr)               # llavor en silenci
    mgr.current_mode.bpm = 96.0
    _report_mode_bpm(mgr)
    assert capsys.readouterr().out.strip() == '♩ 96 BPM'


def test_el_tempo_quiet_no_inunda_la_pantalla(console, capsys):
    mgr = _mgr()
    _report_mode_bpm(mgr)
    capsys.readouterr()
    mgr.current_mode.bpm = 120.4       # micro-deriva: per sota del llindar
    for _ in range(50):
        _report_mode_bpm(mgr)
    assert capsys.readouterr().out == ''


def test_cada_mode_nou_torna_a_començar_en_silenci(console, capsys):
    mgr = _mgr()
    _report_mode_bpm(mgr)
    mgr.current_mode.bpm = 96.0
    _report_mode_bpm(mgr)
    capsys.readouterr()
    mgr.current_mode_name = 'Techno'    # canvi de mode: el nou tempo és llavor
    mgr.current_mode = _Fake()
    mgr.current_mode.bpm = 128.0
    _report_mode_bpm(mgr)
    assert capsys.readouterr().out == ''


def test_sense_consola_el_tempo_no_costa_res(capsys):
    mgr = _mgr()
    _report_mode_bpm(mgr)
    mgr.current_mode.bpm = 60.0
    _report_mode_bpm(mgr)
    assert capsys.readouterr().out == ''


def test_un_mode_sense_pols_no_diu_tempo(console, capsys):
    mgr = _mgr()
    mgr.current_mode = _Fake()          # cap atribut de tempo
    _report_mode_bpm(mgr)
    _report_mode_bpm(mgr)
    assert capsys.readouterr().out == ''


def test_el_testimoni_de_tempo_mai_trenca_el_so(console, capsys):
    """Un testimoni és decoració: si falla, calla (mai no puja l'excepció:
    a CircuitPython una excepció aquí es menjava tot l'update del mode)."""
    _report_mode_bpm(None)
    _report_mode_bpm(_Fake())


# ── Arpegiador de la capa de teclat: el pot de velocitat parla en BPM ─────

def test_l_arpegiador_diu_el_tempo_en_bpm(console, capsys):
    kbd = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)
    kbd.arp_pot_x_function = 'Velocitat (BPM)'
    apply_arp_pot_function(kbd, 'arp_pot_x', 0)      # llavor en silenci
    capsys.readouterr()
    apply_arp_pot_function(kbd, 'arp_pot_x', 64)
    sortida = capsys.readouterr().out.strip()
    assert sortida.startswith('♩ ') and sortida.endswith(' BPM')
    # El número dit és el pols real que sona (60 / segons per pas)
    assert int(sortida.split()[1]) == pytest.approx(round(60.0 / kbd.arp_speed), abs=1)


def test_el_tempo_de_l_arp_no_es_diu_en_cru(console, capsys):
    """Regressió: abans sortia "Pot Velocitat: 1022" — un número sense unitat
    que no servia per sincronitzar."""
    kbd = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)
    kbd.arp_pot_x_function = 'Velocitat (BPM)'
    apply_arp_pot_function(kbd, 'arp_pot_x', 0)
    apply_arp_pot_function(kbd, 'arp_pot_x', 64)
    assert 'Pot Velocitat' not in capsys.readouterr().out


def test_el_pot_dual_diu_el_tempo_quan_l_arp_esta_actiu(console, capsys):
    from modes.kbd_pots import apply_pot_function
    kbd = KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)
    kbd.pot_x_function = 'Velocity/Arp Speed (dual)'
    kbd.arp_mode_active = True
    apply_pot_function(kbd, 'pot_x', 20)
    capsys.readouterr()
    apply_pot_function(kbd, 'pot_x', 100)
    assert '♩' in capsys.readouterr().out


def test_el_llindar_del_tempo_de_l_arp_evita_l_allau(console, capsys):
    kbd = _Fake()
    _report_bpm(kbd, 120)
    capsys.readouterr()
    _report_bpm(kbd, 121)              # per sota del llindar
    assert capsys.readouterr().out == ''
    _report_bpm(kbd, 140)
    assert capsys.readouterr().out.strip() == '♩ 140 BPM'
