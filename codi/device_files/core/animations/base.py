"""
BaseAnimation - Clase base para animaciones en TECLA
Define la interfaz común y funcionalidades básicas para todas las animaciones
"""
import time
import displayio
import terminalio
from adafruit_display_text import label

class BaseAnimation:
    """
    Clase base para todas las animaciones de TECLA.
    Cada modo debe implementar su propia subclase con visualizaciones únicas.
    """
    
    def __init__(self, display_manager):
        """
        Inicializa la animación con el gestor de display proporcionado.
        
        Args:
            display_manager: Instancia del DisplayManager para controlar la pantalla
        """
        self.display_manager = display_manager
        self.frame = 0
        self.last_update = time.monotonic()
        self.elements = []  # Elementos visuales de esta animación
        
    def update(self, pot_values):
        """
        Actualiza el estado interno de la animación basado en los potenciómetros.
        
        Args:
            pot_values: Lista de valores de los potenciómetros (0-127)
            
        Returns:
            bool: True si es necesario renderizar
        """
        current_time = time.monotonic()
        # Reducimos la frecuencia de actualización para minimizar el parpadeo
        # Aumentando el intervalo mínimo entre actualizaciones
        if current_time - self.last_update >= self.get_update_interval() / 1000:
            self.last_update = current_time
            return True
        return False
        
    def render(self, pot_values):
        """
        Renderiza la animación en la pantalla.
        
        Args:
            pot_values: Lista de valores de los potenciómetros (0-127)
        """
        self.display_manager.clear()
        
        # La animación específica se implementa en las subclases
        # No mostramos texto de nombre de modo ni valores de potenciómetros
        # siguiendo la solicitud del usuario
        
        # Actualizar la pantalla
        self.display_manager.display.refresh()
        
    def get_update_interval(self):
        """
        Devuelve el intervalo de actualización en milisegundos.
        
        Returns:
            int: Intervalo en milisegundos entre actualizaciones de la animación
        """
        return 250  # Por defecto, 4 fps
        
    def cleanup(self):
        """
        Limpia los recursos utilizados por la animación.
        """
        self.elements = []
