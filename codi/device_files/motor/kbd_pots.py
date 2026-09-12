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
        from motor.kbd_notes import _console_on
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
        from motor.kbd_notes import _console_on
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


def _set_bpm(kbd, pot_value, force_update=False, sub=4):
    """Fixa el tempo de l'arpegiador des d'un pot, AMB HISTÈRESI.

    Sense ella, aquesta línia corria a cada volta del bucle —unes 500 per
    segon— amb el valor CRU de l'ADC. L'ADC de l'RP2040 balla ±1 tot sol, i
    ±1 aquí són ±1,6 BPM: `arp_speed` canviava contínuament i cada pas de
    l'arpegiador sortia d'una llargada lleugerament diferent. Reportat: «els
    loops generats i la funció d'acompanyament perden el tempo, no cauen
    sempre igual, hi ha destemps».

    I es notava DOBLE, perquè l'acompanyament sí que acumula passos exactes
    (`_next_t += step_s`): l'un ballava i l'altre anava clavat, o sigui que se
    separaven.

    Els germans d'aquest mateix fitxer ja ho feien bé (`abs(pot_value -
    last_val) >= 3` al selector de patró). Aquesta branca s'ho havia saltat.
    """
    last = getattr(kbd, '_bpm_pot_last', None)
    if not force_update and last is not None and abs(pot_value - last) < 2:
        return
    kbd._bpm_pot_last = pot_value
    bpm = 40 + (max(0, min(127, pot_value)) / 127.0) * 200
    kbd.arp_speed = 15.0 / bpm            # 60/bpm/4 = una semicorxera
    _report_bpm(kbd, bpm, sub)


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
    #
    # RECOLLIDA (pickup) EN CANVIAR DE CAPA. Un pot físic vol dir dues coses
    # segons si l'arpegiador està encès, i en commutar la capa el seu valor
    # ACTUAL passa a significar una altra cosa de cop.
    #
    # El cas real, amb la configuració de fàbrica de la capa Teclat Arp: el
    # pot 0 és `Modulació` amb l'arpegiador i `Octava` sense. Graves un loop
    # d'arpegi, baixes la modulació, apagues l'arp per tocar-hi acords a
    # sobre — i sense haver tocat el pot l'octava salta de 4 a 0. L'octava 0
    # són les notes MIDI 0-11, que no reprodueix cap sintetitzador. Les notes
    # surten, la Pantalla les mostra, i no se sent res.
    #
    # La regla, la de qualsevol sintetitzador de maquinari: en canviar de
    # capa, cada pot es queda QUIET fins que el mous. Llavors mana on és, que
    # és el que has decidit tu. Es congelen un per un: moure'n un no
    # descongela els altres.
    congelats = _recollida(kbd, pot_values, force_update)
    if kbd.arp_mode_active:
        parells = (('arp_pot_x', 1), ('arp_pot_y', 0), ('arp_pot_z', 2))
        aplica = apply_arp_pot_function
    else:
        parells = (('pot_x', 1), ('pot_y', 0), ('pot_z', 2))
        aplica = apply_pot_function
    for nom, i in parells:
        if congelats[i] is not None:
            continue
        aplica(kbd, nom, pot_values[i], force_update=force_update)


# Quant s'ha de moure un pot per descongelar-se. Per sobre del soroll de
# l'ADC i dels llindars de 2-3 que fan servir les funcions.
LLINDAR_RECOLLIDA = 4


def _recollida(kbd, pot_values, force_update):
    """Quins pots estan congelats esperant que els moguis. Llista de 3:
    el valor on es van congelar, o None si estan lliures."""
    capa = 1 if kbd.arp_mode_active else 0
    congelats = getattr(kbd, '_pot_congelats', None)
    if congelats is None or len(congelats) != 3:
        congelats = [None, None, None]
        kbd._pot_congelats = congelats
    if force_update:
        # Primera volta del mode: s'ha d'aplicar tot, i encara no hi ha cap
        # capa anterior de la qual protegir-se.
        kbd._pot_capa = capa
        congelats[0] = congelats[1] = congelats[2] = None
        return congelats
    if getattr(kbd, '_pot_capa', None) != capa:
        kbd._pot_capa = capa
        for i in range(3):
            congelats[i] = pot_values[i]
        return congelats
    for i in range(3):
        if congelats[i] is not None and abs(pot_values[i] - congelats[i]) >= LLINDAR_RECOLLIDA:
            congelats[i] = None
    return congelats


# ── Memòria de potes: el pot quiet no repeteix la feina ───────────────────
# `apply_pot_function` és una cadena d'una quinzena de comparacions de cadena
# que acaba enviant CC, calculant octaves o reconfigurant el Gate. Es cridava
# tres cops a CADA volta del bucle principal (177 voltes/s) tant si havies
# tocat els potes com si no: 1,40 ms de les 3,64 que costava un update() del
# teclat es gastaven a tornar a decidir el mateix.
#
# Es recorda la FUNCIÓ i el VALOR aplicats a cada pot. La funció hi ha de ser
# perquè recarregar la configuració canvia què fa el pot sense moure'l, i
# `setup()` no torna a posar `first_update`: ningú més ho detectaria.
#
# Dues llistes paral·leles i no una de tuples a posta: una tupla per pot i per
# volta són al·locacions al camí calent, que és justament el que s'evita.
def _memoritza(kbd, atrib_f, atrib_v, i, function, valor):
    """True si aquest pot ja s'ha aplicat amb aquesta funció i aquest valor."""
    fs = getattr(kbd, atrib_f, None)
    if fs is None:
        fs = [None, None, None]
        setattr(kbd, atrib_f, fs)
        setattr(kbd, atrib_v, [-1, -1, -1])
    vs = getattr(kbd, atrib_v)
    if vs[i] == valor and fs[i] == function:
        return True
    vs[i] = valor
    fs[i] = function
    return False


def oblida(kbd):
    """Esborra la memòria de potes: la propera volta els tornarà a aplicar.

    Cal cridar-ho des de qualsevol lloc que toqui, per l'esquena del pot, un
    valor que en depèn. El cas real: `stop_all_notes()` posa `sustain_level`
    a 0 comptant que el pot ho reimposi a la volta següent — amb memòria i
    sense oblit, el sustain es quedaria mort fins que el toquessis."""
    for atrib in ('_pot_memo_f', '_pot_memo_v', '_arp_memo_f', '_arp_memo_v'):
        if getattr(kbd, atrib, None) is not None:
            setattr(kbd, atrib, None)


def apply_pot_function(kbd, pot_name, pot_value, force_update=False):
    if pot_name == 'pot_x':
        function = kbd.pot_x_function; _i = 0
    elif pot_name == 'pot_y':
        function = kbd.pot_y_function; _i = 1
    elif pot_name == 'pot_z':
        function = kbd.pot_z_function; _i = 2
    else:
        return

    # Es REGISTRA sempre, encara que sigui un force_update: si no, la volta
    # següent a un force tornaria a fer tota la feina per no haver-la apuntat.
    if _memoritza(kbd, '_pot_memo_f', '_pot_memo_v', _i, function,
                  pot_value) and not force_update:
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
            _set_bpm(kbd, pot_value, force_update)

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
        function = kbd.arp_pot_x_function; _i = 0
    elif pot_name == 'arp_pot_y':
        function = kbd.arp_pot_y_function; _i = 1
    elif pot_name == 'arp_pot_z':
        function = kbd.arp_pot_z_function; _i = 2
    else:
        return

    # Es REGISTRA sempre, encara que sigui un force_update: si no, la volta
    # següent a un force tornaria a fer tota la feina per no haver-la apuntat.
    if _memoritza(kbd, '_arp_memo_f', '_arp_memo_v', _i, function,
                  pot_value) and not force_update:
        return

    threshold = 0 if force_update else 2

    if function in ('Velocitat (BPM)', 'Arp Speed (BPM)'):
        # Tempo MUSICAL de negra (40–240, el rang d'un metrònom o d'un DAW) i
        # l'arpegiador trepitja SEMICORXERES d'aquest tempo. Abans el pot donava
        # 30–2000 passos/min: 33 notes per segon a dalt (un brunzit, no un tempo)
        # i mig segon per nota a baix, o sigui que la meitat del recorregut era
        # inservible. Ara el número que es veu és el que es posa al DAW.
        _set_bpm(kbd, pot_value, force_update)

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
