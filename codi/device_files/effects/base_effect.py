"""
BaseEffect - Interfície comuna per a tots els efectes temporals del TECLA
"""
from adafruit_midi.control_change import ControlChange

class BaseEffect:
    def __init__(self, midi_out):
        self.midi = midi_out
        self.name = self.__class__.__name__.replace('Effect', '')

    def on_activate(self):
        """S'executa quan l'efecte s'activa"""
        pass

    def on_deactivate(self):
        """S'executa quan l'efecte es desactiva"""
        pass

    def update_params(self, x=0, y=0, z=0):
        """Actualitza paràmetres de l'efecte en temps real"""
        pass
