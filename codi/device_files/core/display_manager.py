"""
DisplayManager - Pantalla OLED SSD1306 per a TECLA (mòdul OPCIONAL)

Mòdul EXTERN i autònom: el firmware funciona exactament igual amb o sense
aquest fitxer. main.py l'importa dins d'un try/except; si el fitxer no està
instal·lat (versió sense pantalla) o no es detecta cap pantalla per I2C,
tot continua com sempre.

Principis de disseny:
  - Zero dependències externes: driver SSD1306 mínim propi (no cal displayio
    ni cap llibreria adafruit addicional). Framebuffer d'1KB + font de 320B.
  - Mai pot trencar el dispositiu: qualsevol error d'I2C (pantalla
    desconnectada en calent, soroll al bus...) marca self.ok = False i totes
    les crides posteriors es converteixen en no-op silenciosos.
  - Refresc NOMÉS per esdeveniments (canvi de mode, capa, octava...), mai
    dins del bucle ràpid: el cost (~25ms per refresc I2C a 400kHz) només es
    paga en moments on ja hi ha càrrega (canvi de mode) o interacció lenta.
  - Auto-detecció de pins: prova les parelles I2C lliures de la Pico
    (els GP0-15 són botons i els GP26-28 potenciòmetres).
"""
import time

# Geometria del panell. Els SSD1306 més habituals (0.96") són 128x64;
# per a un panell 128x32 canvia _HEIGHT a 32.
_WIDTH = 128
_HEIGHT = 64

# Parelles (SDA, SCL) candidates, per nom d'atribut de `board`.
# Només pins lliures al hardware TECLA i vàlids al mux I2C del RP2040.
_I2C_PIN_PAIRS = (
    ("GP16", "GP17"),  # I2C0
    ("GP20", "GP21"),  # I2C0
    ("GP18", "GP19"),  # I2C1
)
_I2C_ADDRS = (0x3C, 0x3D)

# Font 5x7 (columna a columna, bit 0 = fila superior), ASCII 0x20-0x5F.
# Les minúscules i els accents catalans es normalitzen a majúscules.
_FONT = (
    b'\x00\x00\x00\x00\x00'  # (espai)
    b'\x00\x00\x5f\x00\x00'  # !
    b'\x00\x07\x00\x07\x00'  # "
    b'\x14\x7f\x14\x7f\x14'  # #
    b'\x24\x2a\x7f\x2a\x12'  # $
    b'\x23\x13\x08\x64\x62'  # %
    b'\x36\x49\x55\x22\x50'  # &
    b'\x00\x05\x03\x00\x00'  # '
    b'\x00\x1c\x22\x41\x00'  # (
    b'\x00\x41\x22\x1c\x00'  # )
    b'\x14\x08\x3e\x08\x14'  # *
    b'\x08\x08\x3e\x08\x08'  # +
    b'\x00\x50\x30\x00\x00'  # ,
    b'\x08\x08\x08\x08\x08'  # -
    b'\x00\x60\x60\x00\x00'  # .
    b'\x20\x10\x08\x04\x02'  # /
    b'\x3e\x51\x49\x45\x3e'  # 0
    b'\x00\x42\x7f\x40\x00'  # 1
    b'\x42\x61\x51\x49\x46'  # 2
    b'\x21\x41\x45\x4b\x31'  # 3
    b'\x18\x14\x12\x7f\x10'  # 4
    b'\x27\x45\x45\x45\x39'  # 5
    b'\x3c\x4a\x49\x49\x30'  # 6
    b'\x01\x71\x09\x05\x03'  # 7
    b'\x36\x49\x49\x49\x36'  # 8
    b'\x06\x49\x49\x29\x1e'  # 9
    b'\x00\x36\x36\x00\x00'  # :
    b'\x00\x56\x36\x00\x00'  # ;
    b'\x00\x08\x14\x22\x41'  # <
    b'\x14\x14\x14\x14\x14'  # =
    b'\x41\x22\x14\x08\x00'  # >
    b'\x02\x01\x51\x09\x06'  # ?
    b'\x32\x49\x79\x41\x3e'  # @
    b'\x7e\x11\x11\x11\x7e'  # A
    b'\x7f\x49\x49\x49\x36'  # B
    b'\x3e\x41\x41\x41\x22'  # C
    b'\x7f\x41\x41\x22\x1c'  # D
    b'\x7f\x49\x49\x49\x41'  # E
    b'\x7f\x09\x09\x09\x01'  # F
    b'\x3e\x41\x49\x49\x7a'  # G
    b'\x7f\x08\x08\x08\x7f'  # H
    b'\x00\x41\x7f\x41\x00'  # I
    b'\x20\x40\x41\x3f\x01'  # J
    b'\x7f\x08\x14\x22\x41'  # K
    b'\x7f\x40\x40\x40\x40'  # L
    b'\x7f\x02\x0c\x02\x7f'  # M
    b'\x7f\x04\x08\x10\x7f'  # N
    b'\x3e\x41\x41\x41\x3e'  # O
    b'\x7f\x09\x09\x09\x06'  # P
    b'\x3e\x41\x51\x21\x5e'  # Q
    b'\x7f\x09\x19\x29\x46'  # R
    b'\x46\x49\x49\x49\x31'  # S
    b'\x01\x01\x7f\x01\x01'  # T
    b'\x3f\x40\x40\x40\x3f'  # U
    b'\x1f\x20\x40\x20\x1f'  # V
    b'\x3f\x40\x38\x40\x3f'  # W
    b'\x63\x14\x08\x14\x63'  # X
    b'\x07\x08\x70\x08\x07'  # Y
    b'\x61\x51\x49\x45\x43'  # Z
    b'\x00\x7f\x41\x41\x00'  # [
    b'\x02\x04\x08\x10\x20'  # (barra invertida)
    b'\x00\x41\x41\x7f\x00'  # ]
    b'\x04\x02\x01\x02\x04'  # ^
    b'\x40\x40\x40\x40\x40'  # _
)

# Normalització d'accents catalans (les dues caixes: el .upper() de
# CircuitPython només cobreix ASCII).
_ACCENTS = {
    'à': 'A', 'á': 'A', 'À': 'A', 'Á': 'A',
    'è': 'E', 'é': 'E', 'È': 'E', 'É': 'E',
    'ì': 'I', 'í': 'I', 'ï': 'I', 'Ì': 'I', 'Í': 'I', 'Ï': 'I',
    'ò': 'O', 'ó': 'O', 'Ò': 'O', 'Ó': 'O',
    'ù': 'U', 'ú': 'U', 'ü': 'U', 'Ù': 'U', 'Ú': 'U', 'Ü': 'U',
    'ç': 'C', 'Ç': 'C', 'ñ': 'N', 'Ñ': 'N', '·': '-',
}

# Seqüència d'inicialització SSD1306 (panell 128x64, charge pump intern)
_INIT_SEQ = (
    0xAE,        # display off
    0xD5, 0x80,  # clock divide
    0xA8, _HEIGHT - 1,  # multiplex
    0xD3, 0x00,  # display offset
    0x40,        # start line 0
    0x8D, 0x14,  # charge pump ON
    0x20, 0x00,  # horizontal addressing mode
    0xA1,        # segment remap
    0xC8,        # COM scan direction (descendent)
    0xDA, 0x12 if _HEIGHT == 64 else 0x02,  # COM pins
    0x81, 0x7F,  # contrast moderat (allarga la vida del panell)
    0xD9, 0xF1,  # pre-charge
    0xDB, 0x40,  # VCOMH
    0xA4,        # mostra RAM
    0xA6,        # no invertit
    0xAF,        # display on
)


class DisplayManager:
    """Gestor de la pantalla OLED. Si self.ok és False, totes les crides
    públiques són no-op: el codi que el fa servir no ha de comprovar res."""

    def __init__(self, i2c=None, addr=None):
        self.ok = False
        self._i2c = i2c
        self._addr = addr
        self._pages = _HEIGHT // 8
        self._buf = None   # [0x40 + framebuffer]; s'assigna només si hi ha pantalla
        self._fb = None
        self._cbuf = bytearray(2)  # buffer per comandes (0x00, cmd)
        try:
            if self._i2c is None:
                self._detect()
            if self._i2c is not None and self._addr is not None:
                self._alloc()
                self._init_display()
                self.ok = True
        except Exception:
            self.ok = False

    # ── Detecció i inicialització ────────────────────────────────────

    def _detect(self):
        """Prova les parelles de pins candidates i busca un SSD1306."""
        import board
        import busio
        for sda_name, scl_name in _I2C_PIN_PAIRS:
            i2c = None
            try:
                sda = getattr(board, sda_name)
                scl = getattr(board, scl_name)
                i2c = busio.I2C(scl, sda, frequency=400000)
                if not i2c.try_lock():
                    raise RuntimeError("bus ocupat")
                found = i2c.scan()
                for a in _I2C_ADDRS:
                    if a in found:
                        # Mantenim el bus bloquejat: la pantalla n'és l'únic client
                        self._i2c = i2c
                        self._addr = a
                        return
                i2c.unlock()
                i2c.deinit()
            except Exception:
                try:
                    if i2c:
                        i2c.deinit()
                except Exception:
                    pass

    def _alloc(self):
        """Reserva el framebuffer (només quan hi ha pantalla real)."""
        self._buf = bytearray(1 + _WIDTH * self._pages)
        self._buf[0] = 0x40  # control byte: dades GDDRAM
        self._fb = memoryview(self._buf)[1:]

    def _init_display(self):
        for c in _INIT_SEQ:
            self._cmd(c)
        self._fill(0)
        self._show()

    def _cmd(self, c):
        self._cbuf[0] = 0x00
        self._cbuf[1] = c
        self._i2c.writeto(self._addr, self._cbuf)

    def _show(self):
        """Envia el framebuffer sencer a la pantalla (~25ms a 400kHz)."""
        self._cmd(0x21); self._cmd(0); self._cmd(_WIDTH - 1)        # columnes
        self._cmd(0x22); self._cmd(0); self._cmd(self._pages - 1)   # pàgines
        self._i2c.writeto(self._addr, self._buf)

    # ── Primitives de dibuix (només toquen el framebuffer) ──────────

    def _fill(self, color):
        v = 0xFF if color else 0x00
        fb = self._fb
        for i in range(len(fb)):
            fb[i] = v

    def _pixel(self, x, y):
        if 0 <= x < _WIDTH and 0 <= y < _HEIGHT:
            self._fb[x + (y >> 3) * _WIDTH] |= 1 << (y & 7)

    def _hline(self, x, y, w):
        for i in range(w):
            self._pixel(x + i, y)

    @staticmethod
    def _norm(s):
        """Majúscules + accents fora; només queden glifs de la font."""
        out = []
        for ch in str(s):
            ch = _ACCENTS.get(ch, ch)
            o = ord(ch)
            if 97 <= o <= 122:
                o -= 32
            if o < 32 or o > 95:
                o = 32  # caràcter no suportat -> espai
            out.append(chr(o))
        return "".join(out)

    def _text(self, s, x, y, scale=1):
        fb = self._fb
        for ch in self._norm(s):
            if x >= _WIDTH:
                break
            base = (ord(ch) - 32) * 5
            for col in range(5):
                bits = _FONT[base + col]
                if bits:
                    px0 = x + col * scale
                    for row in range(7):
                        if bits & (1 << row):
                            py0 = y + row * scale
                            for sx in range(scale):
                                for sy in range(scale):
                                    self._pixel(px0 + sx, py0 + sy)
            x += 6 * scale

    def _center(self, s, y, scale=1):
        w = len(s) * 6 * scale - scale
        self._text(s, max(0, (_WIDTH - w) // 2), y, scale)

    def _screen(self, header, big, footer=None):
        """Plantilla comuna: capçalera petita + títol gran + peu petit."""
        self._fill(0)
        if header:
            self._text(header, 0, 0, 1)
            self._hline(0, 10, _WIDTH)
        big = self._norm(big)
        if len(big) <= 10:
            self._center(big, 26, 2)
        else:
            self._center(big[:21], 30, 1)
        if footer:
            self._center(footer, 56, 1)
        self._show()

    # ── API pública (tota fail-safe) ─────────────────────────────────

    def boot_animation(self):
        """Animació d'arrencada: T E C L A lletra a lletra + subratllat."""
        if not self.ok:
            return
        try:
            word = "TECLA"
            x0 = (_WIDTH - (9 * 12 - 2)) // 2  # "T E C L A" a escala 2
            for n in range(1, len(word) + 1):
                self._fill(0)
                for k in range(n):
                    self._text(word[k], x0 + k * 24, 22, 2)
                self._show()
                time.sleep(0.12)
            for w in (32, 64, 96, 120):
                self._hline((_WIDTH - w) // 2, 44, w)
                self._show()
                time.sleep(0.05)
            time.sleep(0.35)
        except Exception:
            self.ok = False

    def show_mode(self, mode_name, bank_name=None):
        """Mode actiu de la capa de modes."""
        if not self.ok:
            return
        try:
            footer = ("CAPA: " + str(bank_name)) if bank_name else None
            self._screen("MODE", mode_name, footer)
        except Exception:
            self.ok = False

    def show_keyboard(self, octave):
        """Capa teclat activa, amb l'octava actual."""
        if not self.ok:
            return
        try:
            self._screen("CAPA", "TECLAT", "OCTAVA: %d" % octave)
        except Exception:
            self.ok = False

    def show_layer(self, bank_name, hint=None):
        """Capa de modes activa (o canvi de banc)."""
        if not self.ok:
            return
        try:
            self._screen("CAPA", bank_name, hint or "TRIA UN MODE (1-12)")
        except Exception:
            self.ok = False

    def show_stop(self):
        """Aturada d'emergència (botó 16)."""
        if not self.ok:
            return
        try:
            self._screen(None, "STOP", "SO ATURAT")
        except Exception:
            self.ok = False

    def show_message(self, line1, line2=None):
        """Missatge informatiu breu (dues línies petites centrades)."""
        if not self.ok:
            return
        try:
            self._fill(0)
            self._center(self._norm(line1)[:21], 22, 1)
            if line2:
                self._center(self._norm(line2)[:21], 36, 1)
            self._show()
        except Exception:
            self.ok = False
