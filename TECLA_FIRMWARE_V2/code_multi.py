"""
TECLA Launcher - Sistema Multi-Slot
Permet seleccionar entre TECLA i múltiples projectes TECLA Blocks

Configuració inicial:
1. Renombra el code.py de TECLA → tecla_main.py
2. Copia aquest fitxer com a code.py
3. Llest!

Selecció de Mode:
- Sense prémer res → TECLA Normal
- Botó 16 (long press 1.5s) → Projecte Blocks #1
- Botó 15 (long press 1.5s) → Projecte Blocks #2
- Botó 14 (long press 1.5s) → Projecte Blocks #3
- Botó 13 (long press 1.5s) → Projecte Blocks #4
"""
import board
import digitalio
import time

# Configuració dels botons selectors
BUTTONS = {
    16: {'pin': board.GP14, 'file': 'tecla_blocks_1.py', 'name': 'Projecte 1'},
    15: {'pin': board.GP13, 'file': 'tecla_blocks_2.py', 'name': 'Projecte 2'},
    14: {'pin': board.GP12, 'file': 'tecla_blocks_3.py', 'name': 'Projecte 3'},
    13: {'pin': board.GP11, 'file': 'tecla_blocks_4.py', 'name': 'Projecte 4'}
}

# Configuració del long press
LONG_PRESS_DURATION = 1.5  # segons
CHECK_INTERVAL = 0.1  # comprova cada 100ms

# LED per feedback visual
try:
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    has_led = True
except:
    has_led = False

def setup_buttons():
    """Configura tots els botons com a inputs"""
    buttons = {}
    for btn_num, config in BUTTONS.items():
        btn = digitalio.DigitalInOut(config['pin'])
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.DOWN
        buttons[btn_num] = btn
    return buttons

def check_long_press(button):
    """Comprova si un botó es manté premut durant LONG_PRESS_DURATION"""
    if not button.value:
        return False  # No està premut
    
    # Botó premut, comptar temps
    start_time = time.monotonic()
    
    # Animació visual durant la comprovació
    while time.monotonic() - start_time < LONG_PRESS_DURATION:
        if not button.value:
            # Botó alliberat abans de temps
            if has_led:
                led.value = False
            return False
        
        # Piscar LED durant la comprovació
        if has_led:
            led.value = not led.value
        
        time.sleep(CHECK_INTERVAL)
    
    # Si arriba aquí, és un long press vàlid
    if has_led:
        led.value = True  # Deixar LED encès
    return True

def blink_error():
    """Animació d'error"""
    if has_led:
        for _ in range(10):
            led.value = True
            time.sleep(0.1)
            led.value = False
            time.sleep(0.1)
    while True:
        time.sleep(1)

def run_module(module_name):
    """Importa i executa el mòdul especificat"""
    try:
        print(f"Carregant {module_name}...")
        mod = __import__(module_name.replace('.py', ''))
        
        # Si el mòdul té una funció main(), l'executem
        if hasattr(mod, 'main'):
            print(f"Executant {module_name}.main()...")
            mod.main()
        else:
            print(f"Nota: {module_name} importat (sense funció main)")
            
    except ImportError as e:
        print(f"\n⚠️  ERROR: {module_name} no trobat")
        print(f"   Detalls: {e}\n")
        blink_error()
    except Exception as e:
        print(f"\n⚠️  ERROR EXECUTANT {module_name}:")
        print(f"{e}\n")
        blink_error()

def select_mode():
    """Selecciona quin mode/projecte executar"""
    print("\n" + "="*40)
    print("🎮 TECLA LAUNCHER - Multi-Slot")
    print("="*40)
    print("\nOpcions disponibles:")
    print("  [Cap botó] → TECLA Normal")
    
    for btn_num, config in BUTTONS.items():
        print(f"  [Botó {btn_num}] → {config['name']}")
    
    print("\nEsperant selecció (long press 1.5s)...")
    
    # Configurar botons
    buttons_io = setup_buttons()
    
    # Comprovar cada botó
    for btn_num, button_io in buttons_io.items():
        if check_long_press(button_io):
            # Long press detectat en aquest botó
            config = BUTTONS[btn_num]
            print(f"\n✅ {config['name']} seleccionat")
            run_module(config['file'])
            return
    
    # Cap botó premut → Mode TECLA normal
    print("\n✅ TECLA Normal seleccionat")
    if has_led:
        led.value = False
    
    run_module('tecla_main.py')

# Executar selector
if __name__ == "__main__":
    select_mode()
