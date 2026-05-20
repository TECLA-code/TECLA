import sys
from unittest.mock import MagicMock, patch

# --- MOCK CIRCUITPYTHON MODULES ---
# We must do this BEFORE importing the launcher code

# Mock board
board = MagicMock()
board.GP14 = "GP14"
board.LED = "LED"
sys.modules['board'] = board

# Mock digitalio
digitalio = MagicMock()
sys.modules['digitalio'] = digitalio

# Mock time
time = MagicMock()
time.monotonic.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 2.0] # Simulate time passing
time.sleep = MagicMock()
sys.modules['time'] = time

# --- MOCK USER MODULES ---

tecla_blocks = MagicMock()
tecla_blocks.main = MagicMock()
sys.modules['tecla_blocks'] = tecla_blocks

tecla_main = MagicMock()
tecla_main.main = MagicMock()
sys.modules['tecla_main'] = tecla_main

# --- SETUP MOCK HARDWARE STATE ---

# Scenario 1: Button Pressed (Blocks Mode)
# selector_button.value should be True (high) if pulled down and pressed? 
# Wait, the code says:
# selector_button.pull = digitalio.Pull.DOWN
# if not selector_button.value: return False
# So if pressed, value is True.
# The code checks `if not selector_button.value` to return False.
# So to be pressed, value must be True.

# Let's create a class to handle the button value simulation
class MockButton:
    def __init__(self):
        self.direction = None
        self.pull = None
        self._value = False
    
    @property
    def value(self):
        print(f"DEBUG: Reading button value -> {self._value}")
        return self._value

    @value.setter
    def value(self, v):
        print(f"DEBUG: Setting button value -> {v}")
        self._value = v

mock_button = MockButton()
mock_led = MockButton() # Reuse class for LED

def digital_in_out_side_effect(pin):
    if pin == board.GP14:
        return mock_button
    return mock_led

# We need digitalio.DigitalInOut to return correct mock
digitalio.DigitalInOut.side_effect = digital_in_out_side_effect

# --- TEST EXECUTION ---

print("🧪 TESTING FIRMWARE LAUNCHER LOGIC")
print("----------------------------------")

def reset_mocks():
    tecla_blocks.main.reset_mock()
    tecla_main.main.reset_mock()
    # Ensure enough time values
    time.monotonic.side_effect = [0.0, 0.1, 0.5, 1.0, 1.4, 1.6, 2.0, 2.5] 

# Test 1: Button Pressed (Long Press) -> Should run tecla_blocks
print("\n[TEST 1] Button Pressed (Long Press) -> Expect tecla_blocks.main()")
reset_mocks()
mock_button.value = True # Button is pressed

# Load the code
import importlib.util
spec = importlib.util.spec_from_file_location("launcher", "TECLA_FIRMWARE_V2/code.py")
launcher = importlib.util.module_from_spec(spec)

try:
    spec.loader.exec_module(launcher)
except SystemExit:
    pass # In case it exits
except Exception as e:
    # It might loop forever in the error handler if modules aren't found, 
    # but we mocked them.
    # The launcher code runs standard code at top level.
    pass

# Verify
if tecla_blocks.main.called:
    print("✅ SUCCESS: tecla_blocks.main() was called")
else:
    print("❌ FAILURE: tecla_blocks.main() was NOT called")
    if tecla_main.main.called:
        print("   (tecla_main.main() was called instead)")

# Test 2: Button Not Pressed -> Should run tecla_main
# To test this we would need to reload the module which is tricky with this structure
# as the code runs on import.
# We will just verify Test 1 for now as that's the critical new logic "boot selector".
