"""
Programa generat amb TECLA Blocks
Creat per programació visual amb blocs
"""

import time
import board
import usb_midi
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

# Inicialitzar MIDI
midi = MIDI(midi_out=usb_midi.ports[1])

# Variables globals
current_octave = 4
button_states = [False] * 16
last_button_states = [False] * 16
pot_values = [0, 0, 0]

# Funció principal
def main():
    """Programa principal"""
    print("Iniciant programa TECLA Blocks...")
    
    try:
        # Repetir per sempre
        while True:
            # Quan es prem botó 1
            if button_states[0] and not last_button_states[0]:
                midi.send(NoteOn(60, 100))
                time.sleep(0.2)
                midi.send(NoteOff(60, 0))
            
            # Quan es prem botó 2
            if button_states[1] and not last_button_states[1]:
                midi.send(NoteOn(62, 100))
                time.sleep(0.2)
                midi.send(NoteOff(62, 0))

            time.sleep(0.05)  # Petit delay per evitar bloqueig

    except KeyboardInterrupt:
        print("\nPrograma aturat per l'usuari")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Aturar totes les notes
        for note in range(128):
            midi.send(NoteOff(note, 0))
        print("Programa finalitzat")

if __name__ == "__main__":
    main()

# ==========================================
# TECLA BLOCKS DATA (DO NOT EDIT BELOW)
# ==========================================
# TECLA_BLOCKS_EMBEDDED_JSON = '''{"blocks":{"languageVersion":0,"blocks":[{"type":"tecla_repeat_forever","id":"loop1","x":50,"y":50,"inputs":{"DO":{"block":{"type":"controls_if","id":"if1","inputs":{"IF0":{"block":{"type":"tecla_read_button","id":"btn1","fields":{"BUTTON":"1"}}},"DO0":{"block":{"type":"tecla_play_note","id":"play1","fields":{"NOTE":"60","VELOCITY":100,"DURATION":0.2},"next":{"block":{"type":"controls_if","id":"if2","inputs":{"IF0":{"block":{"type":"tecla_read_button","id":"btn2","fields":{"BUTTON":"2"}}},"DO0":{"block":{"type":"tecla_play_note","id":"play2","fields":{"NOTE":"62","VELOCITY":100,"DURATION":0.2}}}}}}}}}}}}}]}}'''
# ==========================================
