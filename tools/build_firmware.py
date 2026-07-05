#!/usr/bin/env python3
"""
build_firmware.py - Construeix el firmware TECLA optimitzat per a l'app-web.

Que fa:
  1. Compila a .mpy (amb mpy-cross -O2) totes les fonts .py de codi/device_files/
     EXCEPTE els fitxers que han de quedar com a font: boot.py, main.py, reset.py
     i tots els __init__.py.
  2. Regenera codi/device_files_manifest.json perque referenciï els .mpy compilats
     (i els .py mantinguts, els .json, i els .mpy de tercers ja existents).
  3. Elimina .mpy obsolets (sense .py font corresponent) generats per builds antics,
     conservant els .mpy de tercers (lib/adafruit_hid) que no tenen font .py.

Resultat: l'app-web (Firmware -> Instal·lar) desplega el firmware optimitzat .mpy,
amb el pic de compilacio eliminat i menys ocupacio de disc.

Requereix: tools/mpy-cross (binari de CircuitPython compatible amb el device).
Us: python3 tools/build_firmware.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF = os.path.join(ROOT, "codi", "device_files")
MPY = os.environ.get("MPY_CROSS", os.path.join(ROOT, "tools", "mpy-cross"))
MANIFEST = os.path.join(ROOT, "codi", "device_files_manifest.json")

# Fitxers .py que NO es compilen (queden com a font al dispositiu)
KEEP_PY = {"boot.py", "main.py", "reset.py"}

# Brossa a ignorar sempre
SKIP_NAMES = {".DS_Store", "README.md", ".VolumeIcon.icns", "boot_out.txt",
              "tecla_config.json", "tecla_icon.png", "tecla_version.txt"}
SKIP_EXTS = (".pyc", ".bak", ".crswap")


def is_kept_py(fname):
    return fname in KEEP_PY or fname == "__init__.py"


def should_skip(fname):
    if fname in SKIP_NAMES:
        return True
    if fname.startswith(".") or fname.startswith("._"):
        return True
    if any(fname.endswith(e) for e in SKIP_EXTS):
        return True
    return False


def main():
    if not (os.path.isfile(MPY) and os.access(MPY, os.X_OK)):
        sys.exit(f"ERROR: no trobo mpy-cross executable a {MPY}")
    try:
        ver = subprocess.check_output([MPY, "--version"], text=True).strip()
    except Exception as e:
        sys.exit(f"ERROR executant mpy-cross: {e}")
    print(f"mpy-cross: {ver}")

    # ── 1. Compilar .py -> .mpy ──────────────────────────────────────────────
    compiled = 0
    failed = []
    compiled_py_paths = set()   # rel paths de .py que tenen .mpy
    for root, dirs, fnames in os.walk(DF):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".vscode")
                   and not d.startswith(".")]
        for f in sorted(fnames):
            if not f.endswith(".py") or is_kept_py(f) or should_skip(f):
                continue
            src = os.path.join(root, f)
            out = src[:-3] + ".mpy"
            try:
                subprocess.run([MPY, "-O2", src, "-o", out],
                               check=True, capture_output=True, text=True)
                compiled += 1
                compiled_py_paths.add(os.path.relpath(src, DF))
            except subprocess.CalledProcessError as e:
                failed.append((os.path.relpath(src, DF), e.stderr.strip()))

    if failed:
        print(f"\nERRORS DE COMPILACIO ({len(failed)}):")
        for rel, err in failed:
            print(f"  x {rel}: {err}")
        sys.exit("AVORTAT: arregla els errors abans de generar el manifest.")
    print(f"Compilats: {compiled} .mpy")

    # ── 2. Eliminar .mpy obsolets (sense .py font) generats per nosaltres ────
    #     Conservem els .mpy de tercers que NO tenen .py (lib/adafruit_hid).
    removed = 0
    for root, dirs, fnames in os.walk(DF):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".vscode")
                   and not d.startswith(".")]
        for f in sorted(fnames):
            if not f.endswith(".mpy"):
                continue
            mpy_path = os.path.join(root, f)
            py_path = mpy_path[:-4] + ".py"
            rel_py = os.path.relpath(py_path, DF)
            # Si NO existeix el .py i NO es un .mpy compilat ara per nosaltres,
            # pero SI esta dins un paquet on hi havia .py (heuristica): el deixem
            # si es tercer. Considerem tercer nomes lib/adafruit_hid.
            if not os.path.isfile(py_path):
                rel_mpy = os.path.relpath(mpy_path, DF)
                if rel_mpy.startswith("lib/adafruit_hid/"):
                    continue  # vendored, conservar
                os.remove(mpy_path)
                removed += 1
    if removed:
        print(f"Eliminats {removed} .mpy obsolets")

    # ── 3. Generar manifest ──────────────────────────────────────────────────
    files = []
    for root, dirs, fnames in os.walk(DF):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", ".vscode")
                         and not d.startswith("."))
        for f in sorted(fnames):
            if should_skip(f):
                continue
            rel = os.path.relpath(os.path.join(root, f), DF)
            if f.endswith(".py"):
                if is_kept_py(f):
                    files.append(rel)            # font mantinguda
                elif rel in compiled_py_paths:
                    files.append(rel[:-3] + ".mpy")  # referenciar el .mpy
                else:
                    files.append(rel)            # .py sense compilar (rar)
            elif f.endswith(".mpy"):
                # nomes afegir si NO prove d'un .py ja afegit com a .mpy
                rel_py = rel[:-4] + ".py"
                if rel_py in compiled_py_paths:
                    continue  # ja afegit via el seu .py
                files.append(rel)                # tercer (adafruit_hid) o solt
            else:
                files.append(rel)                # .json i altres assets

    files = sorted(set(files))
    with open(MANIFEST, "w") as fh:
        json.dump({"files": files}, fh, indent=2)
    print(f"Manifest: {len(files)} fitxers -> {os.path.relpath(MANIFEST, ROOT)}")
    print("FET.")


if __name__ == "__main__":
    main()
