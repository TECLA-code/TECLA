
import subprocess
import json
import time
import sys
import os

# The Python code we expect generated from the Instrument blocks
CODE_TO_TEST = """
import time
import board
import usb_midi
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
import random

# Mocking MIDI port for standalone test if needed, but midi_proxy sets mocks via PYTHONPATH
# midi_proxy handles the env, so we just write the code.

midi = MIDI(midi_out=usb_midi.ports[1])

def main():
    print("DEBUG: Script starting...")
    try:
        print("DEBUG: Sending ProgramChange...")
        midi.send(ProgramChange(25))
        time.sleep(0.5)
        print("DEBUG: ProgramChange sent.")
    except Exception as e:
        print(f"DEBUG: Error in script: {e}")

if __name__ == "__main__":
    main()
"""

def run_test():
    print("--- STARTING BACKEND TEST ---")
    
    # Start midi_proxy.py
    proc = subprocess.Popen(
        ["python3", "midi_proxy.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0 # Unbuffered
    )
    
    # Read initial ready message
    print("Waiting for ready...")
    ready_line = proc.stdout.readline()
    print(f"PROXY SAYS: {ready_line.strip()}")
    
    # Send run_script command
    cmd = {
        "command": "run_script",
        "code": CODE_TO_TEST
    }
    
    print("Sending run_script command...")
    proc.stdin.write(json.dumps(cmd) + "\n")
    proc.stdin.flush()
    
    # Read output for 5 seconds
    start_time = time.time()
    while time.time() - start_time < 5:
        line = proc.stdout.readline()
        if line:
            print(f"OUTPUT: {line.strip()}")
        else:
            time.sleep(0.1)
            
    # Cleanup
    print("Terminating...")
    proc.terminate()

if __name__ == "__main__":
    run_test()
