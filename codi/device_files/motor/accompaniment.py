"""Accompaniment — motor d'acompanyament del firmware TECLA (port de tecla-accompaniment.js).

Hostatja diversos PATRONS (ritme/baix/arpegi/seqüència) sobre un rellotge compartit.
Cada patró emet MIDI pel SEU canal (→ el seu so en un sinte extern) i segueix un
CONTEXT HARMÒNIC compartit (tònica + escala) que el TECLAT actualitza quan canvies
de to/escala. Així l'acompanyament encaixa amb el que toques. (El ritme ignora
l'harmonia.) Algorisme idèntic al del simulador (tecla-accompaniment.js); temps en
SEGONS (time.monotonic) en lloc de ms.

Mòdul amb càrrega lazy: només s'importa si alguna tecla té un patró assignat.
"""


try:
    from core.pantalla import diu
except Exception:                       # simulador i proves sense core/
    def diu(text):
        print(text)
        return True
# Cada patró: (n=pas global, ctx={'root','scale'}, rng) → llista de (note, dur, vel).
# dur en PASSOS (corxeres de setze). El motor programa el note_off.
#
# REGISTRE: tots els patrons sonen PER SOTA del teclat. El teclat toca de
# root a root+12 (els vuit graus), i la base va de root-24 a root-1: mai la
# mateixa nota. Amb un DAW que escolta tots els canals en un sol instrument
# (el que fan per defecte), un note-off de la base sobre una nota que el
# teclat aguanta la tallava, i l'arpegi que passava per la tònica ho feia a
# cada compàs. La base segueix el teclat quan canvia d'octava (sync_context).


def _pat_pols(n, ctx, rng):
    """Pols/Ritme: pulsació percussiva sobre la tònica greu, a la negra (no harmònic)."""
    if n % 4 == 0:
        return ((ctx['root'] - 24, 1, 110),)
    return ()


def _pat_baix(n, ctx, rng):
    """Baix: tònica/quinta/tònica/quinta greu, una nota per negra, sota el teclat."""
    if n % 4 != 0:
        return ()
    offs = (0, 7, 0, -5)
    return ((ctx['root'] - 12 + offs[(n >> 2) % 4], 3, 100),)


def _pat_arpegi(n, ctx, rng):
    """Arpegi/Pad: arpegia la tríada diatònica (graus 0,2,4), una octava sota el teclat."""
    if n % 2 != 0:
        return ()
    sc = ctx['scale']
    triad = (sc[0], sc[2 % len(sc)], sc[4 % len(sc)])
    return ((ctx['root'] - 12 + triad[(n >> 1) % 3], 2, 85),)


def _pat_sequencia(n, ctx, rng):
    """Seqüència: línia generativa dins l'escala (determinista via rng), una octava sota el teclat."""
    if n % 2 != 0:
        return ()
    deg = int(rng() * len(ctx['scale']))
    if deg >= len(ctx['scale']):
        deg = len(ctx['scale']) - 1
    return ((ctx['root'] - 12 + ctx['scale'][deg], 1, 90),)


PATTERNS = {
    'pols': _pat_pols,
    'baix': _pat_baix,
    'arpegi': _pat_arpegi,
    'sequencia': _pat_sequencia,
}


def _make_custom(spec):
    """Patró CUSTOM creat a l'editor "Acompanyaments" de l'app.

    spec: {'sequence': [grau 0-7 | -1(silenci), ...], 'octave': -2..2,
           'velocity': 30-127, 'gate': 10-100 (% del pas), 'bpm': 60-200}
    Cada pas de la seqüència dura 2 setzens (corxera). El grau indexa l'escala
    del context (7 = tònica una octava amunt), com l'editor de l'arpegiador.
    Mirall de makeCustomPattern (tecla-accompaniment.js)."""
    seq = spec.get('sequence') or [0]
    oct_off = 12 * int(spec.get('octave', 0) or 0)
    vel = max(1, min(127, int(spec.get('velocity', 90) or 90)))
    gate = max(10, min(100, int(spec.get('gate', 90) or 90)))
    dur = 2.0 * gate / 100.0          # passos de setzè (fraccional permès)

    def pat(n, ctx, rng):
        if n % 2 != 0:
            return ()
        deg = seq[(n >> 1) % len(seq)]
        if deg is None or deg < 0:
            return ()
        sc = ctx['scale']
        note = ctx['root'] + oct_off + sc[deg % len(sc)] + 12 * (deg // len(sc))
        return ((note, dur, vel),)

    return pat


def _mulberry(seed):
    """RNG determinista (port de mulberry32). Retorna funció () → [0,1)."""
    state = [seed & 0xFFFFFFFF]

    def _imul(x, y):
        return ((x & 0xFFFFFFFF) * (y & 0xFFFFFFFF)) & 0xFFFFFFFF

    def rng():
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        a = state[0]
        t = _imul(a ^ (a >> 15), (1 | a) & 0xFFFFFFFF)
        t = ((t + _imul(t ^ (t >> 7), (61 | t) & 0xFFFFFFFF)) ^ t) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    return rng


class Accompaniment:
    def __init__(self, midi_out):
        self.midi_out = midi_out
        self.bpm = 110
        self.ctx = {'root': 60, 'scale': (0, 2, 4, 5, 7, 9, 11)}
        self.patterns = []       # [{'type', 'channel', 'rng'}]
        self._step = 0
        self._next_t = 0.0
        self._running = False
        self._note_offs = []     # [(t_abs, note, channel)]

    # El teclat ho crida quan canvia de to/escala perquè l'acompanyament el segueixi.
    def set_context(self, root, scale):
        self.ctx = {'root': root,
                    'scale': tuple(scale) if scale else (0, 2, 4, 5, 7, 9, 11)}

    def set_tempo(self, bpm):
        self.bpm = max(40, min(240, bpm))

    @property
    def step_s(self):
        """Segons per corxera de setze."""
        return 60.0 / self.bpm / 4.0

    # ── Patrons ──────────────────────────────────────────────────────────────
    def add_pattern(self, pat_type, channel, now=0.0):
        if pat_type not in PATTERNS:
            return False
        self.remove_pattern(channel)
        self.patterns.append({'type': pat_type, 'fn': PATTERNS[pat_type], 'channel': channel,
                              'rng': _mulberry(0x9E37 + channel * 131 + len(pat_type))})
        if not self._running:
            self._running = True
            self._step = 0
            self._next_t = now
        return True

    def add_custom(self, spec, channel, now=0.0):
        """Afegeix un acompanyament CUSTOM (editor de l'app). Aplica el seu BPM."""
        self.remove_pattern(channel)
        try:
            fn = _make_custom(spec)
        except Exception:
            return False
        self.set_tempo(int(spec.get('bpm', self.bpm) or self.bpm))
        self.patterns.append({'type': 'custom', 'fn': fn, 'channel': channel,
                              'rng': _mulberry(0x9E37 + channel * 131)})
        if not self._running:
            self._running = True
            self._step = 0
            self._next_t = now
        return True

    def add_fn(self, fn, channel, now=0.0, tipus='fn'):
        """Un patró qualsevol, (n, ctx, rng) → ((nota, dur, vel), …): el que
        fa servir la funció 'progression' (motor/kbd_progressio.py)."""
        self.remove_pattern(channel)
        self.patterns.append({'type': tipus, 'fn': fn, 'channel': channel,
                              'rng': _mulberry(0x9E37 + channel * 131)})
        if not self._running:
            self._running = True
            self._step = 0
            self._next_t = now
        return True

    def remove_pattern(self, channel):
        self._channel_off(channel)
        self.patterns = [p for p in self.patterns if p['channel'] != channel]
        if not self.patterns:
            self._running = False

    def clear(self):
        self.all_off()
        self.patterns = []
        self._running = False

    # ── Rellotge ─────────────────────────────────────────────────────────────
    def tick(self, now):
        if self._running:
            step_s = self.step_s
            # RESINCRONITZACIÓ: si ve d'una pausa llarga, no disparis
            # centenars de passos. És l'ÚNIC lloc on val reprogramar la fase
            # des d'ara —allà no hi ha graella a mantenir—; el pas normal la
            # suma (`_next_t += step_s`), que és el que fa que el tempo no es
            # perdi. Vegeu tests/test_cap_mode_perd_el_tempo.py.
            if now - self._next_t > step_s * 8:
                self._next_t = now          # resincronitza
            guard = 0
            while now >= self._next_t and guard < 64:
                guard += 1
                self._fire_step(self._step, now)
                self._step = (self._step + 1) % 65536
                self._next_t += step_s
        self._flush_offs(now)

    def _fire_step(self, n, now):
        step_s = self.step_s
        for pat in self.patterns:
            fn = pat.get('fn') or PATTERNS.get(pat['type'])
            if not fn:
                continue
            try:
                events = fn(n, self.ctx, pat['rng']) or ()
            except Exception:
                events = ()
            for note, dur, vel in events:
                note = max(0, min(127, int(note)))
                self._send_on(note, vel, pat['channel'])
                self._note_offs.append((now + dur * step_s * 0.9, note, pat['channel']))

    # ── Note-offs programats ─────────────────────────────────────────────────
    def _flush_offs(self, now):
        if not self._note_offs:
            return                  # el cas de cada volta: res pendent, res a al·locar
        kept = []
        for t, note, ch in self._note_offs:
            if now >= t:
                self._send_off(note, ch)
            else:
                kept.append((t, note, ch))
        self._note_offs = kept

    def _channel_off(self, channel):
        kept = []
        for t, note, ch in self._note_offs:
            if ch == channel:
                self._send_off(note, ch)
            else:
                kept.append((t, note, ch))
        self._note_offs = kept

    def all_off(self):
        for _t, note, ch in self._note_offs:
            self._send_off(note, ch)
        self._note_offs = []

    # ── Enviament MIDI (canal propi per patró) ───────────────────────────────
    def _send_on(self, note, vel, channel):
        try:
            from adafruit_midi.note_on import NoteOn
            msg = NoteOn(note & 0x7F, vel & 0x7F)
            msg.channel = channel
            self.midi_out.send(msg)
        except Exception:
            pass

    def _send_off(self, note, channel):
        try:
            from adafruit_midi.note_off import NoteOff
            msg = NoteOff(note & 0x7F, 0)
            msg.channel = channel
            self.midi_out.send(msg)
        except Exception:
            pass


# ═══ Integració amb el Mode Teclat (capa teclat v3) ══════════════════════════
# La "base" del teclat: UN patró actiu que segueix la tonalitat/escala del
# teclat i sona per un canal propi. Gest del botó 'accomp' (kbd_buttons.py):
# tap = activa / cicla el patró · premuda llarga = desactiva.

ACCOMP_PATTERN_IDS = ('pols', 'baix', 'arpegi', 'sequencia')
ACCOMP_PATTERN_NAMES = ('Pols', 'Baix', 'Arpegi', 'Sequencia')
ACCOMP_CHANNEL = 1   # canal MIDI 0-indexat amb el canal de sortida per defecte (0)


def _canal(kbd):
    """El canal de la base segons el canal de sortida configurat (el mateix
    que el mode de fons: motor/modeloop.canals_auxiliars)."""
    try:
        from motor.modeloop import canals_auxiliars
        return canals_auxiliars(kbd.midi)[0]
    except Exception:
        return ACCOMP_CHANNEL

_KEY_OFFSET = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5,
               'F#': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}


def _engine(kbd):
    eng = getattr(kbd, '_accomp', None)
    if eng is None:
        eng = Accompaniment(kbd.midi)
        kbd._accomp = eng
    return eng


def sync_context(kbd):
    """Actualitza la tònica+escala de la base amb l'estat actual del teclat.
    Cridat en activar-la i en canviar tonalitat/escala/octava (kbd_buttons)."""
    eng = getattr(kbd, '_accomp', None)
    if eng is None:
        return
    try:
        from music_constants import SCALES
    except ImportError:
        SCALES = ((0, 2, 4, 5, 7, 9, 11),)
    sid = 0
    if getattr(kbd, 'available_scales', None):
        sid = kbd.available_scales[kbd.scale_mode_index]
    # Escales custom/progressions (ids >= 1000): la base cau a l'escala major.
    intervals = SCALES[sid] if 0 <= sid < len(SCALES) else SCALES[0]
    key = kbd.available_keys[kbd.key_index] if getattr(kbd, 'available_keys', None) else 'C'
    root = kbd.octave * 12 + _KEY_OFFSET.get(key, 0)
    eng.set_context(max(24, min(96, root)), intervals)


def _custom_specs(kbd):
    """Acompanyaments custom de la config (editor "Acompanyaments" de l'app)."""
    cm = getattr(kbd, 'config_manager', None)
    if cm is None:
        return []
    try:
        return cm.get_custom_accompaniments()
    except Exception:
        return []


def handle_button(kbd, held, now):
    """Gest del botó 'accomp': tap = activa/cicla patró (integrats + customs)
    · premuda llarga = desactiva."""
    active = getattr(kbd, '_accomp_active', False)
    if held >= 0.5 and active:
        kbd._accomp_active = False
        eng = getattr(kbd, '_accomp', None)
        if eng is not None:
            eng.clear()
        diu("Base OFF")
        return
    eng = _engine(kbd)
    customs = _custom_specs(kbd)
    total = len(ACCOMP_PATTERN_IDS) + len(customs)
    if not active:
        kbd._accomp_active = True
        kbd._accomp_pat_idx = 0
    else:
        kbd._accomp_pat_idx = (getattr(kbd, '_accomp_pat_idx', 0) + 1) % total
    idx = kbd._accomp_pat_idx % total
    sync_context(kbd)
    if idx < len(ACCOMP_PATTERN_IDS):
        eng.set_tempo(110)   # els integrats tornen al tempo estàndard
        eng.add_pattern(ACCOMP_PATTERN_IDS[idx], _canal(kbd), now)
        diu("Base: %s" % ACCOMP_PATTERN_NAMES[idx])
    else:
        spec = customs[idx - len(ACCOMP_PATTERN_IDS)]
        eng.add_custom(spec, _canal(kbd), now)
        diu("Base: %s" % spec.get('name', 'Custom'))


def stop(kbd):
    """Atura la base del tot (STOP global / cleanup del mode)."""
    eng = getattr(kbd, '_accomp', None)
    if eng is not None:
        eng.clear()
    kbd._accomp_active = False
