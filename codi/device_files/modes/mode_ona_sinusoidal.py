"""
Mode Sinusoidal - Genera ones sinusoidals modulables amb efectes de rizado
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeOnaSinusoidal(BaseMode):
    PARAMS = ('Nota base', 'Amplitud', 'Freqüència', 'Força', 'Quantització')
    POTS = ('Nota base', 'Amplitud', 'Freqüència')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Sinusoidal"
        self.phase = 0.0
        self.last_update = time.monotonic()
        self.notes_playing = set()
        self.base_frequency = 220.0  # Hz (A3)
        self.current_note = None
        self.mod_amount = 0.5
        self.mod_freq = 5.5
        self.forca = 80
        self.quantitza = False

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Nota base':
            self.base_frequency = 55.0 + f * 880.0   # aprox. A1 a A6
        elif nom == 'Amplitud':
            self.mod_amount = f
        elif nom == 'Freqüència':
            self.mod_freq = 0.5 + f * 10.0            # de 0,5 Hz a 10,5 Hz
        elif nom == 'Força':
            self.forca = 20 + int(f * 107)
        elif nom == 'Quantització':
            self.quantitza = f >= 0.5
        else:
            return False
        return True

    def setup(self):
        self.initialized = True
        self.phase = 0.0
        self.last_update = time.monotonic()
        self.notes_playing = set()
        self.current_note = None
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        self.potes(pot_values)
        mod_amount = self.mod_amount
        mod_freq = self.mod_freq
        
        # Calcular la fase actual amb modulació
        mod = math.sin(self.phase * mod_freq * 2 * math.pi) * mod_amount
        current_freq = self.base_frequency * (1.0 + mod)
        
        # Actualitzar fase
        self.phase += dt
        if self.phase >= 1.0:
            self.phase -= 1.0
        
        # Convertir freqüència a nota MIDI (12 semitons per octava, 69 = A4 = 440Hz)
        # Utilitzem logaritme natural i canvi de base per compatibilitat amb MicroPython
        note_num = 12 * (math.log(current_freq / 440.0) / math.log(2)) + 69
        note_num = max(0, min(127, int(round(note_num))))
        if self.quantitza:                        # a la pentatònica: de sirena a música
            pc = note_num % 12
            for d in (0, -1, 1, -2, 2):
                if (pc + d) % 12 in (0, 2, 4, 7, 9):
                    note_num = max(0, min(127, note_num + d))
                    break
        
        # Si la nota ha canviat, actualitzar
        if self.current_note != note_num:
            # Aturar nota anterior
            if self.current_note is not None:
                self.midi_out.send(self.note_off(self.current_note, 0))
                self.notes_playing.discard(self.current_note)
            
            # Reproduir nova nota
            velocity = self.forca
            self.midi_out.send(self.note_on(note_num, velocity))
            self.notes_playing.add(note_num)
            self.current_note = note_num
        
        return {
            'freq': current_freq,
            'note': note_num,
            'mod_amount': mod_amount,
            'mod_freq': mod_freq
        }
    
    def cleanup(self):
        for note in list(self.notes_playing):
            self.midi_out.send(self.note_off(note, 0))
        self.notes_playing.clear()
        if self.current_note is not None:
            self.midi_out.send(self.note_off(self.current_note, 0))
            self.current_note = None
