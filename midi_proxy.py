import sys
import json
import mido
import threading
import time

# Variables globals
current_port = None
running = True

def send_response(data):
    """Envia resposta JSON al procés Node.js"""
    print(json.dumps(data), flush=True)

import os
import subprocess

# Variables globals
current_port = None
running = True
script_process = None

def send_response(data):
    """Envia resposta JSON al procés Node.js"""
    print(json.dumps(data), flush=True)

def kill_script():
    global script_process
    if script_process:
        try:
            script_process.terminate()
            script_process.wait(timeout=0.5)
        except:
            try: script_process.kill() 
            except: pass
        script_process = None

def run_user_script(code):
    global script_process
    
    kill_script()
    
    try:
        # Guardar codi a fitxer temporal
        # Use directory of this script (midi_proxy.py) as base
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, "temp_script.py")
        with open(script_path, "w") as f:
            f.write(code)
            
        # Preparar entorn amb mocks
        env = os.environ.copy()
        mocks_path = os.path.join(base_dir, "mocks")
        
        # Afegir mocks al PYTHONPATH
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = mocks_path + os.pathsep + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = mocks_path
            
        # Executar subprocess
        # -u per unbuffered output
        script_process = subprocess.Popen(
            ["python3", "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=True,
            bufsize=1
        )
        
        # Fil per llegir stdout del script
        def reader_thread():
            while script_process and script_process.poll() is None:
                line = script_process.stdout.readline()
                if line:
                    try:
                        # Si és JSON del mock midi, el processem
                        data = json.loads(line)
                        if data.get("type") == "midi_event":
                            # 1. Enviar a l'App (Visualitzador)
                            send_response(data)
                            
                            # 2. Enviar a Port Real (si connectat)
                            if current_port:
                                evt = data["data"]
                                msg_type = evt.get("type")
                                if msg_type == "NoteOn":
                                    msg = mido.Message('note_on', note=evt["note"], velocity=evt["velocity"])
                                    current_port.send(msg)
                                elif msg_type == "NoteOff":
                                    msg = mido.Message('note_off', note=evt["note"], velocity=evt["velocity"])
                                    current_port.send(msg)
                                elif msg_type == "ControlChange":
                                    msg = mido.Message('control_change', control=evt["control"], value=evt["value"])
                                    current_port.send(msg)
                                elif msg_type == "ProgramChange":
                                    msg = mido.Message('program_change', program=evt["patch"])
                                    current_port.send(msg)
                        else:
                            # Altre JSON?
                            print("SCRIPT_JSON:", line.strip(), file=sys.stderr)
                    except json.JSONDecodeError:
                        # Text normal (print de l'usuari)
                        send_response({"type": "console_log", "message": line.strip()})
                else:
                    break
        
        t = threading.Thread(target=reader_thread, daemon=True)
        t.start()
        
        send_response({"type": "script_started"})
        
    except Exception as e:
        send_response({"type": "error", "message": f"Run Error: {e}"})


def handle_command(cmd_data):
    global current_port
    
    command = cmd_data.get("command")
    
    if command == "list_ports":
        try:
            ports = mido.get_output_names()
            clean_ports = list(set(ports)) 
            send_response({"type": "ports_list", "ports": clean_ports})
        except Exception as e:
            send_response({"type": "error", "message": str(e)})

    elif command == "connect":
        port_name = cmd_data.get("port")
        try:
            if current_port:
                current_port.close()
                current_port = None
            
            if port_name:
                current_port = mido.open_output(port_name)
                send_response({"type": "connected", "port": port_name})
            else:
                send_response({"type": "disconnected"})
        except Exception as e:
            send_response({"type": "error", "message": str(e)})

    elif command == "run_script":
        code = cmd_data.get("code")
        run_user_script(code)

    elif command == "stop_script":
        kill_script()
        # Panic MIDI
        if current_port:
            for n in range(128): current_port.send(mido.Message('note_off', note=n))
        send_response({"type": "script_stopped"})

    elif command == "send":
        # Legacy manual send (ja no s'usa tant si executem scripts)
        msg_bytes = cmd_data.get("message")
        try:
            if current_port and len(msg_bytes) == 3:
                msg = mido.Message.from_bytes(msg_bytes)
                current_port.send(msg)
        except: pass


def main():
    send_response({"type": "ready", "message": "Python MIDI Proxy Started"})
    
    while running:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
                
            try:
                cmd_data = json.loads(line)
                handle_command(cmd_data)
            except json.JSONDecodeError:
                pass
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            send_response({"type": "error", "message": f"Bridge Error: {e}"})

if __name__ == "__main__":
    main()
