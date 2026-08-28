"""boot.py — decideix QUINA TECLA és aquest dispositiu, i configura l'USB.

Corre abans que res, i és l'ÚNIC lloc on es pot configurar l'USB (MIDI, HID,
canal de dades). Només s'executa en arrencada freda: `supervisor.reload()` no
hi torna a passar, i per això canviar de personalitat demana un reinici dur.

Ordre de feines:
  1. Rescat: les 4 cantonades premudes en endollar → fa rotar la personalitat.
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

_pers = 0

# ── 1. Rescat: rotar sense poder arribar al firmware ───────────────────────
# Si una personalitat es penja o s'instal·la a mitges, aquest és l'únic camí
# per sortir-ne. Es llegeixen els quatre pins A MÀ i es DEIXEN ANAR de seguida:
# si es quedessin reservats, code.py no els podria fer servir.
try:
    import board
    import digitalio

    # Les quatre cantonades: tecles 1, 4, 13 i 16 → GP0, GP3, GP12, GP15.
    # El MATEIX gest que en marxa (core/personalitat.CANTONADES), perquè
    # l'usuari no n'hagi d'aprendre dos.
    _pins = []
    for _gp in (board.GP0, board.GP3, board.GP12, board.GP15):
        _p = digitalio.DigitalInOut(_gp)
        _p.direction = digitalio.Direction.INPUT
        _p.pull = digitalio.Pull.DOWN
        _pins.append(_p)
    _rescat = all(_p.value for _p in _pins)
    for _p in _pins:
        _p.deinit()                 # SEMPRE: si es queden reservats, code.py
                                    # no els podria fer servir
except Exception:
    _rescat = False

# ── 2. Quina personalitat toca ─────────────────────────────────────────────
try:
    from core import personalitat
    if _rescat:
        _pers = personalitat.seguent()
    else:
        # Una app pot haver demanat una personalitat en instal·lar-se (les apps
        # veuen el disc, no la NVM). La petició val UN COP i s'esborra.
        _demanada = personalitat.aplica_peticio()
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
    print("TECLA boot: personalitat %d%s" % (_pers, " (rescat)" if _rescat else ""))
except Exception:
    pass
