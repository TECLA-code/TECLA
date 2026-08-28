"""
TECLA - Mode Teclat
Mode especial que converteix els botons 1-12 en un teclat chromàtic
Activat pel botó 13, amb controls de potenciòmetres per personalitzar
"""

import time
from adafruit_midi.control_change import ControlChange
from adafruit_midi.pitch_bend import PitchBend
# (NoteOn/NoteOff ja no s'importen: tot el camí calent usa els missatges
#  POOLED de modes.base_mode — zero al·locacions per nota.)

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
_KEY_OFFSET = {'C':0,'C#':1,'D':2,'Eb':3,'E':4,'F':5,'F#':6,'G':7,'Ab':8,'A':9,'Bb':10,'B':11}
# Eixos d'harmonia negativa (offset en semitones respecte la tònica)
# 0=Quinta/Levy(3.5), 1=Unisonant(0.0), 2=Tercera M(2.0), 3=Tercera m(1.5), 4=Tritó(6.0)
# 5=Quarta(2.5), 6=Sexta M(4.5), 7=Sèptima m(5.5)
_NEG_HARM_AXES = (3.5, 0.0, 2.0, 1.5, 6.0, 2.5, 4.5, 5.5)
_NEG_HARM_NAMES = ('Quinta', 'Unisonant', 'Tercera M', 'Tercera m', 'Trito', 'Quarta', 'Sexta M', 'Septima m')

_SCALE_NAMES = (
    'Major', 'Doric', 'Frigi', 'Lidi', 'Mixolidi', 'Menor', 'Locri',
    'Pentat.Maj', 'Pentat.Men', 'Japonesa', 'Egipcia', 'Arabiga', 'Hongaresa',
    'Lidia Dom', 'Alterada', 'Men.Melod', 'Bhairav', 'Todi',
    'Flamenca', 'Catalana', 'Frigia', 'Balcanica', 'Tons Senc', 'Harm.Maj')

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
        self.available_keys = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
        self.scale_mode_index = 0  # Índex d'escala actual
        self.chord_mode_active = False  # Mode acords desactivat per defecte
        self.available_chord_types = ['Major']  # Tipologies d'acord disponibles
        self.chord_type_index = 0  # Índex de la tipologia activa
        self.chord_btn_press_time = 0.0  # Per detecció de click mantingut (botó 11)
        self.arp_mode_active = False  # Mode arpegiador desactivat per defecte
        self.last_button_states = [False] * 15
        # Mapatge de notes per botó per NoteOff ràpid i precís (15 botons configurables)
        self.button_notes = {i: set() for i in range(15)}
        self.latch_active = False  # Latch: les notes/acords continuen sonant en deixar anar
        self.loop_state = 0  # Looper: 0=inactiu (la resta d'estat es crea lazy a kbd_looper)
        self.voice_lead_active = False  # Conducció de veus (kbd_voicelead, lazy)
        # Base d'acompanyament (modes/accompaniment.py, lazy): motor i estat
        self._accomp = None
        self._accomp_active = False
        self._accomp_pat_idx = 0
        self._accomp_btn_press_time = 0.0
        self._vl_type = 'proximitat'
        self._vl_type_idx = 0
        self.available_vl_types = ['proximitat', 'comu', 'baix', 'ascendent', 'descendent',
                                   'obert', 'tancat', 'fonamental', 'inv1', 'inv2', 'drop2', 'pendol']
        # Config àudio: tecla synth_cfg activa (-1 = cap) i mapatge de potes per tecla
        self._audio_cfg_key = -1
        self.audio_pot_functions = {}
        # Harmonia negativa
        self.neg_harmony_active = False
        self.neg_harmony_type = 0
        self.available_neg_harm_ids = list(range(len(_NEG_HARM_AXES)))
        self._neg_harm_btn_press_time = 0.0
        self._neg_harm_last_release = 0.0
        self._neg_harm_just_activated = False
        # (Inversions d'acord: ara són FORMES de la conducció de veus —
        #  fonamental/inv1/inv2 a kbd_voicelead. L'antic índex propi s'ha retirat.)
        # Acords diatònics — funcions harmòniques
        self.diatonic_fn_idx = -1  # -1 = inactiu
        self.available_diatonic_fns = ['diatonic']
        self._diatonic_btn_press_time = 0.0
        # Mode debug (evitar prints per latència)
        self.debug = False
        
        # Obtenir escales (incloent progressions com IDs >= 1000) i modes d'arpegiador
        if self.config_manager:
            self.available_scales = self.config_manager.get_keyboard_scales()
            self.available_arp_modes = self.config_manager.get_arpeggiator_modes()
            self.available_keys = self.config_manager.get_keyboard_keys()
            self.btn_functions = self.config_manager.get_keyboard_button_functions()
            self.neg_harmony_type = self.config_manager.get_neg_harmony_type()
            self.available_neg_harm_ids = self.config_manager.get_neg_harmony_axes()
            # Obtenir funcions dels potenciòmetres (MODE TECLAT)
            pot_functions = self.config_manager.get_potentiometer_functions()
            self.pot_x_function = pot_functions.get('pot_x', 'Velocity/Arp Speed (dual)')
            self.pot_y_function = pot_functions.get('pot_y', 'Modulation (CC1)')
            self.pot_z_function = pot_functions.get('pot_z', 'Sustain (CC64)')
            # Obtenir funcions dels potenciòmetres (MODE ARPEGIADOR)
            # (Les capes de potes d'acords i d'harmonia negativa s'han retirat:
            #  només queden teclat i arpegiador — vegeu kbd_pots.update_parameters.)
            arp_pf = self.config_manager.get_arp_potentiometer_functions()
            self.arp_pot_x_function = arp_pf.get('arp_pot_x', 'Arp Speed (BPM)')
            self.arp_pot_y_function = arp_pf.get('arp_pot_y', 'Arp Pattern Selector')
            self.arp_pot_z_function = arp_pf.get('arp_pot_z', 'Gate Length')
            # Config àudio: mapatge dels potes per tecla amb 'synth_cfg'
            self.audio_pot_functions = self.config_manager.get_audio_potentiometer_functions()
            # Obtenir tipologies d'acord disponibles
            self.available_chord_types = self.config_manager.get_chord_types()
            self.available_diatonic_fns = self.config_manager.get_diatonic_functions()
            self.available_vl_types = self.config_manager.get_voice_lead_types()
            if self._vl_type_idx >= len(self.available_vl_types):
                self._vl_type_idx = 0
            self._vl_type = self.available_vl_types[self._vl_type_idx]
        else:
            self.btn_functions = (
                'note','note','note','note','note','note','note','note',
                'scale','tonality','chord','arp',
                'modes_layer','octave_down','octave_up','stop'
            )
        self._build_fn_mappings()
            
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
        self._scale_btn_press_time = 0.0
        self._key_btn_press_time = 0.0
        self._chord_last_release = 0.0
        self._arp_last_release = 0.0
        self._chord_just_activated = False
        self._arp_just_activated = False
        self._arp_pat_sel_last_val = None  # Tracking del pot per evitar sobreescriptura
        
        # Sustain PROGRESSIU (gestionat per TECLA, independent del synth): el pot fixa
        # el temps de release (quant ressonen les notes en deixar anar la tecla).
        #   sustain_release_time:  0 = release immediat | >0 = segons | -1 = indefinit (hold)
        #   _sustain_pending: {nota: off_time_monotonic | None(indefinit)} note-offs ajornats
        self.sustain_hold_enabled = False   # True només a release_time == -1 (compatibilitat)
        self.sustain_hold_value = 0  # Valor actual del potenciòmetre sustain (0-127)
        self.sustain_level = 0  # Nivell de sustain (0-127); >=64 => "actiu" (HUD, baking)
        self.sustain_release_time = 0.0
        self._sustain_pending = {}
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
        # Pre-carregar mòduls pesats ara que la memòria és lliure
        import gc; gc.collect()
        try:
            import modes.kbd_notes
            import modes.kbd_arp
            import modes.kbd_pots
        except Exception:
            pass
        gc.collect()
        self.stop_all_notes()
        self.active_notes.clear()
        
        # Preservar estat del Gate abans de recarregar configuracions
        self._previous_gate_enabled = self.gate_enabled
        self._previous_gate_period = self.gate_period
        
        # Recarregar configuracions (incloent funcions dels potenciòmetres)
        if self.config_manager:
            self.available_scales = self.config_manager.get_keyboard_scales()
            self.available_arp_modes = self.config_manager.get_arpeggiator_modes()
            self.available_keys = self.config_manager.get_keyboard_keys()
            if self.key_index >= len(self.available_keys):
                self.key_index = 0
            
            # Recarregar funcions dels botons + potenciòmetres (MODE TECLAT)
            self.btn_functions = self.config_manager.get_keyboard_button_functions()
            self.neg_harmony_type = self.config_manager.get_neg_harmony_type()
            self.available_neg_harm_ids = self.config_manager.get_neg_harmony_axes()
            self._build_fn_mappings()
            pot_functions = self.config_manager.get_potentiometer_functions()
            self.pot_x_function = pot_functions.get('pot_x', 'Velocity/Arp Speed (dual)')
            self.pot_y_function = pot_functions.get('pot_y', 'Modulation (CC1)')
            self.pot_z_function = pot_functions.get('pot_z', 'Sustain (CC64)')
            
            # Recarregar funcions dels potenciòmetres (MODE ARPEGIADOR)
            # (Capes d'acords i h.negativa retirades — només teclat i arpegiador.)
            arp_pot_functions = self.config_manager.get_arp_potentiometer_functions()
            self.arp_pot_x_function = arp_pot_functions.get('arp_pot_x', 'Arp Speed (BPM)')
            self.arp_pot_y_function = arp_pot_functions.get('arp_pot_y', 'Arp Pattern Selector')
            self.arp_pot_z_function = arp_pot_functions.get('arp_pot_z', 'Gate Length')
            # Config àudio: mapatge dels potes per tecla amb 'synth_cfg'
            self.audio_pot_functions = self.config_manager.get_audio_potentiometer_functions()
            # Recarregar tipologies d'acord disponibles
            self.available_chord_types = self.config_manager.get_chord_types()
            
        for i in range(15):
            self.button_notes[i].clear()
        
        # Restaurar estat del Gate després de recarregar
        if self._previous_gate_enabled:
            self.gate_enabled = self._previous_gate_enabled
            self.gate_period = self._previous_gate_period
            print(f"🎛️ Gate restaurat: enabled={self.gate_enabled}, period={self.gate_period:.2f}s")
        
        # IMPORTANT: Inicialitzar tots els CC MIDI a valors per defecte
        # Això assegura que no hi ha efectes residuals del sintetitzador
        try:
            for cc_num, default_value in self.cc_values.items():
                self.midi.send(ControlChange(cc_num, default_value))
        except Exception:
            pass
        
    def cleanup(self):
        """Neteja en sortir del mode"""
        # Silenciar el looper (les seves notes no són a active_notes i quedarien
        # penjades en destruir la instància en canviar de capa)
        self.pause_looper()
        # Aturar la base d'acompanyament (les seves notes van per canal propi)
        if self._accomp is not None:
            try:
                from modes.accompaniment import stop as _accomp_stop
                _accomp_stop(self)
            except Exception:
                pass
        self.stop_all_notes()
        self.active_notes.clear()
        for i in range(15):
            self.button_notes[i].clear()
        
        # Desactivar tots els CC al sortir
        try:
            self.midi.send(ControlChange(1, 0))   # Modulation OFF
            self.midi.send(ControlChange(64, 0))  # Sustain OFF
            self.midi.send(ControlChange(91, 0))  # Reverb OFF
            self.midi.send(ControlChange(93, 0))  # Chorus OFF
        except Exception:
            pass
        

        print("🎹 Mode Teclat desactivat")
        
    def pause_looper(self):
        """Pausa el looper i silencia les seves notes (cridat per l'STOP general).
        NO és dins stop_all_notes: l'arpegiador crida stop_all_notes a CADA pas
        i pausaria el loop a l'instant."""
        if self.loop_state:
            try:
                from modes.kbd_looper import pause_for_panic
                pause_for_panic(self)
            except Exception:
                pass

    def stop_all_notes(self):
        """Para totes les notes actives i neteja tot el tracking"""
        # Primer, desactivar sustain per assegurar que cap nota queda enganxada
        try:
            self.midi.send(ControlChange(64, 0))  # Sustain OFF (per si el synth en tenia)
            self.sustain_level = 0
        except Exception:
            pass
        self._sustain_pending = {}  # descarta els note-offs de sustain ajornats

        # Enviar NoteOff per totes les notes actives (missatge POOLED: zero
        # al·locacions — l'arpegiador passa per aquí a cada pas)
        from modes.base_mode import _note_off_msg
        off = _note_off_msg()
        off.velocity = 0
        off.channel = None
        for note in self.active_notes.copy():
            try:
                off.note = note
                self.midi.send(off)
            except Exception:
                pass

        # Netejar tots els trackings
        self.active_notes.clear()
        for i in range(15):
            self.button_notes[i].clear()

            
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

        # Alliberar les notes amb release de sustain ja vençut
        self._process_sustain_pending()

        # Processar els botons 1-15 com a notes/funcions del teclat
        self._process_keyboard_buttons(button_states[:15])

        # Motor del looper (només quan hi ha un loop reproduint-se)
        if self.loop_state == 3:  # PLAYING
            from modes.kbd_looper import tick
            tick(self, time.monotonic())

        # Rellotge de la base d'acompanyament (només si s'ha creat el motor)
        if self._accomp is not None:
            self._accomp.tick(time.monotonic())
            
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
        """Envia un CC MIDI al canal configurat"""
        self.cc_values[cc_num] = value
        try:
            self.midi.send(ControlChange(cc_num, value))
        except Exception:
            pass
    
    def _reapply_active_ccs(self):
        """Re-aplica tots els CC MIDI actius (útil després de stop_all_notes)"""
        try:
            for cc_num, value in self.cc_values.items():
                self.midi.send(ControlChange(cc_num, value))
        except Exception:
            pass
    
    def _send_pitch_bend(self, pitch_value):
        """Envia un PitchBend MIDI a tots els canals
        Args:
            pitch_value: Valor de pitch bend (-8192 a +8191, 0 = centrat)
        """
        # NOMÉS quan el valor canvia. Abans s'enviava a cada volta del bucle
        # (500 per segon amb el pot quiet): inundava la sortida USB-MIDI i les
        # notes sortien darrere de la cua — el "retard" que es notava tocant.
        if getattr(self, '_last_pitch_bend', None) == pitch_value:
            return
        self._last_pitch_bend = pitch_value

        try:
            self.midi.send(PitchBend(pitch_value))
        except Exception as e:
            if self.debug:
                print(f"Error enviant PitchBend: {e}")
            
    def _build_fn_mappings(self):
        from modes.kbd_buttons import build_fn_mappings
        build_fn_mappings(self)

    def _process_keyboard_buttons(self, button_states):
        from modes.kbd_buttons import process_keyboard_buttons
        process_keyboard_buttons(self, button_states)
        
    def _generate_notes_for_button(self, slot, btn_idx):
        from modes.kbd_notes import generate_notes_for_button
        generate_notes_for_button(self, slot, btn_idx)
    
    def _generate_chord_from_progression(self, slot, btn_idx, progression):
        from modes.kbd_notes import generate_chord_from_progression
        generate_chord_from_progression(self, slot, btn_idx, progression)
    
    def _generate_note_from_custom_scale(self, slot, btn_idx, custom_scale):
        from modes.kbd_notes import generate_note_from_custom_scale
        generate_note_from_custom_scale(self, slot, btn_idx, custom_scale)
    
    def _generate_chord_from_custom_scale(self, slot, btn_idx, custom_scale):
        from modes.kbd_notes import generate_chord_from_custom_scale
        generate_chord_from_custom_scale(self, slot, btn_idx, custom_scale)
    
    def _generate_chord_for_button(self, slot, btn_idx):
        from modes.kbd_notes import generate_chord_for_button
        generate_chord_for_button(self, slot, btn_idx)
    
    def _process_arpeggiator(self, button_states, current_time):
        from modes.kbd_arp import process_arpeggiator
        process_arpeggiator(self, button_states, current_time)
    
    def _get_arp_name(self, mode_index):
        from modes.kbd_arp import get_arp_name
        return get_arp_name(self, mode_index)

    def _play_arp_pattern(self, direction):
        from modes.kbd_arp import play_arp_pattern
        play_arp_pattern(self, direction)

    def _cycle_neg_harm_type(self, step):
        from modes.kbd_notes import cycle_neg_harm_type
        return cycle_neg_harm_type(self, step)

    def _reflect_note(self, note):
        from modes.kbd_notes import reflect_note
        return reflect_note(self, note)

    def _note_on(self, note, button_index):
        """Activa una nota amb la velocitat configurada.
        Si neg_harmony_active, aplica l'inversió simètrica abans d'enviar."""
        if self.neg_harmony_active:
            note = self._reflect_note(note)
        # Re-articulació: si la nota tenia un release ajornat (sustain), cancel·la'l.
        if self._sustain_pending:
            self._sustain_pending.pop(note, None)
        # Para qualsevol nota anterior d'aquest botó (només si no és arpeggiador)
        if button_index >= 0:
            self._note_off_for_button(button_index)
        
        # Envia NoteOn amb velocitat del potenciòmetre (missatge POOLED: una
        # al·locació aquí pot disparar un gc.collect de 10-40ms — el "no va
        # al toc" que se sent en directe)
        try:
            from modes.base_mode import _note_on_msg
            msg = _note_on_msg()
            msg.note = note
            msg.velocity = self.velocity
            msg.channel = None
            self.midi.send(msg)
            self.active_notes.add(note)
            if button_index >= 0:
                self.button_notes[button_index].add(note)
            elif self.loop_state:
                # Nota de l'arpegiador (button_index == -1): capturar-la al
                # looper si està armat/gravant — permet loopejar l'arp
                from modes.kbd_looper import record_live_note
                record_live_note(self, note, self.velocity, time.monotonic())
            

            # Testimoni per a la consola virtual de l'app: només amb consola
            # connectada (cost zero en directe) i mai per als passos de
            # l'arpegiador (button_index -1), que inundarien el monitor.
            if button_index >= 0:
                from modes.kbd_notes import _console_on, note_name
                if _console_on():
                    try:
                        print("♪ " + note_name(note))
                    except Exception:
                        pass
            
            # Gate funciona amb CC11 Expression, no necessita tracking de notes
            
            # Debug info (opcional per evitar latència)
            if self.debug:
                note_name = self._note_to_name(note)
                scale_name = f"Escala#{self.scale_mode}"
                key_name = self.available_keys[self.key_index]
                context = f"BTN{button_index+1}" if button_index >= 0 else "ARP"
                mode = "Acords" if self.chord_mode_active else ("Arp" if self.arp_mode_active else "Normal")
                print(f"🎵 {note_name} | {key_name} {scale_name} | {mode} | Vel:{self.velocity}")
            
        except Exception as e:
            print(f"Error enviant NoteOn: {e}")
            
    # Sustain SEGMENTAT: trams discrets i clarament perceptibles en girar el
    # pot (l'antiga corba quadràtica contínua feia difícil "trobar" un temps i
    # el tram d'infinit començava a 125 — molts pots físics no hi arriben amb
    # l'escalat de l'ADC, i l'infinit quedava inabastable). El tram es mostra
    # per consola quan canvia. (llindar_inferior, release_s, nom) — l'últim
    # tram (>=118) és hold INDEFINIT.
    SUSTAIN_ZONES = (
        (118, -1.0, 'Infinit'),
        (103, 8.0, 'Maxim (8s)'),
        (83, 5.0, 'Molt llarg (5s)'),
        (60, 2.5, 'Llarg (2.5s)'),
        (34, 1.2, 'Mig (1.2s)'),
        (8, 0.5, 'Curt (0.5s)'),
        (0, 0.0, 'OFF'),
    )

    def _set_sustain(self, pot_value):
        """Sustain per TRAMS (TECLA-side, sense CC64): el pot tria un tram de
        temps de release — OFF, 0.5s, 1.2s, 2.5s, 5s, 8s o INFINIT (hold).
        Re-ajusta els note-offs ja pendents perquè el pot respongui en directe
        (abaixar-lo escurça/atura les notes que ressonen)."""
        self.sustain_hold_value = pot_value
        self.sustain_level = pot_value
        # Histèresi de 2 passos: el soroll de l'ADC a la frontera d'un tram no
        # ha de fer parpellejar el tram (ni omplir la consola de prints).
        prev = getattr(self, '_sustain_pot_prev', None)
        if prev is not None and -2 < (pot_value - prev) < 2:
            pot_value = prev
        else:
            self._sustain_pot_prev = pot_value
        for llindar, rt, nom in self.SUSTAIN_ZONES:
            if pot_value >= llindar:
                if rt != self.sustain_release_time:
                    self.sustain_release_time = rt
                    self.sustain_hold_enabled = rt < 0
                    print("Sustain: %s" % nom)
                break
        if self._sustain_pending:
            rt = self.sustain_release_time
            if rt == 0.0:
                self._flush_sustain_pending()
            elif rt < 0:
                for n in self._sustain_pending:
                    self._sustain_pending[n] = None
            else:
                now = time.monotonic()
                for n in self._sustain_pending:
                    self._sustain_pending[n] = now + rt

    def _process_sustain_pending(self):
        """Envia els note-offs ajornats que ja han vençut (cridat des d'update)."""
        if not self._sustain_pending:
            return
        now = time.monotonic()
        due = [n for n, t in self._sustain_pending.items() if t is not None and now >= t]
        if not due:
            return
        from modes.base_mode import _note_off_msg
        off = _note_off_msg()
        off.velocity = 0
        off.channel = None
        for note in due:
            try:
                off.note = note
                self.midi.send(off)
            except Exception:
                pass
            self.active_notes.discard(note)
            self._sustain_pending.pop(note, None)

    def _flush_sustain_pending(self):
        """Atura immediatament totes les notes amb release ajornat."""
        from modes.base_mode import _note_off_msg
        off = _note_off_msg()
        off.velocity = 0
        off.channel = None
        for note in list(self._sustain_pending.keys()):
            try:
                off.note = note
                self.midi.send(off)
            except Exception:
                pass
            self.active_notes.discard(note)
        self._sustain_pending = {}

    def _note_off_for_button(self, button_index, from_release=False):
        """Para totes les notes associades a un botó específic
        
        Args:
            button_index: Índex del botó (0-11)
            from_release: True si ve d'alliberar el botó, False si ve de tocar una nova nota
        """
        # Sustain progressiu: en alliberar la tecla, els note-offs s'AJORNEN segons
        # sustain_release_time (indefinit si -1). Val per a notes, ACORDS i
        # harmonia negativa (des del tancament v3.1 el pot Z fa Sustain també
        # en aquests modes). NOMÉS l'arpegiador en queda fora: cada pas seu ja
        # gestiona els seus note-offs i el sustain hi faria una pasta de notes.
        # Les notes ajornades segueixen a active_notes (sonant) i s'alliberen
        # del botó; les atura update() via _process_sustain_pending. El loop NO
        # es veu afectat (gestiona les seves).
        if from_release and self.sustain_release_time != 0 and not self.arp_mode_active:
            notes_set = self.button_notes.get(button_index)
            if notes_set:
                off_t = None if self.sustain_release_time < 0 else (
                    time.monotonic() + self.sustain_release_time)
                for note in list(notes_set):
                    self._sustain_pending[note] = off_t
                notes_set.clear()
            return

        try:
            notes_set = self.button_notes.get(button_index, set())
            if not notes_set:
                return

            # Missatge POOLED: cap al·locació al camí calent (vegeu _note_on)
            from modes.base_mode import _note_off_msg
            off = _note_off_msg()
            off.velocity = 0
            off.channel = None
            for note in list(notes_set):
                try:
                    off.note = note
                    self.midi.send(off)
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
        
        # Enviar el valor de CC11 (Expression) segons l'estat. Amb
        # _send_cc_if_changed només surt a les transicions high/low (~20 per
        # segon amb període 0.1 s); amb _send_cc en sortien 500, i la resta
        # eren el mateix valor repetit tapant les notes.
        val = 127 if self.gate_high else self.gate_min_expr
        self._send_cc_if_changed(11, val, threshold=1)
    
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
        if getattr(self, '_accomp_active', False):
            from modes.accompaniment import sync_context
            sync_context(self)
            
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
                key_name = self.available_keys[self.key_index]
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
