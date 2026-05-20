"""
TECLA - Mode Teclat
Mode especial que converteix els botons 1-12 en un teclat chromàtic
Activat pel botó 13, amb controls de potenciòmetres per personalitzar
"""

import time
import random
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

# OPTIMITZACIÓ DE MEMÒRIA: Funció per obtenir escales sota demanda
def get_scale_mode(scale_id):
    """Retorna la configuració d'una escala per ID (lazy loading)"""
    scales = {
        0: {'name': 'Jònic (Major)', 'intervals': [0, 2, 4, 5, 7, 9, 11]},
        1: {'name': 'Dòric', 'intervals': [0, 2, 3, 5, 7, 9, 10]},
        2: {'name': 'Frigi', 'intervals': [0, 1, 3, 5, 7, 8, 10]},
        3: {'name': 'Lidi', 'intervals': [0, 2, 4, 6, 7, 9, 11]},
        4: {'name': 'Mixolidi', 'intervals': [0, 2, 4, 5, 7, 9, 10]},
        5: {'name': 'Eòlic (Minor)', 'intervals': [0, 2, 3, 5, 7, 8, 10]},
        6: {'name': 'Locri', 'intervals': [0, 1, 3, 5, 6, 8, 10]},
        7: {'name': 'Pentatònica Major', 'intervals': [0, 2, 4, 7, 9]},
        8: {'name': 'Pentatònica Menor', 'intervals': [0, 3, 5, 7, 10]},
        9: {'name': 'Japonesa (Hirajōshi)', 'intervals': [0, 1, 4, 6, 7]},
        10: {'name': 'Egípcia', 'intervals': [0, 2, 5, 7, 9]},
        11: {'name': 'Aràbiga/Bizantina', 'intervals': [0, 1, 4, 5, 7, 8, 11]},
        12: {'name': 'Hongaresa Menor', 'intervals': [0, 2, 3, 6, 7, 9, 10]},
        13: {'name': 'Lídia Dominant', 'intervals': [0, 2, 4, 6, 7, 9, 10]},
        14: {'name': 'Alterada (Superlòcria)', 'intervals': [0, 1, 3, 4, 6, 8, 10]},
        15: {'name': 'Menor Melòdica', 'intervals': [0, 2, 3, 5, 7, 9, 11]},
        16: {'name': 'Raga Bhairav', 'intervals': [0, 1, 4, 5, 7, 8, 11]},
        17: {'name': 'Raga Todi', 'intervals': [0, 1, 3, 6, 7, 8, 11]},
        18: {'name': 'Flamenca (Frígia Dominant)', 'intervals': [0, 1, 4, 5, 7, 8, 10]},
        19: {'name': 'Catalana', 'intervals': [0, 1, 4, 5, 7, 9, 11]},
        20: {'name': 'Frígia', 'intervals': [0, 1, 3, 5, 7, 8, 10]},
        21: {'name': 'Balcànica', 'intervals': [0, 1, 4, 5, 7, 8, 11]},
        22: {'name': 'Tons Sencers (Debussy)', 'intervals': [0, 2, 4, 6, 8, 10]},
        23: {'name': 'Harmònica Major', 'intervals': [0, 2, 4, 5, 7, 8, 11]}
    }
    return scales.get(scale_id, {'name': 'Jònic (Major)', 'intervals': [0, 2, 4, 5, 7, 9, 11]})

# Cercle de quintes (tonalitats)
KEY_CIRCLE = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'Ab', 'Eb', 'Bb', 'F']
KEY_OFFSETS = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]  # Offset en semitons

# OPTIMITZACIÓ DE MEMÒRIA: Funció per obtenir modes d'arpegiador sota demanda
def get_arp_mode(mode_id):
    """Retorna la configuració d'un mode d'arpegiador per ID (lazy loading)"""
    modes = {
        0: {'name': 'Amunt', 'direction': 'up'},
        1: {'name': 'Avall', 'direction': 'down'},
        2: {'name': 'Ping-Pong', 'direction': 'pingpong'},
        3: {'name': 'Aleatori', 'direction': 'random'},
        4: {'name': 'Ordre', 'direction': 'order'},
        5: {'name': 'Alberti', 'direction': 'alberti'},
        6: {'name': 'Alberti Alt', 'direction': 'alberti_alt'},
        7: {'name': 'Vals', 'direction': 'waltz'},
        8: {'name': 'Broken', 'direction': 'broken'},
        9: {'name': 'Trèmolo', 'direction': 'tremolo'},
        10: {'name': 'Zig-Zag', 'direction': 'zigzag'},
        11: {'name': 'Block', 'direction': 'block'},
        12: {'name': 'Rolled', 'direction': 'rolled'},
        13: {'name': 'Octaves', 'direction': 'octaves'},
        14: {'name': 'Contrari', 'direction': 'contrary'},
        15: {'name': 'Spread', 'direction': 'spread'}
    }
    return modes.get(mode_id, {'name': 'Ping-Pong', 'direction': 'pingpong'})

# Notes musicals (mapatge nom → offset MIDI)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NOTE_OFFSETS = {note: i for i, note in enumerate(NOTE_NAMES)}

# OPTIMITZACIÓ DE MEMÒRIA: Funció per obtenir tipus d'acords sota demanda
def get_chord_intervals(chord_type='Major'):
    """Retorna els intervals d'un tipus d'acord (lazy loading)"""
    chords = {
        'Major': [0, 4, 7],
        'm': [0, 3, 7],
        '7': [0, 4, 7, 10],
        'maj7': [0, 4, 7, 11],
        'm7': [0, 3, 7, 10],
        'dim': [0, 3, 6],
        'aug': [0, 4, 8],
        'sus4': [0, 5, 7],
        'sus2': [0, 2, 7],
        'm7b5': [0, 3, 6, 10],
        'add9': [0, 4, 7, 14],
        '6': [0, 4, 7, 9]
    }
    return chords.get(chord_type, [0, 4, 7])

class KeyboardMode:
    """Mode teclat que converteix botons 1-12 en notes MIDI"""
    
    def __init__(self, midi_out, config=None, config_manager=None):
        self.midi = midi_out
        self.config = config or {}
        self.config_manager = config_manager
        self.name = "Teclat"
        
        # Estat del mode teclat
        self.active_notes = set()
        self.octave = self.config.get('octave', 4)  # Octava per defecte
        self.last_button_states = [False] * 12
        # Mapatge de notes per botó per NoteOff ràpid i precís
        self.button_notes = {i: set() for i in range(12)}
        # Mode debug (evitar prints per latència)
        self.debug = False
        
        # Obtenir escales (incloent progressions com IDs >= 1000) i modes d'arpegiador
        if self.config_manager:
            self.available_scales = self.config_manager.get_keyboard_scales()
            self.available_arp_modes = self.config_manager.get_arpeggiator_modes()
            
            # Obtenir funcions configurades dels potenciòmetres (MODE TECLAT)
            pot_functions = self.config_manager.get_potentiometer_functions()
            self.pot_x_function = pot_functions.get('pot_x', 'Velocity')
            self.pot_y_function = pot_functions.get('pot_y', 'Modulation (CC1)')
            self.pot_z_function = pot_functions.get('pot_z', 'Sustain (CC64)')
            
            # Obtenir funcions configurades dels potenciòmetres (MODE ARPEGIADOR)
            arp_pot_functions = self.config_manager.get_arp_potentiometer_functions()
            self.arp_pot_x_function = arp_pot_functions.get('arp_pot_x', 'Arp Speed (BPM)')
            self.arp_pot_y_function = arp_pot_functions.get('arp_pot_y', 'Arp Pattern Selector')
            self.arp_pot_z_function = arp_pot_functions.get('arp_pot_z', 'Pitch Bend')
            
            print(f"🎵 Escales/Progressions disponibles: {self.available_scales}")
            print(f"🎛️ Potenciòmetres Teclat: X={self.pot_x_function}, Y={self.pot_y_function}, Z={self.pot_z_function}")
            print(f"🎛️ Potenciòmetres Arpegiador: X={self.arp_pot_x_function}, Y={self.arp_pot_y_function}, Z={self.arp_pot_z_function}")
        else:
            self.available_scales = [0, 1, 4, 5, 7, 8]  # Per defecte
            self.available_arp_modes = [0, 1, 2, 3, 4]  # Tots els modes per defecte
            # Funcions per defecte dels potenciòmetres (MODE TECLAT)
            self.pot_x_function = 'Velocity'
            self.pot_y_function = 'Modulation (CC1)'
            self.pot_z_function = 'Sustain (CC64)'
            # Funcions per defecte dels potenciòmetres (MODE ARPEGIADOR)
            self.arp_pot_x_function = 'Arp Speed (BPM)'
            self.arp_pot_y_function = 'Arp Pattern Selector'
            self.arp_pot_z_function = 'Pitch Bend'
        
        # Configuració musical
        self.scale_mode_index = 0  # Índex dins available_scales
        self.key_index = 0  # Índex al cercle de quintes (0=C)
        self.chord_mode_active = False  # Mode acords activat?
        self.arp_mode_active = False  # Mode arpeggiador activat?
        
        # Paràmetres controlables per potenciòmetres (tracking de valors)
        self.velocity = 100  # Velocitat/intensitat (0-127)
        self.cc_values = {  # Tracking dels valors dels CC MIDI
            1: 0,    # Modulation
            10: 64,  # Pan (centrat)
            11: 64,  # Expression (valor neutral - el potenciòmetre determinarà el valor real)
            64: 0,   # Sustain (OFF)
            72: 64,  # Release
            74: 64,  # Brightness
            91: 0,   # Reverb
            93: 0    # Chorus
        }
        
        # Arpeggiador
        self.arp_index = 0
        self.arp_direction = 1  # 1=amunt, -1=avall
        self.last_arp_time = 0
        self.arp_speed = 0.15  # segons entre notes (fix)
        self.arp_notes = []  # Notes a arpeggiar
        self.arp_mode_index = 2  # Mode per defecte: Ping-Pong
        self.arp_button_order = []  # Ordre de pulsació dels botons
        
        # Detecció de doble click per desactivar arpegiador
        self.last_arp_button_press = 0
        self.double_click_threshold = 0.5  # segons
        
        # Gate (parpelleig) - Efecte de note repeat
        self.gate_active = False
        self.gate_speed = 0.1  # Velocitat del parpelleig (segons)
        self.gate_last_toggle = 0
        self.gate_state = True  # True = alt, False = baix per considerar doble click
        
        # Flag per primer update (sincronitzar potenciòmetres)
        self.first_update = True
        print(f"🎹 Mode Teclat activat | Octava: {self.octave} | Tonalitat: {KEY_CIRCLE[self.key_index]}")
        
        # Forçar garbage collection després d'inicialitzar
        try:
            import gc
            gc.collect()
        except:
            pass
    
    @property
    def scale_mode(self):
        """Retorna l'ID real de l'escala actual des de available_scales"""
        if len(self.available_scales) > 0:
            return self.available_scales[self.scale_mode_index]
        return 0  # Fallback a Jònic
        
    def setup(self):
        """Configuració inicial del mode"""
        self.stop_all_notes()
        self.active_notes.clear()
        
        # Recarregar configuracions (incloent funcions dels potenciòmetres)
        if self.config_manager:
            self.available_scales = self.config_manager.get_keyboard_scales()
            self.available_arp_modes = self.config_manager.get_arpeggiator_modes()
            
            # Recarregar funcions dels potenciòmetres (MODE TECLAT)
            pot_functions = self.config_manager.get_potentiometer_functions()
            self.pot_x_function = pot_functions.get('pot_x', 'Velocity/Arp Speed (dual)')
            self.pot_y_function = pot_functions.get('pot_y', 'Modulation (CC1)')
            self.pot_z_function = pot_functions.get('pot_z', 'Sustain (CC64)')
            
            # Recarregar funcions dels potenciòmetres (MODE ARPEGIADOR)
            arp_pot_functions = self.config_manager.get_arp_potentiometer_functions()
            self.arp_pot_x_function = arp_pot_functions.get('arp_pot_x', 'Arp Speed (BPM)')
            self.arp_pot_y_function = arp_pot_functions.get('arp_pot_y', 'Arp Pattern Selector')
            self.arp_pot_z_function = arp_pot_functions.get('arp_pot_z', 'Gate Length')
            
            print(f"🎛️ Potenciòmetres Teclat: X={self.pot_x_function}, Y={self.pot_y_function}, Z={self.pot_z_function}")
            print(f"🎛️ Potenciòmetres Arpegiador: X={self.arp_pot_x_function}, Y={self.arp_pot_y_function}, Z={self.arp_pot_z_function}")
        for i in range(12):
            self.button_notes[i].clear()
        
        # IMPORTANT: Inicialitzar tots els CC MIDI a valors per defecte
        # Això assegura que no hi ha efectes residuals del sintetitzador
        try:
            for ch in range(16):
                for cc_num, default_value in self.cc_values.items():
                    self.midi.send(ControlChange(cc_num, default_value, channel=ch))
        except Exception:
            pass
        
    def cleanup(self):
        """Neteja en sortir del mode"""
        self.stop_all_notes()
        self.active_notes.clear()
        for i in range(12):
            self.button_notes[i].clear()
        
        # Netejar llistes per alliberar memòria
        self.arp_notes = []
        self.arp_button_order = []
        
        # Desactivar tots els CC al sortir
        try:
            for ch in range(16):
                self.midi.send(ControlChange(1, 0, channel=ch))   # Modulation OFF
                self.midi.send(ControlChange(64, 0, channel=ch))  # Sustain OFF
                self.midi.send(ControlChange(91, 0, channel=ch))  # Reverb OFF
                self.midi.send(ControlChange(93, 0, channel=ch))  # Chorus OFF
        except Exception:
            pass
        
        # Silenciar i deinicialitzar PWM completament
        try:
            import main
            if hasattr(main, 'pwm') and main.pwm is not None:
                main.pwm.duty_cycle = 0  # Silenciar primer
                main.pwm.deinit()  # Deinicialitzar el pin
                main.pwm = None  # Eliminar referència
        except Exception:
            pass  # No interrumpir per errors en el PWM
        
        print("🎹 Mode Teclat desactivat")
        
    def stop_all_notes(self):
        """Para totes les notes actives i neteja tot el tracking - PANIC BUTTON"""
        # PANIC COMPLET: Aturar TOTES les notes immediatament
        try:
            for ch in range(16):
                # 1. All Sound Off (CC 120) - Atura tot el so immediatament
                self.midi.send(ControlChange(120, 0, channel=ch))
                # 2. All Notes Off (CC 123) - Para totes les notes
                self.midi.send(ControlChange(123, 0, channel=ch))
                # 3. Sustain OFF per evitar notes enganxades
                self.midi.send(ControlChange(64, 0, channel=ch))
                # 4. Reset pitch bend al centre
                try:
                    from adafruit_midi.pitch_bend import PitchBend
                    self.midi.send(PitchBend(0, channel=ch))
                except:
                    pass
            self.sustain_level = 0
        except Exception as e:
            print(f"Error en panic MIDI: {e}")
        
        # Enviar NoteOff per totes les notes actives (redundància per seguretat)
        for note in self.active_notes.copy():
            try:
                for ch in range(16):
                    self.midi.send(NoteOff(note, 0, channel=ch))
            except Exception:
                pass
        
        # Silenciar PWM
        try:
            import main
            if hasattr(main, 'pwm'):
                main.pwm.duty_cycle = 0
        except Exception:
            pass
        
        # Netejar tots els trackings
        self.active_notes.clear()
        for i in range(12):
            self.button_notes[i].clear()
            
    def update(self, pot_values, button_states):
        """Actualització principal del mode teclat"""
        # Al primer update, forçar aplicació de tots els potenciòmetres
        force_update = False
        if self.first_update and len(pot_values) >= 3:
            self.first_update = False
            force_update = True
            print("🎛️ Sincronitzant potenciòmetres...")
        
        # Actualitzar paràmetres des dels potenciòmetres
        self._update_parameters(pot_values, force_update=force_update)
        
        # Processar gate (parpelleig) si està actiu
        self._process_gate()
        
        # Processar els botons 1-12 com a notes del teclat
        self._process_keyboard_buttons(button_states[:12])
            
    def _update_parameters(self, pot_values, force_update=False):
        """Actualitza paràmetres basats en els potenciòmetres amb funcions configurables"""
        if len(pot_values) < 3:
            return
        
        # Decidir quin conjunt de funcions aplicar segons si l'arpegiador està actiu
        if self.arp_mode_active:
            # Mode Arpegiador: aplicar funcions específiques de l'arpegiador
            self._apply_arp_pot_function('arp_pot_x', pot_values[1], force_update=force_update)
            self._apply_arp_pot_function('arp_pot_y', pot_values[0], force_update=force_update)
            self._apply_arp_pot_function('arp_pot_z', pot_values[2], force_update=force_update)
        else:
            # Mode Teclat Normal: aplicar funcions del mode teclat
            self._apply_pot_function('pot_x', pot_values[1], force_update=force_update)
            self._apply_pot_function('pot_y', pot_values[0], force_update=force_update)
            self._apply_pot_function('pot_z', pot_values[2], force_update=force_update)
    
    def _apply_pot_function(self, pot_name, pot_value, force_update=False):
        """Aplica la funció configurada per un potenciòmetre del mode teclat"""
        # Obtenir la funció configurada
        if pot_name == 'pot_x':
            function = self.pot_x_function
        elif pot_name == 'pot_y':
            function = self.pot_y_function
        elif pot_name == 'pot_z':
            function = self.pot_z_function
        else:
            return
        
        # Threshold: 0 si es força l'actualització, 2 si no
        threshold = 0 if force_update else 2
        
        # Aplicar funció segons configuració
        if function == 'Velocity':
            # Velocity: Modifica la intensitat/volum de les notes
            # Rang: 20-127 per evitar notes massa baixes
            self.velocity = max(20, min(127, pot_value))
                
        elif function == 'Modulation (CC1)':
            # Modulació estàndard
            self._send_cc_if_changed(1, pot_value, threshold=threshold)
            
        elif function == 'Sustain (CC64)':
            # Sustain amb actualització constant per fade suau (sense threshold)
            # Això permet un control gradual del sustain sense talls bruscs
            if force_update or 64 not in self.cc_values or self.cc_values[64] != pot_value:
                self._send_cc(64, pot_value)
                
        elif function == 'Pitch Bend':
            # Pitch Bend - centrat al valor del potenciòmetre
            # Rang suau similar als efectes temporals
            self._send_pitch_bend_keyboard(pot_value)
            
        elif function == 'Gate (CC11)':
            # Gate: Efecte de parpelleig (note repeat)
            # Valor del potenciòmetre controla la velocitat del parpelleig
            # 0 = lent, 127 = molt ràpid
            if pot_value > 10:  # Threshold per activar
                self.gate_active = True
                # Mapear 10-127 a velocitat: 0.5s (lent) a 0.02s (ràpid)
                self.gate_speed = 0.5 - ((pot_value - 10) / 117.0) * 0.48
            else:
                self.gate_active = False
                # Quan està desactivat, mantenir expressió al màxim
                self._send_cc(11, 127)
    
    def _process_gate(self):
        """Processa l'efecte de gate (parpelleig) si està actiu"""
        if not self.gate_active:
            return
        
        import time
        current_time = time.monotonic()
        
        # Comprovar si és hora d'alternar
        if current_time - self.gate_last_toggle >= self.gate_speed:
            self.gate_state = not self.gate_state
            self.gate_last_toggle = current_time
            
            # Alternar entre expressió alta i baixa
            # Alt = 127 (so complet), Baix = 0 (silenci)
            gate_value = 127 if self.gate_state else 0
            
            # Enviar CC11 (Expression) per crear l'efecte de parpelleig
            self._send_cc(11, gate_value)
    
    def _apply_arp_pot_function(self, pot_name, pot_value, force_update=False):
        """Aplica la funció configurada per un potenciòmetre en mode arpegiador"""
        # Obtenir la funció configurada
        if pot_name == 'arp_pot_x':
            function = self.arp_pot_x_function
        elif pot_name == 'arp_pot_y':
            function = self.arp_pot_y_function
        elif pot_name == 'arp_pot_z':
            function = self.arp_pot_z_function
        else:
            return
        
        # Threshold: 0 si es força l'actualització, 2 si no
        threshold = 0 if force_update else 2
        
        # Aplicar funció segons configuració
        if function == 'Arp Speed (BPM)':
            # NOMÉS controlar velocitat BPM, NO tocar velocity (volum)
            # Convertir valor del potenciòmetre a velocitat d'arpegiador
            # Range: 0.01 segons (molt ràpid) a 0.5 segons (lent)
            speed_value = max(0, min(127, pot_value))
            self.arp_speed = 0.5 - (speed_value / 127.0) * 0.49
            
        elif function == 'Arp Pattern Selector':
            # Selector de patró d'arpegiador
            # Mapear valor del potenciòmetre (0-127) al nombre de patrons disponibles
            if len(self.available_arp_modes) > 0:
                # Calcular índex dins dels modes disponibles
                pattern_index = int((pot_value / 127.0) * len(self.available_arp_modes))
                pattern_index = min(pattern_index, len(self.available_arp_modes) - 1)
                
                # Obtenir el mode d'arpegiador corresponent
                new_arp_mode = self.available_arp_modes[pattern_index]
                
                # Només canviar si és diferent (evitar spam de prints)
                if new_arp_mode != self.arp_mode_index:
                    self.arp_mode_index = new_arp_mode
                    self.arp_index = 0
                    self.arp_direction = 1
                    arp_info = get_arp_mode(self.arp_mode_index)
                    arp_name = arp_info['name']
                    print(f"🎶 Patró Arpeggiador: {arp_name}")
            
        elif function == 'Modulation (CC1)':
            # Modulació estàndard
            self._send_cc_if_changed(1, pot_value, threshold=threshold)
            
        elif function == 'Pitch Bend':
            # Pitch Bend - convertir valor 0-127 a -8192 a +8191 (14 bits)
            # Centrar a 64 (8192): 0=màxim negatiu, 64=neutre, 127=màxim positiu
            self._send_pitch_bend(pot_value)
    
    def _send_pitch_bend_keyboard(self, pot_value):
        """Envia Pitch Bend MIDI per al mode teclat (rang suau similar a efectes temporals)"""
        try:
            from adafruit_midi.pitch_bend import PitchBend
            
            # Rang suau similar als efectes temporals: -2000 a +2000 aprox.
            bend_value = int((pot_value - 64) * 32)  # Rang curt i suau
            midi_value = max(0, min(16383, bend_value + 8192))
            
            # Enviar a tots els canals
            for ch in range(16):
                self.midi.send(PitchBend(midi_value, channel=ch))
        except Exception as e:
            print(f"Error enviant pitch bend (mode teclat): {e}")
    
    def _send_pitch_bend(self, pot_value):
        """Envia Pitch Bend MIDI centrat al valor del potenciòmetre (mode arpegiador - rang complet)"""
        from adafruit_midi.pitch_bend import PitchBend
        
        # Convertir 0-127 a -8192 a +8191 (rang de pitch bend MIDI)
        # 64 = neutre (0), 0 = -8192, 127 = +8191
        if pot_value < 64:
            bend_value = int((pot_value / 64.0) * 8192 - 8192)
        else:
            bend_value = int(((pot_value - 64) / 63.0) * 8191)
        midi_value = max(0, min(16383, bend_value + 8192))
        
        # Enviar a tots els canals
        try:
            for ch in range(16):
                self.midi.send(PitchBend(midi_value, channel=ch))
        except Exception as e:
            print(f"Error enviant pitch bend: {e}")
    
    def _send_cc_if_changed(self, cc_num, new_value, threshold=2):
        """Envia un CC MIDI només si ha canviat significativament"""
        if cc_num not in self.cc_values or abs(new_value - self.cc_values[cc_num]) >= threshold:
            self._send_cc(cc_num, new_value)
    
    def _send_cc(self, cc_num, value):
        """Envia un CC MIDI a tots els canals i actualitza tracking"""
        self.cc_values[cc_num] = value
        
        # Debug: Mostrar què s'està enviant (només quan canvia significativament)
        if not hasattr(self, '_last_debug_value'):
            self._last_debug_value = {}
        
        if cc_num not in self._last_debug_value or abs(value - self._last_debug_value[cc_num]) > 10:
            cc_names = {1: "Modulation", 10: "Pan", 11: "Expression", 64: "Sustain", 
                       72: "Release", 74: "Brightness", 91: "Reverb", 93: "Chorus"}
            cc_name = cc_names.get(cc_num, f"CC{cc_num}")
            print(f"🎛️ {cc_name} (CC{cc_num}): {value}")
            self._last_debug_value[cc_num] = value
        
        try:
            for ch in range(16):
                self.midi.send(ControlChange(cc_num, value, channel=ch))
        except Exception:
            pass
            
    def _process_keyboard_buttons(self, button_states):
        """Processa els botons: 1-8 notes, 9-12 funcions"""
        current_time = time.monotonic()
        
        # Processar botons de funcions 9-12 (índexs 8-11)
        for btn_idx in range(8, 12):
            if btn_idx < len(button_states):
                current_pressed = button_states[btn_idx]
                was_pressed = btn_idx < len(self.last_button_states) and self.last_button_states[btn_idx]
                
                if current_pressed and not was_pressed:
                    # Botó acabat de prémer
                    # print(f"DEBUG: Botó {btn_idx+1} premut")  # Descomentar per debug
                    
                    if btn_idx == 8:  # Botó 9: Ciclar escales, progressions i escales personalitzades
                        # IMPORTANT: Aturar totes les notes abans de canviar
                        self.stop_all_notes()
                        
                        # Ciclar entre escales, progressions i escales personalitzades disponibles
                        if len(self.available_scales) > 0:
                            self.scale_mode_index = (self.scale_mode_index + 1) % len(self.available_scales)
                            actual_scale_id = self.available_scales[self.scale_mode_index]
                            
                            # Detectar tipus: escala personalitzada (>= 2000), progressió (1000-1999) o escala normal (< 1000)
                            if actual_scale_id >= 2000:
                                # És una escala personalitzada
                                custom_scale = self.config_manager.get_custom_scale_by_scale_id(actual_scale_id) if self.config_manager else None
                                if custom_scale:
                                    scale_name = custom_scale.get('name', 'Sense nom')
                                    print(f"🎼 Escala Personalitzada: {scale_name} ({self.scale_mode_index + 1}/{len(self.available_scales)})")
                                else:
                                    print(f"🎼 Escala Personalitzada #{actual_scale_id - 2000} ({self.scale_mode_index + 1}/{len(self.available_scales)})")
                            elif actual_scale_id >= 1000:
                                # És una progressió
                                progression = self.config_manager.get_progression_by_scale_id(actual_scale_id) if self.config_manager else None
                                if progression:
                                    prog_name = progression.get('name', 'Sense nom')
                                    print(f"♪ Progressió: {prog_name} ({self.scale_mode_index + 1}/{len(self.available_scales)})")
                                else:
                                    print(f"♪ Progressió #{actual_scale_id - 1000} ({self.scale_mode_index + 1}/{len(self.available_scales)})")
                            else:
                                # És una escala normal
                                scale_info = get_scale_mode(actual_scale_id)
                                scale_name = scale_info['name']
                                print(f"🎼 Escala: {scale_name} ({self.scale_mode_index + 1}/{len(self.available_scales)})")
                    
                    elif btn_idx == 9:  # Botó 10: Canviar tonalitat
                        # IMPORTANT: Aturar totes les notes abans de canviar de tonalitat
                        self.stop_all_notes()
                        self.key_index = (self.key_index + 1) % 12
                        key_name = KEY_CIRCLE[self.key_index]
                        print(f"🎵 Tonalitat: {key_name}")
                    
                    elif btn_idx == 10:  # Botó 11: Toggle mode acords
                        # IMPORTANT: Aturar totes les notes abans de canviar de mode
                        self.stop_all_notes()
                        self.chord_mode_active = not self.chord_mode_active
                        status = "ACTIVAT" if self.chord_mode_active else "DESACTIVAT"
                        print(f"🎹 Mode Acords: {status}")
                    
                    elif btn_idx == 11:  # Botó 12: Ciclar modes d'arpegiador / Doble click desactiva
                        # IMPORTANT: Aturar totes les notes abans de canviar de mode
                        self.stop_all_notes()
                        
                        # Detectar doble click
                        time_since_last_press = current_time - self.last_arp_button_press
                        is_double_click = time_since_last_press < self.double_click_threshold
                        self.last_arp_button_press = current_time
                        
                        if is_double_click and self.arp_mode_active:
                            # DOBLE CLICK: Desactivar arpeggiador completament
                            self.arp_mode_active = False
                            self.arp_notes = []
                            self.arp_button_order = []
                            print(f"🎶 Arpeggiador DESACTIVAT")
                        elif not self.arp_mode_active:
                            # Activar arpeggiador per primera vegada
                            self.arp_mode_active = True
                            self.arp_notes = []
                            self.arp_button_order = []
                            # Assegurar que el mode inicial està dins dels disponibles
                            if self.arp_mode_index not in self.available_arp_modes:
                                self.arp_mode_index = self.available_arp_modes[0] if self.available_arp_modes else 2
                            arp_info = get_arp_mode(self.arp_mode_index)
                            arp_name = arp_info['name']
                            print(f"🎶 Arpeggiador ACTIVAT | Mode: {arp_name}")
                        else:
                            # CLICK SIMPLE: Ciclar només entre modes disponibles per aquest banc
                            if len(self.available_arp_modes) > 0:
                                # Trobar índex actual dins available_arp_modes
                                try:
                                    current_idx = self.available_arp_modes.index(self.arp_mode_index)
                                    next_idx = (current_idx + 1) % len(self.available_arp_modes)
                                    self.arp_mode_index = self.available_arp_modes[next_idx]
                                except ValueError:
                                    # Si el mode actual no està disponible, agafar el primer
                                    self.arp_mode_index = self.available_arp_modes[0]
                                
                                arp_info = get_arp_mode(self.arp_mode_index)
                                arp_name = arp_info['name']
                                # Reset de variables d'arpegiador
                                self.arp_index = 0
                                self.arp_direction = 1
                                self.arp_button_order = []
                                print(f"🎶 Mode Arpeggiador: {arp_name}")
        
        # Processar botons de notes 1-8 (índexs 0-7)
        if self.arp_mode_active:
            # Mode arpeggiador: recollir notes premudes
            self._process_arpeggiator(button_states[:8], current_time)
        else:
            # Mode normal o acords
            for btn_idx in range(8):
                if btn_idx < len(button_states):
                    current_pressed = button_states[btn_idx]
                    was_pressed = btn_idx < len(self.last_button_states) and self.last_button_states[btn_idx]
                    
                    if current_pressed and not was_pressed:
                        # Botó acabat de prémer
                        if self.chord_mode_active:
                            self._generate_chord_for_button(btn_idx)
                        else:
                            self._generate_notes_for_button(btn_idx)
                    elif not current_pressed and was_pressed:
                        # Botó acabat d'alliberar
                        self._note_off_for_button(btn_idx)
        
        # Actualitzar estat anterior
        self.last_button_states = button_states[:12].copy()
        
    def _generate_notes_for_button(self, btn_idx):
        """Genera nota(es) per al botó segons el mode actiu (escales, progressions o escales personalitzades)"""
        # Obtenir ID d'escala/progressió/escala personalitzada actual
        if len(self.available_scales) == 0:
            return
        
        current_scale_id = self.available_scales[self.scale_mode_index]
        
        # Detectar tipus: escala personalitzada (>= 2000), progressió (1000-1999) o escala normal (< 1000)
        if current_scale_id >= 2000:
            # Mode escala personalitzada: tocar nota directament des de la configuració
            custom_scale = self.config_manager.get_custom_scale_by_scale_id(current_scale_id) if self.config_manager else None
            if custom_scale:
                self._generate_note_from_custom_scale(btn_idx, custom_scale)
            else:
                print(f"Error: Escala personalitzada {current_scale_id} no trobada")
        elif current_scale_id >= 1000:
            # Mode progressions: generar acord des de la progressió
            progression = self.config_manager.get_progression_by_scale_id(current_scale_id) if self.config_manager else None
            if progression:
                self._generate_chord_from_progression(btn_idx, progression)
            else:
                print(f"Error: Progressió {current_scale_id} no trobada")
        else:
            # Mode escales: generar nota individual
            # Calcular la nota base del botó en l'escala i tonalitat actual
            scale_info = get_scale_mode(current_scale_id)
            scale_intervals = scale_info['intervals']
            key_offset = KEY_OFFSETS[self.key_index]
            
            # El botó representa una posició dins l'escala (màxim 8 botons)
            scale_degree = btn_idx % len(scale_intervals)
            octave_offset = btn_idx // len(scale_intervals)
            
            # Nota = octava + tonalitat + grau d'escala
            base_note = (self.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
            base_note = max(0, min(127, base_note))
            
            # Tocar la nota amb la velocitat del potenciòmetre
            self._note_on(base_note, btn_idx)
    
    def _generate_chord_from_progression(self, btn_idx, progression):
        """Genera un acord des de la progressió personalitzada
        Args:
            btn_idx: Índex del botó (0-7)
            progression: Diccionari amb la progressió (id, name, chords)
        """
        if not progression:
            return
        
        # Primer, aturar notes anteriors d'aquest botó
        self._note_off_for_button(btn_idx)
        
        # Trobar l'acord configurat per aquest botó
        chords = progression.get('chords', [])
        chord_config = None
        for chord in chords:
            if chord.get('button') == btn_idx:
                chord_config = chord
                break
        
        if not chord_config:
            return
        
        # Extreure configuració de l'acord
        root_note_name = chord_config.get('root_note', 'C')
        chord_type = chord_config.get('chord_type', 'Major')
        octave = chord_config.get('octave', 4)
        
        # Calcular nota MIDI base
        root_offset = NOTE_OFFSETS.get(root_note_name, 0)
        base_note = octave * 12 + root_offset
        
        # Obtenir intervals de l'acord
        chord_intervals = get_chord_intervals(chord_type)
        
        # Generar totes les notes de l'acord
        for interval in chord_intervals:
            note = base_note + interval
            note = max(0, min(127, note))
            try:
                self.midi.send(NoteOn(note, self.velocity))
                self.active_notes.add(note)
                self.button_notes[btn_idx].add(note)
            except Exception as e:
                print(f"Error tocant acord: {e}")
    
    def _generate_note_from_custom_scale(self, btn_idx, custom_scale):
        """Genera una nota des de l'escala personalitzada
        Args:
            btn_idx: Índex del botó (0-7)
            custom_scale: Diccionari amb l'escala personalitzada (id, name, notes)
        """
        if not custom_scale:
            return
        
        # Primer, aturar notes anteriors d'aquest botó
        self._note_off_for_button(btn_idx)
        
        # Trobar la nota configurada per aquest botó
        notes = custom_scale.get('notes', [])
        note_config = None
        for note in notes:
            if note.get('button') == btn_idx:
                note_config = note
                break
        
        if not note_config:
            # Si no hi ha nota configurada per aquest botó, no tocar res
            return
        
        # Obtenir nota MIDI directament de la configuració
        midi_note = note_config.get('midi_note')
        
        if midi_note is None:
            # Si no hi ha midi_note, calcular-la des del nom i octava
            note_name = note_config.get('note_name', 'C')
            octave = note_config.get('octave', 4)
            note_offset = NOTE_OFFSETS.get(note_name, 0)
            midi_note = (octave + 1) * 12 + note_offset
        
        # Assegurar que està dins del rang MIDI vàlid
        midi_note = max(0, min(127, midi_note))
        
        # Tocar la nota amb la velocitat del potenciòmetre
        self._note_on(midi_note, btn_idx)
    
    def _generate_chord_from_custom_scale(self, btn_idx, custom_scale):
        """Genera un acord (tríada major) des de l'escala personalitzada
        Args:
            btn_idx: Índex del botó (0-7)
            custom_scale: Diccionari amb l'escala personalitzada (id, name, notes)
        """
        if not custom_scale:
            return
        
        # Primer, aturar notes anteriors d'aquest botó
        self._note_off_for_button(btn_idx)
        
        # Trobar la nota configurada per aquest botó
        notes = custom_scale.get('notes', [])
        note_config = None
        for note in notes:
            if note.get('button') == btn_idx:
                note_config = note
                break
        
        if not note_config:
            # Si no hi ha nota configurada per aquest botó, no tocar res
            return
        
        # Obtenir nota MIDI base
        midi_note = note_config.get('midi_note')
        if midi_note is None:
            note_name = note_config.get('note_name', 'C')
            octave = note_config.get('octave', 4)
            note_offset = NOTE_OFFSETS.get(note_name, 0)
            midi_note = (octave + 1) * 12 + note_offset
        
        # Assegurar que està dins del rang MIDI vàlid
        midi_note = max(0, min(127, midi_note))
        
        # Generar tríada major cromàtica: root, tercera major (+4), quinta justa (+7)
        chord_notes = [
            midi_note,      # Root
            midi_note + 4,  # Tercera major
            midi_note + 7   # Quinta justa
        ]
        
        # Tocar totes les notes de l'acord
        for note in chord_notes:
            note = max(0, min(127, note))
            try:
                self.midi.send(NoteOn(note, self.velocity))
                self.active_notes.add(note)
                self.button_notes[btn_idx].add(note)
            except Exception as e:
                print(f"Error tocant acord: {e}")
    
    def _generate_chord_for_button(self, btn_idx):
        """Genera un acord per al botó segons l'escala actual"""
        # Obtenir escala actual (només funciona si no és progressió ni escala personalitzada)
        if len(self.available_scales) == 0:
            return
        
        current_scale_id = self.available_scales[self.scale_mode_index]
        
        # Si és una escala personalitzada, generar acord a partir de la nota configurada
        if current_scale_id >= 2000:
            custom_scale = self.config_manager.get_custom_scale_by_scale_id(current_scale_id) if self.config_manager else None
            if custom_scale:
                self._generate_chord_from_custom_scale(btn_idx, custom_scale)
            return
        
        # Si és una progressió, utilitzar el mètode específic
        if current_scale_id >= 1000:
            progression = self.config_manager.get_progression_by_scale_id(current_scale_id) if self.config_manager else None
            if progression:
                self._generate_chord_from_progression(btn_idx, progression)
            return
        
        scale_info = get_scale_mode(current_scale_id)
        scale_intervals = scale_info['intervals']
        key_offset = KEY_OFFSETS[self.key_index]
        
        # Primer, aturar notes anteriors d'aquest botó
        self._note_off_for_button(btn_idx)
        
        # Calcular nota base
        scale_degree = btn_idx % len(scale_intervals)
        octave_offset = btn_idx // len(scale_intervals)
        root_note = (self.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
        
        # Construir acord amb tríada (root, tercera, quinta)
        chord_notes = []
        
        # Root
        chord_notes.append(root_note)
        
        # Tercera (2 graus d'escala amunt)
        third_degree = (scale_degree + 2) % len(scale_intervals)
        third_octave = octave_offset + ((scale_degree + 2) // len(scale_intervals))
        third_note = (self.octave + third_octave) * 12 + key_offset + scale_intervals[third_degree]
        chord_notes.append(third_note)
        
        # Quinta (4 graus d'escala amunt)
        fifth_degree = (scale_degree + 4) % len(scale_intervals)
        fifth_octave = octave_offset + ((scale_degree + 4) // len(scale_intervals))
        fifth_note = (self.octave + fifth_octave) * 12 + key_offset + scale_intervals[fifth_degree]
        chord_notes.append(fifth_note)
        
        # Tocar totes les notes de l'acord SIMULTÀNIAMENT
        for note in chord_notes:
            note = max(0, min(127, note))
            # Enviar NoteOn directament sense esborrar les anteriors
            try:
                self.midi.send(NoteOn(note, self.velocity))
                self.active_notes.add(note)
                self.button_notes[btn_idx].add(note)
            except Exception as e:
                print(f"Error tocant acord: {e}")
    
    def _process_arpeggiator(self, button_states, current_time):
        """Processa l'arpeggiador (amb suport per acords i múltiples modes)"""
        # Trobar botons premuts (només 1-8)
        pressed_buttons = [i for i in range(8) if i < len(button_states) and button_states[i]]
        
        if not pressed_buttons:
            # No hi ha botons premuts - aturar arpeggiador
            self.stop_all_notes()
            self.arp_index = 0
            self.arp_notes = []
            self.arp_button_order = []
            return
        
        # Mode 'Ordre': Detectar canvis en botons premuts per actualitzar ordre
        arp_info = get_arp_mode(self.arp_mode_index)
        if arp_info['direction'] == 'order':
            # Afegir nous botons a l'ordre
            for btn in pressed_buttons:
                if btn not in self.arp_button_order:
                    self.arp_button_order.append(btn)
            # Eliminar botons que ja no estan premuts
            self.arp_button_order = [btn for btn in self.arp_button_order if btn in pressed_buttons]
        
        # Generar notes per als botons premuts amb tonalitat i escala
        all_notes = []
        
        # Obtenir escala actual
        if len(self.available_scales) == 0:
            return
        
        current_scale_id = self.available_scales[self.scale_mode_index]
        
        # Detectar tipus: escala personalitzada (>= 2000), progressió (1000-1999) o escala normal (< 1000)
        if current_scale_id >= 2000:
            # Per escales personalitzades, obtenir notes directament de la configuració
            custom_scale = self.config_manager.get_custom_scale_by_scale_id(current_scale_id) if self.config_manager else None
            if not custom_scale:
                return
            
            notes_data = custom_scale.get('notes', [])
            for btn_idx in pressed_buttons:
                # Trobar la nota per aquest botó
                note_config = None
                for note in notes_data:
                    if note.get('button') == btn_idx:
                        note_config = note
                        break
                
                if note_config:
                    # Obtenir nota MIDI directament
                    midi_note = note_config.get('midi_note')
                    if midi_note is None:
                        note_name = note_config.get('note_name', 'C')
                        octave = note_config.get('octave', 4)
                        note_offset = NOTE_OFFSETS.get(note_name, 0)
                        midi_note = (octave + 1) * 12 + note_offset
                    
                    midi_note = max(0, min(127, midi_note))
                    all_notes.append(midi_note)
        elif current_scale_id >= 1000:
            # Per progressions, generar directament els acords configurats
            progression = self.config_manager.get_progression_by_scale_id(current_scale_id) if self.config_manager else None
            if not progression:
                return
            
            chords_data = progression.get('chords', [])
            for btn_idx in pressed_buttons:
                # Trobar l'acord per aquest botó
                chord_config = None
                for chord in chords_data:
                    if chord.get('button') == btn_idx:
                        chord_config = chord
                        break
                
                if chord_config:
                    # Generar notes de l'acord
                    root_note_name = chord_config.get('root_note', 'C')
                    chord_type = chord_config.get('chord_type', 'Major')
                    octave = chord_config.get('octave', 4)
                    
                    root_offset = NOTE_OFFSETS.get(root_note_name, 0)
                    base_note = octave * 12 + root_offset
                    
                    chord_intervals = get_chord_intervals(chord_type)
                    for interval in chord_intervals:
                        note = base_note + interval
                        note = max(0, min(127, note))
                        all_notes.append(note)
        else:
            # Escala normal
            scale_info = get_scale_mode(current_scale_id)
            scale_intervals = scale_info['intervals']
            key_offset = KEY_OFFSETS[self.key_index]
            
            for btn_idx in pressed_buttons:
                if self.chord_mode_active:
                    # Mode acords: generar tríada (root, 3a, 5a) per cada botó
                    scale_degree = btn_idx % len(scale_intervals)
                    octave_offset = btn_idx // len(scale_intervals)
                    root_note = (self.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
                    
                    # Root
                    all_notes.append(root_note)
                    
                    # Tercera (2 graus d'escala amunt)
                    third_degree = (scale_degree + 2) % len(scale_intervals)
                    third_octave = octave_offset + ((scale_degree + 2) // len(scale_intervals))
                    third_note = (self.octave + third_octave) * 12 + key_offset + scale_intervals[third_degree]
                    all_notes.append(third_note)
                    
                    # Quinta (4 graus d'escala amunt)
                    fifth_degree = (scale_degree + 4) % len(scale_intervals)
                    fifth_octave = octave_offset + ((scale_degree + 4) // len(scale_intervals))
                    fifth_note = (self.octave + fifth_octave) * 12 + key_offset + scale_intervals[fifth_degree]
                    all_notes.append(fifth_note)
                else:
                    # Mode normal: una nota per botó
                    scale_degree = btn_idx % len(scale_intervals)
                    octave_offset = btn_idx // len(scale_intervals)
                    note = (self.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
                    note = max(0, min(127, note))
                    all_notes.append(note)
        
        # Processar notes segons el mode d'arpegiador
        arp_info = get_arp_mode(self.arp_mode_index)
        arp_direction = arp_info['direction']
        
        if arp_direction == 'order':
            # Mode 'Ordre': Mantenir ordre de pulsació dels botons
            # Generar notes per cada botó en l'ordre en què es van prémer
            ordered_notes = []
            for btn_idx in self.arp_button_order:
                if self.chord_mode_active:
                    # Generar acord per aquest botó
                    scale_degree = btn_idx % len(scale_intervals)
                    octave_offset = btn_idx // len(scale_intervals)
                    root_note = (self.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
                    ordered_notes.append(max(0, min(127, root_note)))
                    # Tercera
                    third_degree = (scale_degree + 2) % len(scale_intervals)
                    third_octave = octave_offset + ((scale_degree + 2) // len(scale_intervals))
                    third_note = (self.octave + third_octave) * 12 + key_offset + scale_intervals[third_degree]
                    ordered_notes.append(max(0, min(127, third_note)))
                    # Quinta
                    fifth_degree = (scale_degree + 4) % len(scale_intervals)
                    fifth_octave = octave_offset + ((scale_degree + 4) // len(scale_intervals))
                    fifth_note = (self.octave + fifth_octave) * 12 + key_offset + scale_intervals[fifth_degree]
                    ordered_notes.append(max(0, min(127, fifth_note)))
                else:
                    # Una nota per botó
                    scale_degree = btn_idx % len(scale_intervals)
                    octave_offset = btn_idx // len(scale_intervals)
                    note = (self.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
                    ordered_notes.append(max(0, min(127, note)))
            self.arp_notes = ordered_notes
        else:
            # Altres modes: eliminar duplicats i ordenar
            all_notes = sorted(set(max(0, min(127, n)) for n in all_notes))
            self.arp_notes = all_notes
        
        # Comprovar si és hora de la següent nota
        if current_time - self.last_arp_time >= self.arp_speed:
            # Aturar nota anterior
            self.stop_all_notes()
            
            # Tocar nota(es) actual(s)
            if self.arp_notes:
                # Processar segons tipus de patró
                self._play_arp_pattern(arp_direction)
                self.last_arp_time = current_time
    
    def _play_arp_pattern(self, direction):
        """Toca les notes segons el patró d'arpegiador seleccionat"""
        if not self.arp_notes:
            return
        
        num_notes = len(self.arp_notes)
        
        # PATRONS BÀSICS
        if direction == 'random':
            # Aleatori
            current_note = self.arp_notes[random.randint(0, num_notes - 1)]
            self._note_on(current_note, -1)
            
        elif direction == 'up':
            # Amunt
            current_note = self.arp_notes[self.arp_index % num_notes]
            self._note_on(current_note, -1)
            self.arp_index = (self.arp_index + 1) % num_notes
            
        elif direction == 'down':
            # Avall
            current_note = self.arp_notes[self.arp_index % num_notes]
            self._note_on(current_note, -1)
            self.arp_index = (self.arp_index - 1) % num_notes
            
        elif direction == 'pingpong':
            # Ping-pong
            current_note = self.arp_notes[self.arp_index % num_notes]
            self._note_on(current_note, -1)
            self.arp_index += self.arp_direction
            if self.arp_index >= num_notes:
                self.arp_index = num_notes - 2
                self.arp_direction = -1
            elif self.arp_index < 0:
                self.arp_index = 1
                self.arp_direction = 1
                
        elif direction == 'order':
            # Ordre de pulsació
            current_note = self.arp_notes[self.arp_index % num_notes]
            self._note_on(current_note, -1)
            self.arp_index = (self.arp_index + 1) % num_notes
        
        # PATRONS CLÀSSICS
        elif direction == 'alberti':
            # Alberti clàssic: baix-quinta-tercera-quinta (1-3-2-3)
            if num_notes >= 3:
                alberti_pattern = [0, 2, 1, 2]  # Índexs: baix, 5a, 3a, 5a
                idx = alberti_pattern[self.arp_index % 4]
                current_note = self.arp_notes[min(idx, num_notes - 1)]
                self._note_on(current_note, -1)
                self.arp_index = (self.arp_index + 1) % 4
            else:
                # Si no hi ha prou notes, alternança simple
                current_note = self.arp_notes[self.arp_index % num_notes]
                self._note_on(current_note, -1)
                self.arp_index = (self.arp_index + 1) % num_notes
                
        elif direction == 'alberti_alt':
            # Alberti invertit: baix-tercera-quinta-tercera (1-2-3-2)
            if num_notes >= 3:
                alberti_alt_pattern = [0, 1, 2, 1]  # Índexs: baix, 3a, 5a, 3a
                idx = alberti_alt_pattern[self.arp_index % 4]
                current_note = self.arp_notes[min(idx, num_notes - 1)]
                self._note_on(current_note, -1)
                self.arp_index = (self.arp_index + 1) % 4
            else:
                current_note = self.arp_notes[self.arp_index % num_notes]
                self._note_on(current_note, -1)
                self.arp_index = (self.arp_index + 1) % num_notes
                
        elif direction == 'waltz':
            # Vals: baix-acord-acord (1, 2+3, 2+3)
            if num_notes >= 3:
                if self.arp_index % 3 == 0:
                    # Primera pulsació: baix sol
                    self._note_on(self.arp_notes[0], -1)
                else:
                    # Segona i tercera pulsació: acord (notes superiors)
                    for i in range(1, min(num_notes, 4)):
                        self._note_on(self.arp_notes[i], -1)
                self.arp_index = (self.arp_index + 1) % 3
            else:
                current_note = self.arp_notes[self.arp_index % num_notes]
                self._note_on(current_note, -1)
                self.arp_index = (self.arp_index + 1) % num_notes
                
        elif direction == 'broken':
            # Acord trencat clàssic: 1-3-5-1-5-3
            if num_notes >= 3:
                broken_pattern = [0, 1, 2, 0, 2, 1]  # Amunt i baixa variant
                idx = broken_pattern[self.arp_index % 6]
                current_note = self.arp_notes[min(idx, num_notes - 1)]
                self._note_on(current_note, -1)
                self.arp_index = (self.arp_index + 1) % 6
            else:
                current_note = self.arp_notes[self.arp_index % num_notes]
                self._note_on(current_note, -1)
                self.arp_index = (self.arp_index + 1) % num_notes
                
        elif direction == 'tremolo':
            # Trèmolo: alternança ràpida entre baix i tercera (1-2-1-2)
            if num_notes >= 2:
                tremolo_pattern = [0, 1]
                idx = tremolo_pattern[self.arp_index % 2]
                current_note = self.arp_notes[idx]
                self._note_on(current_note, -1)
                self.arp_index = (self.arp_index + 1) % 2
            else:
                current_note = self.arp_notes[0]
                self._note_on(current_note, -1)
        
        # PATRONS ESPECIALS
        elif direction == 'zigzag':
            # Zig-zag: 1,3,2,5,4,7,6,9...
            if self.arp_index % 2 == 0:
                idx = self.arp_index // 2
            else:
                idx = (self.arp_index // 2) + 1
            current_note = self.arp_notes[idx % num_notes]
            self._note_on(current_note, -1)
            self.arp_index = (self.arp_index + 1) % (num_notes * 2)
            
        elif direction == 'block':
            # Block: totes les notes simultàniament
            for note in self.arp_notes:
                self._note_on(note, -1)
            self.arp_index = 0
                
        elif direction == 'rolled':
            # Rolled: ascendent ràpid (més ràpid que block)
            # Tocar nota actual i potser la següent si és ràpid
            current_note = self.arp_notes[self.arp_index % num_notes]
            self._note_on(current_note, -1)
            self.arp_index = (self.arp_index + 1) % num_notes
            
        elif direction == 'octaves':
            # Octaves: duplicar amb octava superior
            current_note = self.arp_notes[self.arp_index % num_notes]
            self._note_on(current_note, -1)
            # Afegir octava superior si està dins del rang
            if current_note + 12 <= 127:
                self._note_on(current_note + 12, -1)
            self.arp_index = (self.arp_index + 1) % num_notes
            
        elif direction == 'contrary':
            # Contrari: mitja puja, mitja baixa
            mid_point = num_notes // 2
            if self.arp_index < mid_point:
                # Primera meitat: amunt
                current_note = self.arp_notes[self.arp_index]
            else:
                # Segona meitat: avall
                idx = num_notes - 1 - (self.arp_index - mid_point)
                current_note = self.arp_notes[idx]
            self._note_on(current_note, -1)
            self.arp_index = (self.arp_index + 1) % num_notes
            
        elif direction == 'spread':
            # Spread: salts grans (cada 3a o 4a nota)
            jump = max(2, num_notes // 3)
            current_note = self.arp_notes[self.arp_index % num_notes]
            self._note_on(current_note, -1)
            self.arp_index = (self.arp_index + jump) % num_notes
        
        else:
            # Fallback: mode up
            current_note = self.arp_notes[self.arp_index % num_notes]
            self._note_on(current_note, -1)
            self.arp_index = (self.arp_index + 1) % num_notes
            
    def _note_on(self, note, button_index):
        """Activa una nota amb la velocitat configurada"""
        # Para qualsevol nota anterior d'aquest botó (només si no és arpeggiador)
        if button_index >= 0:
            self._note_off_for_button(button_index)
        
        # Envia NoteOn amb velocitat del potenciòmetre
        try:
            self.midi.send(NoteOn(note, self.velocity))
            self.active_notes.add(note)
            if button_index >= 0:
                self.button_notes[button_index].add(note)
            
            # Debug info (opcional per evitar latència)
            if self.debug:
                note_name = self._note_to_name(note)
                scale_info = get_scale_mode(self.scale_mode)
                scale_name = scale_info['name']
                key_name = KEY_CIRCLE[self.key_index]
                context = f"BTN{button_index+1}" if button_index >= 0 else "ARP"
                mode = "Acords" if self.chord_mode_active else ("Arp" if self.arp_mode_active else "Normal")
                print(f"🎵 {note_name} | {key_name} {scale_name} | {mode} | Vel:{self.velocity}")
            
        except Exception as e:
            print(f"Error enviant NoteOn: {e}")
            
    def _note_off_for_button(self, button_index):
        """Para totes les notes associades a un botó específic"""
        try:
            notes_set = self.button_notes.get(button_index, set())
            if not notes_set:
                return
            
            # Crear una còpia de les notes per iterar
            notes_to_stop = list(notes_set)
            
            for note in notes_to_stop:
                try:
                    # Enviar NoteOff
                    self.midi.send(NoteOff(note, 0))
                except Exception as e:
                    if self.debug:
                        print(f"Error enviant NoteOff per nota {note}: {e}")
                
                # Sempre netejar del tracking
                self.active_notes.discard(note)
            
            # Netejar completament el set d'aquest botó
            notes_set.clear()
            
        except Exception as e:
            if self.debug:
                print(f"Error _note_off_for_button: {e}")
                
    def _note_to_name(self, midi_note):
        """Converteix número MIDI a nom de nota"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi_note // 12 - 1
        note = note_names[midi_note % 12]
        return f"{note}{octave}"
        
    def change_octave(self, direction):
        """Canvia l'octava (+1 o -1)"""
        if direction > 0 and self.octave < 8:
            self.octave += 1
            print(f"🎹 Octava pujada a {self.octave}")
        elif direction < 0 and self.octave > 0:
            self.octave -= 1
            print(f"🎹 Octava baixada a {self.octave}")
        else:
            limit = "màxima (8)" if direction > 0 else "mínima (0)"
            print(f"🎹 Ja estàs a l'octava {limit}")
            
    def get_info(self):
        """Retorna informació de l'estat actual"""
        # Gestionar el cas inicial on sustain_level == -1
        if self.sustain_level < 0:
            sustain_status = 'INIT'
        else:
            sustain_status = 'ON' if self.sustain_level >= 64 else 'OFF'
        
        # Mostrar info de ADC0 segons el mode actiu
        if self.arp_mode_active:
            adc0_info = f'Arp Speed: {self.arp_speed:.2f}s'
            arp_info = get_arp_mode(self.arp_mode_index)
            arp_mode_name = arp_info['name']
            arp_status = f'ON ({arp_mode_name})'
        else:
            adc0_info = f'Velocity: {self.velocity}'
            arp_status = 'OFF'
        
        # Obtenir l'escala/progressió actual
        if len(self.available_scales) > 0:
            current_scale_id = self.available_scales[self.scale_mode_index]
            
            # Detectar si és progressió o escala
            if current_scale_id >= 1000:
                # És una progressió
                progression = self.config_manager.get_progression_by_scale_id(current_scale_id) if self.config_manager else None
                if progression:
                    mode_info = f"♪ {progression.get('name', 'Progressió')}"
                else:
                    mode_info = f"♪ Prog #{current_scale_id - 1000}"
                key_info = "-"  # Progressions no usen tonalitat
            else:
                # És una escala normal
                scale_info = get_scale_mode(current_scale_id)
                scale_name = scale_info['name']
                key_name = KEY_CIRCLE[self.key_index]
                mode_info = scale_name
                key_info = key_name
        else:
            mode_info = "Cap escala"
            key_info = "-"
        
        return {
            'name': self.name,
            'octave': self.octave,
            'key': key_info,
            'scale': mode_info,
            'active_notes': len(self.active_notes),
            'chord_mode': 'ON' if self.chord_mode_active else 'OFF',
            'arp_mode': arp_status,
            'adc0_x': adc0_info,
            'filter': self.filter_cutoff,
            'sustain': f'{sustain_status} ({max(0, self.sustain_level)})'
        }
