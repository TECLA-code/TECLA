"""
MODE NEWTON-RAPHSON - Adaptat a BaseMode
Generació de notes basades en iteracions del mètode de Newton-Raphson
"""

import time
import random
from modes.base_mode import BaseMode

class ModeNewtonRaphson(BaseMode):
    """Mode que genera notes basades en el mètode de Newton-Raphson"""
    
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Newton-Raphson"
        self.active_notes = set()
        self.last_note_time = 0
        self.current_note = None
        self.note_duration = 0.2
        
    def setup(self):
        """Inicialitza l'estat del mode"""
        super().setup()
        self.stop_all_notes()
        self.active_notes.clear()
        self.last_note_time = time.monotonic()
        self.current_note = None
        print(f"🔢 {self.name} activat")
        
    def cleanup(self):
        """Neteja en sortir del mode"""
        self.stop_all_notes()
        print(f"🔢 {self.name} desactivat")
        
    def stop_all_notes(self):
        """Para totes les notes actives"""
        for note in list(self.active_notes):
            try:
                self.midi_out.send(self.note_off(note, 0))
            except:
                pass
        self.active_notes.clear()
    
    def midi_newton_iterations(self, input_value):
        """
        Calcula iteracions del mètode de Newton-Raphson
        
        Args:
            input_value: Valor entre 0-127
            
        Returns:
            Nombre d'iteracions normalitzat a 0-127
        """
        x0 = input_value / 127  # Escalar a 0-1
        
        # Funció: x^2 - 2 = 0
        f = lambda x: x**2 - 2
        df = lambda x: 2 * x
        
        tolerance = 1e-6
        max_iterations = 127
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            if df(x0) == 0:
                break
            x1 = x0 - f(x0) / df(x0)
            if abs(x1 - x0) < tolerance:
                break
            x0 = x1
        
        return int((iterations / max_iterations) * 127)
    
    def scale_with_randomness(self, input_value):
        """Escala un valor amb aleatorietat"""
        if not (0 <= input_value <= 15):
            input_value = 10
        
        scaled_value = (input_value / 15) * 127
        random_adjustment = random.uniform(-10, 10)
        adjusted_value = scaled_value + random_adjustment
        
        return max(0, min(127, int(adjusted_value)))
        
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
            if current_time - self.last_note_time >= self.note_duration:
                try:
                    self.midi_out.send(self.note_off(self.current_note, 0))
                    self.active_notes.discard(self.current_note)
                except:
                    pass
                self.current_note = None
        
        # Tocar nova nota si ja ha passat el tempo
        if current_time - self.last_note_time >= tempo:
            # Generar input aleatori basat en Y i Z
            input_value = random.uniform(min(y, z), max(y, z))
            input_value = max(0, min(127, input_value))
            
            # Calcular iteracions Newton-Raphson
            salida = self.midi_newton_iterations(int(input_value))
            escalada_newton = self.scale_with_randomness(salida)
            
            # Tocar nota
            try:
                self.midi_out.send(self.note_on(escalada_newton, 100))
                self.active_notes.add(escalada_newton)
                self.current_note = escalada_newton
                self.last_note_time = current_time
                print(f"🔢 Nota Newton-Raphson: {escalada_newton} (iter: {salida})")
            except Exception as e:
                print(f"Error tocant nota: {e}")
        
        return {
            'note': self.current_note,
            'tempo': tempo
        }

# Informació del mode
MODE_INFO = {
    'name': 'Newton-Raphson',
    'description': 'Generació de notes basades en iteracions del mètode de Newton-Raphson',
    'potentiometer_x': 'Velocitat temporal',
    'potentiometer_y': 'Límit rang càlcul',
    'potentiometer_z': 'Límit rang càlcul'
}
