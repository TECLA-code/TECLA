"""
TECLA - Sintetitzador MIDI modular
Controla el maquinari i gestiona els diferents modes MIDI
"""
import time
import board
import digitalio
import analogio
import usb_midi
try:
    from core import llum as _llum
except Exception:
    _llum = None
from adafruit_midi import MIDI
from adafruit_midi.control_change import ControlChange
try:
    from core.pantalla import diu
except Exception:                       # simulador i proves sense core/
    def diu(text):
        print(text)
        return True

# El to PWM intern s'ha retirat a la v3.16 (GP22 ara és el blau del LED).
# mode_manager i mode_keyboard s'importen de forma lazy dins main() per estalviar RAM a l'inici

# Configuració de pins
# Nova versió del hardware: pins ordenats correctament (GP0, GP1, GP2, GP3...)
BUTTON_PINS = [
    board.GP0, board.GP1, board.GP2, board.GP3,
    board.GP4, board.GP5, board.GP6, board.GP7,
    board.GP8, board.GP9, board.GP10, board.GP11,
    board.GP12, board.GP13, board.GP14, board.GP15
]
POT_PINS = [board.A0, board.A1, board.A2]

# ── Lectura dels potes: calibratge viu ───────────────────────────────────────
# L'ADC del RP2040 no arriba als extrems i CADA pot té el seu recorregut: en un
# TECLA real un pot toca a 256 counts i un altre a 1488 (mesurat), i amunt no
# arriben a 65535. L'escala crua `raw * 127 // 65535` feia que el mínim físic
# donés 1-2 en comptes de 0 i el màxim 126 en comptes de 127. Com que els terres
# són diferents entre pots i entre unitats (hi ha maquinari al carrer), no serveix
# un marge fix: se segueix el recorregut OBSERVAT de cada pot (mínim i màxim que
# ha donat) i s'escala contra ell. Mentre el pot no s'ha mogut prou, s'usa l'escala
# clàssica [0, 65535] (cap regressió a l'arrencada); en girar-lo de banda a banda
# un cop, el seu mínim passa a 0 i el màxim a 127, exactes. Es recalibra sol amb
# l'ús; només viu a la RAM (es refà en segons en tornar a arrencar).
POT_ADC_MAX = 65535
POT_SPAN_MIN = 8000        # recorregut observat mínim per fiar-se'n

def escala_pot(raw, lo, hi):
    """raw ADC (0-65535) → 0-127 contra el recorregut observat [lo, hi]. Fins que
    [lo, hi] no cobreix POT_SPAN_MIN s'usa l'escala clàssica sobre tot el rang."""
    if hi - lo < POT_SPAN_MIN:
        lo = 0
        hi = POT_ADC_MAX
    v = (raw - lo) * 127 // (hi - lo)
    return 0 if v < 0 else (127 if v > 127 else v)


class TeclaHardware:
    """Classe per gestionar el maquinari de TECLA"""
    
    def __init__(self):
        self.buttons = self._init_buttons()
        self.pots = self._init_pots()
        self.last_button_states = [False] * len(BUTTON_PINS)
        # BÚFERS REUTILITZATS del camí calent. El bucle fa 500 voltes per segon
        # i cada llista nova és brossa que acaba disparant un gc de 10-30 ms
        # enmig del que estàs tocant. Contracte: qui rebi aquestes llistes les
        # ha de LLEGIR a l'acte, mai guardar-se'n la referència (tots els modes
        # fan `x, y, z = pot_values`; sim_link i potlayers en fan còpia).
        self._buf_buttons = [False] * len(BUTTON_PINS)
        self._buf_pots = [0] * len(POT_PINS)
        # Calibratge viu del recorregut de cada pot (vegeu escala_pot). Es
        # sembra "girat del revés" (lo alt, hi baix) perquè la primera lectura
        # de cada pot l'estableixi i, a partir d'aquí, només s'eixampla.
        self._pot_lo = [POT_ADC_MAX] * len(POT_PINS)
        self._pot_hi = [0] * len(POT_PINS)
        self._buf_kb = [False] * 15      # els 15 que rep el mode teclat
        self.last_pot_read = 0
        self.midi_out = None
        self.button_press_times = [0.0] * len(BUTTON_PINS)
        self.long_press_threshold = 0.8  # segons per canviar de banc amb Botó 13
        
        # Afegir accés al gestor de configuració
        from core.config_manager import ConfigManager
        self.config_manager = ConfigManager()
        
        # Referència al mode_manager (s'assignarà des de main())
        self.mode_manager = None
        
        # Pantalla OLED opcional (mòdul extern core/display_manager).
        # Si el fitxer no està instal·lat (versió sense pantalla) o no es
        # detecta cap SSD1306 per I2C, tot funciona exactament igual.
        self.has_display = False
        self.display_manager = None
        try:
            from core.display_manager import DisplayManager
            _dm = DisplayManager()
            if _dm.ok:
                self.display_manager = _dm
                self.has_display = True
                print("Pantalla OLED detectada")
            else:
                _dm = None
        except Exception:
            pass
        
        # Variables per al mode teclat
        self.keyboard_mode_active = False  # S'activarà al main()
        self.keyboard_mode = None
        self.keyboard_octave = 4
        self.keyboard_toggle_blocked_until = 0.0  # Bloqueig temporal per evitar toggle múltiple
    
    def display_event(self, method, *args):
        """Crida segura a la pantalla: no-op si no n'hi ha, i cap error de
        la pantalla pot afectar mai el so ni el bucle principal."""
        dm = self.display_manager
        if dm:
            try:
                getattr(dm, method)(*args)
            except Exception:
                pass

    def llum_de_capa(self, bank=None):
        """Pinta el LED amb el color de la capa. Mai pot petar ni bloquejar.

        El color viu al banc com a `color: [r, g, b]` (0-255). L'escriuen les
        apps; si una capa no en té, es fa servir el de la personalitat, que
        almenys diu quina TECLA ets. Mateix contracte que display_event: un
        testimoni no pot afectar el so.
        """
        try:
            from core import llum
            b = bank if bank is not None else (self.config_manager.get_current_bank() or {})
            rgb = b.get('color')
            mode_led = b.get('led', 'fix')       # fix · pols · to (core/llum)
            # La intensitat de la capa, 0-100 (%). Sense la clau, la de sempre.
            try:
                intens = max(0, min(100, int(b.get('llum', 100)))) / 100.0
            except Exception:
                intens = 1.0
            if rgb and len(rgb) == 3:
                llum.capa(rgb, mode_led, intens)
                return
            from core import personalitat
            llum.capa(llum.COLORS[int(personalitat.actual()) % len(llum.COLORS)], mode_led, intens)
        except Exception:
            pass

    def _init_buttons(self):
        """Inicialitza tots els botons"""
        buttons = []
        for i, pin in enumerate(BUTTON_PINS):
            try:
                btn = digitalio.DigitalInOut(pin)
                btn.direction = digitalio.Direction.INPUT
                btn.pull = digitalio.Pull.DOWN
                buttons.append(btn)
            except Exception:
                buttons.append(None)
        return buttons
    
    def _init_pots(self):
        """Inicialitza tots els potenciòmetres"""
        pots = []
        for i, pin in enumerate(POT_PINS):
            try:
                pot = analogio.AnalogIn(pin)
                # Fer una lectura inicial per verificar que funciona
                test_value = pot.value
                pots.append(pot)
            except Exception:
                pots.append(None)
        return pots
    
    def read_buttons(self):
        """Llegeix l'estat actual dels botons. Retorna el BÚFER reutilitzat."""
        buf = self._buf_buttons
        for i, btn in enumerate(self.buttons):
            buf[i] = btn.value if btn else False
        return buf
    
    def read_pots(self):
        """Escala els potes a 0-127 contra el recorregut viu de cada un. Retorna
        el BÚFER reutilitzat."""
        buf = self._buf_pots
        lo = self._pot_lo
        hi = self._pot_hi
        for i, pot in enumerate(self.pots):
            if pot:
                raw = pot.value
                if raw < lo[i]:
                    lo[i] = raw
                if raw > hi[i]:
                    hi[i] = raw
                buf[i] = escala_pot(raw, lo[i], hi[i])
            else:
                buf[i] = 0
        return buf
    
    def _switch_layer(self, step):
        """Cicla a la capa (banc) següent/anterior i activa el motor del seu tipus.

        Les capes són TIPADES ('teclat' o 'modes'): una capa de teclat porta la
        seva pròpia configuració (escales, funcions de botó, harmonia, potes…)
        que config_manager llegeix per-banc; per això el teclat es RECREA a cada
        canvi — sense recrear-lo, una segona capa de teclat sonaria com la primera.
        """
        try:
            banks = self.config_manager.config.get('banks', []) or []
            if not banks:
                return
            old_name = self.config_manager.get_current_bank().get('name', '')
            new_index = (self.config_manager.current_bank_index + step) % len(banks)
            self.config_manager.set_current_bank(new_index)
            bank = self.config_manager.get_current_bank() or {}
            name = bank.get('name', '') or ('Capa %d' % (new_index + 1))
            btype = bank.get('type', 'modes')
            diu(f"🔁 Capa: {old_name} → {name} ({btype})")
            self.display_event('show_layer', name)
            self.llum_de_capa(bank)          # el LED diu a quina capa ets
            self.keyboard_toggle_blocked_until = time.monotonic() + 0.5
            if btype == 'teclat':
                self._activate_keyboard_layer()
            else:
                self._activate_modes_layer()
            # (cada _activate_* ja fa el seu gc.collect; no en cal un altre aquí
            #  — cada collect extra són ~10-30ms que es noten al toc)
        except Exception as e:
            print(f"Error canviant de capa: {e}")

    def _all_notes_off(self):
        """CC120 (All Sound Off) + CC123 (All Notes Off) a tots els canals,
        amb UN missatge reutilitzat (32 al·locacions costaven gc al canvi de capa)."""
        cc = ControlChange(120, 0, channel=0)
        for ch in range(16):
            for ctrl in (120, 123):
                cc.control = ctrl
                cc.value = 0
                cc.channel = ch
                self.midi_out.send(cc)

    def _activate_keyboard_layer(self):
        """Activa una capa de tipus TECLAT amb la config del banc actual."""
        # Desactivar els efectes temporals NO persistents (Sustain, Pausa…)
        # amb el seu on_deactivate: si el Sustain quedés actiu en passar al
        # teclat, el pedal CC64 continuaria premut al synth i la primera nota
        # del teclat quedaria enganxada. 'Config Modes' i 'Loop' es conserven.
        if self.mode_manager:
            from motor.mm_update import mm_deactivate_efectes_no_persistents
            mm_deactivate_efectes_no_persistents(self.mode_manager)
            # El loop de modes es conserva (continua sonant des del bucle
            # principal), però una presa OBERTA es tanca: si no, gravaria el
            # teclat fins a tornar a la capa de modes.
            _lp = getattr(self.mode_manager, '_modeloop', None)
            if _lp is not None:
                try:
                    _lp.tanca_presa(time.monotonic())
                except Exception:
                    pass
        # Aturar i descarregar el mode actiu ABANS de crear el teclat: evita
        # notes penjades (el mode deixaria de rebre update() i no enviaria mai
        # els NoteOff) i allibera RAM per a la instància nova.
        if self.mode_manager:
            if self.mode_manager.current_mode:
                try:
                    self.mode_manager._stop_current_mode()
                except Exception:
                    pass
                self.mode_manager.current_mode = None
                self.mode_manager.current_mode_name = None
            # TOTS els modes, no només l'actiu. El ModeManager en manté fins a
            # tres de vius perquè tornar-hi sigui instantani; en SORTIR de la
            # capa de modes això és RAM retinguda per a res, i el que ve ara
            # —KeyboardMode i els seus set mòduls— és l'al·locació més gran de
            # tot el firmware.
            try:
                self.mode_manager.unload_all_modes()
            except Exception:
                pass
        self._all_notes_off()
        # RECREAR sempre el teclat: cada capa de teclat té la seva pròpia config
        # (config_manager la llegeix per-banc). Els bytecodes ja són a sys.modules,
        # així que només es paga la instanciació.
        if self.keyboard_mode:
            try:
                self.keyboard_mode.cleanup()
            except Exception:
                pass
            self.keyboard_mode = None
        import gc
        gc.collect()
        try:
            from motor.mode_keyboard import KeyboardMode
            self.keyboard_mode = KeyboardMode(
                self.midi_out,
                {'octave': self.keyboard_octave},
                config_manager=self.config_manager
            )
            self.keyboard_mode.mode_manager = self.mode_manager   # per al mode de fons
            self.keyboard_mode.setup()
        except MemoryError:
            # L'ÚNIC diagnòstic de memòria que es diu en veu alta, perquè només
            # apareix quan alguna cosa ja ha fallat. Mentre tot vagi bé, la
            # Pantalla no ha de saber res de RAM: és de l'usuari, no meva.
            print("⚠ SENSE MEMÒRIA creant la capa de teclat")
            self.keyboard_mode = None
            raise
        except Exception as e:
            print(f"Error creant teclat: {e}")
        self.keyboard_mode_active = True
        # Diagnòstic: la capa porta config pròpia o cau a la global? Si aquí
        # surt "global" per a una capa que hauries configurat, guarda-la de nou
        # des de l'app (Guardar configuració) i reinstal·la la config.
        try:
            _own = 'pròpia' if (self.config_manager.get_current_bank() or {}).get('keyboard_button_functions') else 'global'
            print(f"Capa teclat activa | Octava: {self.keyboard_octave} | config: {_own}")
        except Exception:
            print(f"Capa teclat activa | Octava: {self.keyboard_octave}")

    def _activate_modes_layer(self):
        """Activa una capa de tipus MODES amb els modes/efectes del banc actual."""
        if not self.mode_manager:
            print("⚠ Capa de modes no disponible")
            return
        self.keyboard_mode_active = False
        # Cleanup i destruir la INSTÀNCIA del teclat. El seu BYTECODE es
        # queda: purgar-lo va deixar el teclat mort a la primera volta (són
        # ~60 KB i en una capa de modes no n'hi ha ni la meitat de lliures).
        # Vegeu tests/test_memoria_canvi_de_capa.py.
        if self.keyboard_mode:
            try:
                self.keyboard_mode.cleanup()
            except Exception:
                pass
            self.keyboard_mode = None
        import gc
        gc.collect()
        # Atura el mode que sonava, ALLIBERA la capa que deixes i carrega la
        # config del banc nou. L'alliberament és el que faltava: sense ell el
        # mode actiu quedava orfe (mm_set_mode només descarrega l'anterior si
        # `current_mode` és cert) i el seu bytecode es quedava al heap fins que
        # no passaves per una capa de teclat. Vegeu mm_enter_modes_layer.
        try:
            self.mode_manager.enter_modes_layer()
        except Exception as e:
            print(f"Error entrant a la capa de modes: {e}")
        print("Capa de modes activa")
        self._all_notes_off()

    def check_mode_change(self, mode_names, button_states=None):
        """Comprova si s'ha canviat de mode i retorna el nou mode o None"""
        if button_states is None:
            button_states = self.read_buttons()
            
        mode_changed = None
        
        # Gestionar botons especials primer
        
        # Botó 13 (index 12) - Curt: Teclat ON/OFF | Llarg: Canvi de banc
        if button_states[12] and not self.last_button_states[12]:
            # Just pressed: enregistrar temps
            self.button_press_times[12] = time.monotonic()
        elif (not button_states[12]) and self.last_button_states[12]:
            pressed_time = self.button_press_times[12] or 0.0
            duration = time.monotonic() - pressed_time if pressed_time else 0.0
            current_time = time.monotonic()
            if current_time < self.keyboard_toggle_blocked_until:
                # Descartar el flanc, no ajornar-lo: cal actualitzar l'estat
                # anterior del botó 13; si no, el release es re-detecta a cada
                # cicle i en expirar el bloqueig la duració acumulada pot
                # superar el llindar i disparar un canvi no desitjat.
                # NOMÉS l'índex 12: copiar tota la llista podria empassar-se
                # un flanc simultani d'un altre botó (p.ex. l'emergency stop).
                self.last_button_states[12] = button_states[12]
                return None
            # Tecla 13 = CICLAR CAPES (noves capes tipades: teclat o modes).
            # Toc curt → capa següent (esquerra→dreta, amb volta) · premuda
            # llarga → capa anterior. Cada capa s'activa amb el motor del seu
            # tipus i la SEVA configuració pròpia.
            self._switch_layer(-1 if duration >= self.long_press_threshold else 1)
        
        # Botó 16 (index 15) - EMERGENCY STOP + NETEJA DE MEMÒRIA
        if button_states[15] and not self.last_button_states[15]:
            diu("ATURA!")
            self.display_event('show_stop')
            try:
                # 1. PRIORITAT MÀXIMA: Aturar TOT el so immediatament
                if self.mode_manager:
                    self.mode_manager.stop_all_sound()
                
                # 2. Netejar mode teclat (incloent pausar el looper si sona)
                if self.keyboard_mode:
                    try:
                        if hasattr(self.keyboard_mode, 'pause_looper'):
                            self.keyboard_mode.pause_looper()
                        _acc = getattr(self.keyboard_mode, '_accomp', None)
                        if _acc is not None:
                            _acc.clear()
                            self.keyboard_mode._accomp_active = False
                        if getattr(self.keyboard_mode, '_fons', None) is not None:
                            from motor.kbd_fons import atura as _fons_atura
                            _fons_atura(self.keyboard_mode)
                        # I la progressió en una tecla: si no, el rellotge del
                        # teclat la tornava a fer sonar a l'acord següent
                        if getattr(self.keyboard_mode, '_prog', None) is not None:
                            from motor.kbd_progressio import atura as _prog_atura
                            _prog_atura(self.keyboard_mode)
                        self.keyboard_mode.stop_all_notes()
                    except:
                        pass
                
                # 2b. Aturar el loop MIDI i les capes de potes de la capa de modes
                if self.mode_manager:
                    _lp = getattr(self.mode_manager, '_modeloop', None)
                    if _lp is not None:
                        try:
                            _lp.clear(self.midi_out)
                        except Exception:
                            pass
                    _lay = getattr(self.mode_manager, '_potcfg', None)
                    if _lay is not None:
                        _lay.off()

                # 3. EMERGENCY STOP del mode_manager: descarrega tots els modes
                if self.mode_manager:
                    self.mode_manager.emergency_stop_and_cleanup()
                    
            except Exception as e:
                print(f"Error STOP: {e}")
        
        # Si estem en mode teclat, no processar canvis de mode normal
        if self.keyboard_mode_active:
            # Actualizar el estado anterior
            self.last_button_states[:] = button_states
            return None
        
        # Obtenir el banc actual i les seves assignacions (només si no estem en mode teclat)
        current_bank = self.config_manager.get_current_bank()
        button_assignments = current_bank.get('modes', [])
        disabled_modes = current_bank.get('disabled_modes', [])
        
        # Processar botons 1-12 per canvis de mode normal
        for i in range(min(12, len(button_assignments))):
            if button_states[i] and not self.last_button_states[i]:
                # Utilitzar l'assignació del botó des de la configuració
                assigned_mode = button_assignments[i]
                # Validar contra el mode_manager: load_config() manté button_mappings
                # sincronitzat amb el banc actual. La llista mode_names del bucle
                # principal queda obsoleta després d'un canvi de banc (botó 13 llarg)
                # i faria invisible qualsevol mode que no fos al banc inicial.
                if self.mode_manager:
                    valid = self.mode_manager.button_mappings.get(i) == assigned_mode
                else:
                    valid = assigned_mode in mode_names
                if valid and assigned_mode not in disabled_modes:
                    mode_changed = assigned_mode
                    break
                
        # Actualizar el estado anterior
        self.last_button_states[:] = button_states
        
        return mode_changed
    
    def _kb_buttons(self, button_states):
        """Els 15 botons del mode teclat, al BÚFER reutilitzat.

        `button_states[:15]` era una llista nova a cada volta del bucle: 500
        per segon només per retallar una llista que ja tenim."""
        buf = self._buf_kb
        n = len(button_states)
        for i in range(15):
            buf[i] = button_states[i] if i < n else False
        return buf

    def update_keyboard_mode(self, pot_values, button_states):
        """Actualitza el mode teclat si està actiu"""
        if self.keyboard_mode_active:
            # Crear el mode al primer cicle si no existeix
            if not self.keyboard_mode:
                try:
                    print("🎹 Inicialitzant Mode Teclat...")
                    import gc; gc.collect()
                    from motor.mode_keyboard import KeyboardMode
                    self.keyboard_mode = KeyboardMode(
                        self.midi_out,
                        {'octave': self.keyboard_octave},
                        config_manager=self.config_manager
                    )
                    self.keyboard_mode.setup()
                    print(f"🎹 Mode Teclat activat | Octava: {self.keyboard_octave}")
                    
                    # IMPORTANT: Cridar update() immediatament per sincronitzar potenciòmetres
                    keyboard_buttons = self._kb_buttons(button_states)
                    self.keyboard_mode.update(pot_values, keyboard_buttons)
                    self.keyboard_octave = self.keyboard_mode.octave
                    return True
                except Exception as e:
                    print(f"❌ Error creant Mode Teclat: {e}")
                    self.keyboard_mode_active = False
                    return False
            
            # Passar els botons 1-15 al mode teclat (octàva gestionada internament)
            keyboard_buttons = self._kb_buttons(button_states)
            try:
                self.keyboard_mode.update(pot_values, keyboard_buttons)
                if self.keyboard_mode.octave != self.keyboard_octave:
                    self.keyboard_octave = self.keyboard_mode.octave
                    self.display_event('show_keyboard', self.keyboard_octave)
            except Exception as e:
                # AMB SOSTRE. Aquest `print` era a cada volta d'un bucle de
                # 500 Hz: quan el teclat es queda sense RAM en surten centenars
                # de línies seguides (360 mesurades en un minut), i cada una
                # CONSTRUEIX una cadena nova just quan no queda memòria i
                # bloqueja escrivint al CDC. El gestor d'errors s'afegia al
                # problema que reportava. Un avís cada 3 s, amb el recompte.
                self._kb_err_n = getattr(self, '_kb_err_n', 0) + 1
                _ara = time.monotonic()
                if _ara - getattr(self, '_kb_err_t', 0) > 3.0:
                    self._kb_err_t = _ara
                    print("❌ Error update Mode Teclat (%d cops): %r"
                          % (self._kb_err_n, e))
            return True
        return False


SENYAL_RECARREGA = '.config_reload'


def senyal_de_recarrega(ultim, signal_file=SENYAL_RECARREGA):
    """Hi ha senyal de recàrrega de configuració? Retorna (cal_recarregar, ultim).

    L'app deixa aquest fitxer per dir "he canviat la config, torna-la a llegir",
    i el firmware l'esborra en atendre'l. Però mentre el disc estigui muntat a
    un ordinador, el sistema de fitxers és de NOMÉS LECTURA per al dispositiu:
    l'os.remove falla, el senyal es queda posat i, sense guarda, la config es
    recarregava SENCERA cada 0,5 s —registre, modes, mode actual reiniciat—
    mentre el cable estigués endollat. Es notava com un dispositiu que va a
    batzegades i no es podia atribuir a res.

    Per això el senyal s'identifica pel seu CONTINGUT: un que ja s'ha atès no
    es torna a atendre encara que el fitxer no s'hagi pogut esborrar.
    """
    try:
        with open(signal_file, 'r') as f:
            marca = f.read().strip()
    except OSError:
        return False, None          # no hi ha senyal: el següent sí que valdrà

    nou = marca != ultim
    if nou:
        print("📡 Senyal de recàrrega detectada (timestamp: %s)" % marca)
    try:
        import os
        os.remove(signal_file)
        return nou, None
    except OSError:
        return nou, marca           # no s'ha pogut esborrar: recorda'l


def main():
    """Funció principal de TECLA"""
    # Esperar que la connexió USB s'estabilitzi (evita KeyboardInterrupt espuri de Thonny/REPL)
    time.sleep(1.5)
    # Banner simple
    print("\nT E C L A\n")
    
    # Habilitar el recollidor de brossa si està disponible
    try:
        import gc
        gc.enable()
        last_gc_time = time.monotonic()
    except ImportError:
        gc = None

    # Marca d'aigua de RAM: mínim de memòria lliure POST-collect. NOMÉS té
    # sentit mesurar-la després d'un gc.collect(): entre col·leccions la RAM
    # lliure baixa en dent de serra fins gairebé zero per disseny (MicroPython
    # només recull quan una assignació falla), així que el valor instantani
    # no diu res del marge real.
    ram_watermark = None

    # Watchdog hardware: si el firmware es penja del tot, el dispositiu es
    # reinicia sol (clau en actuacions en directe; supervisor.reload() només
    # cobreix excepcions, no els bloquejos). NOMÉS s'activa sense consola
    # serial connectada: amb Thonny/REPL actiu seguiria corrent dins del REPL
    # i reiniciaria el dispositiu mentre desenvolupes.
    _wdt = None
    try:
        import supervisor
        if not supervisor.runtime.serial_connected:
            import microcontroller
            from watchdog import WatchDogMode
            _wdt = microcontroller.watchdog
            _wdt.timeout = 8  # segons (màx ~8.3 al RP2040); el bucle el refresca cada ~20ms
            _wdt.mode = WatchDogMode.RESET
            print("Watchdog actiu (8s)")
    except Exception:
        _wdt = None
    
    # ── Tallafoc anti boot-loop: 3 crashes seguits → MODE SEGUR (només teclat).
    # El comptador viu a la NVM (sobreviu el reset) i es neteja quan el bucle
    # porta 10s viu. Sense això, un error persistent = reinicis infinits.
    try:
        from core import crashguard
    except Exception:
        crashguard = None
    safe_boot, last_crash = crashguard.boot_status() if crashguard else (False, '')
    if safe_boot:
        print("⛑ MODE SEGUR (3 crashes seguits). Últim error:", last_crash)

    # Inicialitzar maquinari
    hardware = TeclaHardware()

    # Animació d'arrencada a la pantalla (no-op si no hi ha pantalla)
    hardware.display_event('boot_animation')
    if safe_boot:
        hardware.display_event('show_message', 'MODE SEGUR',
                               (last_crash or 'REINSTALLA')[:11])


    # Inicialitzar sortida MIDI. El port avisa el LED de cada NoteOn que surt
    # (teclat, modes, looper, acompanyament, fons: tot passa per aquí), i el
    # LED decideix si hi fa res segons el mode de la capa (core/llum).
    try:
        midi_out = MIDI(midi_out=usb_midi.ports[1])
        if _llum is not None:
            midi_out = _llum.PortAmbLlum(midi_out)
    except Exception:
        print("Error: No s'ha pogut inicialitzar MIDI")
        return
    
    # Assignar sortida MIDI al maquinari. Reutilitzar el ConfigManager ja creat
    # a TeclaHardware (evita una 2a instància que duplicaria el JSON ~7.6KB i
    # podria desincronitzar-se respecte check_mode_change).
    config_manager = hardware.config_manager
    try:
        _midi_ch = config_manager.get_midi_channel()
        midi_out.out_channel = max(0, min(15, _midi_ch - 1))
        print(f"Canal MIDI: {_midi_ch}")
    except Exception:
        pass
    hardware.midi_out = midi_out

    # L'ENTRADA MIDI s'ha de buidar encara que l'Instrument no la faci servir.
    # Quan un programa del PC tria el dispositiu (Resolume, Ableton...), li
    # envia MIDI de retorn —rellotge, feedback dels controls. Si ningú no ho
    # llegeix mai, la cua del port s'omple, l'ordinador es queda esperant i el
    # programa es penja en triar-lo. Un buidatge per volta del bucle, i prou.
    _midi_in = None
    _midi_in_buf = bytearray(64)
    try:
        _midi_in = usb_midi.ports[0] if len(usb_midi.ports) > 0 else None
        if not hasattr(_midi_in, 'readinto'):
            _midi_in = None
    except Exception:
        _midi_in = None

    def _midi_drain():
        if _midi_in is None:
            return
        try:
            for _ in range(8):
                if not _midi_in.readinto(_midi_in_buf):
                    break
        except Exception:
            pass

    # SEMPRE arrencar a la PRIMERA capa (ordre previsible en connectar): la
    # config porta el 'current_bank' que l'app tenia seleccionat en guardar
    # (s'usa per al hot-reload mentre edites), però una arrencada freda ha de
    # començar per la capa 1 de la pestanya Dispositiu. Es fa ABANS de crear
    # KeyboardMode/ModeManager perquè llegeixen la config per-banc del banc
    # actual. No es desa a disc.
    try:
        config_manager.current_bank_index = 0
    except Exception:
        pass

    # ── SENSE ÀUDIO INTERN: EL LED HI VA OCUPAR EL LLOC ─────────────────────
    # Fins a la v3.16 GP22 era la sortida d'àudio (minijack) i el firmware hi
    # feia un to PWM monofònic a cada nota del teclat. El maquinari ha canviat:
    # ara hi ha un LED multicolor i el to intern s'ha retirat sencer
    # (core/tone.py). El LED de la placa va a GP20/GP21/GP22, o sigui que GP22
    # hi ha tornat com a BLAU. Els seus pins són de core/llum.py i de ningú
    # més: dos amos al mateix pin volia dir soroll al LED a cada tecla.
    hardware.audio = None

    # CRÍTIC: Crear KeyboardMode ANTES de ModeManager mentre la memòria és neta
    if gc:
        gc.collect()
    try:
        from motor.mode_keyboard import KeyboardMode
        hardware.keyboard_mode = KeyboardMode(
            midi_out,
            {'octave': hardware.keyboard_octave},
            config_manager=hardware.config_manager
        )
        hardware.keyboard_mode.setup()
        hardware.keyboard_mode_active = True
        print("🎹 Mode Teclat inicialitzat")
    except Exception as e:
        print(f"⚠ Mode Teclat no disponible: {e}")
        hardware.keyboard_mode = None
        hardware.keyboard_mode_active = False
    if gc:
        gc.collect()

    mode_manager = None
    mode_names = []
    if safe_boot:
        # MODE SEGUR: sense ModeManager els canvis de mode són no-ops al bucle
        # i el teclat funciona amb normalitat (el crash persistent probablement
        # venia d'un mode o de la seva càrrega).
        print("⛑ MODE SEGUR: modes desactivats en aquesta arrencada")
    else:
        try:
            from motor.mode_manager import ModeManager
            if gc:
                gc.collect()
            mode_manager = ModeManager(midi_out, config_manager=hardware.config_manager)
            hardware.mode_manager = mode_manager
            if hardware.keyboard_mode is not None:
                hardware.keyboard_mode.mode_manager = mode_manager   # per al mode de fons
            mode_names = mode_manager.get_available_modes()
            print(f"Modes: {len(mode_names)} disponibles")
        except MemoryError:
            print("⚠ ModeManager no disponible (poca RAM)")
        except Exception as _mm_e:
            print(f"⚠ ModeManager error: {_mm_e}")
    
    # Mostrar capa actual
    try:
        current_bank = config_manager.get_current_bank()
        bank_name = current_bank.get('name', 'Defecte')
        print(f"\nCapa actual: {bank_name}\n")
    except Exception:
        current_bank = {}

    # Arrencar amb el motor del TIPUS de la capa actual (capes tipades v3).
    # El KeyboardMode ja s'ha creat abans (moment de RAM neta: així els seus
    # bytecodes queden carregats); si la capa inicial és de modes, se'n destrueix
    # la instància (els bytecodes es conserven per al proper canvi de capa).
    # En MODE SEGUR (sense mode_manager) sempre queda el teclat.
    try:
        hardware.llum_de_capa(current_bank)   # el color de la capa d'arrencada
        if (current_bank or {}).get('type', 'teclat') == 'modes' and mode_manager is not None:
            hardware._activate_modes_layer()
            hardware.display_event('show_layer', bank_name)
        elif hardware.keyboard_mode_active:
            hardware.display_event('show_keyboard', hardware.keyboard_octave)
    except Exception:
        if hardware.keyboard_mode_active:
            hardware.display_event('show_keyboard', hardware.keyboard_octave)
    
    # Sincronització periòdica del sistema de fitxers
    last_sync_time = time.monotonic()
    sync_interval = 300  # segons (~5 minuts)

    # Variable para detectar cambios en la configuración
    last_config_check_time = time.monotonic()
    config_check_interval = 0.5  # Comprovar canvis cada 0.5s (redueix I/O de filesystem; imperceptible)
    ultim_senyal = None          # senyal de recàrrega ja atès (vegeu senyal_de_recarrega)
    last_config_hash = config_manager.get_config_hash()

    # Detectar el simulador UN SOL COP (evita reintentar l'import 10x/s al hardware real)
    _sim_shared_state = None
    try:
        from core.simulator_mocks import shared_state as _sim_shared_state
    except (ImportError, AttributeError):
        _sim_shared_state = None

    # ── Mode CONTROLADOR (sync amb el simulador de l'app) ───────────────────
    # Quan l'app obre el canal de dades USB (usb_cdc.data), el dispositiu
    # deixa de sonar en local i envia botons+pots al navegador: les tecles
    # físiques CONTROLEN el simulador (core/sim_link.py, protocol de la v2).
    # En desconnectar, el firmware reprèn el funcionament autònom.
    _simlink = None
    _sim_ctrl_active = False
    _sim_obert = False          # el port de dades és obert (encara no se sap qui)
    _pantalla_dades = False     # …i és la Pantalla de l'app (core/pantalla.dades)
    try:
        import usb_cdc as _usb_cdc
        if _usb_cdc.data is not None:
            from core.sim_link import SimLink
            _simlink = SimLink(_usb_cdc.data, hardware.display_manager)
    except Exception:
        _simlink = None

    # ── La Pantalla de l'app: TECLA es presenta a qui s'hi connecta ────────
    # TECLA exposa dos ports USB que des de l'ordinador són iguals (a Windows,
    # dos «COM»). Abans la Pantalla només servia per la consola i l'havia
    # d'endevinar per descart; ara qualsevol port val: la consola s'anuncia
    # quan algú l'obre (DTR), i el port de dades quan l'app hi diu
    # {"s":"pantalla"}. La presentació és «⌁ TECLA v…» + la capa i el mode.
    _versio = ''
    try:
        with open('tecla_version.txt') as _fv:
            _versio = _fv.read().strip()
    except Exception:
        pass
    _consola_ant = False
    try:
        import supervisor as _sup
    except Exception:
        _sup = None

    def _anuncia(via):
        try:
            from core import pantalla as _pant
            _capa = ''
            try:
                _capa = config_manager.get_current_bank().get('name', '')
            except Exception:
                pass
            _mode = None
            if (mode_manager is not None and not hardware.keyboard_mode_active
                    and getattr(mode_manager, 'current_mode', None) is not None):
                _mode = mode_manager.current_mode_name
            _pant.anuncia(_versio, _capa, _mode, via)
        except Exception:
            pass

    # Gest de canvi de PERSONALITAT: les quatre cantonades, 3 s. Tota la
    # lògica és a core/personalitat.vigila() i les tres personalitats hi
    # passen — el Macropad i el Blocks són codi GENERAT per les seves apps, i
    # com menys n'hagin d'escriure, menys se'n poden deixar (se n'havien deixat
    # el gest sencer).
    try:
        from core import personalitat as _pers_mod
    except Exception:
        _pers_mod = None

    def _silencia():
        """Abans del reinici dur: que no quedi res sonant a l'altra banda."""
        if hardware.keyboard_mode:
            hardware.keyboard_mode.stop_all_notes()
        if mode_manager:
            mode_manager.stop_all_sound()

    # Bucle principal
    _ctrl_c_count = 0
    _last_ctrl_c_time = 0
    _mem_fails = 0          # MemoryError empassats al bucle (abans, en silenci)
    _last_mem_warn = 0
    
    boot_ok_at = time.monotonic() + 10   # 10s vius = boot consolidat (crashguard)

    # ── El POLS del bucle: el sostre de precisió de tot l'instrument ────────
    #
    # El rellotge dels modes ja no perd el tempo —suma la fase en comptes de
    # llegir-la (motor/rellotge.py)—, però cap pas no pot caure abans que la
    # volta on li toca. O sigui que el JITTER de tot l'instrument és, com a
    # màxim, la durada d'una volta d'aquest bucle. Una volta de 2 ms no es
    # nota; una recollida de memòria de 30 ms enmig d'un compàs, sí.
    #
    # Es mesura sempre perquè costa dues restes d'enters per volta, i perquè
    # un instrument que diu que va com un rellotge ha de poder-ho ensenyar.
    # Va amb ticks_ms (enters, sense al·locar) i no amb time.monotonic(), que
    # és un float de precisió simple i es degrada amb les hores enceses.
    try:
        from motor.rellotge import ara as _tick, diferencia as _tickdif
    except Exception:
        _tick = None
    _pols_voltes = 0
    _pols_pitjor = 0
    _pols_5 = 0
    _pols_15 = 0
    _pols_ant = _tick() if _tick else 0

    try:
        while True:
            current_time = time.monotonic()
            _midi_drain()          # que el PC mai no es quedi amb la cua plena

            if _tick:
                _t = _tick()
                _d = _tickdif(_t, _pols_ant)
                _pols_ant = _t
                _pols_voltes += 1
                if _d > _pols_pitjor:
                    _pols_pitjor = _d
                if _d >= 5:
                    _pols_5 += 1
                    if _d >= 15:
                        _pols_15 += 1

            try:
                # Refrescar el watchdog (si està actiu)
                if _wdt:
                    _wdt.feed()

                if boot_ok_at is not None and current_time > boot_ok_at:
                    boot_ok_at = None
                    if crashguard:
                        crashguard.mark_ok()   # reset del comptador de crashes

                # Llegir botons i potenciòmetres
                button_states = hardware.read_buttons()
                pot_values = hardware.read_pots()

                # ── Canvi de personalitat (4 cantonades, 3 s) ──────────────
                # Va ABANS de tot el processament: si el gest s'ha completat,
                # aquesta volta ja no ha de fer sonar res.
                if _pers_mod is not None:
                    # Si el gest es completa, vigila() no torna: reinicia en dur.
                    _pers_mod.vigila(button_states, current_time, _silencia)

                # ── L'entrada de la consola es BUIDA: ningú no la llegeix ──
                # mentre l'instrument corre, i el FIFO USB (256 bytes) es
                # quedava ple per sempre amb el que qualsevol programa hi
                # hagués escrit un dia. Ple, el port ja no accepta res: ni el
                # Ctrl-C ×3 per aturar. Es llegeix i es llença (cada 8 voltes).
                if (_pols_voltes & 7) == 0:
                    try:
                        _nc = _usb_cdc.console.in_waiting
                        if _nc:
                            _usb_cdc.console.read(_nc)
                    except Exception:
                        pass

                # ── La consola: qui l'obre (DTR) rep la presentació ────────
                try:
                    _sc = bool(_sup.runtime.serial_connected) if _sup else False
                except Exception:
                    _sc = False
                if _sc != _consola_ant:
                    _consola_ant = _sc
                    if _sc:
                        _anuncia('consola')

                # ── El port de dades: simulador (mode controlador) o Pantalla ──
                if _simlink is not None:
                    if _simlink.connected:
                        if not _sim_obert:
                            _sim_obert = True
                            _simlink.reset()
                        _mask = 0
                        for _bi in range(min(16, len(button_states))):
                            if button_states[_bi]:
                                _mask |= (1 << _bi)
                        _qui = _simlink.pump(_mask, pot_values, current_time)
                        if _qui == 'sim':
                            if not _sim_ctrl_active:
                                _sim_ctrl_active = True
                                # Silenciar el so local: mentre el simulador mana,
                                # el que sona és el navegador (mirall exacte).
                                try:
                                    if hardware.keyboard_mode:
                                        hardware.keyboard_mode.stop_all_notes()
                                    if mode_manager:
                                        mode_manager.stop_all_sound()
                                except Exception:
                                    pass
                                print("Simulador connectat: mode controlador")
                            if _simlink.diag_requested:
                                _simlink.diag_requested = False
                                try:
                                    _simlink.send_diag({
                                        'v': '3.2', 'ram': gc.mem_free() if gc else 0})
                                except Exception:
                                    pass
                            time.sleep(0.005)
                            continue
                        elif _qui == 'pantalla' and not _pantalla_dades:
                            _pantalla_dades = True
                            try:
                                from core import pantalla as _pant
                                _pant.dades(_usb_cdc.data)
                            except Exception:
                                pass
                            _anuncia('dades')
                        # (esperant la presentació: el dispositiu segueix sonant)
                    elif _sim_obert:
                        _sim_obert = False
                        if _sim_ctrl_active:
                            _sim_ctrl_active = False
                            print("Simulador desconnectat: mode autònom")
                        if _pantalla_dades:
                            _pantalla_dades = False
                            try:
                                from core import pantalla as _pant
                                _pant.dades(None)
                            except Exception:
                                pass

                # Comprovar canvis de mode (inclou gestió del botó teclat)
                new_mode = hardware.check_mode_change(mode_names, button_states)
                if new_mode and mode_manager and new_mode != mode_manager.current_mode_name:
                    mode_manager.set_mode(new_mode)
                    # Mostrar el mode actiu a la pantalla (només si s'ha activat)
                    if mode_manager.current_mode_name == new_mode:
                        try:
                            _bn = config_manager.get_current_bank().get('name', '')
                        except Exception:
                            _bn = ''
                        hardware.display_event('show_mode', new_mode, _bn)
                
                # Actualitzar el mode teclat si està actiu
                _mm_ha_girat = False
                if hardware.update_keyboard_mode(pot_values, button_states):
                    # Mode teclat actiu - no processar altres modes
                    pass
                elif mode_manager and mode_manager.current_mode:
                    # Mode normal actiu
                    status = mode_manager.update(pot_values, button_states)
                    _mm_ha_girat = True
                if mode_manager and not _mm_ha_girat:
                    # El loop de modes «continua sonant en canviar de mode o de
                    # capa»: mm_update només gira amb un mode carregat i fora
                    # de la capa de teclat. Sense això, al teclat el loop es
                    # quedava congelat amb les notes obertes al canal 3.
                    _lp = getattr(mode_manager, '_modeloop', None)
                    if _lp is not None and _lp.state:
                        try:
                            _lp.tick(mode_manager.effect_manager.midi, current_time)
                        except Exception:
                            pass

                if _llum is not None:
                    _llum.tick(current_time)       # el LED reactiu cau sol
                    
                    # Sense pantalla - no cal actualitzar animacions
                
                # Comprobar si ha habido cambios en la configuración (desde la GUI u otra fuente)
                if current_time - last_config_check_time > config_check_interval:
                    try:
                        signal_file = SENYAL_RECARREGA
                        config_changed = False
                        
                        # SUPORT SIMULADOR: Comprovar flag config_reload_requested
                        if _sim_shared_state is not None and _sim_shared_state.config_reload_requested:
                            print(f"🎮 Simulador: Recàrrega de configuració sol·licitada")
                            config_changed = True
                            _sim_shared_state.config_reload_requested = False  # Reset flag
                        
                        hi_ha_senyal, ultim_senyal = senyal_de_recarrega(
                            ultim_senyal, signal_file)
                        if hi_ha_senyal:
                            config_changed = True
                        else:
                            # Sempre, encara que hi hagi un senyal ENCALLAT que ja
                            # s'ha atès: si no, un senyal que no es pot esborrar
                            # (disc muntat a un ordinador) tapava per sempre
                            # l'altra via de detectar canvis.
                            current_config_hash = config_manager.get_config_hash()
                            if current_config_hash != last_config_hash:
                                config_changed = True
                                last_config_hash = current_config_hash
                        
                        if config_changed:
                            print("🔄 Aplicant canvis de configuració...")
                            # CRÍTIC: partir d'un heap net abans del transitori de
                            # recàrrega (config vella + nova + registre conviuen un
                            # instant). Mesurat al hardware: amb 3 bancs el mínim
                            # de RAM lliure cau per sota d'1KB sense aquest collect.
                            if gc:
                                gc.collect()
                            config_manager.config = config_manager._load_config()
                            if gc:
                                gc.collect()
                            config_manager.current_bank_index = config_manager.config.get('current_bank', 0)
                            if mode_manager:
                                try:
                                    mode_manager.load_config()
                                    print("✅ Configuració aplicada")
                                except Exception as e:
                                    print(f"Error config: {e}")
                                if mode_manager.reload_current_mode():
                                    print("✅ Mode reiniciat")
                                try:
                                    mode_names = mode_manager.get_available_modes()
                                except Exception:
                                    pass
                            
                            # Actualitzar hash després de recarregar
                            last_config_hash = config_manager.get_config_hash()

                            # Re-aplicar el motor de la capa actual amb la config
                            # NOVA: si és de teclat, el KeyboardMode es recrea (si
                            # no, seguiria sonant amb la config antiga); si ara és
                            # de modes i el teclat era actiu, s'hi canvia.
                            try:
                                _bt = (config_manager.get_current_bank() or {}).get('type', 'teclat')
                                if _bt == 'teclat':
                                    hardware._activate_keyboard_layer()
                                elif hardware.keyboard_mode_active:
                                    hardware._activate_modes_layer()
                            except Exception as e:
                                print(f"Error re-aplicant capa: {e}")

                            # Tornar a mostrar l'estat actual a la pantalla
                            if hardware.keyboard_mode_active:
                                hardware.display_event('show_keyboard', hardware.keyboard_octave)
                            else:
                                try:
                                    _bn = config_manager.get_current_bank().get('name', '')
                                except Exception:
                                    _bn = ''
                                if mode_manager and mode_manager.current_mode_name:
                                    hardware.display_event('show_mode', mode_manager.current_mode_name, _bn)
                                else:
                                    hardware.display_event('show_layer', _bn)
                            
                            # Forzar sincronización del sistema de archivos tras detectar cambios
                            try:
                                import os
                                os.sync()
                            except (ImportError, AttributeError, NotImplementedError):
                                pass
                    except Exception as e:
                        print(f"Error al comprovar canvis a la configuració: {e}")
                    
                    last_config_check_time = current_time
                
                # Neteja de memòria periòdica (cada 30 segons)
                if gc and current_time - last_gc_time > 30:
                    gc.collect()
                    last_gc_time = current_time
                    if hasattr(gc, 'mem_free'):
                        _free = gc.mem_free()
                        if ram_watermark is None or _free < ram_watermark:
                            ram_watermark = _free
                        print(f"[RAM] lliure post-gc: {_free} | mínim post-gc: {ram_watermark}")
                    if _tick and _pols_voltes:
                        # El gc.collect() d'aquesta mateixa volta es comptarà a
                        # la següent: es reporta el que ha passat, no el que
                        # aquesta línia està causant.
                        print("[POLS] %d voltes/s | pitjor %d ms | >=5ms: %d | >=15ms: %d"
                              % (_pols_voltes // 30, _pols_pitjor, _pols_5, _pols_15))
                        _pols_voltes = 0
                        _pols_pitjor = 0
                        _pols_5 = 0
                        _pols_15 = 0

                # Sincronització periòdica del sistema de fitxers (cada ~5 min).
                # Basat en temps, no en cycle_count: la condició antiga
                # (cycle_count % 3000 dins del bloc de GC de 30s) gairebé mai
                # coincidia i el sync no s'executava.
                if current_time - last_sync_time > sync_interval:
                    last_sync_time = current_time
                    try:
                        import os
                        os.sync()
                    except (ImportError, AttributeError, NotImplementedError):
                        pass
                
                # Control de velocitat del bucle. 2ms de tope: sense el motor
                # d'àudio l'RP2040 va sobrat, i el que mana és la LATÈNCIA de
                # tecla — amb l'antic 20ms (50Hz) una pulsació podia esperar
                # fins a 20ms només per ser detectada, i es notava al toc.
                elapsed = time.monotonic() - current_time
                target_cycle_time = 0.002
                if elapsed < target_cycle_time:
                    time.sleep(target_cycle_time - elapsed)
                    
            except MemoryError:
                # NO en silenci. Aquest `except` sense veu és el que feia que
                # el dispositiu es degradés sense explicar-ho: modes que no
                # carreguen, tecles que no fan res i cap pista a la Pantalla.
                # Va amb prefix `⚠` perquè la Pantalla el reconegui com a error
                # i amb un sostre d'un avís cada 3 s: el bucle va a 500 Hz i
                # dir-ho a cada volta ompliria el CDC i bloquejaria l'instrument
                # —que és exactament el que la regla diu()/print() evita.
                _mem_fails += 1
                if gc:
                    gc.collect()
                if current_time - _last_mem_warn > 3.0:
                    _last_mem_warn = current_time
                    _lliure = gc.mem_free() if (gc and hasattr(gc, 'mem_free')) else -1
                    print("⚠ SENSE MEMÒRIA al bucle (%d cops) | lliure: %d"
                          % (_mem_fails, _lliure))
            except KeyboardInterrupt:
                # Permetre interrupció manual amb 3x Ctrl+C en 2 segons
                if current_time - _last_ctrl_c_time < 2.0:
                    _ctrl_c_count += 1
                else:
                    _ctrl_c_count = 1
                _last_ctrl_c_time = current_time
                if _ctrl_c_count >= 3:
                    print("\n⚠ Interrupció manual detectada (3x Ctrl+C)")
                    raise  # Sortir al REPL
                print(f"⚡ Ctrl+C {_ctrl_c_count}/3 (prem 3 vegades per aturar)")
            except Exception:
                time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nAturant T E C L A per sol·licitud de l'usuari...")
    except MemoryError as _me:
        print("\nError crític: Memòria insuficient. Reiniciant...")
        if crashguard:
            crashguard.record_crash(_me)
        import supervisor
        supervisor.reload()  # Reiniciar el dispositiu
    except Exception as e:
        print(f"\nError crític: {e}")
        if crashguard:
            crashguard.record_crash(e)
        try:
            import traceback
            traceback.print_exception(e)  # Més detall en CircuitPython
        except Exception:
            pass
    finally:
        # Assegurar que sempre es neteja correctament
        print("Netejant recursos...")
        try:
            # Neteja del mode teclat
            if 'hardware' in locals() and hardware is not None:
                if hardware.keyboard_mode_active and hardware.keyboard_mode:
                    hardware.keyboard_mode.cleanup()
                    print("Mode teclat netejat")
            
            if 'mode_manager' in locals() and mode_manager is not None:
                mode_manager.cleanup()

            # NOTA: no es desa la config aquí. El filesystem de CircuitPython és
            # de només lectura per al codi mentre USB està actiu, així que el
            # save_config() que hi havia fallava sempre i només generava soroll.

            # Sincronizar sistema de archivos si es posible
            try:
                import os
                os.sync()
            except (ImportError, AttributeError, NotImplementedError):
                pass
        except Exception as e:
            print(f"Error en la neteja final: {e}")
        
        # Alliberar memòria final
        if gc:
            gc.collect()
            
        print("T E C L A aturat correctament.")
        # Petita pausa abans de sortir
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Ctrl+C espuri durant l'arranc (habitual amb Thonny/serial connectat)
        # Reiniciar automàticament per continuar funcionant
        print("Interrupt durant l'arranc — reiniciant...")
    except Exception as _e:
        # Crash durant l'ARRENC (abans que main() tingui el seu crashguard):
        # registrar-lo perquè el tallafoc anti boot-loop el compti igualment.
        print(f"Error fatal: {_e}")
        try:
            from core import crashguard as _cg
            _cg.record_crash(_e)
        except Exception:
            pass
    # Reiniciar sempre (plug-and-play). supervisor.reload() només DEMANA la
    # recàrrega (ReloadException pendent, disparada al següent punt de control
    # del VM); si el script s'acaba abans, la petició es perd i el dispositiu
    # cau al REPL. El bucle de sleep dona al VM el punt on disparar-la.
    try:
        import supervisor as _sv
        _sv.reload()
    except Exception:
        _sv = None
    while _sv is not None:
        time.sleep(0.1)
