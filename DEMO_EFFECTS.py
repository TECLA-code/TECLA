
import time
import board
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
import random

# TECLA_BLOCKS_EMBEDDED_JSON = '''{"blocks":{"languageVersion":0,"blocks":[{"type":"tecla_repeat_forever","id":"loop","x":50,"y":50,"inputs":{"DO":{"block":{"type":"tecla_set_instrument","id":"instr1","fields":{"INSTRUMENT":"25"},"next":{"block":{"type":"tecla_set_pan","id":"pan_left","inputs":{"PAN":{"shadow":{"type":"math_number","fields":{"NUM":"10"}}}},"next":{"block":{"type":"tecla_play_note","id":"note1","inputs":{"NOTE":{"shadow":{"type":"math_number","fields":{"NUM":"60"}}},"VELOCITY":{"shadow":{"type":"math_number","fields":{"NUM":"100"}}},"DURATION":{"shadow":{"type":"math_number","fields":{"NUM":"0.5"}}}},"next":{"block":{"type":"tecla_set_pan","id":"pan_right","inputs":{"PAN":{"shadow":{"type":"math_number","fields":{"NUM":"110"}}}},"next":{"block":{"type":"tecla_play_note","id":"note2","inputs":{"NOTE":{"shadow":{"type":"math_number","fields":{"NUM":"64"}}},"VELOCITY":{"shadow":{"type":"math_number","fields":{"NUM":"100"}}},"DURATION":{"shadow":{"type":"math_number","fields":{"NUM":"0.5"}}}}}}}}}}}}}}}}]}}'''

def main():
    pass # Codi placeholder, serà regenerat

if __name__ == "__main__":
    main()
