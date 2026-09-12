"""Loop de la capa de MODES — looper a nivell MIDI, curt i lleuger.

Port reduït del MidiLooper del simulador (tecla-midiloop.js): grava els
note_on/note_off que EMET el mode actiu embolcallant midi_out.send, i els
repeteix en bucle. Serveix per gravar el motiu d'un mode i tocar-hi un altre
mode (o el teclat) a sobre — el loop continua sonant en canviar de mode o de
capa; la tecla 16 (STOP) l'esborra.

Gest (tecla d'efecte 'Loop' a 14/15):
  tap 1 → GRAVA (des d'ara)
  tap 2 → tanca i SONA en bucle
  tap 3 → atura i esborra

Límits durs (RAM primer): MAX_EVENTS esdeveniments i MAX_LEN_S segons — si la
gravació arriba al límit, es tanca sola i comença a sonar. Sense overdub en
aquesta versió. Mòdul amb càrrega lazy.
"""

MAX_EVENTS = 96
MAX_LEN_S = 8.0
MIN_LEN_S = 0.3

IDLE = 0
RECORDING = 1
PLAYING = 2


class ModeLoop:
    def __init__(self):
        self.state = IDLE
        self.events = []          # [t_rel, is_on, note, vel] ordenats per t_rel
        self.loop_len = 0.0
        self._t0 = 0.0
        self._pos = 0             # índex del proper esdeveniment a reproduir
        self._cycle_t0 = 0.0
        self._playing_back = False
        self._active = set()      # notes que el loop manté sonant
        self._held_rec = set()    # notes obertes durant la gravació

    # ── Captura (embolcall de midi_out.send) ─────────────────────────────────
    def attach(self, midi_out):
        """Embolcalla midi_out.send UNA sola vegada per capturar note_on/off."""
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
        if self._playing_back or self.state != RECORDING:
            return
        # endswith: cobreix tant les classes reals ('NoteOn') com els mocks del
        # simulador/tests ('_NoteOn').
        name = type(msg).__name__
        is_on = name.endswith('NoteOn')
        if not is_on and not name.endswith('NoteOff'):
            return
        vel = getattr(msg, 'velocity', 0)
        if is_on and vel == 0:
            is_on = False
        import time
        t = time.monotonic() - self._t0
        if len(self.events) < MAX_EVENTS:
            self.events.append([t, is_on, msg.note, vel])
        note = msg.note
        if is_on:
            self._held_rec.add(note)
        else:
            self._held_rec.discard(note)

    # ── Gest principal (tap a la tecla d'efecte 'Loop') ──────────────────────
    def tap(self, now):
        """Cicla l'estat: IDLE→GRAVANT→SONANT→IDLE. Retorna l'estat nou."""
        if self.state == IDLE:
            self.events = []
            self._held_rec.clear()
            self._t0 = now
            self.state = RECORDING
        elif self.state == RECORDING:
            self._close_and_play(now)
        else:
            self.clear(None)
        return self.state

    def _close_and_play(self, now):
        self.loop_len = min(now - self._t0, MAX_LEN_S)
        if not self.events or self.loop_len < MIN_LEN_S:
            self.state = IDLE
            self.events = []
            return
        # Tanca les notes que han quedat obertes al final de la presa
        for note in self._held_rec:
            self.events.append([self.loop_len, False, note, 0])
        self._held_rec.clear()
        # Fora esdeveniments més enllà del límit (si el tap ha arribat tard)
        self.events = [e for e in self.events if e[0] <= self.loop_len]
        self.events.sort(key=lambda e: e[0])
        self.state = PLAYING
        self._cycle_t0 = now
        self._pos = 0

    # ── Motor (cridat a cada update del gestor de modes) ─────────────────────
    def tick(self, midi_out, now):
        if self.state == RECORDING:
            # Límit dur: la presa es tanca sola (loop curt garantit)
            if (now - self._t0) >= MAX_LEN_S or len(self.events) >= MAX_EVENTS:
                self._close_and_play(now)
            return
        if self.state != PLAYING or not self.events:
            return
        pos_t = now - self._cycle_t0
        if pos_t >= self.loop_len:
            # Final de volta: silenci de seguretat de les notes del loop i wrap
            self._silence(midi_out)
            self._cycle_t0 = now
            self._pos = 0
            pos_t = 0.0
        while self._pos < len(self.events) and self.events[self._pos][0] <= pos_t:
            _t, is_on, note, vel = self.events[self._pos]
            self._pos += 1
            self._playing_back = True
            try:
                if is_on:
                    from adafruit_midi.note_on import NoteOn
                    midi_out.send(NoteOn(note, vel or 100))
                    self._active.add(note)
                else:
                    from adafruit_midi.note_off import NoteOff
                    midi_out.send(NoteOff(note, 0))
                    self._active.discard(note)
            except Exception:
                pass
            self._playing_back = False

    # ── Neteja ────────────────────────────────────────────────────────────────
    def _silence(self, midi_out):
        if midi_out is None:
            self._active.clear()
            return
        self._playing_back = True
        try:
            from adafruit_midi.note_off import NoteOff
            for note in self._active:
                try:
                    midi_out.send(NoteOff(note, 0))
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
