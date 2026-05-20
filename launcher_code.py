"""
TECLA Launcher - Selector de mode amb Long Press
Executa TECLA o TECLA Blocks segons Botó 16 (long press)

Configuració inicial:
1. Renombra el code.py de TECLA → tecla_main.py
2. Copia aquest fitxer com a code.py
3. Llest!

Ús:
- Encendre normalment → TECLA
- Mantenir Botó 16 durant 1.5s + Encendre → TECLA Blocks
  (El LED piscarà durant la comprovació)

Nota: Igual que el Botó 13 per canviar de banc, es fa servir long press
per evitar canvis accidentals de mode.
"""
import board
import digitalio
import time

# Configuració del botó selector (Botó 16 - GP14)
selector_button = digitalio.DigitalInOut(board.GP14)
selector_button.direction = digitalio.Direction.INPUT
selector_button.pull = digitalio.Pull.DOWN

# LED per indicar mode (opcional)
try:
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    has_led = True
except:
    has_led = False

# Configuració del long press
LONG_PRESS_DURATION = 1.5  # segons (igual que botó 13 per banc)
CHECK_INTERVAL = 0.1  # comprova cada 100ms

def check_long_press():
    """Comprova si el Botó 16 es manté premut durant LONG_PRESS_DURATION"""
    if not selector_button.value:
        return False  # No està premut
    
    # Botó premut, comptar temps
    start_time = time.monotonic()
    
    # Animació visual durant la comprovació
    while time.monotonic() - start_time < LONG_PRESS_DURATION:
        if not selector_button.value:
            # Botó alliberat abans de temps
            return False
        
        # Piscar LED durant la comprovació (feedback visual)
        if has_led:
            led.value = not led.value
        
        time.sleep(CHECK_INTERVAL)
    
    # Si arriba aquí, és un long press vàlid
    if has_led:
        led.value = True  # Deixar LED encès
    return True

# Seleccionar mode amb long press
if check_long_press():
    # Mode TECLA Blocks (Botó 16 premut)
    print("\n" + "="*40)
    print("🟢 TECLA BLOCKS MODE")
    print("="*40)
    
    if has_led:
        # LED encès = Mode Blocks
        led.value = True
    
    try:
        import tecla_blocks
    except ImportError as e:
        print("\n⚠️  ERROR: tecla_blocks.py no trobat")
        print("Puja un programa des de TECLA Blocks primer")
        print(f"Detalls: {e}\n")
        while True:
            time.sleep(1)
            
else:
    # Mode TECLA Normal (per defecte)
    print("\n" + "="*40)
    print("🎵 TECLA MODE")
    print("="*40)
    
    if has_led:
        # LED apagat = Mode TECLA
        led.value = False
    
    try:
        import tecla_main
    except ImportError as e:
        print("\n⚠️  ERROR: tecla_main.py no trobat")
        print("Renombra code.py → tecla_main.py primer")
        print(f"Detalls: {e}\n")
        while True:
            time.sleep(1)
