#!/usr/bin/env python3
"""sync_simulator.py - Sincronitza la còpia del simulador web des de la font canònica.

FONT ÚNICA DE VERITAT: codi/device_files/ (el que corre al dispositiu).
codi/py/ és una CÒPIA GENERADA que el simulador web (Pyodide) carrega via fetch:
  - py/modes/<mode>.py      <- device_files/modes/<mode>.py  (només els ja presents a py/)
  - py/base_mode.py          <- device_files/modes/base_mode.py
  - py/modes/base_mode.py    <- device_files/modes/base_mode.py

NO editis mai els fitxers de py/ a mà: qualsevol canvi s'ha de fer a
device_files/ i propagar-se amb aquest script (dev.sh el crida automàticament).

Ús:
  python3 tools/sync_simulator.py            # sincronitza
  python3 tools/sync_simulator.py --check    # només comprova (exit 1 si divergeix)
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE_MODES = os.path.join(ROOT, "codi", "device_files", "modes")
PY_DIR = os.path.join(ROOT, "codi", "py")
PY_MODES = os.path.join(PY_DIR, "modes")


def sync_pairs():
    """Retorna llista de (origen, destí) a mantenir sincronitzats."""
    pairs = []
    base_src = os.path.join(DEVICE_MODES, "base_mode.py")
    pairs.append((base_src, os.path.join(PY_DIR, "base_mode.py")))
    pairs.append((base_src, os.path.join(PY_MODES, "base_mode.py")))
    # Tots els .py que ja existeixen a py/modes/ i tenen font a device_files/modes/
    for fname in sorted(os.listdir(PY_MODES)):
        if not fname.endswith(".py") or fname == "base_mode.py":
            continue
        src = os.path.join(DEVICE_MODES, fname)
        if os.path.isfile(src):
            pairs.append((src, os.path.join(PY_MODES, fname)))
    return pairs


def differs(a, b):
    if not os.path.isfile(b):
        return True
    with open(a, "rb") as fa, open(b, "rb") as fb:
        return fa.read() != fb.read()


def main():
    check_only = "--check" in sys.argv
    drifted = []
    for src, dst in sync_pairs():
        if differs(src, dst):
            drifted.append((src, dst))

    # Fitxers de py/modes sense font canònica (esborrats de device_files?)
    orphans = []
    for fname in sorted(os.listdir(PY_MODES)):
        if fname.endswith(".py") and fname != "base_mode.py":
            if not os.path.isfile(os.path.join(DEVICE_MODES, fname)):
                orphans.append(fname)

    if check_only:
        if drifted:
            print(f"DIVERGÈNCIA: {len(drifted)} fitxer(s) de py/ no coincideixen amb device_files/:")
            for src, dst in drifted:
                print(f"  - {os.path.relpath(dst, ROOT)}")
            print("Executa: python3 tools/sync_simulator.py")
            sys.exit(1)
        if orphans:
            print(f"AVÍS: {len(orphans)} fitxer(s) a py/modes/ sense font a device_files/modes/: {orphans}")
        print("OK: py/ sincronitzat amb device_files/")
        return

    for src, dst in drifted:
        shutil.copyfile(src, dst)
        print(f"  sync: {os.path.relpath(src, ROOT)} -> {os.path.relpath(dst, ROOT)}")
    if orphans:
        print(f"AVÍS: fitxers a py/modes/ sense font canònica (revisa si cal esborrar-los): {orphans}")
    print(f"Sincronitzats {len(drifted)} fitxer(s)." if drifted else "Ja estava tot sincronitzat.")


if __name__ == "__main__":
    main()
