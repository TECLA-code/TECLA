"""
TECLA - Sintetitzador MIDI modular
Controla el maquinari i gestiona els diferents modes MIDI
"""
import time
import board
import pwmio
import digitalio
import analogio
import usb_midi
from adafruit_midi import MIDI
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange


# Funció global per convertir notes MIDI a freqüència
def midi_to_frequency(midi_note):
    """Converteix una nota MIDI a freqüència en Hz"""
    return round(440 * (2 ** ((midi_note - 69) / 12)))

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

class TeclaHardware:
    """Classe per gestionar el maquinari de TECLA"""
    
    def __init__(self):
        self.buttons = self._init_buttons()
        self.pots = self._init_pots()
        self.last_button_states = [False] * len(BUTTON_PINS)
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
        """Llegeix l'estat actual dels botons"""
        return [btn.value if btn else False for btn in self.buttons]
    
    def read_pots(self):
        """Llegeix i escala els valors dels potenciòmetres a 0-127"""
        values = []
        for pot in self.pots:
            if pot:
                # Llegir i escalar el valor directament
                raw_value = pot.value
                scaled_value = max(0, min(127, raw_value * 127 // 65535))
                values.append(scaled_value)
            else:
                values.append(0)
        return values
    
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
            if duration >= self.long_press_threshold:
                # Canvi de banc
                try:
                    old_bank_name = self.config_manager.get_current_bank().get('name', 'N/A')
                    
                    # CRÍTIC: Alliberar memòria abans de canviar de banc
                    import gc
                    gc.collect()
                    mem_before = gc.mem_free() if hasattr(gc, 'mem_free') else None
                    
                    self.config_manager.next_bank()
                    new_bank_name = self.config_manager.get_current_bank().get('name', 'N/A')
                    print(f"🔁 Capa canviada: {old_bank_name} → {new_bank_name}")
                    self.display_event('show_layer', new_bank_name)
                    
                    # IMPORTANT: Recarregar la configuració del mode_manager
                    # per actualitzar els efectes temporals i modes del nou banc
                    if self.mode_manager:
                        self.mode_manager.load_config()
                        print("✓ Configuració de la nova capa carregada")
                    
                    # Forçar garbage collection després del canvi
                    gc.collect()
                    mem_after = gc.mem_free() if hasattr(gc, 'mem_free') else None
                    
                    if mem_before and mem_after:
                        mem_freed = mem_after - mem_before
                        print(f"[MEMÒRIA] RAM alliberada: {mem_freed} bytes | Lliure ara: {mem_after} bytes")
                    
                except Exception as e:
                    print(f"Error canviant de capa: {e}")
            else:
                # Curt: toggle entre mode teclat i capa de modes
                current_time = time.monotonic()
                if current_time < self.keyboard_toggle_blocked_until:
                    # Descartar el flanc, no ajornar-lo: cal actualitzar l'estat
                    # anterior del botó 13; si no, el release es re-detecta a cada
                    # cicle i en expirar el bloqueig la duració acumulada pot
                    # superar el llindar i disparar un canvi de banc no desitjat.
                    # NOMÉS l'índex 12: copiar tota la llista podria empassar-se
                    # un flanc simultani d'un altre botó (p.ex. l'emergency stop).
                    self.last_button_states[12] = button_states[12]
                    return None
                
                if not self.keyboard_mode_active:
                    # Tornar a mode teclat
                    print("Activant capa teclat...")
                    # Aturar i descarregar el mode actiu ABANS de crear el teclat:
                    # evita notes penjades (el mode deixa de rebre update() i no
                    # enviaria mai els NoteOff) i allibera RAM per a la instància nova
                    if self.mode_manager and self.mode_manager.current_mode:
                        prev_mode = self.mode_manager.current_mode_name
                        try:
                            self.mode_manager._stop_current_mode()
                        except Exception:
                            pass
                        self.mode_manager.current_mode = None
                        self.mode_manager.current_mode_name = None
                        if prev_mode and prev_mode != 'Teclat':
                            try:
                                self.mode_manager._unload_mode(prev_mode)
                            except Exception:
                                pass
                    for ch in range(16):
                        self.midi_out.send(ControlChange(120, 0, channel=ch))
                        self.midi_out.send(ControlChange(123, 0, channel=ch))
                    self.keyboard_mode_active = True
                    self.keyboard_toggle_blocked_until = time.monotonic() + 0.5
                    import gc; gc.collect()
                    # Crear instància del teclat (bytecodes ja en sys.modules)
                    try:
                        from modes.mode_keyboard import KeyboardMode
                        self.keyboard_mode = KeyboardMode(
                            self.midi_out,
                            {'octave': self.keyboard_octave},
                            config_manager=self.config_manager
                        )
                        self.keyboard_mode.setup()
                    except Exception as e:
                        print(f"Error creant teclat: {e}")
                    print(f"Capa teclat activa | Octava: {self.keyboard_octave}")
                    self.display_event('show_keyboard', self.keyboard_octave)
                else:
                    # Canviar a capa de modes
                    if not self.mode_manager:
                        print("⚠ Capa de modes no disponible")
                        return None
                    print("Activant capa de modes...")
                    self.keyboard_mode_active = False
                    self.keyboard_toggle_blocked_until = time.monotonic() + 0.5
                    # Cleanup i destruir la instància del teclat
                    if self.keyboard_mode:
                        try:
                            self.keyboard_mode.cleanup()
                        except Exception:
                            pass
                        self.keyboard_mode = None  # Allibera la instància
                    # Alliberar memòria: esborrar INSTÀNCIA però mantenir bytecodes
                    # (evita recompilació de 29KB en tornar al teclat)
                    import gc
                    gc.collect()
                    # Netejar estat del mode actual
                    if self.mode_manager.current_mode:
                        try:
                            if hasattr(self.mode_manager.current_mode, 'cleanup'):
                                self.mode_manager.current_mode.cleanup()
                        except Exception:
                            pass
                        self.mode_manager.current_mode = None
                        self.mode_manager.current_mode_name = None
                    print("Capa de modes activa")
                    try:
                        _bn = self.config_manager.get_current_bank().get('name', '')
                    except Exception:
                        _bn = ''
                    self.display_event('show_layer', _bn)
                    for ch in range(16):
                        self.midi_out.send(ControlChange(120, 0, channel=ch))
                        self.midi_out.send(ControlChange(123, 0, channel=ch))
        
        # Botó 16 (index 15) - EMERGENCY STOP + NETEJA DE MEMÒRIA
        if button_states[15] and not self.last_button_states[15]:
            print("ATURA!")
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
                        self.keyboard_mode.stop_all_notes()
                    except:
                        pass
                
                # 3. EMERGENCY STOP del mode_manager: descarrega tots els modes
                if self.mode_manager:
                    self.mode_manager.emergency_stop_and_cleanup()
                    
            except Exception as e:
                print(f"Error STOP: {e}")
        
        # Si estem en mode teclat, no processar canvis de mode normal
        if self.keyboard_mode_active:
            # Actualizar el estado anterior
            self.last_button_states = button_states.copy()
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
        self.last_button_states = button_states.copy()
        
        return mode_changed
    
    def update_keyboard_mode(self, pot_values, button_states):
        """Actualitza el mode teclat si està actiu"""
        if self.keyboard_mode_active:
            # Crear el mode al primer cicle si no existeix
            if not self.keyboard_mode:
                try:
                    print("🎹 Inicialitzant Mode Teclat...")
                    import gc; gc.collect()
                    from modes.mode_keyboard import KeyboardMode
                    self.keyboard_mode = KeyboardMode(
                        self.midi_out,
                        {'octave': self.keyboard_octave},
                        config_manager=self.config_manager
                    )
                    self.keyboard_mode.setup()
                    print(f"🎹 Mode Teclat activat | Octava: {self.keyboard_octave}")
                    
                    # IMPORTANT: Cridar update() immediatament per sincronitzar potenciòmetres
                    keyboard_buttons = button_states[:15]
                    self.keyboard_mode.update(pot_values, keyboard_buttons)
                    self.keyboard_octave = self.keyboard_mode.octave
                    return True
                except Exception as e:
                    print(f"❌ Error creant Mode Teclat: {e}")
                    self.keyboard_mode_active = False
                    return False
            
            # Passar els botons 1-15 al mode teclat (octàva gestionada internament)
            keyboard_buttons = button_states[:15]
            try:
                self.keyboard_mode.update(pot_values, keyboard_buttons)
                if self.keyboard_mode.octave != self.keyboard_octave:
                    self.keyboard_octave = self.keyboard_mode.octave
                    self.display_event('show_keyboard', self.keyboard_octave)
            except Exception as e:
                print(f"❌ Error update Mode Teclat: {e}")
            return True
        return False


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
    
    # Inicialitzar maquinari
    hardware = TeclaHardware()

    # Animació d'arrencada a la pantalla (no-op si no hi ha pantalla)
    hardware.display_event('boot_animation')


    # Inicialitzar sortida MIDI
    try:
        midi_out = MIDI(midi_out=usb_midi.ports[1])
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

    # CRÍTIC: Crear KeyboardMode ANTES de ModeManager mentre la memòria és neta
    if gc:
        gc.collect()
    try:
        from modes.mode_keyboard import KeyboardMode
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
    try:
        from modes.mode_manager import ModeManager
        if gc:
            gc.collect()
        mode_manager = ModeManager(midi_out, config_manager=hardware.config_manager)
        hardware.mode_manager = mode_manager
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
        pass

    # Pantalla inicial: el dispositiu arrenca a la capa teclat
    if hardware.keyboard_mode_active:
        hardware.display_event('show_keyboard', hardware.keyboard_octave)
    
    # Sincronització periòdica del sistema de fitxers
    last_sync_time = time.monotonic()
    sync_interval = 300  # segons (~5 minuts)

    # Variable para detectar cambios en la configuración
    last_config_check_time = time.monotonic()
    config_check_interval = 0.5  # Comprovar canvis cada 0.5s (redueix I/O de filesystem; imperceptible)
    last_config_hash = config_manager.get_config_hash()

    # Detectar el simulador UN SOL COP (evita reintentar l'import 10x/s al hardware real)
    _sim_shared_state = None
    try:
        from core.simulator_mocks import shared_state as _sim_shared_state
    except (ImportError, AttributeError):
        _sim_shared_state = None
    
    
    # Bucle principal
    _ctrl_c_count = 0
    _last_ctrl_c_time = 0
    
    try:
        while True:
            current_time = time.monotonic()

            try:
                # Refrescar el watchdog (si està actiu)
                if _wdt:
                    _wdt.feed()

                # Llegir botons i potenciòmetres
                button_states = hardware.read_buttons()
                pot_values = hardware.read_pots()
                
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
                if hardware.update_keyboard_mode(pot_values, button_states):
                    # Mode teclat actiu - no processar altres modes
                    pass
                elif mode_manager and mode_manager.current_mode:
                    # Mode normal actiu
                    status = mode_manager.update(pot_values, button_states)
                    
                    # Sense pantalla - no cal actualitzar animacions
                
                # Comprobar si ha habido cambios en la configuración (desde la GUI u otra fuente)
                if current_time - last_config_check_time > config_check_interval:
                    try:
                        # Comprovar si existeix fitxer de senyal de recàrrega
                        signal_file = '.config_reload'
                        config_changed = False
                        
                        # SUPORT SIMULADOR: Comprovar flag config_reload_requested
                        if _sim_shared_state is not None and _sim_shared_state.config_reload_requested:
                            print(f"🎮 Simulador: Recàrrega de configuració sol·licitada")
                            config_changed = True
                            _sim_shared_state.config_reload_requested = False  # Reset flag
                        
                        try:
                            # Si el fitxer de senyal existeix, recarregar configuració
                            with open(signal_file, 'r') as f:
                                timestamp = f.read().strip()
                                print(f"📡 Senyal de recàrrega detectada (timestamp: {timestamp})")
                                config_changed = True
                                
                            # Eliminar el fitxer de senyal després de processar-lo
                            try:
                                import os
                                os.remove(signal_file)
                            except OSError:
                                pass
                        except OSError:
                            # El fitxer no existeix, comprovar hash normal
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
                
                # Control de velocitat del bucle adaptativo
                elapsed = time.monotonic() - current_time
                target_cycle_time = 0.02  # 20ms (50Hz) para mejor estabilidad
                if elapsed < target_cycle_time:
                    time.sleep(target_cycle_time - elapsed)
                    
            except MemoryError:
                if gc:
                    gc.collect()
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
    except MemoryError:
        print("\nError crític: Memòria insuficient. Reiniciant...")
        import supervisor
        supervisor.reload()  # Reiniciar el dispositiu
    except Exception as e:
        print(f"\nError crític: {e}")
        try:
            import sys
            sys.print_exception(e)  # Més detall en CircuitPython
        except ImportError:
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
        print(f"Error fatal: {_e}")
    # Reiniciar sempre (plug-and-play)
    try:
        import supervisor as _sv
        _sv.reload()
    except Exception:
        pass
