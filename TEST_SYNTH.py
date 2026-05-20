
import time
import board
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange

# Inicialització del sistema MIDI
midi = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1],
    out_channel=0
)

print("--- INICI TEST SÍNTESI ---")

# 1. Provar canvi d'instrument (Violí = 40)
print("Canviant a Violí...")
midi.send(ProgramChange(40))
time.sleep(1)

# 2. Provar Pan (Esquerra -> Centre -> Dreta)
print("Provant Panning...")
midi.send(ControlChange(10, 0))   # Esquerra
time.sleep(0.5)
midi.send(ControlChange(10, 64))  # Centre
time.sleep(0.5)
midi.send(ControlChange(10, 127)) # Dreta
time.sleep(0.5)

# 3. Provar Volum
print("Provant Volum...")
midi.send(ControlChange(7, 50))   # Baix
time.sleep(0.5)
midi.send(ControlChange(7, 127))  # Alt
time.sleep(0.5)

print("--- TEST FINALITZAT ---")
