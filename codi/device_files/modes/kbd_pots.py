"""Funcions de potenciòmetre per al Mode Teclat - mòdul separat per estalviar RAM"""



try:
    from core.pantalla import diu
except Exception:                       # simulador i proves sense core/
    def diu(text):
        print(text)
        return True
def _try_free_cc(kbd, function, pot_value, threshold):
    """CC lliure: el número de CC viatja dins el nom de la funció.
    Format: 'CC Lliure (CC74)' → envia CC74. Retorna True si s'ha gestionat."""
    if not function.startswith('CC Lliure'):
        return False
    digits = ''
    for ch in function[9:]:
        if '0' <= ch <= '9':
            digits += ch
    if digits:
        cc = min(127, int(digits))
        kbd._send_cc_if_changed(cc, pot_value, threshold=threshold)
    return True


_SYNTH_POT_CC = {
    'Filtre': 74,       # cutoff (Brightness)
    'Ressonància': 71,  # ressonància (Timbre)
    'Atac': 73,         # attack
    'Release': 72,      # release
    'LFO Vel.': 76,     # vibrato rate
    'LFO Prof.': 77,    # vibrato depth
    'Env Filtre': 78,   # filtre: quantitat d'envelope
    'Env Decay': 79,    # filtre: decay de l'envelope
    'LFO→Filtre': 80,   # LFO → cutoff (wobble)
    'Decay': 75,        # decay de l'ADSR
    'Env Sustain': 81,  # sustain de l'ADSR
    'Trèmol': 82,       # trèmol (profunditat)
    'Trèmol vel.': 83,  # trèmol (velocitat)
    'Detune': 85,       # desafinació de l'oscil·lador
    'Filtre tipus': 86, # LP / HP / BP
    'Pitch env': 87,    # envolupant de to
    "Forma d'ona": 70,  # forma d'ona
    'Volum': 7,         # volum
}


def _try_synth_cc(kbd, function, pot_value, threshold):
    """Funcions del sinte intern: el pot envia un Sound Controller estàndard que
    el motor d'àudio (core/audio_engine) interpreta com a cutoff/ressonància/ADSR/
    LFO. Mirall de _applyPotFn a index.html. Retorna True si s'ha gestionat."""
    cc = _SYNTH_POT_CC.get(function)
    if cc is None:
        return False
    kbd._send_cc_if_changed(cc, pot_value, threshold=threshold)
    return True


def _report(kbd, nom, valor):
    """Testimoni de pot per a la PANTALLA virtual de l'app: "Pot Nom: valor".
    Només amb consola connectada (cost zero en directe) i amb llindar per no
    inundar (el valor ha de moure's ≥3 passos). MAI pot llançar: un testimoni
    no pot trencar el so (i res de kbd.__dict__ — a CircuitPython no és fiable
    i trencava update() sencer amb la Pantalla connectada)."""
    try:
        from modes.kbd_notes import _console_on
        if not _console_on():
            return
        c = getattr(kbd, '_pot_report_cache', None)
        if c is None:
            c = {}
            kbd._pot_report_cache = c
        v = int(valor)
        if nom not in c:
            c[nom] = v      # primera lectura = sync de capa: silenci
            return
        if -3 < (v - c[nom]) < 3:
            return
        c[nom] = v
        diu("Pot %s: %d" % (nom, v))
    except Exception:
        pass


def _report_bpm(kbd, bpm, sub=1):
    """Testimoni de TEMPO per a la PANTALLA: "♩ 120 BPM 1/16". El tempo es diu
    en NEGRES per minut, com un metrònom o un DAW, i la fracció diu què s'hi
    trepitja (sub=4 → semicorxeres). Mateixes regles que _report (primera
    lectura en silenci, llindar, i mai llança)."""
    try:
        from modes.kbd_notes import _console_on
        if not _console_on():
            return
        c = getattr(kbd, '_pot_report_cache', None)
        if c is None:
            c = {}
            kbd._pot_report_cache = c
        v = int(bpm + 0.5)
        if '_bpm' not in c:
            c['_bpm'] = v
            return
        if -2 < (v - c['_bpm']) < 2:
            return
        c['_bpm'] = v
        if sub > 1:
            diu("♩ %d BPM 1/%d" % (v, sub * 4))
        else:
            diu("♩ %d BPM" % v)
    except Exception:
        pass


def _apply_audio_cfg_pots(kbd, pot_values, force_update):
    """Config àudio activa: els 3 potes editen el so segons el mapatge de la tecla
    activa. Mateix mapeig físic que la resta (X=pot[1], Y=pot[0], Z=pot[2])."""
    m = kbd.audio_pot_functions.get(str(kbd._audio_cfg_key)) or {'x': 'Filtre', 'y': 'Ressonància', 'z': "Forma d'ona"}
    threshold = 0 if force_update else 2
    _try_synth_cc(kbd, m.get('x', ''), pot_values[1], threshold)
    _try_synth_cc(kbd, m.get('y', ''), pot_values[0], threshold)
    _try_synth_cc(kbd, m.get('z', ''), pot_values[2], threshold)


def update_parameters(kbd, pot_values, force_update=False):
    if len(pot_values) < 3:
        return
    # Config àudio té prioritat: mentre activa, els potes editen el sinte (el
    # teclat segueix tocant amb la resta de paràmetres congelats de facto).
    if getattr(kbd, '_audio_cfg_key', -1) >= 0:
        _apply_audio_cfg_pots(kbd, pot_values, force_update)
        return
    # NOMÉS dues capes de potes: teclat i arpegiador. Les capes d'acords i
    # d'harmonia negativa s'han retirat (decisió de tancament v3.1: menys
    # sorpreses en directe — amb acords o h.neg actius els potes segueixen
    # fent les funcions del teclat).
    if kbd.arp_mode_active:
        apply_arp_pot_function(kbd, 'arp_pot_x', pot_values[1], force_update=force_update)
        apply_arp_pot_function(kbd, 'arp_pot_y', pot_values[0], force_update=force_update)
        apply_arp_pot_function(kbd, 'arp_pot_z', pot_values[2], force_update=force_update)
    else:
        apply_pot_function(kbd, 'pot_x', pot_values[1], force_update=force_update)
        apply_pot_function(kbd, 'pot_y', pot_values[0], force_update=force_update)
        apply_pot_function(kbd, 'pot_z', pot_values[2], force_update=force_update)


def apply_pot_function(kbd, pot_name, pot_value, force_update=False):
    if pot_name == 'pot_x':
        function = kbd.pot_x_function
    elif pot_name == 'pot_y':
        function = kbd.pot_y_function
    elif pot_name == 'pot_z':
        function = kbd.pot_z_function
    else:
        return

    threshold = 0 if force_update else 2

    if function in ('Brillantor', 'Velocity', 'Brightness (CC74)'):
        kbd.velocity = max(20, min(127, pot_value))
        _report(kbd, 'Brillantor', kbd.velocity)

    elif function == 'Velocity/Arp Speed (dual)':
        kbd.velocity = max(20, min(127, pot_value))
        _report(kbd, 'Brillantor', kbd.velocity)
        if kbd.arp_mode_active:
            # Mateix tempo musical que el pot de BPM de la capa d'arpegiador
            # (abans: 0.5–0.01 s per pas, fins a 100 notes per segon).
            bpm = 40 + (max(0, min(127, pot_value)) / 127.0) * 200
            kbd.arp_speed = 15.0 / bpm
            _report_bpm(kbd, bpm, 4)

    elif function in ('Modulació', 'Modulation', 'Modulation (CC1)'):
        kbd._send_cc_if_changed(1, pot_value, threshold=threshold)
        _report(kbd, 'Modulació', pot_value)

    elif function == 'Pitch Bend':
        if pot_value < 5:
            pitch_value = 0
        else:
            pitch_value = int((pot_value / 127.0) * 8191)
        kbd._send_pitch_bend(pitch_value)
        _report(kbd, 'Pitch Bend', pot_value)

    elif function in ('Volum', 'Volume', 'Expression (CC11)'):
        kbd._send_cc_if_changed(7, pot_value, threshold=threshold)
        _report(kbd, 'Volum', pot_value)

    elif function in ('Sustain', 'Sustain (CC64)'):
        # Sustain PROGRESSIU gestionat per TECLA (temps de release variable, sense CC64):
        # vegeu KeyboardMode._set_sustain. Independent del synth i del loop.
        kbd._set_sustain(pot_value)

    elif function in ('Gate', 'Gate Length'):
        if pot_value < 10:
            kbd.gate_enabled = False
            # UN cop: restaura l'expressió al màxim en apagar el gate. Amb
            # _send_cc s'enviava a cada volta mentre el pot fos < 10.
            kbd._send_cc_if_changed(11, 127, threshold=1)
        else:
            kbd.gate_enabled = True
            kbd.gate_period = 0.5 - (pot_value / 127.0) * 0.45
            kbd.gate_min_expr = 0
            kbd.gate_duty = 0.5
        _report(kbd, 'Gate', pot_value)

    elif function == 'Expression (CC11)':
        kbd._send_cc_if_changed(11, pot_value, threshold=threshold)

    elif function == 'Pan (CC10)':
        kbd._send_cc_if_changed(10, pot_value, threshold=threshold)

    elif function == 'Reverb (CC91)':
        kbd._send_cc_if_changed(91, pot_value, threshold=threshold)

    elif function == 'Chorus (CC93)':
        kbd._send_cc_if_changed(93, pot_value, threshold=threshold)

    elif function == 'Release (CC72)':
        kbd._send_cc_if_changed(72, pot_value, threshold=threshold)

    elif function == 'Octava':
        last_val = getattr(kbd, '_oct_pot_last_val', None)
        if last_val is None:
            kbd._oct_pot_last_val = pot_value
        elif abs(pot_value - last_val) >= 3:
            kbd._oct_pot_last_val = pot_value
            new_oct = min(8, max(0, round((pot_value / 127.0) * 8)))
            if new_oct != kbd.octave:
                kbd.octave = new_oct
                diu("Octava: %d" % kbd.octave)

    elif function == "Eix d'Harmonia":
        ids = kbd.available_neg_harm_ids if kbd.available_neg_harm_ids else list(range(8))
        last_val = getattr(kbd, '_neg_harm_pot_last_val', None)
        if last_val is None:
            kbd._neg_harm_pot_last_val = pot_value
        elif abs(pot_value - last_val) >= 3:
            kbd._neg_harm_pot_last_val = pot_value
            ci = min(int((pot_value / 128.0) * len(ids)), len(ids) - 1)
            new_type = ids[ci]
            if new_type != kbd.neg_harmony_type:
                kbd.neg_harmony_type = new_type
                _nh_names = ('Quinta', 'Unisonant', 'Terc.M', 'Terc.m', 'Tritó', 'Quarta', 'Sexta', 'Sept.m')
                diu("↕ Harmonia Negativa: %s" % _nh_names[new_type % 8])

    else:
        if not _try_synth_cc(kbd, function, pot_value, threshold):
            _try_free_cc(kbd, function, pot_value, threshold)

    if force_update and function not in ('Velocity/Arp Speed (dual)', 'Brillantor', 'Sustain', 'Modulació', 'Volum'):
        diu(f"🎹 Teclat Pot: {function}")


def apply_arp_pot_function(kbd, pot_name, pot_value, force_update=False):
    if pot_name == 'arp_pot_x':
        function = kbd.arp_pot_x_function
    elif pot_name == 'arp_pot_y':
        function = kbd.arp_pot_y_function
    elif pot_name == 'arp_pot_z':
        function = kbd.arp_pot_z_function
    else:
        return

    threshold = 0 if force_update else 2

    if function in ('Velocitat (BPM)', 'Arp Speed (BPM)'):
        # Tempo MUSICAL de negra (40–240, el rang d'un metrònom o d'un DAW) i
        # l'arpegiador trepitja SEMICORXERES d'aquest tempo. Abans el pot donava
        # 30–2000 passos/min: 33 notes per segon a dalt (un brunzit, no un tempo)
        # i mig segon per nota a baix, o sigui que la meitat del recorregut era
        # inservible. Ara el número que es veu és el que es posa al DAW.
        bpm = 40 + (pot_value / 127.0) * 200
        kbd.arp_speed = 15.0 / bpm            # 60/bpm/4 = una semicorxera
        _report_bpm(kbd, bpm, 4)

    elif function in ('Patró De Direcció', 'Arp Pattern Selector'):
        if len(kbd.available_arp_modes) > 0:
            last_val = kbd._arp_pat_sel_last_val
            if last_val is None:
                kbd._arp_pat_sel_last_val = pot_value
            elif abs(pot_value - last_val) >= 3:
                kbd._arp_pat_sel_last_val = pot_value
                num_modes = len(kbd.available_arp_modes)
                mode_idx = int((pot_value / 128.0) * num_modes)
                mode_idx = min(mode_idx, num_modes - 1)
                new_mode = kbd.available_arp_modes[mode_idx]
                if new_mode != kbd.arp_mode_index:
                    kbd.arp_mode_index = new_mode
                    kbd.arp_index = 0
                    kbd.arp_direction = 1
                    diu("🎶 Arpegiador: %s" % kbd._get_arp_name(kbd.arp_mode_index))

    elif function in ('Brillantor', 'Velocity'):
        kbd.velocity = max(20, min(127, pot_value))
        _report(kbd, 'Brillantor', kbd.velocity)

    elif function in ('Volum', 'Volume'):
        kbd._send_cc_if_changed(7, pot_value, threshold=threshold)
        _report(kbd, 'Volum', pot_value)

    elif function in ('Modulació', 'Modulation', 'Modulation (CC1)'):
        kbd._send_cc_if_changed(1, pot_value, threshold=threshold)
        _report(kbd, 'Modulació', pot_value)

    elif function == 'Pitch Bend':
        if pot_value < 5:
            pitch_value = 0
        else:
            pitch_value = int((pot_value / 127.0) * 8191)
        kbd._send_pitch_bend(pitch_value)
        _report(kbd, 'Pitch Bend', pot_value)

    elif function in ('Gate', 'Gate Length'):
        if pot_value < 10:
            kbd.gate_enabled = False
            # UN cop: restaura l'expressió al màxim en apagar el gate. Amb
            # _send_cc s'enviava a cada volta mentre el pot fos < 10.
            kbd._send_cc_if_changed(11, 127, threshold=1)
        else:
            kbd.gate_enabled = True
            kbd.gate_period = 0.5 - (pot_value / 127.0) * 0.45
            kbd.gate_min_expr = 0
            kbd.gate_duty = 0.5
        _report(kbd, 'Gate', pot_value)

    else:
        if not _try_synth_cc(kbd, function, pot_value, threshold):
            _try_free_cc(kbd, function, pot_value, threshold)

    if force_update and function not in ('Velocitat (BPM)', 'Arp Speed (BPM)', 'Patró De Direcció', 'Arp Pattern Selector'):
        diu(f"🎹 Arp Pot: {function}")


# (apply_chord_pot_function i apply_neg_pot_function s'han retirat: les capes
#  de potes d'acords i d'harmonia negativa ja no existeixen — vegeu
#  update_parameters. Amb acords o h.neg actius, els potes fan les funcions
#  del teclat.)
