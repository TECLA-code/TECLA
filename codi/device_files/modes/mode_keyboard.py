"""
TECLA - Mode Teclat
Mode especial que converteix els botons 1-12 en un teclat chromàtic
Activat pel botó 13, amb controls de potenciòmetres per personalitzar
"""

import time
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.pitch_bend import PitchBend

# Importar constants des de mòdul compartit per estalviar RAM
try:
    import sys
    sys.path.insert(0, '/sd' if '/sd' in sys.path else '.')
    from music_constants import SCALES, KEYS, NOTES, get_chord, note_offset
except ImportError:
    # Fallback si no es troba el mòdul (desenvolupament)
    SCALES = ((0, 2, 4, 5, 7, 9, 11),)  # Només Major
    KEYS = (0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5)
    NOTES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
    _CN=('Major','m','7','maj7','m7','dim','aug','sus4','sus2','m7b5','add9','6','add11','add13','9','9#5','9b5','9#11','11','13','13b9','13#9','7b9','7#9','7sus4','7b13','69','m9','m11','m13','m69')
    _CI=((0,4,7),(0,3,7),(0,4,7,10),(0,4,7,11),(0,3,7,10),(0,3,6),(0,4,8),(0,5,7),(0,2,7),(0,3,6,10),(0,4,7,14),(0,4,7,9),(0,4,7,17),(0,4,7,21),(0,4,7,10,14),(0,4,8,10,14),(0,4,6,10,14),(0,4,7,10,14,18),(0,4,7,10,14,17),(0,4,7,10,14,21),(0,4,7,10,13,21),(0,4,7,10,15,21),(0,4,7,10,13),(0,4,7,10,15),(0,5,7,10),(0,4,7,10,20),(0,4,7,9,14),(0,3,7,10,14),(0,3,7,10,14,17),(0,3,7,10,14,21),(0,3,7,9,14))
    def get_chord(n):
        try: return _CI[_CN.index(n)]
        except: return (0,4,7)
    def note_offset(n):
        try:
            return NOTES.index(n)
        except:
            return 0

# Ordre cromàtic (C, C#, D, ... B) — més intuïtiu que el cercle de quintes
KEY_CIRCLE = ('C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B')
KEY_OFFSETS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

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
        self.key_index = 0  # Índex de tonalitat (C per defecte)
        self.scale_mode_index = 0  # Índex d'escala actual
        self.chord_mode_active = False  # Mode acords desactivat per defecte
        self.available_chord_types = ['Major']  # Tipologies d'acord disponibles
        self.chord_type_index = 0  # Índex de la tipologia activa
        self.chord_btn_press_time = 0.0  # Per detecció de click mantingut (botó 11)
        self.arp_mode_active = False  # Mode arpegiador desactivat per defecte
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
            self.pot_x_function = pot_functions.get('pot_x', 'Velocity/Arp Speed (dual)')
            self.pot_y_function = pot_functions.get('pot_y', 'Modulation (CC1)')
            self.pot_z_function = pot_functions.get('pot_z', 'Sustain (CC64)')
            
            # Obtenir tipologies d'acord disponibles
            self.available_chord_types = self.config_manager.get_chord_types()
            
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
        
        # Gate: efecte temporal amb CC11 (Expression)
        self.gate_enabled = False
        self.gate_period = 0.2  # període total del cicle (segons)
        self.gate_min_expr = 0  # valor mínim d'expressio (0-127)
        self.gate_duty = 0.5  # duty cycle (proporció en high)
        self.gate_last_toggle = 0
        self.gate_high = True  # estat actual: high (127) o low (min_expr)
        
        # Detecció de click mantingut per desactivar arpegiador
        self.arp_btn_press_time = 0.0
        self._arp_pat_sel_last_val = None  # Tracking del pot per evitar sobreescriptura
        
        # Sustain hold: quan està actiu, no s'envien NoteOff (sustain indefinit)
        self.sustain_hold_enabled = False
        self.sustain_hold_value = 0  # Valor actual del potenciòmetre sustain (0-127)
        self.sustain_level = 0  # Tracking del sustain CC64 enviat (0-127)
        self.filter_cutoff = 64  # Tracking del filtre (0-127, valor neutral)
        
        # Flag per primer update (sincronitzar potenciòmetres)
        self.first_update = True
        
        # Guardar estat anterior del Gate per preservar-lo en canvis de capa
        self._previous_gate_enabled = False
        self._previous_gate_period = 0.2
        
        print("🎹 Mode Teclat")
    
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
        
        # Preservar estat del Gate abans de recarregar configuracions
        self._previous_gate_enabled = self.gate_enabled
        self._previous_gate_period = self.gate_period
        
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
            
            # Recarregar tipologies d'acord disponibles
            self.available_chord_types = self.config_manager.get_chord_types()
            
        for i in range(12):
            self.button_notes[i].clear()
        
        # Restaurar estat del Gate després de recarregar
        if self._previous_gate_enabled:
            self.gate_enabled = self._previous_gate_enabled
            self.gate_period = self._previous_gate_period
            print(f"🎛️ Gate restaurat: enabled={self.gate_enabled}, period={self.gate_period:.2f}s")
        
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
        
        # Desactivar tots els CC al sortir
        try:
            for ch in range(16):
                self.midi.send(ControlChange(1, 0, channel=ch))   # Modulation OFF
                self.midi.send(ControlChange(64, 0, channel=ch))  # Sustain OFF
                self.midi.send(ControlChange(91, 0, channel=ch))  # Reverb OFF
                self.midi.send(ControlChange(93, 0, channel=ch))  # Chorus OFF
        except Exception:
            pass
        
        # Apagar el PWM quan no hi ha notes actives
        try:
            import main
            if hasattr(main, 'pwm') and main.pwm is not None:
                main.pwm.duty_cycle = 0
        except Exception:
            pass
        
        print("🎹 Mode Teclat desactivat")
        
    def stop_all_notes(self):
        """Para totes les notes actives i neteja tot el tracking"""
        # Primer, desactivar sustain per assegurar que cap nota queda enganxada
        try:
            for ch in range(16):
                self.midi.send(ControlChange(64, 0, channel=ch))  # Sustain OFF
            self.sustain_level = 0  # Actualitzar el tracking del sustain
        except Exception:
            pass
        
        # Enviar NoteOff per totes les notes actives
        for note in self.active_notes.copy():
            try:
                self.midi.send(NoteOff(note, 0))
            except Exception:
                pass
        
        # Netejar tots els trackings
        self.active_notes.clear()
        for i in range(12):
            self.button_notes[i].clear()
        
        # Apagar el PWM
        try:
            import main
            if hasattr(main, 'pwm') and main.pwm is not None:
                main.pwm.duty_cycle = 0
        except Exception:
            pass
            
    def update(self, pot_values, button_states):
        """Actualització principal del mode teclat"""
        # Al primer update, forçar aplicació de tots els potenciòmetres
        force_update = False
        if self.first_update and len(pot_values) >= 3:
            self.first_update = False
            force_update = True
            # print("✓ Sync pots")  # Silenciós
        
        # Actualitzar paràmetres des dels potenciòmetres
        self._update_parameters(pot_values, force_update=force_update)
        
        # Processar els botons 1-12 com a notes del teclat
        self._process_keyboard_buttons(button_states[:12])
            
    def _update_parameters(self, pot_values, force_update=False):
        from modes.kbd_pots import update_parameters
        update_parameters(self, pot_values, force_update)
    
    def _apply_pot_function(self, pot_name, pot_value, force_update=False):
        from modes.kbd_pots import apply_pot_function
        apply_pot_function(self, pot_name, pot_value, force_update)
    
    def _apply_arp_pot_function(self, pot_name, pot_value, force_update=False):
        from modes.kbd_pots import apply_arp_pot_function
        apply_arp_pot_function(self, pot_name, pot_value, force_update)
    
    def _send_cc_if_changed(self, cc_num, new_value, threshold=2):
        """Envia un CC MIDI només si ha canviat significativament"""
        if cc_num not in self.cc_values or abs(new_value - self.cc_values[cc_num]) >= threshold:
            self._send_cc(cc_num, new_value)
    
    def _send_cc(self, cc_num, value):
        """Envia un CC MIDI a tots els canals"""
        self.cc_values[cc_num] = value
        
        try:
            for ch in range(16):
                self.midi.send(ControlChange(cc_num, value, channel=ch))
        except Exception:
            pass
    
    def _reapply_active_ccs(self):
        """Re-aplica tots els CC MIDI actius (útil després de stop_all_notes)"""
        try:
            for cc_num, value in self.cc_values.items():
                for ch in range(16):
                    self.midi.send(ControlChange(cc_num, value, channel=ch))
        except Exception:
            pass
    
    def _send_pitch_bend(self, pitch_value):
        """Envia un PitchBend MIDI a tots els canals
        Args:
            pitch_value: Valor de pitch bend (-8192 a +8191, 0 = centrat)
        """
        # Tracking de l'últim valor per debug
        if not hasattr(self, '_last_pitch_bend'):
            self._last_pitch_bend = 0
        
        # PitchBend és silenciós, no cal print constant
        
        try:
            # Enviar PitchBend a tots els canals
            for ch in range(16):
                self.midi.send(PitchBend(pitch_value, channel=ch))
        except Exception as e:
            if self.debug:
                print(f"Error enviant PitchBend: {e}")
            
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
                                print(f"🎼 Escala #{actual_scale_id} ({self.scale_mode_index + 1}/{len(self.available_scales)})")
                    
                    elif btn_idx == 9:  # Botó 10: Canviar tonalitat (cromàtic)
                        # IMPORTANT: Aturar totes les notes abans de canviar de tonalitat
                        self.stop_all_notes()
                        self.key_index = (self.key_index + 1) % 12
                        key_name = KEY_CIRCLE[self.key_index]  # ordre cromàtic
                        print(f"🎵 Tonalitat: {key_name}")
                    
                    elif btn_idx == 10:  # Botó 11: Registrar inici de premuda
                        self.chord_btn_press_time = current_time
                    
                    elif btn_idx == 11:  # Botó 12: Registrar inici de premuda
                        self.arp_btn_press_time = current_time
                
                elif not current_pressed and was_pressed:
                    if btn_idx == 11:  # Botó 12: Arpeggiador (1 click=activa/cicla, mantingut=desactiva)
                        elapsed = current_time - self.arp_btn_press_time
                        self.stop_all_notes()
                        if elapsed >= 0.5:  # Click mantingut → desactivar
                            self.arp_mode_active = False
                            self.arp_notes = []
                            self.arp_button_order = []
                            print(f"🎶 Arpeggiador DESACTIVAT")
                        elif not self.arp_mode_active:  # Click curt + inactiu → activar
                            self.arp_mode_active = True
                            self.arp_notes = []
                            self.arp_button_order = []
                            self._arp_pat_sel_last_val = None  # Anchor pot, no override
                            if self.arp_mode_index not in self.available_arp_modes:
                                self.arp_mode_index = self.available_arp_modes[0] if self.available_arp_modes else 2
                            print(f"🎶 Arpeggiador: {self._get_arp_name(self.arp_mode_index)}")
                        else:  # Click curt + actiu → ciclar patró
                            if self.available_arp_modes:
                                try:
                                    current_idx = self.available_arp_modes.index(self.arp_mode_index)
                                    self.arp_mode_index = self.available_arp_modes[(current_idx + 1) % len(self.available_arp_modes)]
                                except ValueError:
                                    self.arp_mode_index = self.available_arp_modes[0]
                                self.arp_index = 0
                                self.arp_direction = 1
                                self.arp_button_order = []
                                self._arp_pat_sel_last_val = None  # Anchor pot after button cycle
                                print(f"🎶 Arpeggiador: {self._get_arp_name(self.arp_mode_index)}")
                        self._reapply_active_ccs()
                    
                    elif btn_idx == 10:  # Botó 11: Mode acords (1 click=activa/cicla, mantingut=desactiva)
                        elapsed = current_time - self.chord_btn_press_time
                        self.stop_all_notes()
                        if elapsed >= 0.5:  # Click mantingut → desactivar
                            self.chord_mode_active = False
                            self.chord_type_index = 0
                            print(f"🎹 Mode Acords DESACTIVAT")
                        elif not self.chord_mode_active:  # Click curt + inactiu → activar
                            self.chord_mode_active = True
                            ct = self.available_chord_types[self.chord_type_index] if self.available_chord_types else 'Major'
                            print(f"🎹 Mode Acords ACTIVAT ({ct})")
                        else:  # Click curt + actiu → ciclar tipologia
                            if self.available_chord_types:
                                self.chord_type_index = (self.chord_type_index + 1) % len(self.available_chord_types)
                                ct = self.available_chord_types[self.chord_type_index]
                                print(f"🎹 Acord: {ct}")
                        self._reapply_active_ccs()
        
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
                        self._note_off_for_button(btn_idx, from_release=True)
            
            # Processar Gate: repetir notes (només mode teclat/acords)
            if self.gate_enabled:
                self._process_gate(current_time)
        
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
            scale_intervals = SCALES[current_scale_id]
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
        config_octave = chord_config.get('octave', 4)
        
        # Calcular nota MIDI base amb offset d'octava actual (botons 14-15)
        root_offset_val = note_offset(root_note_name)
        base_note = (self.octave + config_octave - 4) * 12 + root_offset_val
        
        # Obtenir intervals de l'acord
        chord_intervals = get_chord(chord_type)
        
        # Generar les notes de l'acord
        for interval in chord_intervals:
            note = base_note + interval
            note = max(0, min(127, note))
            try:
                self.midi.send(NoteOn(note, self.velocity))
                self.active_notes.add(note)
                self.button_notes[btn_idx].add(note)
                # Actualitzar PWM sempre amb la primera nota (root)
                if interval == 0:
                    self._update_pwm_for_note(note)
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
            config_octave = note_config.get('octave', 4)
            note_offset_val = note_offset(note_name)
            # Aplicar offset d'octava actual (botons 14-15)
            midi_note = (self.octave + config_octave - 4 + 1) * 12 + note_offset_val
        else:
            # Si ja té midi_note, aplicar offset d'octava actual
            # Calcular quina octava té la nota configurada i aplicar l'offset
            config_octave = midi_note // 12
            note_in_octave = midi_note % 12
            midi_note = (config_octave + self.octave - 4) * 12 + note_in_octave
        
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
            note_offset_val = note_offset(note_name)
            midi_note = (octave + 1) * 12 + note_offset_val
        
        # Assegurar que està dins del rang MIDI vàlid
        midi_note = max(0, min(127, midi_note))
        
        # Generar tríada major cromàtica: root, tercera major (+4), quinta justa (+7)
        chord_notes = [
            midi_note,      # Root
            midi_note + 4,  # Tercera major
            midi_note + 7   # Quinta justa
        ]
        
        # Tocar les notes de l'acord
        for note in chord_notes:
            note = max(0, min(127, note))
            try:
                self.midi.send(NoteOn(note, self.velocity))
                self.active_notes.add(note)
                self.button_notes[btn_idx].add(note)
                # Actualitzar PWM sempre amb la primera nota (root)
                if note == midi_note:
                    self._update_pwm_for_note(note)
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
        
        scale_intervals = SCALES[current_scale_id]
        key_offset = KEY_OFFSETS[self.key_index]
        
        # Primer, aturar notes anteriors d'aquest botó
        self._note_off_for_button(btn_idx)
        
        # Calcular nota base
        scale_degree = btn_idx % len(scale_intervals)
        octave_offset = btn_idx // len(scale_intervals)
        root_note = (self.octave + octave_offset) * 12 + key_offset + scale_intervals[scale_degree]
        
        # Intervals cromàtics des de la tipologia d'acord activa
        chord_type = self.available_chord_types[self.chord_type_index] if self.available_chord_types else 'Major'
        chord_intervals = get_chord(chord_type)
        chord_notes = [root_note + interval for interval in chord_intervals]
        
        # Tocar les notes de l'acord
        for i, note in enumerate(chord_notes):
            note = max(0, min(127, note))
            try:
                self.midi.send(NoteOn(note, self.velocity))
                self.active_notes.add(note)
                self.button_notes[btn_idx].add(note)
                # Actualitzar PWM sempre amb la primera nota (root)
                if i == 0:
                    self._update_pwm_for_note(note)
            except Exception as e:
                print(f"Error tocant acord: {e}")
    
    def _process_arpeggiator(self, button_states, current_time):
        from modes.kbd_arp import process_arpeggiator
        process_arpeggiator(self, button_states, current_time)
    
    def _get_arp_name(self, mode_index):
        from modes.kbd_arp import get_arp_name
        return get_arp_name(self, mode_index)

    def _play_arp_pattern(self, direction):
        from modes.kbd_arp import play_arp_pattern
        play_arp_pattern(self, direction)

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
            
            # Actualitzar PWM amb aquesta nota
            self._update_pwm_for_note(note)
            
            # Gate funciona amb CC11 Expression, no necessita tracking de notes
            
            # Debug info (opcional per evitar latència)
            if self.debug:
                note_name = self._note_to_name(note)
                scale_name = f"Escala#{self.scale_mode}"
                key_name = KEY_CIRCLE[self.key_index]
                context = f"BTN{button_index+1}" if button_index >= 0 else "ARP"
                mode = "Acords" if self.chord_mode_active else ("Arp" if self.arp_mode_active else "Normal")
                print(f"🎵 {note_name} | {key_name} {scale_name} | {mode} | Vel:{self.velocity}")
            
        except Exception as e:
            print(f"Error enviant NoteOn: {e}")
            
    def _note_off_for_button(self, button_index, from_release=False):
        """Para totes les notes associades a un botó específic
        
        Args:
            button_index: Índex del botó (0-11)
            from_release: True si ve d'alliberar el botó, False si ve de tocar una nova nota
        """
        # Si sustain hold està actiu i ve d'un alliberament de botó,
        # NO enviar NoteOff (sustain indefinit)
        # PERÒ si ve de tocar una nova nota del mateix botó, sempre aturar les notes anteriors
        if self.sustain_hold_enabled and from_release:
            return  # Les notes continuen sonant indefinidament quan s'allibera el botó
        
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
                
                # Gate funciona amb CC11 Expression, no necessita tracking de notes
            
            # Netejar completament el set d'aquest botó
            notes_set.clear()
            
            # Si no queden notes actives, apagar el PWM
            if len(self.active_notes) == 0:
                try:
                    import main
                    if hasattr(main, 'pwm') and main.pwm is not None:
                        main.pwm.duty_cycle = 0
                except Exception:
                    pass
            
        except Exception as e:
            if self.debug:
                print(f"Error _note_off_for_button: {e}")
                
    def _process_gate(self, current_time):
        """Processa l'efecte Gate: alterna CC11 (Expression) entre high i low
        Basat en effect_gate.py
        """
        if not self.gate_enabled:
            return
        
        # Calcular temps transcorregut des de l'últim toggle
        elapsed = current_time - self.gate_last_toggle
        
        # Calcular el temps objectiu segons l'estat actual
        # Si estem en high: esperar duty_cycle * period
        # Si estem en low: esperar (1 - duty_cycle) * period
        target = self.gate_period * (self.gate_duty if self.gate_high else (1.0 - self.gate_duty))
        
        # Comprovar si és hora de canviar d'estat
        if elapsed >= target:
            self.gate_high = not self.gate_high
            self.gate_last_toggle = current_time
        
        # Enviar el valor de CC11 (Expression) segons l'estat
        val = 127 if self.gate_high else self.gate_min_expr
        self._send_cc(11, val)
    
    def _update_pwm_for_note(self, note):
        """Actualitza el PWM per a una nota específica (inicialitza si no existeix)"""
        try:
            import main
            import pwmio
            import board
            
            # Calcular freqüència
            freq = main.midi_to_frequency(note)
            
            # Si el PWM ja existeix, actualitzar-lo
            if hasattr(main, 'pwm') and main.pwm is not None:
                try:
                    main.pwm.frequency = freq
                    main.pwm.duty_cycle = 32767  # 50% duty cycle
                    return
                except Exception:
                    # Si falla, reinicialitzar
                    pass
            
            # Si no existeix o ha fallat, inicialitzar-lo
            try:
                main.pwm = pwmio.PWMOut(board.GP22, frequency=freq, duty_cycle=32767, variable_frequency=True)
            except ValueError as e:
                # Pin ja en ús - no fer res (probablement ja està inicialitzat per altre mode)
                if "in use" not in str(e):
                    print(f"Error inicialitzant PWM: {e}")
        except Exception as e:
            # Silenciar errors per no interrompre el flux MIDI
            pass
    
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
            arp_status = f'ON (#{self.arp_mode_index})'
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
                scale_name = f"Escala#{current_scale_id}"
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
