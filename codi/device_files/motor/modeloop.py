"""Loop de la capa de MODES — looper a nivell MIDI, curt i lleuger.

Port reduït del MidiLooper del simulador (tecla-midiloop.js): grava els
note_on/note_off i els pitch bend que EMET el mode actiu embolcallant
midi_out.send, i els repeteix en bucle. Serveix per gravar el motiu d'un mode
i tocar-hi un altre mode (o el teclat) a sobre — el loop continua sonant en
canviar de mode o de capa; la tecla 16 (STOP) l'esborra.

El loop sona pel SEU canal MIDI (MODE_LOOP_CHANNEL), no pel del mode que l'ha
gravat. És el que fa que un pitch bend en viu (l'efecte PitchBend, que bendeja
tots els canals menys els dels loops) no torci el que ja està gravat, i que el
bend que es fa MENTRE es grava quedi dins del loop i es repeteixi amb ell. El
teclat fa el mateix pel seu compte (kbd_looper, KBD_LOOP_CHANNEL).

Gest (tecla d'efecte 'Loop' a 14/15):
  tap 1 → GRAVA (des d'ara)
  tap 2 → tanca i SONA en bucle
  tap 3 → atura i esborra

Límits durs (RAM primer): MAX_EVENTS esdeveniments i MAX_LEN_S segons — si la
gravació arriba al límit, es tanca sola i comença a sonar. Els bends tenen el
seu pressupost a part (MAX_BENDS) i es fusionen si arriben massa seguits: un
escombrat del pot en genera desenes. Sense overdub en aquesta versió. Mòdul
amb càrrega lazy.
"""

MAX_EVENTS = 96
MAX_BENDS = 48
BEND_MIN_GAP = 0.03       # segons: dos bends més seguits es fusionen en un
MAX_LEN_S = 8.0
MIN_LEN_S = 0.3

IDLE = 0
RECORDING = 1
PLAYING = 2

# Tipus d'esdeveniment (camp [1] de cada entrada d'events)
EV_OFF = 0
EV_ON = 1
EV_BEND = 2

BEND_CENTER = 8192

# Canals MIDI dels loops: absoluts, com el de la base (kbd_fons.FONS_CHANNEL = 1).
# El teclat toca pel canal de sortida (0 per defecte), la base pel 2n, i els
# loops pel 3r i el 4t. Els modes MIX del simulador van del 5è al 8è (4–7).
KBD_LOOP_CHANNEL = 2      # el looper del teclat (motor/kbd_looper)
MODE_LOOP_CHANNEL = 3     # aquest
LOOP_CHANNELS = (KBD_LOOP_CHANNEL, MODE_LOOP_CHANNEL)


def canals_auxiliars(midi_out):
    """(base, loop del teclat, loop de modes): els tres primers canals lliures
    a partir de l'1, saltant-se el de SORTIDA configurat i el 9 (percussió GM).

    Amb el canal de sortida per defecte (0) són 1, 2 i 3, els mateixos que el
    simulador té fixos. Si l'usuari configura el canal 3 (índex 2), el teclat
    NO pot compartir canal amb el seu looper: el bend en viu tornaria a torçar
    el loop i els NoteOff del teclat i del loop es tallarien entre ells. Tots
    els que fan servir un canal auxiliar ho pregunten aquí (kbd_looper,
    kbd_fons, accompaniment, els efectes, l'escombrat de l'STOP), un sol cop
    en crear-se: mai al camí calent."""
    try:
        out = int(getattr(midi_out, 'out_channel', 0) or 0)
    except Exception:
        out = 0
    res = []
    c = 1
    while len(res) < 3:
        if c != out and c != 9:
            res.append(c)
        c = (c + 1) & 15
    return res[0], res[1], res[2]


def canal_progressio(midi_out):
    """El canal de la funció 'progression' (motor/kbd_progressio): el QUART
    canal lliure, amb la mateixa regla que canals_auxiliars (4 amb el canal de
    sortida per defecte). Propi i no el de la base: amb un canal compartit, el
    NoteOff d'una nota de la base tallava la mateixa nota sostinguda de
    l'acord de la progressió."""
    try:
        out = int(getattr(midi_out, 'out_channel', 0) or 0)
    except Exception:
        out = 0
    n = 0
    c = 1
    while True:
        if c != out and c != 9:
            n += 1
            if n == 4:
                return c
        c = (c + 1) & 15


class ModeLoop:
    def __init__(self):
        self.state = IDLE
        self.events = []          # [t_rel, tipus, nota|bend, vel] ordenats per t_rel
        self.loop_len = 0.0
        self._t0 = 0.0
        self._pos = 0             # índex del proper esdeveniment a reproduir
        self._cycle_t0 = 0.0
        self._playing_back = False
        self._active = set()      # notes que el loop manté sonant
        self._held_rec = set()    # notes obertes durant la gravació
        self._bends = 0           # bends gravats en aquesta presa
        self._bend_last = None    # últim bend gravat (per fusionar-hi els que vénen seguits)
        self._bend_last_t = 0.0
        self._live_bend = BEND_CENTER   # últim bend que ha passat pel port (el "viu")
        self._bend0 = BEND_CENTER       # bend viu en començar la presa: on torna cada volta
        self._bend_out = None     # últim bend enviat pel canal del loop (per no repetir-lo)
        self._volta_pendent = False  # PLAYING acabat d'arrencar: el tick posa el bend inicial
        self.canal = MODE_LOOP_CHANNEL        # es fixa a attach() segons el canal de sortida
        self._no_captura = (1, KBD_LOOP_CHANNEL, MODE_LOOP_CHANNEL)

    # ── Captura (embolcall de midi_out.send) ─────────────────────────────────
    def attach(self, midi_out):
        """Embolcalla midi_out.send UNA sola vegada per capturar note_on/off i bends."""
        base, kbd_loop, self.canal = canals_auxiliars(midi_out)
        self._no_captura = (base, kbd_loop, self.canal)
        if getattr(midi_out, '_modeloop_wrapped', False):
            return
        orig = midi_out.send
        loop = self

        def send(msg, *a, **k):
            loop._capture(msg)
            return orig(msg, *a, **k)

        midi_out.send = send
        midi_out._modeloop_wrapped = True

    def _capture(self, msg):
        if self._playing_back:
            return
        # La base (kbd_fons) i els dos loops no són material del mode: si es
        # gravessin, tornarien pel canal del loop.
        if getattr(msg, 'channel', None) in self._no_captura:
            return
        # endswith: cobreix tant les classes reals ('NoteOn') com els mocks del
        # simulador/tests ('_NoteOn').
        name = type(msg).__name__
        if name.endswith('PitchBend'):
            val = int(getattr(msg, 'pitch_bend', BEND_CENTER))
            self._live_bend = val
            if self.state == RECORDING:
                self._capture_bend(val)
            return
        if self.state != RECORDING:
            return
        is_on = name.endswith('NoteOn')
        if not is_on and not name.endswith('NoteOff'):
            return
        vel = getattr(msg, 'velocity', 0)
        if is_on and vel == 0:
            is_on = False
        import time
        t = time.monotonic() - self._t0
        if len(self.events) - self._bends < MAX_EVENTS:
            self.events.append([t, EV_ON if is_on else EV_OFF, msg.note, vel])
        note = msg.note
        if is_on:
            self._held_rec.add(note)
        else:
            self._held_rec.discard(note)

    def _capture_bend(self, val):
        """Un bend durant la presa. L'efecte PitchBend envia el MATEIX valor a
        tots els canals d'una tirada: el valor repetit no es grava dos cops. I
        els que vénen massa seguits (un escombrat del pot) es fusionen en el
        darrer, que sempre acaba amb el valor final."""
        import time
        now = time.monotonic()
        last = self._bend_last
        if last is not None and last[2] == val:
            return
        if last is not None and (now - self._bend_last_t) < BEND_MIN_GAP:
            last[2] = val
            return
        if self._bends >= MAX_BENDS:
            if last is not None:
                last[2] = val
            return
        ev = [now - self._t0, EV_BEND, val, 0]
        self.events.append(ev)
        self._bend_last = ev
        self._bend_last_t = now
        self._bends += 1

    # ── Gest principal (tap a la tecla d'efecte 'Loop') ──────────────────────
    def tap(self, now):
        """Cicla l'estat: IDLE→GRAVANT→SONANT→IDLE. Retorna l'estat nou."""
        if self.state == IDLE:
            self.events = []
            self._held_rec.clear()
            self._bends = 0
            self._bend_last = None
            self._bend0 = self._live_bend
            self._t0 = now
            self.state = RECORDING
        elif self.state == RECORDING:
            self._close_and_play(now)
        else:
            self.clear(None)
        return self.state

    def tanca_presa(self, now):
        """Una presa oberta en sortir de la capa de modes es tanca aquí: si
        no, gravaria el teclat fins a tornar-hi (tick, que és qui aplica el
        límit, no gira sense mode) i tot sortiria pel canal 3."""
        if self.state == RECORDING:
            self._close_and_play(now)

    def _close_and_play(self, now):
        self.loop_len = min(now - self._t0, MAX_LEN_S)
        te_notes = False
        for e in self.events:
            if e[1] != EV_BEND:
                te_notes = True
                break
        if not te_notes or self.loop_len < MIN_LEN_S:
            self.state = IDLE
            self.events = []
            self._bends = 0
            self._bend_last = None
            return
        # Tanca les notes que han quedat obertes al final de la presa
        for note in self._held_rec:
            self.events.append([self.loop_len, EV_OFF, note, 0])
        self._held_rec.clear()
        self._bend_last = None
        # Fora esdeveniments més enllà del límit (si el tap ha arribat tard)
        self.events = [e for e in self.events if e[0] <= self.loop_len]
        self.events.sort(key=lambda e: e[0])
        self.state = PLAYING
        self._cycle_t0 = now
        self._pos = 0
        self._volta_pendent = True

    # ── Motor (cridat a cada update del gestor de modes) ─────────────────────
    def tick(self, midi_out, now):
        if self.state == RECORDING:
            # Límit dur: la presa es tanca sola (loop curt garantit)
            if (now - self._t0) >= MAX_LEN_S or len(self.events) - self._bends >= MAX_EVENTS:
                self._close_and_play(now)
            return
        if self.state != PLAYING or not self.events:
            return
        if self._volta_pendent:
            # Primera volta d'aquest passi: el bend del canal del loop, on era
            # en començar la presa (tap() no té el port a mà; el tick sí)
            self._volta_pendent = False
            self._volta(midi_out)
        pos_t = now - self._cycle_t0
        if pos_t >= self.loop_len:
            # Final de volta: silenci de seguretat de les notes del loop i wrap.
            # El bend NO es recentra aquí: es posa directament on comença la volta.
            self._silence(midi_out, afina=False)
            self._cycle_t0 = now
            self._pos = 0
            pos_t = 0.0
            self._volta(midi_out)
        while self._pos < len(self.events) and self.events[self._pos][0] <= pos_t:
            _t, tipus, note, vel = self.events[self._pos]
            self._pos += 1
            self._playing_back = True
            try:
                if tipus == EV_BEND:
                    self._bend(midi_out, note)
                elif tipus == EV_ON:
                    from adafruit_midi.note_on import NoteOn
                    midi_out.send(NoteOn(note, vel or 100, channel=self.canal))
                    self._active.add(note)
                else:
                    from adafruit_midi.note_off import NoteOff
                    midi_out.send(NoteOff(note, 0, channel=self.canal))
                    self._active.discard(note)
            except Exception:
                pass
            self._playing_back = False

    def _volta(self, midi_out):
        """Comença una volta: el canal del loop torna al bend que hi havia en
        començar la presa (només si el loop en porta cap)."""
        if self._bends:
            self._playing_back = True
            try:
                self._bend(midi_out, self._bend0)
            except Exception:
                pass
            self._playing_back = False

    def _bend(self, midi_out, val):
        val = max(0, min(16383, int(val)))
        if val == self._bend_out:
            return
        self._bend_out = val
        from adafruit_midi.pitch_bend import PitchBend
        midi_out.send(PitchBend(val, channel=self.canal))

    # ── Neteja ────────────────────────────────────────────────────────────────
    def _silence(self, midi_out, afina=True):
        """NoteOff de les notes que el loop manté sonant. Amb `afina`, el canal
        del loop torna al centre si el loop l'havia bendejat (pausa, clear)."""
        if midi_out is None:
            self._active.clear()
            return
        self._playing_back = True
        try:
            from adafruit_midi.note_off import NoteOff
            for note in self._active:
                try:
                    midi_out.send(NoteOff(note, 0, channel=self.canal))
                except Exception:
                    pass
            if afina and self._bend_out not in (None, BEND_CENTER):
                try:
                    self._bend(midi_out, BEND_CENTER)
                except Exception:
                    pass
        except Exception:
            pass
        self._playing_back = False
        self._active.clear()

    def clear(self, midi_out):
        """Atura i esborra el loop (tap sobre SONANT, STOP global, cleanup)."""
        self._silence(midi_out)
        self.state = IDLE
        self.events = []
        self._held_rec.clear()
        self.loop_len = 0.0
        self._bends = 0
        self._bend_last = None
