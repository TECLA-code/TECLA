#!/usr/bin/env python3
"""register_mode.py - Registra un mode (o tots els d'una carpeta) a TECLA.

Quan s'afegeix un mode al projecte, NO n'hi ha prou amb deixar el .py: cal
REGISTRAR-LO a tots els llocs canònics o el dispositiu dirà "Mode 'X' no al
registre" (mm_lifecycle._build_mode_info_cache) i l'app no el llistarà. Aquesta
eina ho fa tot d'una tirada:

  1. Copia mode_<x>.py  ->  codi/device_files/modes/   (font única de veritat)
  2. Copia mode_<x>.py  ->  codi/py/modes/             (còpia del simulador web)
  3. Afegeix/actualitza l'entrada a custom_modes_registry.json (device + py)
     -> nom de mostra -> (file_name, class_name) que el dispositiu resol.
  4. Afegeix/actualitza l'entrada a py/modes_index.json (llista de l'app).

Després cal compilar: `python3 tools/build_firmware.py` (genera .mpy + manifest).
`./dev.sh` ja crida el build i desplega.

El nom de mostra surt de `self.name = "..."`; si no hi és, del nom de classe
(ModeEuclid -> Euclid). La classe es detecta de `class Xxx(BaseMode)`.

Ús:
  python3 tools/register_mode.py <fitxer.py | carpeta> [...]
  python3 tools/register_mode.py ~/Desktop/modes2026
"""
import argparse
import ast
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE_MODES = os.path.join(ROOT, "codi", "device_files", "modes")
PY_MODES = os.path.join(ROOT, "codi", "py", "modes")
REGISTRIES = [
    os.path.join(DEVICE_MODES, "custom_modes_registry.json"),
    os.path.join(PY_MODES, "custom_modes_registry.json"),
]
MODES_INDEX = os.path.join(ROOT, "codi", "py", "modes_index.json")


def parse_mode(src, filename):
    """Extreu (display_name, file_name, class_name, metadata) d'un mode .py."""
    file_name = os.path.basename(filename)[:-3]  # sense .py

    m_cls = re.search(r"class\s+(\w+)\s*\(\s*BaseMode\s*\)", src)
    if not m_cls:
        raise ValueError(f"{filename}: no hi ha cap `class X(BaseMode)`")
    class_name = m_cls.group(1)

    m_name = re.search(r"self\.name\s*=\s*[\"']([^\"']+)[\"']", src)
    if m_name:
        display = m_name.group(1)
    elif class_name.startswith("Mode") and len(class_name) > 4:
        display = class_name[4:]
    else:
        display = file_name.replace("mode_", "").replace("_", " ").title()

    try:
        doc = ast.get_docstring(ast.parse(src)) or ""
    except SyntaxError as e:
        raise ValueError(f"{filename}: error de sintaxi: {e}")
    desc = next((ln.strip() for ln in doc.splitlines() if ln.strip()), "Sense descripció")

    meta = {
        "description": desc[:120],
        "has_setup": bool(re.search(r"def\s+setup\b", src)),
        "has_update": bool(re.search(r"def\s+update\b", src)),
        "has_cleanup": bool(re.search(r"def\s+cleanup\b", src)),
    }
    if not meta["has_update"]:
        raise ValueError(f"{filename}: un mode ha de tenir `def update(...)`")
    return display, file_name, class_name, meta


def upsert_registry(path, display, file_name, class_name):
    # NOMÉS file_name + class_name: és l'únic que llegeixen el firmware
    # (mm_lifecycle) i dev.sh. El registre es carrega SENCER a RAM amb json.load
    # a cada canvi de capa; afegir-hi metadata/added_date l'engreixava fins a
    # provocar MemoryError al dispositiu. Es manté prim a propòsit.
    with open(path) as f:
        reg = json.load(f)
    modes = reg.setdefault("custom_modes", {})
    existing = modes.get(display)
    modes[display] = {"file_name": file_name, "class_name": class_name}
    with open(path, "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return existing is None


def upsert_index(display, file_name):
    with open(MODES_INDEX) as f:
        idx = json.load(f)
    modes = idx.setdefault("modes", [])
    pyfile = file_name + ".py"
    for m in modes:
        if m.get("file") == pyfile:
            m["name"] = display
            break
    else:
        modes.append({"name": display, "file": pyfile})
    modes.sort(key=lambda m: m.get("name", "").lower())
    with open(MODES_INDEX, "w") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)
        f.write("\n")


def collect_files(paths):
    out = []
    for p in paths:
        p = os.path.abspath(os.path.expanduser(p))
        if os.path.isdir(p):
            out += [os.path.join(p, f) for f in sorted(os.listdir(p))
                    if f.startswith("mode_") and f.endswith(".py")]
        elif os.path.isfile(p) and p.endswith(".py"):
            out.append(p)
        else:
            print(f"  ⚠ ignorat (no és .py ni carpeta): {p}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Registra modes TECLA a tots els llocs canònics.")
    ap.add_argument("paths", nargs="+", help="fitxers mode_*.py o carpetes")
    args = ap.parse_args()

    files = collect_files(args.paths)
    if not files:
        sys.exit("No s'ha trobat cap mode_*.py.")

    registered = 0
    for src_path in files:
        fname = os.path.basename(src_path)
        with open(src_path) as f:
            src = f.read()
        try:
            display, file_name, class_name, _meta = parse_mode(src, fname)
        except ValueError as e:
            print(f"  ✗ {fname}: {e}")
            continue

        shutil.copyfile(src_path, os.path.join(DEVICE_MODES, fname))
        shutil.copyfile(src_path, os.path.join(PY_MODES, fname))
        # Upsert a cada registre (device + py); is_new = era nou a tots dos.
        is_new = all([upsert_registry(r, display, file_name, class_name) for r in REGISTRIES])
        upsert_index(display, file_name)
        print(f"  ✓ {display:<14} ({fname}, {class_name}) "
              f"{'registrat' if is_new else 'actualitzat'}")
        registered += 1

    print(f"\n{registered} mode(s) registrat(s) a device_files/, py/, "
          f"registre i modes_index.json.")
    print("Següent pas: python3 tools/build_firmware.py   (.mpy + manifest)")


if __name__ == "__main__":
    main()
