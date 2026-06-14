"""Importa tots els modes del dispositiu amb els mocks de maquinari.

Atrapa errors de sintaxi, noms no definits a nivell de mòdul i imports
trencats en qualsevol dels ~70 modes, sense necessitat de flashejar res.
"""
import importlib
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODES_DIR = os.path.join(ROOT, 'codi', 'device_files', 'modes')

_tots_els_moduls = sorted(
    f[:-3] for f in os.listdir(MODES_DIR)
    if f.endswith('.py') and f != '__init__.py'
)


@pytest.mark.parametrize('module_name', _tots_els_moduls)
def test_mode_importable(module_name):
    importlib.import_module(f'modes.{module_name}')
