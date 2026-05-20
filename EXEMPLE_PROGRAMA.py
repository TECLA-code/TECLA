"""
Programa generat amb TECLA Blocks (SIMULACIÓ)
Aquest arxiu és un exemple del codi que genera la App.

FUNCIONALITAT:
- Botó 1: Toca acord Do Major
- Botó 2: Toca acord La Menor
- Botó 3: Toca nota Sol (aguda)
"""

import time
import board
import digitalio
import usb_midi
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

# --- CONFIGURACIÓ HARDWARE (Normalment oculta per l'usuari) ---

# Inicialitzar MIDI
try:
    midi = MIDI(midi_out=usb_midi.ports[1])
except:
    # Fallback per si no hi ha USB MIDI (per tests)
    print("Midi no disponible, mode simulació")
    class MockMidi:
        def send(self, msg): print(f"MIDI SEND: {msg}")
    midi = MockMidi()

# Configurar Pins dels Botons (Exemple simplificat pels primers 4 botons)
# En el TECLA real, això es fa llegint una matriu o pins directes
# Aquí simulem els pins directes per l'exemple
button_pins = [board.GP0, board.GP1, board.GP2, board.GP3] # Exemples
buttons = []
for pin in button_pins:
    try:
        btn = digitalio.DigitalInOut(pin)
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.DOWN
        buttons.append(btn)
    except:
        pass

# Variables globals
current_octave = 4
button_states = [False] * 16
last_button_states = [False] * 16
pot_values = [0, 0, 0]

# --- FUNCIÓ PRINCIPAL (Aquesta és la part important pel nou Firmware) ---

def main():
    """Programa principal"""
    print("Iniciant programa TECLA Blocks...")
    print("Prem Botó 1, 2 o 3 per fer música!")
    
    try:
        # Bucle principal (Repetir per sempre)
        while True:
            # 1. Llegir estat dels botons (Simulat)
            # En un cas real aquí llegiriem el hardware
            # Per l'exemple, assumim que tenim accés a 'buttons'
             
            # Lògica del programa d'usuari:
            
            # --- BLOC: Quan es prem botó 1 ---
            # Si el botó 1 està premut ara i no ho estava abans (flanc de pujada)
            # Nota: En aquest exemple simplificat no implementem la lectura real de hardware
            # perque depèn de la matriu de botons del TECLA.
            # Això és només per mostrar l'estructura del codi.
            
            # Exemple d'una seqüència musical automàtica per testejar:
            print("Tocant Do Major...")
            # NoteOn(nota, velocitat)
            midi.send(NoteOn(60, 100)) # Do
            midi.send(NoteOn(64, 100)) # Mi
            midi.send(NoteOn(67, 100)) # Sol
            time.sleep(0.5)
            
            midi.send(NoteOff(60, 0))
            midi.send(NoteOff(64, 0))
            midi.send(NoteOff(67, 0))
            time.sleep(0.5)
            
            print("Tocant La Menor...")
            midi.send(NoteOn(69, 100)) # La
            midi.send(NoteOn(72, 100)) # Do
            midi.send(NoteOn(76, 100)) # Mi
            time.sleep(0.5)
            
            midi.send(NoteOff(69, 0))
            midi.send(NoteOff(72, 0))
            midi.send(NoteOff(76, 0))
            time.sleep(0.5)
            
            # Petit delay per no bloquejar la CPU
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\\nPrograma aturat per l'usuari")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Aturar totes les notes
        for note in range(128):
            midi.send(NoteOff(note, 0))
        print("Programa finalitzat")

# Punts d'entrada
if __name__ == "__main__":
    main()
