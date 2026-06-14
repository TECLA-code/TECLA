#!/usr/bin/env python3
"""OBSOLET — el manifest el genera tools/build_firmware.py (pipeline canònic).

Aquest script generava el manifest amb regles pròpies (quins .py es mantenen
com a font, etc.) que havien divergit de les del build real. Per evitar dos
generadors en conflicte, ara delega a l'eina canònica.

Ús correcte:  python3 tools/build_firmware.py   (o senzillament ./dev.sh)
"""
import sys

print(__doc__)
sys.exit("AVORTAT: fes servir tools/build_firmware.py")
