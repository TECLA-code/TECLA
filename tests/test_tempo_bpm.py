"""Tempo en BPM per a la PANTALLA virtual.

El pols que es veu a la pantalla ha de ser el que SONA, en negres per minut,
per poder sincronitzar-lo amb la peça que s'està tocant. Tres famílies:
  · patró (techno, acid, euclid…) → self.bpm, ja en negres per minut
  · melòdics (Bach, Glass, Satie…) → self.speed, segons per nota
  · directe (live_*) → self.interval, segons per pas
Les dues últimes donen una CADÈNCIA de notes (fins a 1500/min): es plega a
l'octava de tempo útil i la subdivisió diu què s'hi toca.
"""
import importlib
import inspect
import os

import pytest

from conftest import FakeMidiOut

from modes.mm_update import mode_tempo, _report_mode_bpm
from modes.kbd_pots import _report_bpm, apply_arp_pot_function, apply_pot_function
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


# ── mode_tempo: les tres famílies ──────────────────────────────────────────

def test_mode_de_patro_diu_el_seu_bpm_musical():
    m = _Fake(); m.bpm = 128.0
    assert mode_tempo(m) == (128, 1)


def test_mode_melodic_converteix_segons_per_nota_a_bpm():
    m = _Fake(); m.speed = 0.5          # una nota cada mig segon
    assert mode_tempo(m) == (120, 1)


def test_mode_de_directe_converteix_l_interval_a_bpm():
    m = _Fake(); m.interval = 0.25      # un pas cada quart de segon
    assert mode_tempo(m) == (240, 1)


def test_mode_sense_pols_no_diu_res():
    assert mode_tempo(_Fake()) is None
    m = _Fake(); m.speed = 0            # cap divisió per zero
    assert mode_tempo(m) is None


def test_bpm_al_mode_es_prioritari_sobre_els_segons():
    """Els modes de patró tenen tots dos (bpm musical + step_dur): manen les
    negres per minut, que és el número amb què l'usuari sincronitza."""
    m = _Fake(); m.bpm = 135.0; m.speed = 0.11
    assert mode_tempo(m) == (135, 1)


# ── El plegat: una cadència ràpida es diu com un tempo de debò ─────────────

@pytest.mark.parametrize('notes_per_minut,esperat', [
    (120, (120, 1)),      # ja és un tempo: negres
    (240, (240, 1)),      # just al límit
    (241, (121, 2)),      # passat el límit: corxeres
    (856, (214, 4)),      # Bach al màxim: semicorxeres a 214
    (1500, (188, 8)),     # el mode més ràpid del firmware: fuses
])
def test_la_cadencia_es_plega_a_tempo_musical(notes_per_minut, esperat):
    m = _Fake(); m.speed = 60.0 / notes_per_minut
    assert mode_tempo(m) == esperat


def test_el_plegat_conserva_la_cadencia_real():
    """El plegat és exacte, no una estimació: BPM × subdivisió × 4 ha de
    tornar a donar les notes per minut originals."""
    for npm in (300, 480, 856, 1000, 1500):
        m = _Fake(); m.speed = 60.0 / npm
        bpm, sub = mode_tempo(m)
        assert abs(bpm * sub - npm) <= sub, f'{npm} → {bpm}×{sub}'


def test_cap_mode_del_firmware_no_ensenya_un_bpm_absurd():
    """Barrent el pot de velocitat de TOTS els modes, el número que arriba a
    la pantalla s'ha de quedar dins d'un rang de tempo creïble.
    Regressió: l'arpegiador arribava a dir "2000 BPM"."""
    MD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'codi', 'device_files', 'modes')
    dolents = []
    for f in sorted(os.listdir(MD)):
        if not f.startswith('mode_') or not f.endswith('.py'):
            continue
        try:
            mod = importlib.import_module('modes.' + f[:-3])
        except Exception:
            continue
        cls = next((o for n, o in vars(mod).items()
                    if inspect.isclass(o) and o.__module__ == mod.__name__
                    and n.startswith('Mode')), None)
        if cls is None:
            continue
        try:
            mode = cls(FakeMidiOut()); mode.setup()
        except Exception:
            continue
        for v in (0, 32, 64, 96, 127):
            try:
                mode.update([v, 64, 64], [False] * 16)
            except Exception:
                pass
            t = mode_tempo(mode)
            if t and not (20 <= t[0] <= 240):
                dolents.append((f[:-3], v, t))
    assert not dolents, f'tempos fora de rang: {dolents[:6]}'


# ── Modes REALS: el pols existeix i puja amb el pot de velocitat ───────────

@pytest.mark.parametrize('modul,classe', [
    ('mode_bach', 'ModeBach'),
    ('mode_glass', 'ModeGlass'),
    ('mode_satie', 'ModeSatie'),
    ('mode_part', 'ModePart'),
    ('mode_live_pols', 'ModeLivePols'),
    ('mode_techno', 'ModeTechno'),
])
def test_els_modes_reals_donen_pols_i_puja_amb_el_pot(modul, classe):
    mod = importlib.import_module('modes.' + modul)
    mode = getattr(mod, classe)(FakeMidiOut())
    mode.setup()
    # El pot de velocitat és pot_values[0] (el pot FÍSIC Y) a tots els modes
    mode.update([10, 64, 64], [False] * 16)
    lent = mode_tempo(mode)
    mode.update([120, 64, 64], [False] * 16)
    rapid = mode_tempo(mode)
    assert lent is not None and rapid is not None
    # La cadència real (BPM × subdivisió) sempre creix amb el pot
    assert rapid[0] * rapid[1] > lent[0] * lent[1], \
        f'{classe}: el pot de velocitat no accelera el pols'


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


def test_la_subdivisio_acompanya_el_tempo(console, capsys):
    mgr = _mgr()
    mgr.current_mode = _Fake()
    mgr.current_mode.speed = 0.5        # 120 notes/min: negres
    _report_mode_bpm(mgr)
    mgr.current_mode.speed = 60.0 / 856  # Bach al màxim
    _report_mode_bpm(mgr)
    assert capsys.readouterr().out.strip() == '♩ 214 BPM 1/16'


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


# ── Arpegiador: tempo de metrònom (40–240) en semicorxeres ────────────────

def _kbd():
    return KeyboardMode(FakeMidiOut(), {'octave': 4}, config_manager=None)


@pytest.mark.parametrize('pot,bpm', [(0, 40), (64, 141), (127, 240)])
def test_el_pot_de_l_arp_es_un_tempo_de_metronom(pot, bpm):
    """Rang realista: 40–240 negres per minut, com un metrònom o un DAW.
    Regressió: abans anava de 30 a 2000 passos/min (33 notes per segon a
    dalt i mitja nota per segon a baix — mig recorregut inservible)."""
    kbd = _kbd()
    kbd.arp_pot_x_function = 'Velocitat (BPM)'
    apply_arp_pot_function(kbd, 'arp_pot_x', pot)
    assert round(15.0 / kbd.arp_speed) == pytest.approx(bpm, abs=1)


def test_l_arp_trepitja_semicorxeres_del_tempo():
    """4 passos per negra: el que s'espera d'un arpegiador i el que fa que el
    número de la pantalla sigui el mateix que es posa al DAW."""
    kbd = _kbd()
    kbd.arp_pot_x_function = 'Velocitat (BPM)'
    apply_arp_pot_function(kbd, 'arp_pot_x', 127)      # 240 BPM
    assert kbd.arp_speed == pytest.approx(60.0 / 240 / 4)


def test_l_arpegiador_diu_el_tempo_amb_la_subdivisio(console, capsys):
    kbd = _kbd()
    kbd.arp_pot_x_function = 'Velocitat (BPM)'
    apply_arp_pot_function(kbd, 'arp_pot_x', 0)      # llavor en silenci
    capsys.readouterr()
    apply_arp_pot_function(kbd, 'arp_pot_x', 64)
    sortida = capsys.readouterr().out.strip()
    assert sortida == '♩ 141 BPM 1/16'


def test_el_tempo_de_l_arp_no_es_diu_en_cru(console, capsys):
    """Regressió: abans sortia "Pot Velocitat: 1022" — un número sense unitat
    que no servia per sincronitzar."""
    kbd = _kbd()
    kbd.arp_pot_x_function = 'Velocitat (BPM)'
    apply_arp_pot_function(kbd, 'arp_pot_x', 0)
    apply_arp_pot_function(kbd, 'arp_pot_x', 64)
    assert 'Pot Velocitat' not in capsys.readouterr().out


def test_el_pot_dual_fa_el_mateix_tempo_que_el_de_l_arp(console, capsys):
    """Brillantor/Velocitat (dual) movia l'arp fins a 100 notes per segon."""
    kbd = _kbd()
    kbd.pot_x_function = 'Velocity/Arp Speed (dual)'
    kbd.arp_mode_active = True
    apply_pot_function(kbd, 'pot_x', 127)
    assert round(15.0 / kbd.arp_speed) == pytest.approx(240, abs=1)
    kbd2 = _kbd()
    kbd2.arp_pot_x_function = 'Velocitat (BPM)'
    apply_arp_pot_function(kbd2, 'arp_pot_x', 127)
    assert kbd.arp_speed == pytest.approx(kbd2.arp_speed)


def test_el_llindar_del_tempo_de_l_arp_evita_l_allau(console, capsys):
    kbd = _Fake()
    _report_bpm(kbd, 120)
    capsys.readouterr()
    _report_bpm(kbd, 121)              # per sota del llindar
    assert capsys.readouterr().out == ''
    _report_bpm(kbd, 140)
    assert capsys.readouterr().out.strip() == '♩ 140 BPM'
