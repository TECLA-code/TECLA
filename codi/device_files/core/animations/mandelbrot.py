"""
Animación Mandelbrot para TECLA
Visualización basada en el conjunto fractal de Mandelbrot
"""
import math
import displayio
from core.animations.base import BaseAnimation

class MandelbrotAnimation(BaseAnimation):
    """
    Animación basada en el conjunto de Mandelbrot simplificado.
    Versión dinámica y visual para TECLA.
    """
    
    def __init__(self, display_manager):
        super().__init__(display_manager)
        self.max_iter = 15  # Límite de iteraciones (bajo para rendimiento)
        self.zoom = 1.0
        self.center_x = -0.5
        self.center_y = 0.0
        self.width = display_manager.width
        self.height = display_manager.height
        self.frame = 0
        self.orbit_radius = 30
        self.orbit_speed = 0.05
        
    def render(self, pot_values):
        """
        Renderiza una visualización dinámica inspirada en fractales.
        
        Args:
            pot_values: Valores de los potenciómetros (0-127)
            - pot_values[0]: Controla la densidad y forma del patrón
            - pot_values[1]: Controla la velocidad de rotación
            - pot_values[2]: Controla el comportamiento ondulatorio
        """
        # Limpiar pantalla
        self.display_manager.clear()
        self.elements = []
        
        # Ajustar parámetros según potenciómetros
        if pot_values and len(pot_values) >= 3:
            density = 1 + (pot_values[0] / 127) * 10     # 1-11 puntos por brazo
            self.orbit_speed = 0.02 + (pot_values[1] / 127) * 0.1  # Velocidad de rotación
            wave_factor = 0.5 + (pot_values[2] / 127) * 2.0  # Factor ondulatorio
        else:
            density = 5
            wave_factor = 1.0
        
        # Crear bitmap para dibujar el patrón
        bitmap = displayio.Bitmap(self.width, self.height, 2)
        palette = displayio.Palette(2)
        palette[0] = 0x000000  # Negro (fondo)
        palette[1] = 0xFFFFFF  # Blanco (patrón)
        
        # Parámetros de la animación
        center_x = self.width // 2
        center_y = self.height // 2
        num_arms = 5  # Brazos del patrón
        
        # Dibujar un patrón dinámico orbital
        for arm in range(num_arms):
            angle_offset = arm * (2 * math.pi / num_arms)
            
            # Cada brazo tiene un patrón ondulatorio
            for i in range(int(density * 5)):
                r = i * 2.5  # Radio
                
                # Aplicar efectos de onda y rotación
                angle = angle_offset + self.frame * self.orbit_speed
                angle += math.sin(i * 0.2 * wave_factor) * 0.3
                
                # Calcular posición
                x = int(center_x + r * math.cos(angle))
                y = int(center_y + r * math.sin(angle))
                
                # Dibujar punto si está dentro del área visible
                if 0 <= x < self.width and 0 <= y < self.height:
                    bitmap[x, y] = 1
                    
                    # Añadir efecto dinámico adicional - trazas
                    trail_length = 3
                    for t in range(1, trail_length):
                        trail_angle = angle - t * 0.1
                        tx = int(center_x + r * math.cos(trail_angle))
                        ty = int(center_y + r * math.sin(trail_angle))
                        if 0 <= tx < self.width and 0 <= ty < self.height:
                            bitmap[tx, ty] = 1
        
        # Crear TileGrid y añadirlo
        pattern_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
        self.display_manager.splash.append(pattern_grid)
        self.elements.append(pattern_grid)
        
        # Actualizar el display
        self.display_manager.display.refresh()
        
        # Incrementar el contador de frames para animación continua
        self.frame += 1
        
    def get_update_interval(self):
        """
        Intervalo de actualización para la animación dinámica
        """
        return 100  # 10 FPS para mayor fluidez
