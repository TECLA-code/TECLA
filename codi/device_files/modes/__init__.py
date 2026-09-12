"""Els modes d'operació: els de fàbrica, els del Laboratori i els teus.

Aquest fitxer sembla buit i no ho és. Importar `motor` des d'aquí és el que
fa que `from modes.base_mode import BaseMode` segueixi funcionant ara que la
classe viu congelada a `motor/`: el motor deixa l'àlies a `sys.modules`, i
l'import de CircuitPython mira `sys.modules` abans que el sistema de fitxers.

Ha de passar AQUÍ i no a `main.py` perquè aquí és l'únic lloc amb garantia
d'ordre. CircuitPython importa el paquet abans que cap dels seus submòduls,
sempre; un `main.py` que ho fes primer seria només un costum, i el primer
mode que s'importés per un altre camí —un test, el simulador, un
`import modes.mode_bit` al REPL— es quedaria sense la classe base.

L'única absència legítima del motor és el SIMULADOR: a Pyodide, `modes/` és
una carpeta plana on `base_mode.py` i `negharm.py` són fitxers de debò i no
cal cap pont. Per això l'ImportError es deixa passar en comptes de tombar-ho
tot. Al dispositiu no pot faltar: hi va congelat dins de la UF2.
"""
try:
    import motor  # noqa: F401  (instal·la l'àlies modes.base_mode)
except ImportError:
    pass
