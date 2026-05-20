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
            # Tocar escala C major des de C
            midi.send(NoteOn(60, 100))
            time.sleep(0.3)
            midi.send(NoteOff(60, 0))
            midi.send(NoteOn(62, 100))
            time.sleep(0.3)
            midi.send(NoteOff(62, 0))
            midi.send(NoteOn(64, 100))
            time.sleep(0.3)
            midi.send(NoteOff(64, 0))
            midi.send(NoteOn(65, 100))
            time.sleep(0.3)
            midi.send(NoteOff(65, 0))
            midi.send(NoteOn(67, 100))
            time.sleep(0.3)
            midi.send(NoteOff(67, 0))
            midi.send(NoteOn(69, 100))
            time.sleep(0.3)
            midi.send(NoteOff(69, 0))
            midi.send(NoteOn(71, 100))
            time.sleep(0.3)
            midi.send(NoteOff(71, 0))
            midi.send(NoteOn(72, 100))
            time.sleep(0.3)
            midi.send(NoteOff(72, 0))
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
# TECLA_BLOCKS_EMBEDDED_JSON = '''{"blocks":{"languageVersion":0,"blocks":[{"type":"tecla_repeat_forever","id":"loop_scale","x":50,"y":50,"inputs":{"DO":{"block":{"type":"tecla_play_scale","id":"scale_c","fields":{"SCALE":"major","ROOT":"C"}}}}}]}}'''
# ==========================================
