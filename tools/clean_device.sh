#!/usr/bin/env bash
#
# clean_device.sh - Autoneteja del dispositiu TECLA per evitar saturacio de fitxers.
#
# Fa tres coses:
#   1. Elimina brossa de macOS  (._*, __pycache__, *.pyc, .Trashes, .Spotlight-V100,
#      logs de .fseventsd, .DS_Store, ~*.MET)
#   2. Elimina .py obsolets si ja existeix el .mpy equivalent (evita duplicats que
#      podrien fer servir el .py i recompilar). Mante boot.py, main.py i __init__.py.
#   3. Posa marcadors de prevencio perque macOS no torni a omplir el disc:
#      .metadata_never_index (Spotlight off) i .fseventsd/no_log (fsevents off).
#
# Es segur executar-lo tantes vegades com calgui. Integrat a dev.sh.
#
set -euo pipefail
DEV="${TECLA_DEV:-/Volumes/TECLA}"

[ -d "$DEV" ] || { echo "  clean_device: dispositiu no muntat ($DEV), s'omet."; exit 0; }

cd "$DEV"

# ── 1. Brossa de macOS ───────────────────────────────────────────────────────
JUNK=$(find . \( -name '._*' -o -name '.DS_Store' -o -name '*.pyc' -o -name '~*.MET' \) \
  -not -path '*/.fseventsd/*' 2>/dev/null | wc -l | tr -d ' ')
find . \( -name '._*' -o -name '.DS_Store' -o -name '*.pyc' -o -name '~*.MET' \) \
  -not -path '*/.fseventsd/*' -delete 2>/dev/null || true
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf ./.Trashes ./.Trash-1000 ./.Spotlight-V100 2>/dev/null || true

# ── 2. .py obsolets quan existeix el .mpy ────────────────────────────────────
DUP=0
while IFS= read -r mpy; do
  py="${mpy%.mpy}.py"
  base="$(basename "$py")"
  case "$base" in
    boot.py|main.py|__init__.py) continue ;;
  esac
  if [ -f "$py" ]; then rm -f "$py" && DUP=$((DUP+1)); fi
done < <(find . -name '*.mpy' -not -path '*/.fseventsd/*' 2>/dev/null)

# ── 3. Marcadors de prevencio ────────────────────────────────────────────────
touch ./.metadata_never_index 2>/dev/null || true
mkdir -p ./.fseventsd 2>/dev/null || true
touch ./.fseventsd/no_log 2>/dev/null || true

sync 2>/dev/null || true
echo "  clean_device: brossa=$JUNK eliminada | .py duplicats=$DUP eliminats | marcadors OK"
