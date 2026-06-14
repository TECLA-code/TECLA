"""Tests d'integritat del projecte: font única de veritat i manifest.

Aquests tests fallen quan algú edita py/ a mà (en lloc de device_files/) o
quan el manifest queda desfasat respecte als fitxers reals.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE_FILES = os.path.join(ROOT, 'codi', 'device_files')
MANIFEST = os.path.join(ROOT, 'codi', 'device_files_manifest.json')


def test_py_sincronitzat_amb_device_files():
    """py/ (simulador web) ha de ser còpia exacta de device_files/ (canònic).

    Si falla: executa `python3 tools/sync_simulator.py` — i recorda que els
    canvis SEMPRE es fan a device_files/, mai a py/.
    """
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, 'tools', 'sync_simulator.py'), '--check'],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_manifest_referencia_fitxers_existents():
    files = json.load(open(MANIFEST))['files']
    que_falten = [f for f in files if not os.path.isfile(os.path.join(DEVICE_FILES, f))]
    assert not que_falten, f"El manifest referencia fitxers inexistents: {que_falten}"


def test_manifest_sense_duplicats_py_mpy():
    """Instal·lar .py i .mpy del mateix mòdul deixaria el dispositiu amb
    bytecode ambigu (un dels dos podria ser vell)."""
    files = json.load(open(MANIFEST))['files']
    bases_py = {f[:-3] for f in files if f.endswith('.py')}
    bases_mpy = {f[:-4] for f in files if f.endswith('.mpy')}
    duplicats = bases_py & bases_mpy
    assert not duplicats, f"Mòduls amb .py i .mpy al manifest: {duplicats}"


def test_manifest_inclou_entry_points_com_a_font():
    files = json.load(open(MANIFEST))['files']
    assert 'boot.py' in files
    assert 'main.py' in files


def test_mode_classes_sincronitzat():
    """MODE_CLASSES està duplicat a mode_manager.py (el llegeix la web per
    regex) i mm_lifecycle.py (el funcional). Han de coincidir."""
    import re
    pattern = re.compile(r"MODE_CLASSES\s*=\s*\{([^}]*)\}", re.S)
    entries = {}
    for fname in ('mode_manager.py', 'mm_lifecycle.py'):
        src = open(os.path.join(DEVICE_FILES, 'modes', fname)).read()
        m = pattern.search(src)
        assert m, f"MODE_CLASSES no trobat a {fname}"
        entries[fname] = re.findall(r"'([^']+)':\s*\('([^']+)',\s*'([^']+)'\)", m.group(1))
    assert entries['mode_manager.py'] == entries['mm_lifecycle.py']
