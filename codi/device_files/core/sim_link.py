"""sim_link — mode CONTROLADOR del firmware TECLA (protocol del thin client).

Quan l'app web s'hi connecta per WebSerial (usb_cdc.data), el dispositiu deixa de
sonar en local i passa a ser un controlador del simulador: envia l'estat dels 16
botons i els 3 potenciòmetres, i pinta a l'OLED les trames que el navegador li
retorna. En desconnectar, el firmware reprèn el funcionament autònom.

Protocol (text, una línia per missatge, IDÈNTIC al del firmware thin):
  Device → host:  "I <bitmask16_hex> <p0> <p1> <p2>"
                  "D <json>"  — resposta de diagnòstic (a petició del host)
  Host → device:  JSON, p. ex. {"s":"kbd","oct":4} · {"s":"mode","name":..,"layer":..}
                  · {"s":"layer","name":..} · {"s":"stop"} · {"s":"msg","l1":..,"l2":..}
                  · {"s":"diag"} — demana l'estat (versió, RAM, crashes...)

INTEGRITAT: cap error de serial/JSON/OLED pot llançar cap al bucle principal.
"""

POT_DEADBAND = 2      # ignora moviments de pot < 2 (soroll de l'ADC)
HEARTBEAT = 0.5       # s — reenvia l'estat encara que no canviï
RX_LIMIT = 256        # protecció: descarta brossa sense '\n'
# Qui hi ha a l'altra banda? En obrir el port, l'app es presenta:
#   {"s":"sim"}       → el simulador: mode controlador (com sempre)
#   {"s":"pantalla"}  → la Pantalla de l'app: només hi van les línies de
#                       core/pantalla; el dispositiu segueix sonant sol.
# Sense presentació al cap d'HOLA_S (un amfitrió antic), es dóna per simulador.
HOLA_S = 1.0


def encode_input(mask, pots):
    """Trama d'entrada cap al host: botons com a màscara + 3 pots 0-127."""
    return "I %04X %d %d %d\n" % (mask & 0xFFFF, pots[0], pots[1], pots[2])


def handle_oled(display, line):
    """Pinta una trama OLED rebuda del navegador. Mai llança.
    Retorna el tipus de trama ('kbd', 'diag'...) perquè el pump pugui reaccionar."""
    if not line:
        return None
    try:
        import json
        # A CircuitPython json.loads vol una CADENA: amb els bytes del port
        # llançava (en silenci) i cap trama del navegador —ni la presentació,
        # ni el diag— no s'entenia mai.
        if not isinstance(line, str):
            line = str(line, 'utf-8')
        d = json.loads(line)
    except Exception:
        return None
    try:
        s = d.get('s')
        if s == 'diag' or display is None:
            return s
        if s == 'kbd':
            display.show_keyboard(d.get('oct', 4))
        elif s == 'mode':
            display.show_mode(d.get('name', '?'), d.get('layer'))
        elif s == 'layer':
            display.show_layer(d.get('name', '?'), d.get('hint'))
        elif s == 'stop':
            display.show_stop()
        elif s == 'msg':
            display.show_message(d.get('l1', ''), d.get('l2'))
        return s
    except Exception:
        return None


class SimLink:
    """Bomba d'E/S del mode controlador sobre usb_cdc.data."""

    def __init__(self, serial, display=None):
        self.serial = serial
        self.display = display
        try:
            serial.timeout = 0          # lectures no bloquejants
        except Exception:
            pass
        self._rx = b''
        self._last_mask = -1
        self._last_pots = [-1, -1, -1]
        self._last_send = 0.0
        # El host ha demanat diagnòstic ({"s":"diag"}); el main el consumeix
        # i respon amb send_diag() (ell té accés a runner/gc/crashguard).
        self.diag_requested = False
        self.mode = None            # None (esperant «hola») · 'sim' · 'pantalla'
        self._obert = None          # quan s'ha obert el port (per a HOLA_S)

    def send_diag(self, info):
        """Respon el diagnòstic: línia "D <json>". Mai llança."""
        try:
            import json
            self.serial.write(('D ' + json.dumps(info) + '\n').encode())
        except Exception:
            pass

    @property
    def connected(self):
        try:
            return bool(self.serial and self.serial.connected)
        except Exception:
            return False

    def reset(self):
        """En entrar al mode controlador: força el primer enviament complet."""
        self._rx = b''
        self._last_mask = -1
        self._last_pots = [-1, -1, -1]
        self._last_send = 0.0
        self.mode = None
        self._obert = None

    def pump(self, mask, pots, now):
        """Un cicle amb el port obert: llegeix el que arriba (la presentació
        de l'app, trames OLED, diag) i, si l'altra banda és el simulador,
        envia l'estat (canvis + heartbeat). Torna `self.mode`."""
        if self._obert is None:
            self._obert = now
        # ── Trames entrants (abans d'enviar: la presentació decideix què som) ──
        # RES de `del self._rx[:i]`: a CircuitPython un bytearray no admet
        # esborrar per tall (TypeError), i com que aquí tot va embolcallat,
        # cap línia del navegador no s'havia entès MAI al dispositiu (ni les
        # trames OLED, ni el diag). tests/test_pantalla_qualsevol_port ho vigila.
        try:
            n = self.serial.in_waiting
            if n:
                rx = self._rx + self.serial.read(n)
                while True:
                    i = rx.find(b'\n')
                    if i < 0:
                        break
                    s = handle_oled(self.display, bytes(rx[:i]))
                    rx = rx[i + 1:]
                    if s == 'diag':
                        self.diag_requested = True
                    elif s == 'sim' or s == 'pantalla':
                        self.mode = s
                self._rx = b'' if len(rx) > RX_LIMIT else rx
        except Exception:
            pass
        if self.mode is None and now - self._obert >= HOLA_S:
            self.mode = 'sim'           # amfitrió antic: no es presenta
        if self.mode != 'sim':
            return self.mode
        # ── Enviar estat (canvis o heartbeat) ──
        changed = (mask != self._last_mask)
        if not changed:
            for i in range(3):
                if abs(pots[i] - self._last_pots[i]) >= POT_DEADBAND:
                    changed = True
                    break
        if changed or (now - self._last_send) >= HEARTBEAT:
            try:
                self.serial.write(encode_input(mask, pots).encode())
                self._last_mask = mask
                self._last_pots = list(pots)
                self._last_send = now
            except Exception:
                pass
        return self.mode
