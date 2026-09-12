"""
Mode Dinamo - Genera un drone ambient modular amb múltiples harmònics
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeDinamo(BaseMode):
    PARAMS = ('Nota base', 'Brillantor', 'Velocitat de la respiració', 'Profunditat', 'Veus', 'Dispersió de les veus')
    POTS = ('Nota base', 'Brillantor', 'Velocitat de la respiració')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Dinamo"
        self.notes_playing = set()
        self.harmonics = [
            {'note': 0, 'vel': 0, 'phase': 0.0, 'freq_mult': 1.0},
            {'note': 0, 'vel': 0, 'phase': 0.0, 'freq_mult': 2.0},
            {'note': 0, 'vel': 0, 'phase': 0.0, 'freq_mult': 3.0},
        ]
        self.base_note = 48  # C3
        self.last_update = time.monotonic()
        self.intensity = 0.7
        self.mod_speed = 0.6
        self.profunditat = 0.5        # quant es mou el volum de cada harmònic
        self.veus = 3
        self.dispersio = 1.0          # fases: 0 = totes alhora, 1 = repartides

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Nota base':
            new_base_note = 36 + int(f * 24)
            if new_base_note != self.base_note:
                self.base_note = new_base_note
                self._update_harmonics(self.base_note)
        elif nom == 'Brillantor':
            self.intensity = f
        elif nom == 'Velocitat de la respiració':
            self.mod_speed = 0.1 + f * 2.0
        elif nom == 'Profunditat':
            self.profunditat = 0.1 + f * 0.9
        elif nom == 'Veus':
            self.veus = 1 + min(2, int(f * 3))
        elif nom == 'Dispersió de les veus':
            self.dispersio = f
            self._update_harmonics(self.base_note)
        else:
            return False
        return True

    def setup(self):
        self.initialized = True
        self.last_update = time.monotonic()
        self.notes_playing = set()
        # Inicialitzar harmònics
        self._update_harmonics(self.base_note)
        
    def _update_harmonics(self, base_note):
        """Actualitza les notes dels harmònics basant-se en la nota base"""
        for i, h in enumerate(self.harmonics):
            # Calcula la nota de l'harmònic (afegint intervals justos per a millor harmonia)
            # Utilitzem logaritme natural i canvi de base per compatibilitat amb MicroPython
            note_offset = int(12 * (math.log(h['freq_mult']) / math.log(2)))
            h['note'] = base_note + note_offset
            h['vel'] = int(80 / (i + 1))  # Els harmònics superiors sonen més suaus
            h['phase'] = random.random() * self.dispersio  # Fase aleatòria per a un so més orgànic
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        self.potes(pot_values)
        intensity = self.intensity
        mod_speed = self.mod_speed
        
        # Actualitzar fases i modulació
        for i, h in enumerate(self.harmonics):
            if i >= self.veus:
                if h['note'] in self.notes_playing:
                    self.midi_out.send(self.note_off(h['note'], 0))
                    self.notes_playing.discard(h['note'])
                continue
            # Modulació de volum basada en el temps i la fase
            mod = (math.sin(current_time * mod_speed + h['phase'] * 2 * math.pi) + 1) * 0.5
            vel = int(h['vel'] * intensity * (1.0 - self.profunditat + self.profunditat * mod))
            
            # Si la velocitat és massa baixa, aturem la nota
            if vel < 10:
                if h['note'] in self.notes_playing:
                    self.midi_out.send(self.note_off(h['note'], 0))
                    self.notes_playing.discard(h['note'])
            else:
                # Actualitzar la nota si no està sonant o si la velocitat ha canviat significativament
                if h['note'] not in self.notes_playing or abs(vel - h.get('last_vel', 0)) > 5:
                    if h['note'] in self.notes_playing:
                        self.midi_out.send(self.note_off(h['note'], 0))
                    self.midi_out.send(self.note_on(h['note'], vel))
                    self.notes_playing.add(h['note'])
                    h['last_vel'] = vel
        
        return {
            'base_note': self.base_note,
            'intensity': intensity,
            'mod_speed': mod_speed,
            'active_notes': len(self.notes_playing)
        }
    
    def cleanup(self):
        for note in list(self.notes_playing):
            self.midi_out.send(self.note_off(note, 0))
        self.notes_playing.clear()
