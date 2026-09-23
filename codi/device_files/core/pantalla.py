"""pantalla.py — el canal de la Pantalla, que MAI pot frenar l'instrument.

La Pantalla de l'app és cosmètica: ensenya què fa el TECLA mentre el toques.
El que hi arriba són línies de text pel port sèrie. El problema és com hi
arribaven.

Per què `print()` no serveix
────────────────────────────
`print()` va a parar al supervisor de CircuitPython, que escriu al CDC de la
consola i **espera** si el buffer és ple. I s'omple: n'hi ha prou que la
pestanya del navegador passi a segon pla i deixi de llegir un moment. Mentre
espera, el bucle principal està aturat — no llegeix tecles, no envia MIDI. El
que se sent és retard entre prémer i sonar, i és culpa d'una finestra que
només havia de fer bonic.

`usb_cdc.console` és el MATEIX port, però és un objecte `Serial` amb
`write_timeout`. Amb `write_timeout = 0` l'escriptura no espera mai: escriu el
que hi càpiga i torna. Si no hi cap, la línia es perd — i perdre un testimoni
no és res. El `print()` del supervisor no mira aquest atribut, així que
posar-lo a zero no toca ni el REPL ni els traceback.

La regla
────────
    · cosmètic (el que llegeix la Pantalla) → `diu()`, mai bloqueja, es pot perdre
    · diagnòstics i errors                  → `print()` de sempre, mai es perden

Sense consola connectada, `diu()` no arriba ni a formatar: cost zero mentre
toques sense l'app oberta.
"""

# Sostre de línies per segon. Amb escriptures que no bloquegen ja no és una
# defensa —és impossible encallar-se— però evita omplir el buffer de línies
# velles que la Pantalla ja no farà servir, i acota el cost de formatar-les.
PER_SEGON = 30

_canal = None      # None = per provar · False = no n'hi ha · Serial = a punt
_dades = None      # el port de DADES quan l'app hi ha dit «pantalla» (main)
_finestra = 0.0
_gastats = 0


def _console_on():
    """Hi ha la consola oberta (DTR)? És on va tot per defecte."""
    try:
        import supervisor
        return supervisor.runtime.serial_connected
    except Exception:
        return False


def escolten():
    """Hi ha algú escoltant, per la consola o pel port de dades? Sense ningú,
    els testimonis no s'han ni de formatar. ÚNICA porta: motor/kbd_notes
    (`_console_on`) hi delega, i tots els testimonis passen per allà."""
    return _dades is not None or _console_on()


def dades(canal):
    """El port de dades passa a ser (o deixa de ser) una Pantalla: l'app hi ha
    dit {"s":"pantalla"} (core/sim_link) i des d'ara hi van les mateixes
    línies que a la consola. TECLA exposa dos ports USB iguals i des de
    Windows no es distingeixen: així la Pantalla funciona amb QUALSEVOL dels
    dos. `None` en desconnectar."""
    global _dades
    _dades = canal
    if canal is not None:
        try:
            canal.write_timeout = 0      # mai esperar el navegador
        except Exception:
            pass


def anuncia(versio, capa=None, mode=None, via='consola'):
    """La presentació que TECLA fa a la Pantalla en connectar-s'hi: qui és
    (l'app la reconeix per «⌁ TECLA» i sap que ha trobat el port bo, sigui
    quin sigui) i on és (la capa, i el mode si en sona un), perquè la
    pantalla no comenci en blanc fins al primer gest."""
    v = str(versio or '').strip()
    if v[:5].upper() == 'TECLA':          # tecla_version.txt diu «TECLA v3.17.0»
        v = v[5:].strip()
    if v[:1] in ('v', 'V'):
        v = v[1:]
    diu("⌁ TECLA v%s · %s" % (v or '?', via))
    if capa:
        diu("Capa actual: %s" % capa)
    if mode:
        diu("Mode: %s" % mode)


def _obre():
    """El canal, un sol cop. `False` si aquest dispositiu no en té (simulador,
    proves): llavors s'escriu amb print(), on bloquejar-se no és un problema."""
    global _canal
    if _canal is None:
        _canal = False
        try:
            import usb_cdc
            c = usb_cdc.console
            if c is not None:
                c.write_timeout = 0      # ← el que fa que no esperi MAI
                _canal = c
        except Exception:
            pass
    return _canal


def diu(text):
    """Envia una línia a la Pantalla. Mai bloqueja i mai llança.

    Retorna True si s'ha arribat a escriure. Que torni False no és un error:
    vol dir que no hi havia ningú escoltant, que s'ha exhaurit el sostre, o
    que el buffer era ple — i cap de les tres coses no ha de canviar res del
    que sona.
    """
    global _finestra, _gastats
    try:
        consola = _console_on()
        if not consola and _dades is None:
            return False
        import time
        ara = time.monotonic()
        if ara - _finestra >= 1.0:
            _finestra = ara
            _gastats = 0
        if _gastats >= PER_SEGON:
            return False
        _gastats += 1
        fet = False
        if _dades is not None:
            try:
                _dades.write((text + '\n').encode())
                fet = True
            except Exception:
                pass
        if consola:
            c = _obre()
            if c is False:
                print(text)
            else:
                c.write((text + '\n').encode())
            fet = True
        return fet
    except Exception:
        return False


def _reinicia():
    """Per a les proves: torna a l'estat de sortida."""
    global _canal, _dades, _finestra, _gastats
    _canal = None
    _dades = None
    _finestra = 0.0
    _gastats = 0
