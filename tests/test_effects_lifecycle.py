"""Tests del cicle de vida dels efectes temporals (v3.1.2).

Els bugs reportats al dispositiu real:
  - Efecte Sustain actiu → canvi de mode → el sustain PERSISTIA (CC64=127
    latched al synth). Només 'Config Modes' i 'Loop' han de sobreviure.
  - STOP (tecla 16) posava active=False sense cridar on_deactivate: el pedal
    CC64 quedava premut i la següent nota del teclat quedava ENGANXADA
    ("el botó 16 no atura el so").
  - Els efectes enviaven 16 CCs per CICLE (~2ms) → inundació USB i latència.
  - EffectPitchBend enviava PitchBend(0) = bend a fons AVALL en desactivar
    (el centre és 8192): el synth quedava desafinat.
"""
import json

from conftest import FakeMidiOut

from core.config_manager import ConfigManager
from modes.mode_manager import ModeManager
from modes.mm_update import mm_activate_efecte_temporal
from modes.mm_cleanup import mm_emergency_stop


def _mgr(tmp_path, efectos=None):
    cfg = {
        'banks': [
            {'name': 'Ritmes', 'type': 'modes', 'modes': [''] * 16},
        ],
        'current_bank': 0,
        'efectos_temporales': efectos or {'13': 'Sustain', '14': 'Loop'},
    }
    p = tmp_path / 'cfg.json'
    with open(p, 'w') as f:
        json.dump(cfg, f)
    cm = ConfigManager(config_path=str(p))
    return ModeManager(FakeMidiOut(), config_manager=cm)


def _ccs(midi, control):
    return [m for m in midi.sent
            if type(m).__name__.endswith('ControlChange') and m.control == control]


def test_stop_desactiva_el_sustain_de_veritat(tmp_path):
    """STOP ha d'aixecar el pedal: CC64=0 via on_deactivate (abans només
    marcava active=False i el synth es quedava amb CC64=127 per sempre)."""
    mgr = _mgr(tmp_path)
    mm_activate_efecte_temporal(mgr, 13)
    assert mgr.efectes_temporals[13]['active']
    assert mgr.effect_manager.active_name == 'Sustain'
    assert any(m.value == 127 for m in _ccs(mgr.midi_out, 64)), "no s'ha premut el pedal"

    mgr.midi_out.sent.clear()
    mm_emergency_stop(mgr)

    assert not mgr.efectes_temporals[13]['active']
    assert mgr.effect_manager.active_name is None
    vals64 = [m.value for m in _ccs(mgr.midi_out, 64)]
    assert vals64 and all(v == 0 for v in vals64), f"el pedal no s'ha aixecat: {vals64}"


def test_canvi_de_mode_desactiva_sustain_pero_no_loop(tmp_path):
    """Canviar de mode desactiva els efectes NO persistents; 'Loop' sobreviu."""
    mgr = _mgr(tmp_path)
    mm_activate_efecte_temporal(mgr, 13)          # Sustain ON
    # Loop actiu (l'estat del loop viu a _modeloop; aquí simulem el latch)
    mgr.efectes_temporals[14]['active'] = True

    mgr.midi_out.sent.clear()
    mgr.set_mode('Teclat')                        # únic mode sempre disponible

    assert not mgr.efectes_temporals[13]['active'], "el Sustain ha de caure amb el canvi de mode"
    assert mgr.effect_manager.active_name is None
    assert any(m.value == 0 for m in _ccs(mgr.midi_out, 64)), "no s'ha enviat CC64=0"
    assert mgr.efectes_temporals[14]['active'], "el Loop ha de sobreviure el canvi de mode"
    assert not mgr.sustain_active


def test_efectes_no_inunden_usb_amb_valors_repetits(tmp_path):
    """update_params s'executa a cada cicle (~2ms): amb el mateix valor NO ha
    de reenviar res (abans: 16 CCs per cicle = 8000 msg/s)."""
    from effects.effect_sustain import EffectSustain
    midi = FakeMidiOut()
    eff = EffectSustain(midi)
    eff.update_params(90, 0, 0)
    n1 = len(midi.sent)
    for _ in range(50):
        eff.update_params(90, 0, 0)
    assert len(midi.sent) == n1, "valors repetits han generat tràfic MIDI"
    eff.update_params(95, 0, 0)   # canvi real → sí que envia
    assert len(midi.sent) > n1


def test_pitchbend_es_desactiva_al_centre(tmp_path):
    """En desactivar, el pitch bend ha de tornar al CENTRE (8192), no a 0
    (que és bend a fons avall i deixava el so desafinat)."""
    from effects.effect_pitchbend import EffectPitchBend
    midi = FakeMidiOut()
    eff = EffectPitchBend(midi)
    eff.update_params(127, 0, 0)   # bend amunt
    eff.on_deactivate()
    pbs = [m for m in midi.sent if type(m).__name__.endswith('PitchBend')]
    assert pbs, "no s'ha enviat cap PitchBend"
    assert getattr(pbs[-1], 'pitch_bend', None) == 8192, \
        f"el darrer bend no és al centre: {getattr(pbs[-1], 'pitch_bend', None)}"


def test_config_modes_i_loop_sobreviuen_stop_pero_es_reinicien(tmp_path):
    """STOP també atura Config Modes i Loop (l'usuari vol silenci TOTAL):
    mm_deactivate_efecte_temporal els apaga (potcfg.off / loop.clear)."""
    mgr = _mgr(tmp_path, efectos={'13': 'Config Modes', '14': 'Loop'})
    # Activa la capa de potes (lazy)
    from modes.mm_update import _potcfg
    lay = _potcfg(mgr)
    lay.cycle([0, 0, 0])
    mgr.efectes_temporals[13]['active'] = lay.active
    assert lay.active

    mm_emergency_stop(mgr)
    assert not lay.active, "STOP ha d'apagar la capa de potes"
    assert not mgr.efectes_temporals[13]['active']
