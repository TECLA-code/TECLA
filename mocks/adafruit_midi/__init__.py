# Mock de adafruit_midi
import sys
import json
import time

# Comunicació amb el procés pare (Node.js)
def send_to_app(type, data):
    msg = {"type": type, "data": data}
    print(json.dumps(msg), flush=True)

class MIDI:
    def __init__(self, midi_out=None, out_channel=0, **kwargs):
        self.channel = out_channel

    def send(self, msg, channel=None):
        # Quan l'usuari fa midi.send(), ho capturem aquí
        # msg és un objecte NoteOn, NoteOff, etc.
        
        # Simulem l'enviament JSON a l'App
        message_data = {
            "type": msg.__class__.__name__,
            "note": getattr(msg, "note", 0),
            "velocity": getattr(msg, "velocity", 0),
            "value": getattr(msg, "value", 0), # ControlChange
            "control": getattr(msg, "control", 0),
            "patch": getattr(msg, "patch", 0), # ProgramChange
            "channel": channel if channel is not None else self.channel
        }
        
        send_to_app("midi_event", message_data)
        
        # També hem d'enviar al port REAL via mido (gestionat pel wrapper extern? No, ho fem aquí directament si cal)
        # O millor: Enviem JSON a l'App -> App envia a Proxy -> Proxy envia a Port Real.
        # Això té latencia.
        # MILLOR OPCIÓ: Aquest mock també pot usar `mido` directament si sap quin port usar!
        # Per ara, enviem a stdout i deixem que el 'runner' ho gestioni.

# Classes missatges
class NoteOn:
    def __init__(self, note, velocity):
        self.note = note
        self.velocity = velocity

class NoteOff:
    def __init__(self, note, velocity=0):
        self.note = note
        self.velocity = velocity


class ControlChange:
    def __init__(self, control, value):
        self.control = control
        self.value = value

from .program_change import ProgramChange
