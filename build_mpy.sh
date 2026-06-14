#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  OBSOLET — el build del firmware el fa tools/build_firmware.py
#
#  Aquest script compilava a un staging (build_device/) amb regles pròpies de
#  quins fitxers queden com a font (boot/main/code.py), que havien divergit de
#  les del pipeline canònic (boot/main/reset/__init__.py). Mantenir dos builds
#  en paral·lel produïa firmwares diferents segons quin s'executés.
#
#  Flux actual:
#    ./dev.sh                            # compila + desplega + servidor web
#    python3 tools/build_firmware.py     # només compilar .mpy + manifest
# ─────────────────────────────────────────────────────────────────────────────
echo "OBSOLET: fes servir ./dev.sh o python3 tools/build_firmware.py"
exit 1
