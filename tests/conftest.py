"""Configuració comuna dels tests TECLA.

Els tests s'executen al Mac amb CPython, sense dispositiu: els mòduls de
maquinari de CircuitPython (board, digitalio, adafruit_midi...) se substitueixen
pels mocks del simulador web (codi/py/tecla_mocks.py), que són els mateixos que
fa servir Pyodide al navegador.

Execució:  python3 -m pytest
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE_FILES = os.path.join(ROOT, 'codi', 'device_files')
PY_DIR = os.path.join(ROOT, 'codi', 'py')

# La font canònica (device_files) és el que es testeja: ha d'anar PRIMER al
# path perquè el paquet `modes` es resolgui a device_files/modes (69 mòduls) i
# no a py/modes (la còpia parcial del simulador). PY_DIR només aporta tecla_mocks.
sys.path.insert(0, PY_DIR)
sys.path.insert(0, DEVICE_FILES)

import tecla_mocks

# El bridge MIDI cap a JS no existeix fora de Pyodide: stub silenciós
tecla_mocks._js_midi_send = lambda *args, **kwargs: None
tecla_mocks.install_mocks()


class FakeMidiOut:
    """Sortida MIDI que captura els missatges enviats, per a assercions."""

    def __init__(self):
        self.sent = []

    def send(self, msg):
        self.sent.append(msg)
