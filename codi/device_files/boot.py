"""boot.py — decideix QUINA TECLA és aquest dispositiu, i configura l'USB.

Corre abans que res, i és l'ÚNIC lloc on es pot configurar l'USB (MIDI, HID,
canal de dades). Només s'executa en arrencada freda: `supervisor.reload()` no
hi torna a passar, i per això canviar de personalitat demana un reinici dur.

Ordre de feines:
  1. Rescat: les 4 cantonades premudes en endollar. Curt → la personalitat
     següent; aguantant 5 s → l'Instrument, directe.
  2. Llegeix quina toca: petició d'una app (/config/personalitat.txt, val un
     cop) o el byte de la NVM.
  3. Configura l'USB per a aquella personalitat.
  4. Etiqueta del disc i nom del producte, com sempre.

Regla que mana sobre tota la resta: si QUALSEVOL cosa d'aquí falla, el
dispositiu ha d'arrencar igualment com a Instrument amb la configuració de
sempre. Un boot.py que llança deixa el maquinari inservible i només es
recupera per BOOTSEL, així que tot va embolcallat.
"""
import storage
import time

_pers = 0
_rescat = False
_a_linstrument = False

# ── 1. Rescat: rotar sense poder arribar al firmware ───────────────────────
# Si una personalitat es penja o s'instal·la a mitges, aquest és l'únic camí
# per sortir-ne, i és el que ha de funcionar SEMPRE: és l'únic que no depèn de
# codi generat per cap app. Dues sortides —endollar aguantant les cantonades
# porta a la següent; seguir aguantant-les cinc segons porta a l'Instrument.
#
# La lògica viu a core/personalitat.rescat(), no aquí: així es pot provar
# sense dispositiu. Aquí només hi ha els pins.
_pins = []
try:
    import board
    import digitalio
    from core import personalitat

    try:
        # Les quatre cantonades: tecles 1, 4, 13 i 16 → GP0, GP3, GP12, GP15.
        # El MATEIX gest que en marxa (core/personalitat.CANTONADES), perquè
        # l'usuari no n'hagi d'aprendre dos.
        for _gp in (board.GP0, board.GP3, board.GP12, board.GP15):
            _p = digitalio.DigitalInOut(_gp)
            _p.direction = digitalio.Direction.INPUT
            _p.pull = digitalio.Pull.DOWN
            _pins.append(_p)
        time.sleep(0.05)            # que el pull-down assenti abans de llegir

        def _totes():
            return (_pins[0].value and _pins[1].value
                    and _pins[2].value and _pins[3].value)

        def _sentit():
            from core import llum
            llum.pampallugues(1, (255, 255, 255))   # "t'he sentit"

        _que = personalitat.rescat(_totes, time.monotonic, time.sleep, _sentit)
        _rescat = _que is not None
        _a_linstrument = _que == 'instrument'
    finally:
        # SEMPRE: si es queden reservats, code.py no els podria fer servir i el
        # dispositiu arrencaria sense les quatre cantonades.
        for _p in _pins:
            try:
                _p.deinit()
            except Exception:
                pass
except Exception:
    _rescat = False
    _a_linstrument = False

# ── 2. Quina personalitat toca ─────────────────────────────────────────────
try:
    # Tornar-lo a importar és de franc (ja és a sys.modules) i deixa aquesta
    # secció dempeus encara que la de dalt hagi petat abans d'arribar-hi.
    from core import personalitat

    # Un reinici demanat pel gest EN MARXA no és un endoll nou: les cantonades
    # que hi ha premudes són les mateixes d'aquell gest, que ja s'ha atès. Sense
    # aquesta marca la rotació era doble —el firmware en rotava una i el rescat
    # una altra mig segon després— i des de l'Instrument queies al Blocks
    # saltant-te el Macropad.
    if personalitat.consumeix_reinici_propi():
        _rescat = False
        _a_linstrument = False

    # Una app pot haver demanat una personalitat en instal·lar-se (les apps
    # veuen el disc, no la NVM). La petició val UN COP i s'esborra — i s'ha de
    # consumir encara que hi hagi rescat, o quedaria per a la propera arrencada
    # i desfaria el rescat tot sol.
    _demanada = personalitat.aplica_peticio()

    if _a_linstrument:
        _pers = personalitat.posa(0)
    elif _rescat:
        _pers = personalitat.seguent()
    else:
        _pers = _demanada if _demanada is not None else personalitat.actual()
except Exception:
    _pers = 0

# ── 3. L'USB, segons la personalitat ───────────────────────────────────────
# Cadascuna necessita descriptors diferents, i aquí és l'únic lloc on es poden
# demanar. Tot va per separat i embolcallat: que falli el HID no pot impedir
# que s'engegui el MIDI.

# Canal de dades (usb_cdc.data): el fa servir el mode CONTROLADOR de
# l'Instrument (l'app pren el comandament del dispositiu per WebSerial). Les
# altres dues no el fan servir i s'estalvien un extrem USB.
try:
    import usb_cdc
    usb_cdc.enable(console=True, data=(_pers == 0))
except Exception:
    pass

# HID (teclat i ratolí): el Macropad i el Blocks. L'Instrument no en fa res.
try:
    import usb_hid
    if _pers == 0:
        usb_hid.disable()
except Exception:
    pass

# MIDI: sempre a l'Instrument. A les altres dues, segons la configuració —
# un port MIDI obert que ningú no llegeix penja el Resolume i companyia
# (vegeu la v3.15.4), o sigui que si no es fa servir val més apagar-lo.
try:
    import usb_midi
    _midi_on = True
    if _pers != 0:
        try:
            with open('/config/usb_midi.txt', 'r') as f:
                _midi_on = f.read().strip().lower() not in ('off', '0', 'no')
        except Exception:
            _midi_on = True
    if _midi_on:
        _nom_midi = 'TECLA'
        try:
            with open('/config/device_name.txt', 'r') as f:
                _nom_midi = (f.read().strip() or 'TECLA')[:24]
        except Exception:
            pass
        try:
            usb_midi.set_names(streaming_interface_name=_nom_midi,
                               in_jack_name=_nom_midi, out_jack_name=_nom_midi)
        except Exception:
            pass
    else:
        usb_midi.disable()
except Exception:
    pass

# ── 4. Etiqueta del disc i nom del producte ────────────────────────────────
try:
    with open('/config/disk_label.txt', 'r') as f:
        label = f.read().strip()[:11].upper()
    if label:
        m = storage.getmount("/")
        m.label = label
except Exception:
    pass

try:
    with open('/config/device_name.txt', 'r') as f:
        name = f.read().strip()
    if name:
        import supervisor
        supervisor.set_usb_identification(product=name)
except Exception:
    pass

# El LED diu quina personalitat ha arrencat. És l'única confirmació que hi ha
# abans que el firmware es carregui, i en un rescat és la que et diu si el gest
# ha funcionat.
try:
    from core import llum
    if _rescat:
        llum.pampallugues(_pers + 1, llum.COLORS[_pers])
    llum.personalitat(_pers)
except Exception:
    pass

# Deixa constància per a la consola: en canviar de personalitat, aquesta línia
# és el primer que es veu i diu si el canvi ha anat bé.
try:
    if _a_linstrument:
        _com = " (rescat llarg → Instrument)"
    elif _rescat:
        _com = " (rescat)"
    else:
        _com = ""
    print("TECLA boot: personalitat %d%s" % (_pers, _com))
except Exception:
    pass
