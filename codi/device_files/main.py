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

# Importar només el gestor de modes
from modes.mode_manager import ModeManager
from modes.mode_keyboard import KeyboardMode

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
        
        # No hi ha pantalla en aquest dispositiu
        self.has_display = False
        self.display_manager = None
        
        # Variables per al mode teclat
        self.keyboard_mode_active = False  # S'activarà al main()
        self.keyboard_mode = None
        self.keyboard_octave = 4
        self.keyboard_toggle_blocked_until = 0.0  # Bloqueig temporal per evitar toggle múltiple
    
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
            print(f"[DEBUG] Tecla 13 PREMUDA")
        elif (not button_states[12]) and self.last_button_states[12]:
            # Alliberat: comprovar durada
            pressed_time = self.button_press_times[12] or 0.0
            duration = time.monotonic() - pressed_time if pressed_time else 0.0
            print(f"[DEBUG] Tecla 13 alliberada - Durada: {duration:.2f}s | Umbral: {self.long_press_threshold}s")
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
                    print(f"[DEBUG] Toggle bloquejat per {self.keyboard_toggle_blocked_until - current_time:.2f}s més")
                    return None
                
                print(f"[DEBUG] Toggle capa - keyboard_mode_active actual: {self.keyboard_mode_active}")
                if not self.keyboard_mode_active:
                    # Tornar a mode teclat
                    print("[DEBUG] Activant mode teclat")
                    self.keyboard_mode_active = True
                    # Bloquejar toggle per 0.5 segons
                    self.keyboard_toggle_blocked_until = time.monotonic() + 0.5
                    if not self.keyboard_mode:
                        self.keyboard_mode = KeyboardMode(
                            self.midi_out, 
                            {'octave': self.keyboard_octave},
                            config_manager=self.config_manager
                        )
                        self.keyboard_mode.setup()
                    print(f"🎹 Mode Teclat activat | Octava: {self.keyboard_octave}")
                else:
                    # Canviar a capa de modes
                    print("[DEBUG] Canviant a capa de modes...")
                    self.keyboard_mode_active = False
                    # Bloquejar toggle per 0.5 segons
                    self.keyboard_toggle_blocked_until = time.monotonic() + 0.5
                    if self.keyboard_mode:
                        try:
                            self.keyboard_mode.cleanup()
                        except Exception as e:
                            print(f"[DEBUG] Error en cleanup: {e}")
                    # Netejar completament el mode actual SENSE afectar efectes temporals
                    if self.mode_manager:
                        # Cridar cleanup del mode si existeix
                        if self.mode_manager.current_mode:
                            try:
                                if hasattr(self.mode_manager.current_mode, 'cleanup'):
                                    self.mode_manager.current_mode.cleanup()
                            except Exception as e:
                                print(f"[DEBUG] Error en cleanup: {e}")
                        # Netejar referències
                        self.mode_manager.current_mode = None
                        self.mode_manager.current_mode_name = None
                        # IMPORTANT: NO netejar efectes temporals - es mantenen actius
                    print("Capa de modes activada")
                    # Enviar Control Changes MIDI a tots els canals per silenciar completament
                    # EXCEPTÉ: NO enviar CC que podrien desactivar efectes temporals
                    for ch in range(16):
                        self.midi_out.send(ControlChange(120, 0, channel=ch))  # All Sound Off
                        self.midi_out.send(ControlChange(123, 0, channel=ch))  # All Notes Off
                        # NO enviar Sustain OFF si hi ha efectes actius
                        # self.midi_out.send(ControlChange(64, 0, channel=ch))   # Sustain OFF
        
        # Botó 14 (index 13) - Baixar octava
        if button_states[13] and not self.last_button_states[13]:
            if self.keyboard_mode_active and self.keyboard_mode:
                self.keyboard_mode.change_octave(-1)
                self.keyboard_octave = self.keyboard_mode.octave
        
        # Botó 15 (index 14) - Pujar octava
        if button_states[14] and not self.last_button_states[14]:
            if self.keyboard_mode_active and self.keyboard_mode:
                self.keyboard_mode.change_octave(1)
                self.keyboard_octave = self.keyboard_mode.octave
        
        # Botó 16 (index 15) - EMERGENCY STOP + NETEJA DE MEMÒRIA
        if button_states[15] and not self.last_button_states[15]:
            print("ATURA!")
            try:
                # 1. PRIORITAT MÀXIMA: Aturar TOT el so immediatament
                if self.mode_manager:
                    self.mode_manager.stop_all_sound()
                
                # 2. Netejar mode teclat
                if self.keyboard_mode:
                    try:
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
                # Verificar que el mode assignat existeixi i no sigui un mode deshabilitat
                if assigned_mode in mode_names and assigned_mode not in disabled_modes:
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
                    self.keyboard_mode = KeyboardMode(
                        self.midi_out,
                        {'octave': self.keyboard_octave},
                        config_manager=self.config_manager
                    )
                    self.keyboard_mode.setup()
                    print(f"🎹 Mode Teclat activat | Octava: {self.keyboard_octave}")
                    
                    # IMPORTANT: Cridar update() immediatament per sincronitzar potenciòmetres
                    # Això assegura que els CC MIDI s'apliquen al mateix cicle que setup()
                    keyboard_buttons = button_states[:12]
                    self.keyboard_mode.update(pot_values, keyboard_buttons)
                    return True
                except Exception as e:
                    print(f"❌ Error creant Mode Teclat: {e}")
                    self.keyboard_mode_active = False
                    return False
            
            # Passar només els botons 1-12 al mode teclat
            keyboard_buttons = button_states[:12]
            self.keyboard_mode.update(pot_values, keyboard_buttons)
            return True
        return False


def main():
    """Funció principal de TECLA"""
    # Banner simple
    print("\nT E C L A\n")
    
    # Habilitar el recollidor de brossa si està disponible
    try:
        import gc
        gc.enable()
        last_gc_time = time.monotonic()
    except ImportError:
        gc = None
    
    # Inicialitzar maquinari
    hardware = TeclaHardware()

    
    # Inicialitzar sortida MIDI
    try:
        midi_out = MIDI(midi_out=usb_midi.ports[1])
    except Exception:
        print("Error: No s'ha pogut inicialitzar MIDI")
        return
    
    # Assignar sortida MIDI al maquinari i inicialitzar el gestor de modes i el gestor de configuració
    from core.config_manager import ConfigManager
    config_manager = ConfigManager()
    hardware.midi_out = midi_out
    mode_manager = ModeManager(midi_out)
    hardware.mode_manager = mode_manager
    mode_names = mode_manager.get_available_modes()
    
    # Mostrar modes disponibles (sense numeració)
    print("Modes disponibles:")
    for mode in mode_names:
        print(f"  {mode}")
    
    # Mostrar capa actual
    try:
        current_bank = config_manager.get_current_bank()
        bank_name = current_bank.get('name', 'Defecte')
        print(f"\nCapa actual: {bank_name}\n")
    except Exception:
        pass
    
    # Variables per a gestió de rendiment
    cycle_count = 0
    last_status_time = time.monotonic()
    status_interval = 60  # segons entre informes d'estat
    
    # Variable para detectar cambios en la configuración
    last_config_check_time = time.monotonic()
    config_check_interval = 0.1  # Comprobar cambios cada 0.1 segundos (gairebé instantani)
    last_config_hash = config_manager.get_config_hash()
    
    # Activar el flag perquè es creï el mode teclat al primer cicle
    hardware.keyboard_mode_active = True
    
    
    # Bucle principal
    
    try:
        while True:
            current_time = time.monotonic()
            
            try:
                # Llegir botons i potenciòmetres
                button_states = hardware.read_buttons()
                pot_values = hardware.read_pots()
                
                # Comprovar canvis de mode (inclou gestió del botó teclat)
                new_mode = hardware.check_mode_change(mode_names, button_states)
                if new_mode and new_mode != mode_manager.current_mode_name:
                    mode_manager.set_mode(new_mode)  # El propi mode_manager ja imprimeix el nom
                    
                    # Nou mode configurat (sense pantalla)
                
                # Actualitzar el mode teclat si està actiu
                if hardware.update_keyboard_mode(pot_values, button_states):
                    # Mode teclat actiu - no processar altres modes
                    pass
                elif mode_manager.current_mode:
                    # Mode normal actiu
                    status = mode_manager.update(pot_values, button_states)
                    
                    # Sense pantalla - no cal actualitzar animacions
                
                # Incrementar contador de ciclo
                cycle_count += 1
                
                # Comprobar si ha habido cambios en la configuración (desde la GUI u otra fuente)
                if current_time - last_config_check_time > config_check_interval:
                    try:
                        # Comprovar si existeix fitxer de senyal de recàrrega
                        signal_file = '.config_reload'
                        config_changed = False
                        
                        # SUPORT SIMULADOR: Comprovar flag config_reload_requested
                        try:
                            from core.simulator_mocks import shared_state
                            if shared_state.config_reload_requested:
                                print(f"🎮 Simulador: Recàrrega de configuració sol·licitada")
                                config_changed = True
                                shared_state.config_reload_requested = False  # Reset flag
                        except (ImportError, AttributeError):
                            # No estem en mode simulador, continuar normalment
                            pass
                        
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
                            # La configuración ha cambiado: recargar mappings y reiniciar el modo actual
                            print("🔄 Aplicant canvis de configuració...")
                            
                            # Recarregar configuració des del fitxer
                            config_manager.config = config_manager._load_config()
                            config_manager.current_bank_index = config_manager.config.get('current_bank', 0)
                            
                            try:
                                mode_manager.load_config()
                                print("✅ Configuració de botons/efectes aplicada")
                            except Exception as e:
                                print(f"Error recargando configuración: {e}")
                            if mode_manager.reload_current_mode():
                                print("✅ Mode reiniciat correctament")
                            
                            # CRÍTIC: Actualitzar mode_names amb els nous modes afegits
                            # Sense això, els modes nous no es reconeixerien fins al reinici
                            try:
                                mode_names = mode_manager.get_available_modes()
                                print(f"✅ Llista de modes actualitzada: {len(mode_names)} modes")
                            except Exception as e:
                                print(f"Error actualitzant mode_names: {e}")
                            
                            # Actualitzar hash després de recarregar
                            last_config_hash = config_manager.get_config_hash()
                            
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
                    
                    # Forzar sincronización periódica del sistema de archivos
                    # para asegurar que los cambios se escriban en el dispositivo
                    if cycle_count % 3000 == 0:  # Cada ~5 minutos aproximadamente
                        try:
                            import os
                            os.sync()  # Sincronizar cambios al sistema de archivos
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
                
            # Forzar sincronización final para asegurar que ningún cambio se pierda
            if 'config_manager' in locals() and config_manager is not None:
                config_manager.save_config()
                
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
    main()
