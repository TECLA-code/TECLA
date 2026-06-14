#!/usr/bin/env bash
#
# deploy_mpy.sh - Precompila a .mpy els fitxers .py que JA son al dispositiu TECLA
# i els desplega, eliminant els .py originals. Manté boot.py, main.py i __init__.py
# com a font. Compila tot a un staging primer i avorta si algun fitxer falla
# (mai deixa el dispositiu a mig fer).
#
# Requereix: tools/mpy-cross (binari de CircuitPython, versió que coincideixi amb el device)
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MPY="${MPY_CROSS:-$ROOT/tools/mpy-cross}"
DF="$ROOT/codi/device_files"
DEV="${TECLA_DEV:-/Volumes/TECLA}"
STAGE="$(mktemp -d /tmp/tecla_mpy_stage.XXXXXX)"
export COPYFILE_DISABLE=1

trap 'rm -rf "$STAGE"' EXIT

[ -x "$MPY" ] || { echo "ERROR: no trobo mpy-cross executable a $MPY"; exit 1; }
[ -d "$DEV" ] || { echo "ERROR: dispositiu no muntat a $DEV"; exit 1; }

echo "mpy-cross: $("$MPY" --version)"

# Llista de .py al dispositiu (exclou entry points, __init__ i brossa ._*)
FILES=$(cd "$DEV" && find . -name '*.py' \
  -not -name 'boot.py' -not -name 'main.py' -not -name '__init__.py' \
  -not -name '._*' -not -path '*/.fseventsd/*' | sed 's|^\./||' | sort)

echo "=== FASE 1: compilar a staging (abort si algun falla) ==="
N=0; FAIL=0
for f in $FILES; do
  src="$DF/$f"
  if [ ! -f "$src" ]; then echo "  - sense font local: $f (s'omet)"; continue; fi
  out="$STAGE/${f%.py}.mpy"; mkdir -p "$(dirname "$out")"
  if "$MPY" -O2 "$src" -o "$out" 2>/tmp/mpy_err; then
    N=$((N+1))
  else
    echo "  x FALLA: $f"; cat /tmp/mpy_err; FAIL=$((FAIL+1))
  fi
done
echo "  Compilats OK: $N | Fallits: $FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo "AVORTAT: errors de compilacio. No s'ha tocat el dispositiu."
  exit 1
fi

echo "=== FASE 2: desplegar .mpy i eliminar .py del dispositiu ==="
DEPLOYED=0
for f in $FILES; do
  mpy="$STAGE/${f%.py}.mpy"
  [ -f "$mpy" ] || continue
  dest="$DEV/${f%.py}.mpy"
  cp "$mpy" "$dest"
  rm -f "$DEV/$f"
  DEPLOYED=$((DEPLOYED+1))
done
sync
echo "  Desplegats: $DEPLOYED .mpy (i .py corresponents eliminats)"
echo "FET."
