"""
Animación Sinusoidal para TECLA
Visualización basada en ondas sinusoidales
"""
import math
import displayio
from core.animations.base import BaseAnimation

class SinusoidalAnimation(BaseAnimation):
    """
    Animación basada en ondas sinusoidales.
    Muestra patrones ondulatorios que responden a los potenciómetros.
    """
    
    def __init__(self, display_manager):
        super().__init__(display_manager)
        self.width = display_manager.width
        self.height = display_manager.height
        
    def render(self, pot_values):
        """
        Renderiza ondas sinusoidales en la pantalla.
        
        Args:
            pot_values: Valores de los potenciómetros (0-127)
            - pot_values[0]: Amplitud de la onda
            - pot_values[1]: Frecuencia de la onda
            - pot_values[2]: Fase de la onda
        """
        # Limpiar pantalla
        self.display_manager.clear()
        self.elements = []
        
        # Parámetros por defecto
        amplitude = 15  # Amplitud máxima
        frequency = 0.1  # Frecuencia base
        phase = 0       # Fase inicial
        
        # Ajustar parámetros según potenciómetros
        if pot_values and len(pot_values) >= 3:
            amplitude = 5 + (pot_values[0] / 127) * 20  # Escalar entre 5-25
            frequency = 0.05 + (pot_values[1] / 127) * 0.2  # Escalar entre 0.05-0.25
            phase = (pot_values[2] / 127) * math.pi * 2  # Escalar entre 0-2π
        
        # Crear bitmap para la onda
        bitmap = displayio.Bitmap(self.width, self.height, 2)
        palette = displayio.Palette(2)
        palette[0] = 0x000000  # Negro (fondo)
        palette[1] = 0xFFFFFF  # Blanco (onda)
        
        # Dibujar múltiples ondas sinusoidales
        # Primera onda - basada en seno
        for x in range(self.width):
            y = int(self.height/2 + amplitude * math.sin(frequency * x + phase + self.frame * 0.1))
            if 0 <= y < self.height:
                bitmap[x, y] = 1
                
        # Segunda onda - basada en coseno con parámetros ligeramente diferentes
        for x in range(self.width):
            y = int(self.height/2 + amplitude * 0.6 * math.cos(frequency * 1.5 * x + phase * 0.7 + self.frame * 0.08))
            if 0 <= y < self.height:
                bitmap[x, y] = 1
        
        # Crear TileGrid y añadirlo
        wave_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
        self.display_manager.splash.append(wave_grid)
        self.elements.append(wave_grid)
        
        # Actualizar el display
        self.display_manager.display.refresh()
        
        # Incrementar frame para animar
        self.frame += 1
        
    def get_update_interval(self):
        """
        Intervalo de actualización para este modo
        """
        return 100  # 10 FPS, animación fluida
