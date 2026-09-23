"""El MODE DE FONS de la capa de teclat (SPEC_CAPA_HIBRIDA.md).

Una tecla de la capa de teclat amb la funció 'mode' engega un mode de fàbrica
o del Laboratori que sona PER SOTA mentre toques el teclat amb totes les
seves funcions —el mateix gest que la base d'acompanyament, amb qualsevol
mode com a base. Quin mode toca ho diu `bank['modes'][tecla]`, la llista de
setze que la capa de teclat ja porta.

El gest, en una sola tecla:
    TAP amb el fons aturat  → engega el mode, amb els potes a la seva
                              primera capa de comandaments (Volum · …)
    TAP                     → capa següent; després de l'última, els potes
                              tornen al TECLAT (el mode segueix sonant)
    TAP després d'això      → torna a la primera capa
    PREMUDA LLARGA          → atura i descarrega el mode

Hi pot haver més d'una tecla 'mode' a la capa, cada una amb el seu mode:
un TAP a una altra tecla mentre un fons sona el canvia per aquell (n'hi ha
un de sol sonant: el sostre és el CPU). Premuda llarga a qualsevol l'atura.

El fons no rep tecles (són del teclat) i rep els potes CONGELATS on eren en
engegar-lo (també són del teclat): només hi arriba el que li dona la capa
de comandaments, via set_param i CCs. Surt pel canal de l'ACOMPANYAMENT (1),
que és «l'instrument de fons» al DAW, i que l'STOP ja escombra. Mòdul
mandrós: només s'importa si la tecla s'usa.

Mesurat al dispositiu: la capa de teclat té ~130 KB lliures amb el gestor de
modes viu; un mode de fons en costa entre 5 i 10. El sostre el posa el CPU
(teclat ~3,6 ms + mode 0,5-2 ms per volta), no la RAM: un fons per capa.
"""
try:
    from core.pantalla import diu
except Exception:                       # simulador i proves sense core/
    def diu(text):
        print(text)
        return True

FONS_CHANNEL = 1                        # el de l'acompanyament: «instrument de fons»
_SENSE_BOTONS = [False] * 16
_LLARGA = 0.6                           # segons de premuda per aturar


class MidiCanal:
    """Embolcall de la sortida MIDI que porta al canal del fons tot el que el
    mode envia pel canal per defecte. La percussió (canal 9) es queda com és:
    allà l'alçada és l'instrument.

    El VOLUM del fons (la primera capa de comandaments) no surt com a CC7: es
    queda aquí i escala la velocitat de cada nota del mode. Un CC7 pel canal
    del fons, en un DAW que escolta tots els canals en un sol instrument (el
    que fan per defecte), abaixava també el teclat, i no hi havia manera de
    deixar el fons fluix i tocar-hi a sobre fort."""

    def __init__(self, midi, canal):
        self.midi = midi
        self.canal = canal
        self.volum = 127                # 0-127: escala la velocitat del fons

    def send(self, msg, channel=None):
        try:
            if getattr(msg, 'control', None) == 7:
                self.volum = int(getattr(msg, 'value', 127))
                return None             # no viatja: és del fons, no de l'instrument
            if self.volum < 127 and type(msg).__name__.endswith('NoteOn'):
                vel = int(getattr(msg, 'velocity', 0))
                if vel > 0:
                    msg.velocity = max(1, (vel * self.volum) // 127)
            c = getattr(msg, 'channel', None)
            if c is None or c == 0:
                msg.channel = self.canal
        except Exception:
            pass
        return self.midi.send(msg)

    def __getattr__(self, nom):          # out_channel i companyia: els del port de debò
        return getattr(self.midi, nom)


class Fons:
    def __init__(self, kbd):
        self.kbd = kbd
        self.nom = None
        self.btn = -1                   # la tecla que l'ha engegat
        self.lay = None
        self.pots = None                # els potes congelats que veu el mode
        self.mgr = getattr(kbd, 'mode_manager', None)
        self._midi_real = None          # la sortida del gestor mentre el fons hi posa l'embolcall

    @property
    def actiu(self):
        return self.nom is not None and self.mgr is not None and self.mgr.current_mode is not None

    @property
    def potes_al_mode(self):
        return self.actiu and self.lay is not None and self.lay.active

    def engega(self, nom, pot_values, btn=-1):
        if self.mgr is None:
            diu("⚠ Fons: sense gestor de modes")
            return False
        # El fons surt pel seu canal: el gestor rep l'embolcall ABANS de
        # carregar el mode, perquè el mode neix amb ell i el seu setup() ja
        # hi passa. Abans s'embolcallava després: el drone que Raga engega
        # a setup() sortia pel canal del teclat, i el seu note-off (ja per
        # l'embolcall) pel canal 1, o sigui que es quedava sonant per sempre.
        # I les escombrades del gestor en aturar (notes registrades, CC123)
        # també van així pel canal del fons, no pel del teclat.
        if self._midi_real is None:
            self._midi_real = self.mgr.midi_out
            from motor.modeloop import canals_auxiliars
            self.mgr.midi_out = MidiCanal(self._midi_real, canals_auxiliars(self._midi_real)[0])
        # Els potes directes del fons van congelats (mana la capa de sota):
        # el gestor no ha de dir «🎚 Pots: …», que aquí no seria veritat.
        self.mgr._diu_potes = False
        try:
            ok = self.mgr.set_mode(nom)
        finally:
            self.mgr._diu_potes = True
        if not ok:
            self._restaura_midi()
            return False
        mode = self.mgr.current_mode
        mode.midi_out = self.mgr.midi_out
        self.nom = nom
        self.btn = btn
        self.pots = list(pot_values) if pot_values else [64, 64, 64]
        from motor.potlayers import PotLayers
        self.lay = PotLayers()
        self.lay.set_mode(mode)
        self.lay.cycle(pot_values)       # capa 1: Volum · …
        self._congela_teclat()
        diu("Fons: %s" % nom)
        if self.lay.active:
            diu("🎚 Pots→mode: %s" % self.lay.name())
        return True

    def tap(self, pot_values):
        """El gest de la tecla en deixar-la anar (curt)."""
        if not self.actiu:
            return
        i = self.lay.cycle(pot_values)
        if i < 0:
            # Després de l'última capa: els potes tornen al teclat
            self._retorna_teclat()
            diu("🎚 Pots→teclat")
        else:
            self._congela_teclat()
            diu("🎚 Pots→mode: %s" % self.lay.name())

    def atura(self):
        if self.mgr is None:
            return
        if self.lay is not None:
            self.lay.off()
        if self.actiu:
            try:
                self.mgr._stop_current_mode()
            except Exception:
                pass
            self.mgr.current_mode = None
            self.mgr.current_mode_name = None
            try:
                self.mgr.unload_all_modes()
            except Exception:
                pass
            diu("Fons OFF")
        self._restaura_midi()
        self._retorna_teclat()
        self.nom = None
        self.btn = -1
        self.lay = None

    def _restaura_midi(self):
        """El gestor torna a la sortida de debò (la capa de modes la vol tal qual)."""
        if self._midi_real is not None and self.mgr is not None:
            self.mgr.midi_out = self._midi_real
        self._midi_real = None

    def tick(self, pot_values):
        """Cada volta del bucle, després del teclat."""
        if not self.actiu:
            return
        if self.lay is not None and self.lay.active:
            try:
                self.lay.apply(self.mgr.current_mode.midi_out, pot_values)   # pel canal del fons
            except Exception:
                pass
        try:
            self.mgr.update(self.pots, _SENSE_BOTONS)
        except Exception as e:
            print("Error fons: %s" % e)

    # ── Els potes del teclat: congelats mentre manen sobre el fons ───────────
    def _congela_teclat(self):
        self.kbd._pots_al_fons = True

    def _retorna_teclat(self):
        self.kbd._pots_al_fons = False
        self.kbd._pot_capa = None       # recollida: cap pot mana fins que es mou


def nom_del_fons(kbd, btn_idx):
    """Quin mode toca a la tecla: la llista de modes del banc de teclat."""
    try:
        bank = kbd.config_manager.get_current_bank() or {}
        modes = bank.get('modes') or []
        nom = modes[btn_idx] if btn_idx < len(modes) else ''
        if nom and nom not in ('Silenci', 'Teclat', 'RESERVADO'):
            return nom
    except Exception:
        pass
    return None


def handle_button(kbd, btn_idx, held, pot_values):
    """Gest de la tecla 'mode': tap = engega / capa següent / potes al teclat;
    premuda llarga = atura."""
    fons = getattr(kbd, '_fons', None)
    if fons is None:
        fons = kbd._fons = Fons(kbd)
    if held >= _LLARGA:
        fons.atura()
        return
    if fons.actiu and btn_idx == fons.btn:
        fons.tap(pot_values)
        return
    nom = nom_del_fons(kbd, btn_idx)
    if not nom:
        diu("Fons: cap mode a la tecla %d" % (btn_idx + 1))
        return
    if fons.actiu:
        if nom == fons.nom:             # la mateixa música des d'una altra tecla
            fons.btn = btn_idx
            fons.tap(pot_values)
            return
        fons.atura()                    # canvi de fons: fora l'un, hi va l'altre
    if not fons.engega(nom, pot_values, btn_idx):
        diu("⚠ Fons: no s'ha pogut carregar %s" % nom)


def atura(kbd):
    """STOP global / cleanup del teclat: fora el fons."""
    fons = getattr(kbd, '_fons', None)
    if fons is not None:
        fons.atura()


def tick(kbd, pot_values):
    fons = getattr(kbd, '_fons', None)
    if fons is not None and fons.actiu:
        fons.tick(pot_values)
