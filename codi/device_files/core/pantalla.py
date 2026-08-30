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
_finestra = 0.0
_gastats = 0


def _console_on():
    """Hi ha algú escoltant? Sense consola, tot això no s'ha ni de plantejar."""
    try:
        import supervisor
        return supervisor.runtime.serial_connected
    except Exception:
        return False


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
        if not _console_on():
            return False
        import time
        ara = time.monotonic()
        if ara - _finestra >= 1.0:
            _finestra = ara
            _gastats = 0
        if _gastats >= PER_SEGON:
            return False
        _gastats += 1
        c = _obre()
        if c is False:
            print(text)
            return True
        c.write((text + '\n').encode())
        return True
    except Exception:
        return False


def _reinicia():
    """Per a les proves: torna a l'estat de sortida."""
    global _canal, _finestra, _gastats
    _canal = None
    _finestra = 0.0
    _gastats = 0
