#!/bin/bash
# ─────────────────────────────────────────────
#  TECLA Dev — sync firmware + servidor web
# ─────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CODI_DIR="$SCRIPT_DIR/codi"
DEVICE_FILES="$CODI_DIR/device_files"
DEVICE_MOUNT="/Volumes/TECLA"
PORT=8080

echo ""
echo "🎹  TECLA Dev"
echo "────────────────────────────────────────"

# ── 1. Regenera el firmware optimitzat (.mpy + manifest) ─────────────────────
#    Es la font de veritat: l'app-web i el dispositiu despleguen aquests .mpy.
if [ -x "$SCRIPT_DIR/tools/mpy-cross" ]; then
    echo "  ⚙ Compilant firmware .mpy + manifest..."
    if ! python3 "$SCRIPT_DIR/tools/build_firmware.py" 2>&1 | sed 's/^/    /'; then
        echo "    ⚠ Error compilant el firmware .mpy"
    fi
else
    echo "  ⚠ tools/mpy-cross no trobat → no es pot compilar el firmware .mpy"
    echo "     Baixa'l: https://adafruit-circuit-python.s3.amazonaws.com/bin/mpy-cross/macos/mpy-cross-macos-10.0.3-universal"
fi

# ── 1b. Sincronitza la còpia del simulador web (py/ ← device_files/) ─────────
#    device_files/ és la font única de veritat; py/ és una còpia generada que
#    el simulador Pyodide carrega via fetch. NO editar py/ a mà.
echo "  ⟳ Sincronitzant simulador web (py/ ← device_files/)..."
python3 "$SCRIPT_DIR/tools/sync_simulator.py" 2>&1 | sed 's/^/    /'
echo "────────────────────────────────────────"

# ── 2. Desplega el firmware .mpy al dispositiu (si està muntat) ──────────────
#    Mateixa lògica que l'app-web: copia segons el manifest, filtrant modes
#    assignats, i deixa el dispositiu NOMÉS amb .mpy (sense problemes de memòria).
if [ -d "$DEVICE_MOUNT" ]; then
    echo "✓ Dispositiu TECLA detectat a $DEVICE_MOUNT"

    # Modes assignats (noms base, p.ex. 'mode_chopin') des de config/tecla_config.json.
    #    banks[].modes conté NOMS (p.ex. 'Chopin') que es tradueixen a file_name via
    #    el registre custom_modes_registry.json (p.ex. 'Sinusoidal' -> 'mode_ona_sinusoidal').
    CONFIG_OK=0
    ASSIGNED_BASES=""
    if [ -f "$DEVICE_MOUNT/config/tecla_config.json" ]; then
        CONFIG_OK=1
        ASSIGNED_BASES=$(python3 -c "
import json
DEV = '$DEVICE_MOUNT'
try:
    cfg = json.load(open(DEV + '/config/tecla_config.json'))
except Exception:
    cfg = {}
names = set()
for b in cfg.get('banks', []) or []:
    for m in b.get('modes', []) or []:
        if m: names.add(m)
for m in cfg.get('enabled_modes', []) or []:
    if m: names.add(m)
try:
    reg = json.load(open(DEV + '/modes/custom_modes_registry.json')).get('custom_modes', {})
except Exception:
    reg = {}
bases = set()
for n in names:
    fn = reg.get(n, {}).get('file_name')
    if fn: bases.add(fn)
print(' '.join(sorted(bases)))
" 2>/dev/null)
    fi
    echo "  Modes assignats: ${ASSIGNED_BASES:-cap}"

    # Llista de fitxers a copiar (manifest filtrat), via python
    FILES_TO_COPY=$(ASSIGNED="$ASSIGNED_BASES" python3 -c "
import json, os, re
base = '$DEVICE_FILES'
man = json.load(open('$CODI_DIR/device_files_manifest.json'))['files']
assigned = set(os.environ.get('ASSIGNED','').split())
ESSENTIAL = {'base_mode','mode_manager','mode_keyboard'}
def mode_base(f):
    return re.sub(r'\.(py|mpy)\$','',f)
out = []
for rel in man:
    fname = rel.split('/')[-1]
    if rel.startswith('modes/mode_') and re.search(r'\.(py|mpy)\$', rel):
        b = mode_base(fname)
        if b in ESSENTIAL or b in assigned:
            out.append(rel)
    else:
        out.append(rel)
print('\n'.join(out))
" 2>/dev/null)

    export COPYFILE_DISABLE=1
    COPIED=0
    while IFS= read -r rel; do
        [ -n "$rel" ] || continue
        src="$DEVICE_FILES/$rel"
        [ -f "$src" ] || continue
        dest="$DEVICE_MOUNT/$rel"
        mkdir -p "$(dirname "$dest")"
        if cp "$src" "$dest" 2>/dev/null; then
            COPIED=$((COPIED+1))
            # Eliminar el germà de l'extensió oposada (evita duplicats .py/.mpy)
            case "$rel" in
                *.mpy) rm -f "$DEVICE_MOUNT/${rel%.mpy}.py" 2>/dev/null ;;
                *.py)  rm -f "$DEVICE_MOUNT/${rel%.py}.mpy" 2>/dev/null ;;
            esac
        fi
    done <<< "$FILES_TO_COPY"
    echo "  ✓ $COPIED fitxers desplegats (.mpy)"

    # Eliminar modes no assignats que hagin quedat al dispositiu
    #    NOMES si hem pogut llegir el config (evita esborrar modes per error).
    if [ "$CONFIG_OK" -eq 1 ] && [ -d "$DEVICE_MOUNT/modes" ]; then
        ASSIGNED="$ASSIGNED_BASES" python3 -c "
import os, re
d = '$DEVICE_MOUNT/modes'
assigned = set(os.environ.get('ASSIGNED','').split())
ESSENTIAL = {'base_mode','mode_manager','mode_keyboard'}
for f in os.listdir(d):
    if not f.startswith('mode_'): continue
    if not re.search(r'\.(py|mpy)\$', f): continue
    b = re.sub(r'\.(py|mpy)\$','',f)
    if b in ESSENTIAL or b in assigned: continue
    try: os.remove(os.path.join(d,f))
    except Exception: pass
" 2>/dev/null
    fi

    # Copiar la config del dispositiu (si l'app-web l'ha desat) — preservada
    sync 2>/dev/null || true
    echo "  ⟳ El dispositiu reiniciarà automàticament..."

    # ── Autoneteja: brossa de macOS + marcadors de prevenció ────────────────
    if [ -x "$SCRIPT_DIR/tools/clean_device.sh" ]; then
        TECLA_DEV="$DEVICE_MOUNT" bash "$SCRIPT_DIR/tools/clean_device.sh"
    fi
else
    echo "⚠  Dispositiu TECLA NO detectat (es despleguen els .mpy quan el connectis)"
fi
echo "────────────────────────────────────────"

# ── 2. Allibera el port si ja estava ocupat ──────────────────────────────────
PID_IN_PORT=$(lsof -ti tcp:$PORT 2>/dev/null || true)
if [ -n "$PID_IN_PORT" ]; then
    echo "  Port $PORT ocupat → tancant procés anterior..."
    kill "$PID_IN_PORT" 2>/dev/null || true
    sleep 0.3
fi

# ── 3. Inicia el servidor web ────────────────────────────────────────────────
cd "$CODI_DIR"
python3 server.py &
SERVER_PID=$!
sleep 0.4

echo "✓ Servidor web actiu  →  http://127.0.0.1:$PORT"
echo ""

# ── 4. Obre el navegador ─────────────────────────────────────────────────────
open "http://127.0.0.1:$PORT/index.html"
echo "✓ Navegador obert"
echo ""
echo "  Prem Ctrl+C per aturar el servidor"
echo "────────────────────────────────────────"
echo ""

# ── 5. Espera i neteja en sortir ─────────────────────────────────────────────
cleanup() {
    echo ""
    echo "  Aturant servidor..."
    kill "$SERVER_PID" 2>/dev/null || true
    echo "  Fins aviat 👋"
    echo ""
    exit 0
}
trap cleanup INT TERM

wait "$SERVER_PID"
