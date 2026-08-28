"""
LayerManager - Gestiona les diferents capes (layers) del TECLA
Permet canviar entre la capa principal i la capa de teclat
"""
import time

class LayerManager:
    """Gestor de capes per al controlador TECLA"""
    
    def __init__(self, mode_manager=None):
        """Inicialitza el gestor de capes"""
        # Referències a altres components
        self.mode_manager = mode_manager
        
        # Definicions de botons
        self.keyboard_layer_button = 12  # Botó 13 (índex 12) activa capa de teclat
        self.return_button = 15          # Botó 16 (índex 15) torna a capa principal
        self.effect_buttons = [13, 14]   # Botons 14-15 (índex 13-14) per a efectes
        
        # Gestió de capes
        self.current_layer = 'main'      # 'main' o 'teclat'
        self.previous_mode = None        # Mode anterior abans de canviar de capa
        
        # Control del temps per evitar rebots
        self.last_layer_change_time = 0
        self.debounce_time = 0.2         # 200ms per a debounce en els canvis de capa
        
    def set_mode_manager(self, mode_manager):
        """Assigna una referència al gestor de modes"""
        self.mode_manager = mode_manager
        
    def is_button_in_current_layer(self, button_index):
        """
        Determina si un botó està actiu a la capa actual
        Retorna: True si el botó s'ha de processar a la capa actual
        """
        # Els botons d'efecte (14 i 15) sempre estan actius
        if button_index in self.effect_buttons:
            return True
            
        # El botó de retorn (16) sempre està actiu
        if button_index == self.return_button:
            return True
            
        # El botó de capa de teclat (13) està actiu a la capa principal
        if button_index == self.keyboard_layer_button and self.current_layer == 'main':
            return True
            
        # Botons 1-12 (índexs 0-11) estan actius a ambdues capes
        if 0 <= button_index <= 11:
            return True
            
        return False
        
    def change_layer(self, layer_name):
        """Canvia a la capa especificada"""
        if layer_name not in ['main', 'teclat']:
            print(f"Capa no vàlida: {layer_name}")
            return False
            
        if layer_name == self.current_layer:
            return True  # Ja estem en aquesta capa
            
        print(f"Canviant a la capa: {layer_name}")
        current_time = time.monotonic()
        
        # Comprovar debounce
        if (current_time - self.last_layer_change_time) < self.debounce_time:
            return False
            
        self.last_layer_change_time = current_time
        
        # Canviar la capa sense modificar el ModeManager
        if layer_name == 'teclat':
            # Només canvia l'estat de la capa; el mode teclat es gestiona a main.py
            self.previous_mode = self.mode_manager.current_mode_name if self.mode_manager else None
        elif layer_name == 'main' and self.current_layer == 'teclat':
            # No cal canviar de mode aquí; main.py ja surt del mode teclat
            pass
        
        self.current_layer = layer_name
        return True
        
    def process_layer_buttons(self, button_states):
        """
        Processa els botons relacionats amb el canvi de capa
        Retorna: True si s'ha produït un canvi de capa, False si no
        """
        if not button_states or len(button_states) <= max(self.keyboard_layer_button, self.return_button):
            return False
            
        layer_changed = False
        
        # Botó 13 (índex 12) - Activa capa de teclat des de la capa principal
        if (self.current_layer == 'main' and 
                button_states[self.keyboard_layer_button] and 
                self.is_button_in_current_layer(self.keyboard_layer_button)):
            print(f"Botó 13: Activant capa 'teclat'")
            layer_changed = self.change_layer('teclat')
            
        # Botó 16 (índex 15) - Torna a la capa principal
        elif (self.current_layer == 'teclat' and 
                button_states[self.return_button] and 
                self.is_button_in_current_layer(self.return_button)):
            print(f"Botó 16: Tornant a capa 'main'")
            layer_changed = self.change_layer('main')
            
        return layer_changed
