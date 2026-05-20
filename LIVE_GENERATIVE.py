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
import random

# Inicialitzar MIDI
midi = MIDI(midi_out=usb_midi.ports[1])

# Variables globals
current_octave = 4

# Funció principal
def main():
    """Programa principal"""
    print("Iniciant Mode Generatiu...")
    
    try:
        # Repetir per sempre
        while True:
            # Nota aleatòria entre 48 (C3) i 84 (C6)
            note = random.randint(48, 84)
            velocity = random.randint(60, 110)
            duration = random.uniform(0.1, 0.4)
            
            midi.send(NoteOn(note, velocity))
            time.sleep(duration)
            midi.send(NoteOff(note, 0))
            
            # Temps entre notes
            time.sleep(random.uniform(0.05, 0.2))

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
# TECLA_BLOCKS_EMBEDDED_JSON = '''{"blocks":{"languageVersion":0,"blocks":[{"type":"tecla_repeat_forever","id":"gen_loop","x":50,"y":50,"inputs":{"DO":{"block":{"type":"tecla_play_note","id":"rand_note","inputs":{"NOTE":{"shadow":{"type":"math_number","fields":{"NUM":"60"}},"block":{"type":"tecla_math_random_int","id":"rand_val","inputs":{"FROM":{"shadow":{"type":"math_number","fields":{"NUM":"48"}}},"TO":{"shadow":{"type":"math_number","fields":{"NUM":"84"}}}}}},"VELOCITY":{"shadow":{"type":"math_number","fields":{"NUM":"100"}}},"DURATION":{"shadow":{"type":"math_number","fields":{"NUM":"0.2"}}}},"next":{"block":{"type":"tecla_wait","id":"wait_rand","inputs":{"TIME":{"shadow":{"type":"math_number","fields":{"NUM":"0.1"}}}}}}}}}}]}}'''
# ==========================================
