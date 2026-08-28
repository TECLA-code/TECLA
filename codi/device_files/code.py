"""code.py — el repartidor de personalitats.

CircuitPython busca code.py ABANS que main.py, així que aquest fitxer és el
que arrenca. La seva única feina és mirar quina personalitat toca i cedir-li
el pas.

Per què cal un repartidor
─────────────────────────
Fins ara les tres apps de TECLA es trepitjaven: l'Instrument instal·lava
main.py, i el Macropad i el Blocks escrivien TOTS DOS code.py. No podien
conviure al mateix dispositiu, i instal·lar-ne una deixava muda l'anterior.
Amb un repartidor, cada personalitat viu al seu calaix i cap no toca les
altres:

    code.py                  ← aquest fitxer
    main.py                  ← INSTRUMENT (es queda on sempre)
    personalitats/
        macropad.py          ← el code.py que genera l'app Macropad
        blocks.py            ← el code.py que genera l'app Blocks

Quina arrenca ho diu un byte de la NVM (core/personalitat.py) i el gest
T1+T16 la fa rotar. L'USB el configura boot.py llegint el mateix byte.

Regla que mana: si res d'això funciona, arrenca l'INSTRUMENT. És la
personalitat que porten els dispositius de fàbrica i la que la gent espera.
"""
import time

# A l'escriptori (tests, simulador Pyodide) `code` és un mòdul de la
# biblioteca estàndard, i aquest fitxer el tapa perquè device_files/ va al
# sys.path. CircuitPython executa code.py com a __main__; qualsevol altra cosa
# és algú important-lo, i llavors aquí no s'ha de moure ni un dit.
# (conftest.py, a més, precarrega l'estàndard perquè ningú no es quedi amb
#  aquest a les mans.)
_ES_ARRENCADA = (__name__ == '__main__')

_pers = 0
try:
    from core import personalitat
    _pers = personalitat.actual()
except Exception:
    _pers = 0


def _instrument():
    """main.py només crida main() sota __name__ == '__main__', o sigui que
    importar-lo no engega res: cal cridar-lo a mà."""
    import main
    main.main()


def _personalitat_externa(modul):
    """Macropad i Blocks són fitxers GENERATS per les seves apps. S'executen
    tal com són, sense embolcallar-los en cap funció.

    I com que són generats, poden sortir malament. El cas real: el generador
    del Blocks va petar ("Maximum call stack size exceeded") i l'app va
    escriure el missatge d'error al dispositiu com si fos codi. Un comentari
    és Python perfectament vàlid: s'importava sense queixar-se, tornava de
    seguida, i el TECLA es quedava mut sense dir ni una paraula.

    Una personalitat que TORNA és una personalitat morta. La seva feina és
    engegar el bucle del dispositiu i no tornar mai; si torna, val més
    tractar-ho com el que és —no serveix— i caure a l'Instrument.
    """
    __import__('personalitats.' + modul)
    raise ImportError('%s ha tornat sense engegar res' % modul)


try:
    if not _ES_ARRENCADA:
        raise SystemExit          # importat, no arrencat: res a fer
    if _pers == 1:
        _personalitat_externa('macropad')
    elif _pers == 2:
        _personalitat_externa('blocks')
    else:
        _instrument()
except SystemExit:
    pass
except ImportError as e:
    # La personalitat triada no hi és, o hi és i no serveix: torna a
    # l'Instrument i deixa el byte apuntant-hi, perquè el pròxim boot no hi
    # torni a ensopegar.
    print("Personalitat %d inservible (%s) — arrenco l'Instrument" % (_pers, e))
    try:
        personalitat.posa(0)
    except Exception:
        pass
    try:
        _instrument()
    except Exception as e2:
        print("I l'Instrument tampoc: %s" % e2)
        time.sleep(2)
        import supervisor
        supervisor.reload()
