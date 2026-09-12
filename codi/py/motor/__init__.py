"""El MOTOR de TECLA: el teclat, el gestor de modes i tot el que els sosté.

Per què viu fora de `modes/`
────────────────────────────
Perquè `modes/` no es pot congelar. La UF2 de TECLA grava mòduls a la flash i
el sys.path del dispositiu és ['', '/', '.frozen', '/lib']: l'arrel guanya al
congelat. Una carpeta `modes/` al sistema de fitxers —que HI HA DE SER, hi
viuen els modes de l'usuari i els del Laboratori— tapa sencer el paquet
congelat del mateix nom, submòduls inclosos. Ho decideix
`process_import_at_level` de CircuitPython: un submòdul es busca NOMÉS dins
del `__path__` del paquet pare, i el pare ja s'ha resolt al disc.

Separant el motor en un paquet propi que NO existeix al sistema de fitxers,
el motor sí que es pot congelar. Mesurat al dispositiu: importar-lo des del
disc costa 100.240 B dels 161.152 del heap.

El pont de noms
───────────────
Els modes diuen `from modes.base_mode import BaseMode`. Ho diuen els 64 de
fàbrica, els que genera el Laboratori i —això és el que mana— els que la gent
ja té desats als dispositius que hi ha al carrer. Aquest contracte no es toca.

Per això `modes.base_mode` s'apunta aquí a `sys.modules`. L'import de
CircuitPython mira `sys.modules` ABANS del sistema de fitxers, o sigui que
`from modes.base_mode import ...` troba el mòdul congelat sense que existeixi
cap fitxer. Qui garanteix que l'àlies hi sigui a temps és `modes/__init__.py`,
que CircuitPython executa sempre abans de qualsevol `modes.X`.
"""
import sys

from motor import base_mode as _base_mode
from motor import negharm as _negharm

sys.modules['modes.base_mode'] = _base_mode
sys.modules['modes.negharm'] = _negharm
