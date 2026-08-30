"""mm_lifecycle.py - Gestió del cicle de vida dels modes: càrrega, descàrrega, canvi."""
import time
import os
import json
import sys
try:
    from core.pantalla import diu
except Exception:                       # simulador i proves sense core/
    def diu(text):
        print(text)
        return True

# Registre estàtic: únic mode permanent (KeyboardMode es gestiona per separat)
MODE_CLASSES = {
    'Teclat': ('mode_keyboard', 'KeyboardMode'),
}


_MODES_DIR = None


def _modes_dir():
    """Carpeta de `modes/`, acabada en barra.

    Al dispositiu el cwd és '/' i 'modes/' hi val, però és l'única cosa que ho
    sosté: n'hi havia prou amb executar el firmware des d'una altra carpeta
    perquè el registre no es trobés i TOTES les tecles quedessin mortes. Es
    prova primer la ruta del mòdul (CircuitPython no porta os.path, i per això
    va embolcallat) i es reserva 'modes/' com a segona opció.
    """
    global _MODES_DIR
    if _MODES_DIR is None:
        _MODES_DIR = 'modes/'
        try:
            d = os.path.dirname(os.path.abspath(__file__))
            if d:
                _MODES_DIR = d + '/'
        except Exception:
            pass
    return _MODES_DIR


def _get_mode_info_from_registry(mode_name):
    try:
        registry_path = _modes_dir() + 'custom_modes_registry.json'
        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            modes_data = registry.get('custom_modes', {})
            if mode_name in modes_data:
                mode_info = modes_data[mode_name]
                return (mode_info['file_name'], mode_info['class_name'])
        except OSError:
            pass
    except Exception as e:
        # repr(): un MemoryError té str buit i el motiu quedava invisible
        print(f"Error consultant registre per {mode_name}: {e!r}")
    return None


def _build_mode_info_cache(mgr, configured_modes):
    """Llegeix el registre UNA SOLA VEGADA i crea un cache per als modes del banc."""
    import gc
    # RAM/LATÈNCIA: si tots els modes del banc són de fàbrica (MODE_CLASSES) o
    # marcadors buits ('', 'Silenci', 'Teclat'), NO cal ni obrir el registre —
    # el json.load d'aquest fitxer té un pic transitori de RAM (~3x la mida)
    # i és una de les parts lentes del canvi de capa.
    needed = [m for m in configured_modes
              if m not in ('', 'Silenci', 'Teclat', None) and m not in MODE_CLASSES]
    if not needed:
        mgr.mode_info_cache = {}
        return
    try:
        with open(_modes_dir() + 'custom_modes_registry.json', 'r') as f:
            registry = json.load(f)
        modes_data = registry.get('custom_modes', {})
        mgr.mode_info_cache = {}
        for mode_name in needed:
            if mode_name in modes_data:
                info = modes_data[mode_name]
                mgr.mode_info_cache[mode_name] = (info['file_name'], info['class_name'])
            else:
                print(f"Mode '{mode_name}' no al registre")
        del registry, modes_data
        gc.collect()
    except Exception as e:
        print(f"Error llegint registre: {e}")


def _resol_mode(mgr, mode_name):
    """(fitxer, classe) d'un mode, o None. Mateix ordre de sempre: registre
    estàtic → cache del banc → registre del disc."""
    if mode_name in MODE_CLASSES:
        return MODE_CLASSES[mode_name]
    cache = getattr(mgr, 'mode_info_cache', None)
    if cache and mode_name in cache:
        return cache[mode_name]
    return _get_mode_info_from_registry(mode_name)


def mm_mode_disponible(mgr, mode_name):
    """Hi ha FITXER instal·lat per a aquest mode?

    Ser al registre NO vol dir estar instal·lat: el registre és el catàleg de
    tot el que coneix l'app (53 modes) i el dispositiu només du els fitxers
    dels modes que fa servir. Amb 'Crackle' i 'Bit' al registre però sense
    fitxer, la tecla no era inerta —era LETAL: mm_set_mode aturava i
    descarregava el mode que sonava i només llavors descobria que no podia
    carregar el nou, i el dispositiu es quedava mut i sense mode.
    """
    if mode_name in mgr.modes:
        return True
    info = _resol_mode(mgr, mode_name)
    if not info:
        return False
    module_name = info[0]
    if ('modes.%s' % module_name) in sys.modules:
        return True
    arrel = _modes_dir() + module_name
    for ext in ('.mpy', '.py'):
        try:
            os.stat(arrel + ext)
            return True
        except OSError:
            pass
    return False


def mm_config_efectes(mgr, efectos):
    """(Re)construeix els botons d'efecte i el seu tipus des d'un mapa
    {índex_de_tecla: nom_de_l_efecte}.

    Es crida a CADA canvi de capa. Abans es feia un sol cop a l'arrencada i
    només mirava el mapa GLOBAL de la config; l'app, però, els exporta dins de
    cada banc, o sigui que el firmware requeia sempre al valor per defecte i
    la tecla 15 feia Sustain encara que la capa digués Pausa.

    Els botons que segueixen existint conserven el seu estat (latch, temps);
    els que canvien de tipus o desapareixen es desactiven abans.
    """
    nous = []
    for k in (efectos or {}):
        try:
            i = int(k)
        except Exception:
            continue
        if 0 <= i <= 14 and i != 12 and i not in nous:
            nous.append(i)
    nous.sort()
    if not nous:
        nous = [13, 14]

    from modes.mm_update import mm_deactivate_efecte_temporal, _clear_susp_flags

    def _apaga(btn):
        info = mgr.efectes_temporals.get(btn)
        if not info or not info.get('active'):
            return
        try:
            mm_deactivate_efecte_temporal(mgr, btn)
            _clear_susp_flags(mgr, info['tipus'])
        except Exception:
            info['active'] = False

    for btn in list(mgr.efectes_temporals.keys()):
        if btn not in nous:
            _apaga(btn)
            del mgr.efectes_temporals[btn]

    for btn in nous:
        tipus = (efectos or {}).get(str(btn)) or (efectos or {}).get(btn) \
            or ('Pausa' if btn == 14 else 'Sustain')
        info = mgr.efectes_temporals.get(btn)
        if info is None:
            mgr.efectes_temporals[btn] = {
                'active': False, 'last_state': False, 'press_time': 0,
                'mode_instance': None,
                'pre_mode': None, 'pre_mode_instance': None,
                # Nivell CRU i des de quan s'hi manté: el filtre de rebots va
                # per ESTABILITAT, no per rebuig de flanc (vegeu mm_update).
                'raw_state': False, 'raw_since': 0.0,
                'tipus': tipus,
            }
        elif info['tipus'] != tipus:
            _apaga(btn)
            info['tipus'] = tipus

    mgr.effect_buttons = nous
    return nous


def mm_load_config(mgr):
    """Carrega la configuració de bancs i modes."""
    efectes_preservats = {}
    for btn in list(mgr.effect_buttons):
        if mgr.efectes_temporals.get(btn, {}).get('active'):
            # NOMÉS el nom, no la instància: preservar pre_mode_instance
            # mantenia viva una instància que tot just es descarrega per
            # alliberar RAM (i no es llegeix enlloc del codi)
            efectes_preservats[btn] = {
                'tipus': mgr.efectes_temporals[btn]['tipus'],
                'pre_mode': mgr.efectes_temporals[btn]['pre_mode']
            }

    if mgr.current_mode and mgr.current_mode_name and mgr.current_mode_name != 'Teclat':
        from modes.mm_cleanup import mm_stop_current_mode, mm_all_notes_off
        previous_mode_name = mgr.current_mode_name
        mm_stop_current_mode(mgr)
        mm_all_notes_off(mgr)
        if previous_mode_name and previous_mode_name != 'Teclat':
            mm_unload_mode(mgr, previous_mode_name)
        mgr.current_mode = None
        mgr.current_mode_name = None
        import gc; gc.collect()

    try:
        current_bank = mgr.config_manager.get_current_bank()
        if not current_bank:
            return False

        disabled_modes = current_bank.get('disabled_modes', []) if isinstance(current_bank, dict) else []
        configured_modes = current_bank.get('modes', []) if isinstance(current_bank, dict) else []

        # Els efectes temporals són DE LA CAPA: es reconstrueixen aquí, abans
        # de repartir les tecles, perquè el bucle de sota salta les tecles
        # d'efecte i ha de saber quines són les d'aquest banc.
        try:
            _efectos = mgr.config_manager.get_temporal_effects()
        except Exception:
            _efectos = None
        mm_config_efectes(mgr, _efectos)

        # Pre-cache les dades del registre per als modes del banc (1 sola lectura JSON)
        import gc; gc.collect()
        _build_mode_info_cache(mgr, configured_modes)
        gc.collect()

        # Netejar les assignacions del banc anterior (tecles 0-14): si el nou
        # banc té menys modes vàlids, no han de quedar mapejos residuals
        for button_idx in range(15):
            mgr.button_mappings.pop(button_idx, None)

        # Carregar modes a les tecles que NO són d'efecte (ni la 12 = canvi de capa).
        # Tecles flexibles: una tecla pot tenir mode O efecte (idx 0-14).
        for button_idx in range(15):
            if button_idx == 12 or button_idx in mgr.effect_buttons:
                continue
            mode_name = configured_modes[button_idx] if button_idx < len(configured_modes) else None
            if mode_name and mode_name not in disabled_modes:
                if mode_name not in MODE_CLASSES and mode_name not in mgr.mode_info_cache:
                    print(f"Botó {button_idx+1}: mode '{mode_name}' no trobat")
                elif not mm_mode_disponible(mgr, mode_name):
                    # Al registre però sense fitxer instal·lat: la tecla es
                    # queda SENSE mapejar. Si es mapegés, prémer-la aturaria el
                    # mode que sona per no poder carregar-ne cap altre.
                    print(f"Botó {button_idx+1}: '{mode_name}' no instal·lat")
                else:
                    mgr.button_mappings[button_idx] = mode_name

        mgr.button_mappings[12] = 'RESERVADO_BANCS'

        if efectes_preservats:
            for btn, efecte_data in efectes_preservats.items():
                if btn in mgr.efectes_temporals and \
                        mgr.efectes_temporals[btn]['tipus'] == efecte_data['tipus']:
                    activat = mgr.effect_manager.activate(efecte_data['tipus'])
                    if activat:
                        mgr.efectes_temporals[btn]['active'] = True
                        mgr.efectes_temporals[btn]['pre_mode'] = efecte_data['pre_mode']
                        mgr.efectes_temporals[btn]['pre_mode_instance'] = None

        if mgr.config_manager:
            mgr.available_effects = mgr.config_manager.get_available_effects()

        # Refrescar les capes de potes de 'Config Modes' amb la config del banc
        # nou (només si ja s'havien fet servir; el mòdul és lazy).
        _lay = mgr.__dict__.get('_potcfg')
        if _lay is not None:
            try:
                _lay.set_layers(mgr.config_manager.get_mode_pot_layers()
                                if mgr.config_manager else None)
            except Exception:
                _lay.off()

        for btn in mgr.effect_buttons:
            mgr.button_mappings[btn] = f"RESERVADO_EFECTO_{mgr.efectes_temporals[btn]['tipus']}"
        mgr.button_mappings[15] = 'RESERVADO_TORNAR'

        return True
    except Exception as e:
        print(f"Error carregant configuració: {e}")
        return False


def mm_load_all_modes(mgr):
    """Inicialitza els modes (lazy loading - no crea instàncies innecessàries)."""
    print("✓ ModeManager: lazy loading activat")
    # No precarregar Teclat: ja gestionat per hardware.keyboard_mode


def mm_load_mode(mgr, mode_name):
    """Carrega un mode individual sota demanda."""
    info = _resol_mode(mgr, mode_name)
    if not info:
        return False
    module_name, class_name = info

    if mode_name in mgr.modes:
        if mode_name in mgr.loaded_modes_history:
            mgr.loaded_modes_history.remove(mode_name)
        mgr.loaded_modes_history.append(mode_name)
        return True

    try:
        if len(mgr.modes) >= mgr.MAX_LOADED_MODES:
            for old_mode in mgr.loaded_modes_history:
                if (old_mode in mgr.modes and
                        old_mode != 'Teclat' and
                        old_mode != mgr.current_mode_name and
                        old_mode != mode_name):
                    print(f"[MEMÒRIA] Descarregant: {old_mode}")
                    mm_unload_mode(mgr, old_mode)
                    break

        import gc; gc.collect()
        print(f"[CÀRREGA] Carregant mode: {mode_name}...")

        module = __import__(f'modes.{module_name}')
        module = getattr(module, module_name)
        mode_class = getattr(module, class_name)
        mgr.modes[mode_name] = mode_class(mgr.midi_out, {})
        mgr.loaded_modes_history.append(mode_name)
        # El collect POSTERIOR a l'import torna a ser-hi. El vaig treure per
        # guanyar 10-30 ms i és un mal negoci: la brossa de carregar un mòdul
        # es queda al heap fins al pròxim collect, i el heap de MicroPython NO
        # es compacta — la següent al·locació gran (el KeyboardMode i els seus
        # set mòduls) se la troba al davant i pot no trobar blocs contigus.
        # Els 90 ms que hem tret del pànic MIDI paguen aquests 20 de sobres, i
        # quedar-se sense memòria vol dir que el dispositiu deixa de sonar.
        gc.collect()
        print(f"✓ Mode {mode_name} carregat")
        return True

    except Exception as e:
        print(f"✗ Error carregant {mode_name}: {e}")
        return False


def mm_unload_mode(mgr, mode_name):
    """Descarrega un mode de la memòria."""
    if mode_name not in mgr.modes:
        return False
    try:
        import gc
        info = _resol_mode(mgr, mode_name)
        module_name = info[0] if info else None

        del mgr.modes[mode_name]

        full_module_name = f'modes.{module_name}' if module_name else None
        if full_module_name and full_module_name in sys.modules:
            del sys.modules[full_module_name]
        # CLAU DE RAM: l'import també penja el submòdul com a atribut del
        # paquet `modes`; sense treure'l, el bytecode queda referenciat per
        # sempre i cada mode provat durant la sessió és una fuita.
        if module_name:
            try:
                pkg = sys.modules.get('modes')
                if pkg is not None and hasattr(pkg, module_name):
                    delattr(pkg, module_name)
            except Exception:
                pass

        if mode_name in mgr.loaded_modes_history:
            mgr.loaded_modes_history.remove(mode_name)

        gc.collect()
        return True
    except Exception as e:
        print(f"Error descarregant {mode_name}: {e}")
        return False


def mm_set_mode(mgr, mode_name, force_reload=False, capture_state=True):
    """Canvia al mode especificat: PARA l'actual primer, CARREGA el nou despres."""
    try:
        import gc

        # 0. Els efectes temporals NO persisteixen entre modes: en canviar de
        # mode es desactiven TOTS (amb el seu on_deactivate — el Sustain, per
        # exemple, ha d'aixecar el pedal CC64 o les notes següents queden
        # enganxades). Úniques excepcions: 'Config Modes' (capes de pots) i
        # 'Loop' (la gràcia és canviar de mode i tocar sobre el loop).
        if mgr.current_mode_name != mode_name or force_reload:
            from modes.mm_update import mm_deactivate_efectes_no_persistents
            mm_deactivate_efectes_no_persistents(mgr)

        # 0-bis. COMPROVAR QUE EL MODE NOU ES POT CARREGAR, abans de tocar res.
        # L'ordre importa: aturar primer i descobrir després que el mode no
        # existeix deixava el dispositiu mut i sense mode (les tecles 'Crackle'
        # i 'Bit', al registre però sense fitxer instal·lat). Una tecla que no
        # pot carregar res ha de ser INERTA, no letal.
        if mode_name not in mgr.modes and not mm_mode_disponible(mgr, mode_name):
            print(f"Mode '{mode_name}' no instal·lat: la tecla no fa res")
            mgr.last_mode_error = "mode no instal·lat: %s" % mode_name
            return False

        # 1. PRIMER: aturar i descarregar el mode actual per alliberar RAM
        if mgr.current_mode and (mgr.current_mode_name != mode_name or force_reload):
            previous_mode = mgr.current_mode_name
            print(f"Aturant: {previous_mode}")
            from modes.mm_cleanup import mm_stop_current_mode, mm_all_notes_off
            mm_stop_current_mode(mgr)
            # Xarxa de seguretat de 32 missatges, no el pànic de 192: el pànic
            # sencer és del botó STOP (vegeu mm_all_notes_off).
            mm_all_notes_off(mgr)
            mgr.current_mode = None
            mgr.current_mode_name = None
            if previous_mode and previous_mode != 'Teclat':
                mm_unload_mode(mgr, previous_mode)   # ja fa el seu gc.collect()
            else:
                gc.collect()

        if mgr.current_mode_name == mode_name and not force_reload:
            return True

        # 2. DESPRES: carregar el nou mode amb la RAM alliberada
        if mode_name not in mgr.modes:
            mm_load_mode(mgr, mode_name)
            if mode_name not in mgr.modes:
                print(f"No s'ha pogut carregar '{mode_name}'")
                return False

        # NOMÉS el nom. Aquesta línia la llegeix la Pantalla de l'app
        # (`_monParse`, patró `^Mode: (.+)`) i tot el que hi afegeixis li surt
        # DINS del nom del mode. Hi vaig posar la RAM lliure i el que es veia a
        # la pantalla era «Crackle | RAM lliure: 45000». La Pantalla és de
        # l'usuari; els diagnòstics van a una altra banda.
        diu(f"Mode: {mode_name}")
        mgr.current_mode = mgr.modes[mode_name]
        mgr.current_mode_name = mode_name
        mgr.last_mode_change = time.monotonic()
        mgr.previous_mode_name = mode_name

        if hasattr(mgr.current_mode, 'setup'):
            try:
                mgr.current_mode.setup()
            except Exception as e:
                print(f"Error setup {mode_name}: {e}")

        return True

    except Exception as e:
        print(f"Error canviant a {mode_name}: {e}")
        mgr.last_mode_error = str(e)
        return False


def mm_reload_current_mode(mgr):
    if mgr.current_mode_name:
        return mm_set_mode(mgr, mgr.current_mode_name, force_reload=True)
    return False


def mm_get_available_modes(mgr):
    """Retorna els modes del banc actual (des de button_mappings, NO tot el registre)."""
    modes = []
    for btn_idx in sorted(mgr.button_mappings.keys()):
        name = mgr.button_mappings.get(btn_idx, '')
        if name and not name.startswith('RESERVADO_') and name not in modes:
            modes.append(name)
    return modes
