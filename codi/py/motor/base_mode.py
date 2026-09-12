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


# Comandaments COMUNS a totes les famílies: CCs que el motor resol sol, sense
# que el mode hi hagi de fer res. El nom és el mateix que a l'app (potlayers
# els tradueix a número de CC: els dígits després de 'CC' manen).
CC_COMUNS = ('Volum', 'Reverb (CC91)', 'Brillantor (CC74)', 'Modulació (CC1)',
             'Pan (CC10)', 'Expressió')


class BaseMode:
    # ── Comandaments del mode (vegeu SPEC_VARIABLES_FAMILIA.md) ─────────────
    # PARAMS: les variables que el mode exposa, en ordre de prioritat, amb els
    # noms del vocabulari de la seva família del Laboratori. POTS: els tres
    # que van per defecte als potes físics X, Y i Z. La llista sencera de
    # comandaments (comandaments()) és POTS + Volum + la resta de PARAMS +
    # els CCs comuns; l'app la pot reordenar per mode (config 'comandaments')
    # i el firmware la reparteix: els tres primers als potes, i de tres en
    # tres a cada TAP de 'Config Modes'.
    PARAMS = ()
    POTS = ()

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

    # note_on()/note_off() retornen el missatge DEL POOL, mutat. Abans cada
    # crida feia un `import` dins de la funció i al·locava un NoteOn/NoteOff
    # nou; el comentari de dalt deia que el pool eliminava les al·locacions "de
    # TOTS els modes" i no era cert: només les de qui feia servir
    # send_note_on()/send_note_off(), que són 6 modes de 65. Els altres 59 —i
    # 21 dels 22 instal·lats al dispositiu— seguien al·locant per nota, i cada
    # al·locació pot disparar un gc de 10-40 ms enmig del que estàs tocant.
    #
    # És segur perquè send() serialitza SÍNCRONAMENT: cap receptor no es queda
    # amb la referència. El patró de tot el codi és
    # `self.midi_out.send(self.note_on(...))`, mai acumular missatges en una
    # llista (comprovat a tots els modes) ni enviar-ne una llista de cop.
    #
    # channel=None a cada crida perquè send() el sobreescriu amb out_channel
    # quan és None, i el missatge del pool se'l quedaria per sempre.

    def note_on(self, note, velocity=127):
        msg = _note_on_msg()
        msg.note = note & 0x7F
        msg.velocity = velocity & 0x7F
        msg.channel = None
        return msg

    def note_off(self, note, velocity=0):
        msg = _note_off_msg()
        msg.note = note & 0x7F
        msg.velocity = velocity & 0x7F
        msg.channel = None
        return msg

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

    # ── Comandaments: set_param, potes, capes ────────────────────────────────

    def set_param(self, nom, v):
        """Aplica el comandament `nom` amb el pot a `v` (0-127). Torna True si
        el mode l'ha reconegut. El mapatge (rangs, corbes, trams) és del mode:
        el motor no sap què vol dir 'Tempo' per a cadascú. Els CCs comuns no
        passen per aquí: els resol comanda()."""
        return False

    def comandaments(self):
        """La llista sencera, en ordre: la de la config si l'app n'ha desat
        una per a aquest mode (set_comandaments), o la per defecte:
        POTS + Volum + la resta de PARAMS + els CCs comuns."""
        c = getattr(self, '_cmds', None)
        if c:
            return c
        # La llista per defecte es construeix UN cop: potes() la demana a cada
        # volta, i refer-la (tres bucles amb `in`) costava 1,4 ms al RP2040.
        c = getattr(self, '_cmds_def', None)
        if c:
            return c
        pots = tuple(self.POTS)
        out = list(pots)
        if 'Volum' not in out:
            out.append('Volum')
        for p in self.PARAMS:
            if p not in out:
                out.append(p)
        for p in CC_COMUNS:
            if p not in out:
                out.append(p)
        self._cmds_def = out
        return out

    def set_comandaments(self, llista):
        """L'ordre que l'app ha desat per a aquest mode (o None = defectes)."""
        self._cmds = list(llista) if llista else None
        self.repren_potes()

    def repren_potes(self):
        """Torna a armar la recollida dels potes físics: en sortir d'una capa
        de 'Config Modes', o en canviar la llista, cap pot mana fins que es
        torna a moure. Sense això el mode faria un salt a la posició on els
        vas deixar."""
        r = getattr(self, '_recull', None)
        if r:
            r.clear()

    def potes(self, pot_values):
        """Els tres potes físics, pel mateix camí que les capes: X, Y i Z són
        els tres primers comandaments. RECOLLIDA: en arrencar cap pot mana
        fins que es mou 4 unitats (el soroll de l'ADC és de ±1-2); llavors
        mana on l'has posat. Es descongelen un per un. Amb el botó 16 premut,
        Z està triant l'eix d'harmonia negativa i no s'aplica."""
        cmds = self.comandaments()
        r = getattr(self, '_recull', None)
        if r is None:
            r = self._recull = {}
        n = len(pot_values)
        for ax, idx in ((0, 1), (1, 0), (2, 2)):        # X=pots[1], Y=pots[0], Z=pots[2]
            if ax >= len(cmds) or idx >= n:
                break
            if ax == 2 and self.neg_active:
                continue
            v = pot_values[idx]
            a = r.get(ax, -999)
            if a == -999:
                r[ax] = v                               # primera lectura: on el vas deixar
                continue
            if a != -1:
                if -4 < v - a < 4:
                    continue                            # encara no s'ha mogut prou
                r[ax] = -1                              # ja mana
            self.comanda(cmds[ax], v)

    def comanda(self, nom, v):
        """Un comandament amb el pot a v (0-127): variable del mode o CC comú."""
        if not nom or nom == '—':
            return False
        if self.set_param(nom, v):
            return True
        from motor.potlayers import potfn_to_cc
        cc = potfn_to_cc(nom)
        if cc is None:
            return False
        c = getattr(self, '_cc_enviats', None)
        if c is None:
            c = self._cc_enviats = {}
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if abs(c.get(cc, -99) - v) < 2:
            return True
        c[cc] = v
        try:
            from adafruit_midi.control_change import ControlChange
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass
        return True

    # ── El rellotge dels modes ───────────────────────────────────────────────

    def toca(self, nom, periode_s):
        """Ja toca el pas de `nom`? Un pols regular que no perd el tempo.

        Substitueix el patró que cada mode es feia pel seu compte:

            if ara - self.last_step_t >= self.step_dur:
                self.last_step_t = ara          # <- aquí es perd el tempo

        El bucle principal fa unes 500 voltes per segon, o sigui que la
        condició es compleix fins a 2 ms TARD. Posant-hi `ara`, aquell retard
        es queda per sempre i el pas següent surt encara més tard. Mesurat
        simulant el bucle real: demanant 120 BPM en surten 119,05, i al cap
        d'un minut el pas cau 475 ms fora de la graella —gairebé quatre
        semicorxeres—. El looper, en canvi, ja era exacte, i per això el que es
        notava no era «va lent» sinó «no cau mai igual».

        Aquí la fase se suma, no es llegeix, i va en ENTERS de mil·lisegons:
        `time.monotonic()` és un float de precisió simple i la seva resolució
        es degrada amb les hores enceses (7,8 ms al cap d'un dia, el 6% d'una
        semicorxera). Vegeu motor/rellotge.py.

        Un mode pot tenir-ne diversos, cadascun amb el seu `nom`:

            if self.toca('pas', self.step_dur):   ...
            if self.toca('acord', 4.0):           ...

        El període es passa a cada volta a posta: així seguir el pot de tempo
        no demana res més, i canviar-lo no mou el pas que ja estava programat.
        """
        polsos = getattr(self, '_polsos', None)
        if polsos is None:
            polsos = self._polsos = {}
        p = polsos.get(nom)
        if p is None:
            from motor.rellotge import Pols
            polsos[nom] = Pols(periode_s)
            return True               # el primer pas del mode sona de seguida
        p.periode(periode_s)
        return p.toca()

    def dispara(self, nom):
        """Fes caure el pas de `nom` a la pròxima volta.

        Per als gestos que no poden esperar el pols: canviar d'acord, revocar
        en harmonia negativa. Substitueix el `self.last_x = 0` que feien alguns
        modes per forçar-ho —que amb la fase exacta ja no valdria, perquè
        sumar un període a zero dispararia a cada volta fins a atrapar el
        rellotge."""
        polsos = getattr(self, '_polsos', None)
        if polsos and nom in polsos:
            polsos[nom].dispara_ja()

    def resincronitza(self, nom=None):
        """Torna a arrencar els polsos: entrada al mode, represa d'una pausa."""
        polsos = getattr(self, '_polsos', None)
        if not polsos:
            return
        for n, p in polsos.items():
            if nom is None or n == nom:
                p.resincronitza()

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
            from motor.negharm import reflect_note
            return reflect_note(note, tonic_pc, self.neg_axis)
        return note

    def negharm_axis_name(self):
        """Nom de l'eix d'harmonia negativa actual (p. ex. 'Quinta')."""
        from motor.negharm import NEG_HARM_NAMES
        return NEG_HARM_NAMES[self.neg_axis % len(NEG_HARM_NAMES)]
