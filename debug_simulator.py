import os
import sys
import subprocess

# Add mocks to pythonpath
cwd = os.getcwd()
mocks_path = os.path.join(cwd, "mocks")
env = os.environ.copy()
env["PYTHONPATH"] = mocks_path

print(f"PYTHONPATH: {env['PYTHONPATH']}")

cmd = ["python3", "-u", "LIVE_GENERATIVE.py"]

print("Running subprocess...")
try:
    p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Read first 10 lines
    for i in range(10):
        line = p.stdout.readline()
        if line:
            print(f"STDOUT: {line.strip()}")
        err = p.stderr.readline()
        if err:
            print(f"STDERR: {err.strip()}")
            
    p.kill()
except Exception as e:
    print(f"Error: {e}")
