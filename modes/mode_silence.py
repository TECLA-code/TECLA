"""
Mode Silenci - Mode buit per botons sense assignar
"""

class ModeSilence:
    """Mode que no fa res - per botons sense assignar"""
    
    def __init__(self, midi_out=None):
        """Inicialitza el mode silenci"""
        self.midi = midi_out
        self.name = "Silenci"
    
    def start(self):
        """No fa res"""
        pass
    
    def stop(self):
        """No fa res"""
        pass
    
    def update(self, *args, **kwargs):
        """No fa res - accepta qualsevol argument"""
        pass
    
    def button_pressed(self, button_index):
        """No fa res"""
        pass
    
    def button_released(self, button_index):
        """No fa res"""
        pass
