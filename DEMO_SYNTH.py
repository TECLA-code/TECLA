
import time
import board
import usb_midi
# from adafruit_midi import MIDI # Use generic import if needed, but TECLA usually imports specific messages in header
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

# TECLA_BLOCKS_EMBEDDED_JSON = '''{"blocks":{"languageVersion":0,"blocks":[{"type":"tecla_repeat_forever","id":"loop","x":50,"y":50,"inputs":{"DO":{"block":{"type":"tecla_oscillator","id":"osc","fields":{"WAVEFORM":"SAWTOOTH"},"inputs":{"FREQUENCY":{"shadow":{"type":"math_number","fields":{"NUM":"440"}}},"AMPLITUDE":{"shadow":{"type":"math_number","fields":{"NUM":"127"}}}},"next":{"block":{"type":"tecla_lfo","id":"lfo","fields":{"WAVEFORM":"SINE","TARGET":"PITCH"},"inputs":{"RATE":{"shadow":{"type":"math_number","fields":{"NUM":"5"}}},"DEPTH":{"shadow":{"type":"math_number","fields":{"NUM":"80"}}}},"next":{"block":{"type":"tecla_play_note","id":"note1","inputs":{"NOTE":{"shadow":{"type":"math_number","fields":{"NUM":"50"}}},"VELOCITY":{"shadow":{"type":"math_number","fields":{"NUM":"127"}}},"DURATION":{"shadow":{"type":"math_number","fields":{"NUM":"0.5"}}}}}}}}}}}}]}}'''

def main():
    pass

if __name__ == "__main__":
    main()
