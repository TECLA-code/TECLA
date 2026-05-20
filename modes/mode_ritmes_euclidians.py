"""
MODE RITMES EUCLIDIANS - Adaptat a BaseMode
Generació de ritmes euclidians amb melodies
"""

import time
import random
from modes.base_mode import BaseMode

class ModeRitmesEuclidians(BaseMode):
    """Mode que genera ritmes euclidians amb notes aleatòries"""
    
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Ritmes Euclidians"
        self.active_notes = set()
        self.position = 0
        self.melodia = [0] * 36
        self.last_step_time = 0
        self.current_note = None
        self.note_duration = 0.15
        self.current_pattern = []
        
    def setup(self):
        """Inicialitza l'estat del mode"""
        super().setup()
        self.stop_all_notes()
        self.active_notes.clear()
        self.position = 0
        self.last_step_time = time.monotonic()
        self.current_note = None
        print(f"🥁 {self.name} activat")
        
    def cleanup(self):
        """Neteja en sortir del mode"""
        self.stop_all_notes()
        print(f"🥁 {self.name} desactivat")
        
    def stop_all_notes(self):
        """Para totes les notes actives"""
        for note in list(self.active_notes):
            try:
                self.midi_out.send(self.note_off(note, 0))
            except:
                pass
        self.active_notes.clear()
    
    def generar_ritmo_euclideo(self, pulsos, pasos):
        """
        Genera un ritme euclidià
        
        Args:
            pulsos: Número de pols actius
            pasos: Longitud total del patró
            
        Returns:
            Llista amb el patró rítmic [1,0,1,0,...]
        """
        if pulsos > pasos:
            pulsos = pasos
        
        grupos = [[1] for _ in range(pulsos)] + [[0] for _ in range(pasos - pulsos)]
        
        while len(grupos) > 1:
            nuevos_grupos = []
            for i in range(0, len(grupos) // 2):
                nuevos_grupos.append(grupos[i] + grupos[-(i + 1)])
            if len(grupos) % 2 == 1:
                nuevos_grupos.append(grupos[len(grupos) // 2])
            grupos = nuevos_grupos
        
        return [item for sublist in grupos for item in sublist]
        
    def update(self, pot_values, button_states):
        """
        Actualització principal del mode
        
        Args:
            pot_values: [x, y, z] valors 0-127
            button_states: Estat dels botons
        """
        super().update(pot_values, button_states)
        
        if len(pot_values) < 3:
            return
            
        x, y, z = pot_values[0], pot_values[1], pot_values[2]
        current_time = time.monotonic()
        
        # X controla velocitat temporal
        tempo = max(0.05, x / 127.0 * 0.5)
        
        # Aturar nota actual si ha passat prou temps
        if self.current_note is not None:
            if current_time - self.last_step_time >= self.note_duration:
                try:
                    self.midi_out.send(self.note_off(self.current_note, 0))
                    self.active_notes.discard(self.current_note)
                except:
                    pass
                self.current_note = None
        
        # Avançar al següent pas si ja ha passat el tempo
        if current_time - self.last_step_time >= tempo:
            # Y = número de pulsos (0-36)
            pulsos = int((y / 127.0) * 36)
            
            # Z = longitud del patró (0-36)
            pasos = int((z / 127.0) * 36) + 1  # +1 per evitar 0
            
            # Generar ritme euclidià
            ritmo = self.generar_ritmo_euclideo(pulsos, pasos)
            self.current_pattern = ritmo
            
            # Gestió de posició
            if self.position >= len(ritmo):
                self.position = 0
            
            # Obtenir activació del patró
            to = ritmo[self.position]
            
            # Tocar nota si el ritme ho indica
            if to == 1:
                # Nota amb variació aleatòria
                octava = 2
                nota = 0 + (octava * 12) + random.randint(-3, 3)
                nota = max(0, min(127, nota))
                
                try:
                    self.midi_out.send(self.note_on(nota, 100))
                    self.active_notes.add(nota)
                    self.current_note = nota
                    print(f"🥁 Nota: {nota} | Pos: {self.position}/{len(ritmo)}")
                except Exception as e:
                    print(f"Error tocant nota: {e}")
            else:
                print(f"🥁 --- Silenci | Pos: {self.position}/{len(ritmo)}")
            
            self.position += 1
            self.last_step_time = current_time
        
        return {
            'note': self.current_note,
            'position': self.position,
            'pattern_length': len(self.current_pattern) if self.current_pattern else 0
        }

# Informació del mode
MODE_INFO = {
    'name': 'Ritmes Euclidians',
    'description': 'Generació de ritmes euclidians amb melodies aleatòries',
    'potentiometer_x': 'Velocitat temporal',
    'potentiometer_y': 'Número de pulsos',
    'potentiometer_z': 'Longitud del patró'
}
