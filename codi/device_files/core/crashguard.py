"""crashguard - Tallafoc anti boot-loop (RP2040 NVM).

Un error fatal a main() acaba en supervisor.reload(); si l'error és persistent
(config corrupta, fitxer que falta d'una instal·lació a mitges) el dispositiu
entraria en bucle de reinicis infinit. Aquest mòdul compta els crashes
consecutius a microcontroller.nvm (sobreviu el reset) i al tercer demana
MODE SEGUR: el firmware arrenca mínim (teclat, sense modes) i mostra el motiu.

Layout NVM: [0]=MAGIC  [1]=comptador  [2..2+MSG_MAX]=últim error (utf-8, \0-term)

Ús a main.py:
    safe, last_err = crashguard.boot_status()   # un cop, a l'arrenc
    crashguard.record_crash(e)                  # als handlers fatals, abans de reload
    crashguard.mark_ok()                        # quan el bucle porta ~10s viu

Tot és best-effort: sense nvm (tests, simulador) queda desactivat en silenci.
"""

MAGIC = 0x7E
LIMIT = 3        # crashes consecutius abans d'entrar en MODE SEGUR
MSG_MAX = 64

try:
    import microcontroller
    _nvm = microcontroller.nvm
except Exception:
    _nvm = None


def _set_nvm(nvm):
    """Injecció per a tests."""
    global _nvm
    _nvm = nvm


def boot_status():
    """(mode_segur, últim_error). Cridar UN cop a l'arrenc."""
    if _nvm is None:
        return False, ''
    try:
        if _nvm[0] != MAGIC:
            _nvm[0:2] = bytes((MAGIC, 0))
            return False, ''
        n = _nvm[1]
        msg = ''
        if n:
            try:
                raw = bytes(_nvm[2:2 + MSG_MAX]).split(b'\x00')[0]
                msg = raw.decode('utf-8')
            except Exception:
                msg = ''
        return n >= LIMIT, msg
    except Exception:
        return False, ''


def record_crash(exc):
    """Suma un crash consecutiu i guarda el motiu (OLED/diagnòstic al pròxim boot)."""
    if _nvm is None:
        return
    try:
        n = _nvm[1] + 1 if _nvm[0] == MAGIC else 1
        if n > 255:
            n = 255
        try:
            msg = '%s: %s' % (type(exc).__name__, exc)
        except Exception:
            msg = 'error'
        mb = msg.encode('utf-8')[:MSG_MAX - 1]
        buf = bytearray(2 + MSG_MAX)          # cua a zeros = terminador
        buf[0] = MAGIC
        buf[1] = n
        buf[2:2 + len(mb)] = mb
        _nvm[0:len(buf)] = bytes(buf)
    except Exception:
        pass


def status():
    """(crashes_consecutius, últim_error) sense tocar res — per al diagnòstic."""
    if _nvm is None:
        return 0, ''
    try:
        if _nvm[0] != MAGIC:
            return 0, ''
        msg = ''
        try:
            raw = bytes(_nvm[2:2 + MSG_MAX]).split(b'\x00')[0]
            msg = raw.decode('utf-8')
        except Exception:
            pass
        return _nvm[1], msg
    except Exception:
        return 0, ''


def mark_ok():
    """Boot consolidat: reinicia el comptador (només escriu si cal, la NVM es gasta)."""
    if _nvm is None:
        return
    try:
        if _nvm[0] == MAGIC and _nvm[1]:
            _nvm[1] = 0
    except Exception:
        pass
