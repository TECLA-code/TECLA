"""Classe base per a tots els modes d'operació"""

# Pool de missatges MIDI (RENDIMENT): un NoteOn i un NoteOff compartits que es
# MUTEN i s'envien a l'acte — send() serialitza síncronament, així que cap
# receptor no en guarda referència. Elimina les al·locacions per nota de TOTS
# els modes: aquella brossa era una font d'auto-GC imprevisibles (jitter).
_pool_on = None
_pool_off = None


def _note_on_msg():
    global _pool_on
    if _pool_on is None:
        from adafruit_midi.note_on import NoteOn
        _pool_on = NoteOn(0, 0)
    return _pool_on


def _note_off_msg():
    global _pool_off
    if _pool_off is None:
        from adafruit_midi.note_off import NoteOff
        _pool_off = NoteOff(0, 0)
    return _pool_off


class BaseMode:
    def __init__(self, midi_out, config=None):
        self.midi_out = midi_out
        self.config = config or {}
        self.initialized = False
        self.iteration = 0
        # Tracking unificat de notes sonant: conjunt de (nota, canal).
        # Si el mode envia notes amb send_note_on/send_note_off, la neteja en
        # canviar de mode és automàtica (mm_cleanup crida stop_tracked_notes).
        self.tracked_notes = set()
        # Harmonia negativa (efecte temporal opcional, compartit per tots els modes).
        # Vegeu poll_negharm()/negharm() i modes/negharm.py.
        self.neg_active = False
        self.neg_axis = 0

    def setup(self):
        self.initialized = True
        self.iteration = 0

    def cleanup(self):
        self.stop_tracked_notes()

    def update(self, pot_values, button_states):
        self.iteration += 1
        return {}

    def note_on(self, note, velocity=127):
        from adafruit_midi.note_on import NoteOn
        return NoteOn(note & 0x7F, velocity & 0x7F)

    def note_off(self, note, velocity=0):
        from adafruit_midi.note_off import NoteOff
        return NoteOff(note & 0x7F, velocity & 0x7F)

    # ── Tracking unificat de notes ───────────────────────────────────────────
    # Preferiu aquests helpers a note_on()/note_off() + send manual: registren
    # cada nota sonant i permeten una neteja fiable amb un sol punt d'entrada,
    # sense que mm_cleanup hagi de conèixer les estructures internes del mode.

    def send_note_on(self, note, velocity=127, channel=0):
        """Envia NoteOn i registra la nota com a sonant."""
        msg = _note_on_msg()
        msg.note = note & 0x7F
        msg.velocity = velocity & 0x7F
        msg.channel = channel
        self.midi_out.send(msg)
        self.tracked_notes.add((note & 0x7F, channel))

    def send_note_off(self, note, velocity=0, channel=0):
        """Envia NoteOff i desregistra la nota."""
        msg = _note_off_msg()
        msg.note = note & 0x7F
        msg.velocity = velocity & 0x7F
        msg.channel = channel
        self.midi_out.send(msg)
        self.tracked_notes.discard((note & 0x7F, channel))

    def stop_tracked_notes(self):
        """Atura totes les notes registrades (cridat per mm_cleanup en canviar de mode)."""
        notes = getattr(self, 'tracked_notes', None)
        if not notes:
            return
        for note, channel in list(notes):
            try:
                msg = _note_off_msg()
                msg.note = note
                msg.velocity = 0
                msg.channel = channel
                self.midi_out.send(msg)
            except Exception:
                pass
        notes.clear()

    # ── Harmonia negativa compartida ─────────────────────────────────────────
    # Mecanisme reutilitzable per qualsevol mode melòdic. Recepta:
    #   1) a update(): self.poll_negharm(button_states, pot_eix)
    #   2) embolcalla cada alçada abans d'enviar-la: note = self.negharm(note, tonica_pc)
    #   3) exclou el botó 16 (índex 15) dels gestos propis del mode
    # L'efecte és temporal: actiu mentre es manté premut el botó indicat.

    def poll_negharm(self, button_states, axis_pot=None, button_index=15):
        """Actualitza l'estat d'harmonia negativa des dels botons (i un pot opcional).

        button_states : llista de botons rebuda a update().
        axis_pot      : si es dóna (0-127), tria l'eix mentre l'efecte és actiu.
        button_index  : botó que activa l'efecte mentre es manté premut
                        (per defecte índex 15 = botó 16).
        Retorna True si l'efecte està actiu.
        """
        self.neg_active = (isinstance(button_states, (list, tuple))
                           and len(button_states) > button_index
                           and bool(button_states[button_index]))
        if self.neg_active and axis_pot is not None:
            self.neg_axis = min(7, int((axis_pot / 127.0) * 8))
        return self.neg_active

    def negharm(self, note, tonic_pc):
        """Reflecteix una nota en harmonia negativa si l'efecte està actiu."""
        if self.neg_active:
            from modes.negharm import reflect_note
            return reflect_note(note, tonic_pc, self.neg_axis)
        return note

    def negharm_axis_name(self):
        """Nom de l'eix d'harmonia negativa actual (p. ex. 'Quinta')."""
        from modes.negharm import NEG_HARM_NAMES
        return NEG_HARM_NAMES[self.neg_axis % len(NEG_HARM_NAMES)]
