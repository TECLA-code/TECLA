"""
ConfigManager - Gestiona la configuració i els temes del TECLA
"""
import json
import os

class ConfigManager:
    # Límit dur de capes (banks): tota la config viu en RAM i cada capa de
    # teclat pot pesar 1-2KB de JSON; 6 capes deixen marge còmode per carregar
    # modes a la Pico 1. L'app aplica el mateix límit en crear capes.
    MAX_BANKS = 6

    def __init__(self, config_path='config/tecla_config.json'):
        """Inicialitza el gestor de configuració"""
        self.config_path = config_path
        self.config = self._load_config()
        self.current_bank_index = self.config.get('current_bank', 0)
        self.theme = self.config.get('theme_name', 'default')
        self.button_actions = self.config.get('button_actions', {})
        
    def _load_config(self):
        """Carrega la configuració des del fitxer JSON"""
        try:
            # Comprovar si existeix el fitxer de configuració
            try:
                # En CircuitPython podem provar a obrir el fitxer per veure si existeix
                with open(self.config_path, 'r') as _:
                    pass
            except OSError:
                # El fitxer no existeix, creem la configuració per defecte i la desem
                print("El fitxer de configuració no existeix, creant un nou")
                default_config = self._get_default_config()
                
                # No cal crear directoris, ja existeixen a CircuitPython
                    
                # Guardar la configuració per defecte
                try:
                    with open(self.config_path, 'w') as f:
                        json.dump(default_config, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"Error creant fitxer de configuració: {e}")
                    
                return default_config
                
            # El fitxer existeix: carregar-lo. Si està corromput (escriptura
            # tallada a mig desar/desendollar), provar la còpia .bak que escriu
            # l'app en instal·lar, abans de rendir-se als valors per defecte.
            config = None
            for _path in (self.config_path, self.config_path + '.bak'):
                try:
                    with open(_path, 'r') as f:
                        _cand = json.load(f)
                except (OSError, ValueError):
                    continue
                # Validació bàsica de l'estructura
                if isinstance(_cand, dict) and 'banks' in _cand:
                    config = _cand
                    if _path != self.config_path:
                        print("Avís: config corrupta; recuperada la còpia .bak")
                    break
            if config is None:
                print("Avís: Format de configuració invàlid, utilitzant valors per defecte")
                return self._get_default_config()
            if config:

                # Neteja i compatibilitat: substituir 'Teclat' per 'Silenci'
                # El mode teclat és ara una capa/overlay, no un mode normal
                try:
                    for bank in config.get('banks', []):
                        modes = bank.get('modes', [])
                        # Garantir llista de 16 elements
                        if isinstance(modes, list):
                            # Substituir 'Teclat' per 'Silenci' mantenint marcadors reservats
                            for i in range(len(modes)):
                                if modes[i] == 'Teclat':
                                    modes[i] = 'Silenci'
                            # Ajustar longitud a 16 si cal
                            if len(modes) < 16:
                                modes.extend(['Silenci'] * (16 - len(modes)))
                            bank['modes'] = modes[:16]
                except Exception as e:
                    print(f"Avís: No s'ha pogut netejar la configuració: {e}")
                
                # Migració: copiar camps de nivell superior als bancs si no hi són
                # (configs antigues generades per versions anteriors de la web)
                try:
                    top_pot = config.get('potentiometer_functions')
                    top_arp_pot = config.get('arp_potentiometer_functions')
                    top_scales = config.get('keyboard_scales')
                    top_arp_modes = config.get('arpeggiator_modes')
                    top_chord_types = config.get('chord_types')
                    for bank in config.get('banks', []):
                        if top_pot and 'potentiometer_functions' not in bank:
                            bank['potentiometer_functions'] = top_pot
                        if top_arp_pot and 'arp_potentiometer_functions' not in bank:
                            bank['arp_potentiometer_functions'] = top_arp_pot
                        if top_scales and 'keyboard_scales' not in bank:
                            bank['keyboard_scales'] = top_scales
                        if top_arp_modes and 'arpeggiator_modes' not in bank:
                            bank['arpeggiator_modes'] = top_arp_modes
                        if top_chord_types and 'chord_types' not in bank:
                            bank['chord_types'] = top_chord_types
                except Exception as e:
                    print(f"Avís: No s'ha pogut migrar la configuració: {e}")

                # Migració a CAPES TIPADES (v3): cada banc és 'teclat' o 'modes'.
                # Configs antigues no porten 'type' → són bancs de modes; i si cap
                # banc no és de teclat, se n'afegeix un al final perquè la tecla 13
                # (que ara CICLA les capes) sempre pugui arribar al teclat.
                try:
                    banks = config.get('banks', [])
                    # LÍMIT DUR de capes (RAM): tota la config viu en memòria i
                    # cada capa de teclat pot pesar 1-2KB. Més enllà de MAX_BANKS
                    # el marge per carregar modes es fa perillós → es retallen
                    # (l'app té el mateix límit; això és l'última xarxa).
                    if len(banks) > self.MAX_BANKS:
                        print(f"Avís: {len(banks)} capes; es retallen a {self.MAX_BANKS} (límit de RAM)")
                        del banks[self.MAX_BANKS:]
                        if config.get('current_bank', 0) >= self.MAX_BANKS:
                            config['current_bank'] = 0
                    for bank in banks:
                        if bank.get('type') not in ('teclat', 'modes'):
                            bank['type'] = 'modes'
                    if banks and not any(b.get('type') == 'teclat' for b in banks):
                        banks.append({'name': 'Teclat', 'type': 'teclat',
                                      'modes': ['Silenci'] * 16})
                except Exception as e:
                    print(f"Avís: No s'ha pogut tipar les capes: {e}")
                
                return config
        except (OSError, ValueError) as e:  # ValueError atrapa errors de JSON en CircuitPython
            # Retorna una configuració per defecte si hi ha algun error
            print(f"Error carregant la configuració: {e}. Utilitzant valors per defecte.")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Retorna una configuració per defecte amb els modes favorites i disponibles"""
        # Modes favorites i altres modes populars
        default_modes = [
            'STOP!',      # Botó 1 - Aturada completa de tot so
            'Silenci',    # Botó 2 - Contenció dinàmica (per jugar amb el ritme)
            'Harmonia',   # Botó 3 - Harmonia Celeste (basat en òrbites planetàries)
            'Biomímesi',  # Botó 4 - Biomímesi (basat en ritmes biològics)
            'Mirall',     # Botó 5 - Mirall Quàntic (basat en física quàntica)
            'Jazz',       # Botó 6
            'Cascada',    # Botó 7
            'Pèndol',     # Botó 8
            'Riu',        # Botó 9
            'Matemàtic',  # Botó 10
            'Vida',       # Botó 11
            'Mandelbrot', # Botó 12
            'Caos',       # Botó 13
            'Fractal',    # Botó 14
            'Silenci',    # Botó 15 (reservat per capa teclat)
            'Acords'      # Botó 16
        ]
        
        # Emplenar amb silenci si no hi ha prou modes
        while len(default_modes) < 16:
            default_modes.append('Silenci')
        
        # Crear els bancs per defecte amb còpies independents.
        # El primer és una CAPA DE TECLAT (capes tipades v3): en arrencar de
        # fàbrica el dispositiu comença al teclat i la tecla 13 cicla les capes.
        banks = [{
            'name': 'Teclat',
            'type': 'teclat',
            'modes': ['Silenci'] * 16,
            'keyboard_scales': [0, 1, 4, 5, 7, 8, 13, 15, 18, 19],
            'arpeggiator_modes': list(range(16)),
            'chord_types': ['Major'],
        }]
        bank_names = ['Noise', 'Melodia', 'Natura', 'Ritme']

        for bank_name in bank_names:
            # IMPORTANT: Crear còpies independents per a cada banc
            bank = {
                'name': bank_name,
                'type': 'modes',
                'modes': list(default_modes[:16]),  # Còpia independent
                'keyboard_scales': [0, 1, 4, 5, 7, 8, 13, 15, 18, 19],
                'arpeggiator_modes': list(range(16)),
                'active_progression_id': None,
                'potentiometer_functions': {
                    'pot_x': 'Velocity/Arp Speed (dual)',
                    'pot_y': 'Modulation (CC1)',
                    'pot_z': 'Sustain (CC64)'
                },
                'arp_potentiometer_functions': {
                    'arp_pot_x': 'Arp Speed (BPM)',
                    'arp_pot_y': 'Arp Pattern Selector',
                    'arp_pot_z': 'Gate Length'
                },
                'chord_types': ['Major']
                # NOTE: efectos_temporales ara són globals, no per banc
            }
            banks.append(bank)
        
        return {
            'theme_name': 'default',
            'banks': banks,
            'current_bank': 0,
            'button_actions': {},
            'custom_chord_progressions': [],
            # Sense presets 'Àudio N': el motor d'àudio intern queda reservat
            # per a la propera revisió del maquinari (Pico 2). 'Config Modes'
            # cicla capes de potes (Mescla/Timbre/Expressió) per modificar el
            # mode mentre sona.
            'available_effects': ['Sustain', 'Pausa', 'Gate', 'Modulation', 'PitchBend', 'Harmonia Negativa', 'Config Modes', 'Loop'],
            # Efectes temporals GLOBALS - apliquen a TOTS els bancs
            'efectos_temporales': {
                '13': 'Sustain',
                '14': 'Pausa'
            }
        }
    
    def save_config(self):
        """Guarda la configuració actual al fitxer"""
        try:
            # Validació bàsica abans de desar
            if not isinstance(self.config, dict) or 'banks' not in self.config:
                print("Error: La configuració no és vàlida i no es pot desar")
                return False
                
            # Directoris ja existents a CircuitPython
            
            # Mètode simplificat de guardat per reduir el risc d'errors
            try:
                # Desar directament al fitxer final
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                    f.flush()  # Assegurar que els canvis es desen al disc
                    
                # Forçar una sincronització del sistema de fitxers si està disponible
                try:
                    os.sync()  # Pot no estar disponible en tots els sistemes CircuitPython
                except (AttributeError, NotImplementedError):
                    pass
                    
                return True
            except Exception as e:
                print(f"Error en el guardat directe: {e}")
                # Intentar mètode alternatiu si el directe falla
                try:
                    temp_path = self.config_path + '.tmp'
                    with open(temp_path, 'w') as f:
                        json.dump(self.config, f, indent=2, ensure_ascii=False)
                        f.flush()
                        
                    # Intentar moure el temporal al final
                    try:
                        os.rename(temp_path, self.config_path)
                    except OSError:
                        # Si renomenar falla, copiar manualment
                        with open(temp_path, 'r') as src:
                            with open(self.config_path, 'w') as dst:
                                dst.write(src.read())
                                dst.flush()
                    return True
                except Exception as e2:
                    print(f"Error en el mètode alternatiu de guardat: {e2}")
                    return False
        except Exception as e:
            print(f"Error general en desar la configuració: {e}")
            return False
    
    def get_current_bank(self):
        """Retorna el banc actual"""
        if 0 <= self.current_bank_index < len(self.config['banks']):
            return self.config['banks'][self.current_bank_index]
        return None
    
    def get_available_banks(self):
        """Retorna la llista de tots els bancs disponibles"""
        return [bank['name'] for bank in self.config.get('banks', [])]
    
    def set_current_bank(self, bank_index):
        """Canvia al banc especificat"""
        if 0 <= bank_index < len(self.config['banks']):
            self.current_bank_index = bank_index
            self.config['current_bank'] = bank_index
            # NO guardar al disc - CircuitPython té sistema de fitxers de només lectura durant execució
            # El canvi de banc és temporal i es reseteja al reiniciar
            print(f"Banc canviat a: {self.config['banks'][bank_index]['name']}")
            return True
        return False
    
    def next_bank(self):
        """Canvia al següent banc"""
        new_index = (self.current_bank_index + 1) % len(self.config['banks'])
        return self.set_current_bank(new_index)
    
    def get_mode_for_button(self, button_index, bank_index=None):
        """Retorna el mode assignat a un botó específic"""
        bank = self.get_current_bank() if bank_index is None else \
               self.config['banks'][bank_index]
        if bank and 0 <= button_index < len(bank['modes']):
            return bank['modes'][button_index]
        return None
    
    # Esta función ya está implementada arriba
    # La duplicación fue eliminada
        
    def get_config_hash(self):
        """Genera un hash del CONTINGUT de la configuració (tots els bancs).

        IMPORTANT: el hash ha de ser INDEPENDENT del banc actiu (current_bank_index).
        Si depengués del banc actual, un simple canvi de capa (botó 13) faria
        creure al bucle principal que el fitxer ha canviat i recarregaria la
        config des de disc, revertint el canvi de banc. Per això recorrem TOTS
        els bancs i ignorem quin està seleccionat.
        """
        try:
            banks = self.config.get('banks', [])
            if not banks:
                return 0

            hash_value = 0
            for bank in banks:
                if not bank:
                    continue
                bank_name = bank.get('name', '') or ''
                for char in bank_name:
                    hash_value = (hash_value * 31 + ord(char)) & 0xFFFFFFFF
                for mode in (bank.get('modes', []) or []):
                    if not mode:
                        # slot buit (None / '') -> separador per mantenir posició
                        hash_value = (hash_value * 31 + 35) & 0xFFFFFFFF  # '#'
                        continue
                    for char in mode:
                        hash_value = (hash_value * 31 + ord(char)) & 0xFFFFFFFF
                # separador entre bancs per evitar col·lisions
                hash_value = (hash_value * 31 + 124) & 0xFFFFFFFF  # '|'

            return hash_value
        except Exception as e:
            print(f"Error al calcular el hash de configuración: {e}")
            return 0
    
    def set_mode_for_button(self, button_index, mode_name, bank_index=None):
        """Assigna un mode a un botó específic"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            if 0 <= button_index < len(bank['modes']):
                # Guardar el valor anterior para poder restaurarlo en caso de error
                previous_mode = bank['modes'][button_index]
                
                # Establecer el nuevo modo
                bank['modes'][button_index] = mode_name
                
                # Intentar guardar la configuración
                if self.save_config():
                    return True
                else:
                    # Si no se pudo guardar, restaurar el valor anterior
                    bank['modes'][button_index] = previous_mode
                    print(f"Error: No s'ha pogut desar la configuració del botó {button_index}")
        return False
    
    def get_button_action(self, button_index, action_type='long_press'):
        """Retorna l'acció configurada per un botó"""
        return self.button_actions.get(action_type, {}).get(str(button_index))
    
    def get_keyboard_scales(self, bank_index=None):
        """Retorna les escales configurades per al mode teclat d'un banc
        Inclou escales predefinides (0-23) i progressions custom (1000+)
        """
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            scales = self.config['banks'][bank_idx].get('keyboard_scales', None)
            if scales:  # Non-empty list (empty list treated as unconfigured)
                return list(scales)
        return [0, 1, 4, 5, 7, 8, 13, 15, 18, 19]  # Escales per defecte
    
    def get_keyboard_scales_with_progressions(self, bank_index=None):
        """Retorna escales + progressions fusionades amb IDs únics
        Progressions tenen ID >= 1000
        """
        # Obtenir escales normals
        scales = self.get_keyboard_scales(bank_index)
        
        # Obtenir progressions
        progressions = self.get_all_progressions()
        
        # Afegir progressions amb ID offset de 1000
        result = list(scales)  # Còpia
        for i, prog in enumerate(progressions):
            prog_id = 1000 + i  # ID únic >= 1000
            result.append(prog_id)
        
        return result
    
    def get_progression_by_scale_id(self, scale_id):
        """Si scale_id >= 1000, retorna la progressió corresponent"""
        if scale_id < 1000:
            return None
        
        prog_index = scale_id - 1000
        progressions = self.get_all_progressions()
        
        if 0 <= prog_index < len(progressions):
            return progressions[prog_index]
        return None
    
    def get_scale_name(self, scale_id):
        """Retorna el nom d'una escala o progressió"""
        if scale_id >= 1000:
            # És una progressió
            prog = self.get_progression_by_scale_id(scale_id)
            if prog:
                return f"♪ {prog.get('name', 'Sense nom')}"
            return "♪ Progressió"
        else:
            # És una escala predefinida
            # Aquest mètode s'hauria d'utilitzar al mode_keyboard
            return f"Escala {scale_id}"
    
    def set_keyboard_scales(self, scales, bank_index=None):
        """Assigna les escales disponibles per al mode teclat d'un banc"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            # Guardar el valor anterior per restaurar si hi ha error
            previous_scales = bank.get('keyboard_scales', [0, 1, 4, 5, 7, 8])
            
            # Establir les noves escales
            bank['keyboard_scales'] = scales
            
            # Intentar guardar la configuració
            if self.save_config():
                return True
            else:
                # Si no es pot guardar, restaurar el valor anterior
                bank['keyboard_scales'] = previous_scales
                print("Error: No s'ha pogut desar la configuració d'escales")
        return False
    
    def get_keyboard_keys(self, bank_index=None):
        """Retorna les tonalitats configurades i el seu ordre per al mode teclat del banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        default = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
        if 0 <= bank_idx < len(self.config['banks']):
            return self.config['banks'][bank_idx].get('keyboard_keys', default)
        return default

    def set_keyboard_keys(self, keys, bank_index=None):
        """Assigna les tonalitats disponibles (i el seu ordre) per al mode teclat d'un banc"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            previous = bank.get('keyboard_keys', ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'])
            bank['keyboard_keys'] = keys
            if self.save_config():
                return True
            else:
                bank['keyboard_keys'] = previous
                print("Error: No s'ha pogut desar la configuració de tonalitats")
        return False

    def get_arpeggiator_modes(self, bank_index=None):
        """Retorna els modes d'arpegiador configurats per al mode teclat del banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            # Si no hi ha modes d'arpegiador configurats, retornar tots per defecte
            return bank.get('arpeggiator_modes', list(range(16)))
        return list(range(16))  # Fallback per defecte: tots els 16 modes
    
    def set_arpeggiator_modes(self, arp_modes, bank_index=None):
        """Assigna els modes d'arpegiador disponibles per al mode teclat d'un banc"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            # Guardar el valor anterior per restaurar si hi ha error
            previous_arp_modes = bank.get('arpeggiator_modes', list(range(16)))
            
            # Establir els nous modes d'arpegiador
            bank['arpeggiator_modes'] = arp_modes
            
            # Intentar guardar la configuració
            if self.save_config():
                return True
            else:
                # Si no es pot guardar, restaurar el valor anterior
                bank['arpeggiator_modes'] = previous_arp_modes
                print("Error: No s'ha pogut desar la configuració de modes d'arpegiador")
        return False
    
    def get_all_custom_arps(self):
        """Retorna tots els patrons d'arpegiador personalitzats (per-capa)"""
        return self._bank_or_global('custom_arpeggiator_patterns', []) or []
        
    def get_custom_arp_by_id(self, pattern_id):
        """Retorna un patró d'arpegiador específic pel seu ID"""
        for arp in self.get_all_custom_arps():
            if arp.get('id') == pattern_id:
                return arp
        return None

    # ========== GESTIÓ DE PROGRESSIONS D'ACORDS CUSTOM ==========
    
    def get_all_progressions(self):
        """Retorna totes les progressions d'acords personalitzades (per-capa)"""
        return self._bank_or_global('custom_chord_progressions', []) or []
    
    def get_progression_by_id(self, progression_id):
        """Retorna una progressió específica pel seu ID"""
        progressions = self.get_all_progressions()
        for prog in progressions:
            if prog.get('id') == progression_id:
                return prog
        return None
    
    def create_progression(self, name, chords):
        """Crea una nova progressió d'acords
        Args:
            name: Nom de la progressió
            chords: Llista de diccionaris amb claus: button, root_note, chord_type, octave
        Returns:
            progression_id si té èxit, None si falla
        """
        # Generar un ID únic a partir dels existents. (Abans es derivava de
        # time.monotonic(), que es reinicia a cada arrencada i podia produir
        # IDs duplicats entre sessions.)
        max_n = 0
        for prog in self.get_all_progressions():
            pid = str(prog.get('id', ''))
            if pid.startswith('prog_'):
                try:
                    n = int(pid[5:])
                    if n > max_n:
                        max_n = n
                except ValueError:
                    pass
        progression_id = f"prog_{max_n + 1}"
        
        print(f"🎼 Creant progressió: '{name}' amb ID {progression_id}")
        print(f"   Acords: {len(chords)}")
        
        new_progression = {
            'id': progression_id,
            'name': name,
            'chords': chords
        }
        
        # Assegurar que existeix la llista
        if 'custom_chord_progressions' not in self.config:
            self.config['custom_chord_progressions'] = []
            print("   Llista de progressions creada (era buida)")
        
        # Afegir la nova progressió
        self.config['custom_chord_progressions'].append(new_progression)
        print(f"   Total progressions ara: {len(self.config['custom_chord_progressions'])}")
        
        # Guardar
        print(f"   Guardant al fitxer: {self.config_path}")
        if self.save_config():
            print(f"   ✅ Progressió '{name}' guardada correctament!")
            return progression_id
        else:
            # Si falla, eliminar la progressió afegida
            print(f"   ❌ ERROR: No s'ha pogut guardar la progressió!")
            self.config['custom_chord_progressions'].remove(new_progression)
            return None
    
    def update_progression(self, progression_id, name=None, chords=None):
        """Actualitza una progressió existent"""
        progression = self.get_progression_by_id(progression_id)
        if not progression:
            return False
        
        # Guardar valors anteriors
        old_name = progression.get('name')
        old_chords = progression.get('chords')
        
        # Actualitzar camps
        if name is not None:
            progression['name'] = name
        if chords is not None:
            progression['chords'] = chords
        
        # Guardar
        if self.save_config():
            return True
        else:
            # Restaurar valors anteriors
            progression['name'] = old_name
            progression['chords'] = old_chords
            return False
    
    def delete_progression(self, progression_id):
        """Elimina una progressió"""
        progressions = self.get_all_progressions()
        for i, prog in enumerate(progressions):
            if prog.get('id') == progression_id:
                # Guardar per si cal restaurar
                deleted_prog = progressions.pop(i)
                
                # Guardar
                if self.save_config():
                    return True
                else:
                    # Restaurar si falla
                    progressions.insert(i, deleted_prog)
                    return False
        return False
    
    def get_active_progression(self, bank_index=None):
        """Retorna la progressió activa per al banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            prog_id = bank.get('active_progression_id')
            if prog_id:
                return self.get_progression_by_id(prog_id)
        return None
    
    def set_active_progression(self, progression_id, bank_index=None):
        """Estableix la progressió activa per a un banc"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            old_prog_id = bank.get('active_progression_id')
            
            bank['active_progression_id'] = progression_id
            
            if self.save_config():
                return True
            else:
                bank['active_progression_id'] = old_prog_id
                return False
        return False
    
    # ========== GESTIÓ DE FUNCIONS DELS POTENCIÒMETRES ==========
    
    def get_potentiometer_functions(self, bank_index=None):
        """Retorna les funcions configurades per als potenciòmetres del banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            # Retornar funcions configurades o valors per defecte
            return bank.get('potentiometer_functions', {
                'pot_x': 'Velocity/Arp Speed (dual)',
                'pot_y': 'Modulation (CC1)',
                'pot_z': 'Sustain (CC64)'
            })
        # Fallback per defecte
        return {
            'pot_x': 'Velocity/Arp Speed (dual)',
            'pot_y': 'Modulation (CC1)',
            'pot_z': 'Sustain (CC64)'
        }
    
    def set_potentiometer_functions(self, pot_x, pot_y, pot_z, bank_index=None):
        """Assigna les funcions dels potenciòmetres per al banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            # Guardar valors anteriors per restaurar si hi ha error
            previous_functions = bank.get('potentiometer_functions', {})
            
            # Establir les noves funcions
            bank['potentiometer_functions'] = {
                'pot_x': pot_x,
                'pot_y': pot_y,
                'pot_z': pot_z
            }
            
            # Intentar guardar la configuració
            if self.save_config():
                return True
            else:
                # Si no es pot guardar, restaurar els valors anteriors
                bank['potentiometer_functions'] = previous_functions
                print("Error: No s'han pogut desar les funcions dels potenciòmetres")
        return False
    
    def get_chord_types(self, bank_index=None):
        """Retorna les tipologies d'acord activades per al mode acords del banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            return bank.get('chord_types', ['Major'])
        return ['Major']
    
    def set_chord_types(self, chord_types, bank_index=None):
        """Assigna les tipologies d'acord disponibles per al mode acords del banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            previous = bank.get('chord_types', ['Major'])
            bank['chord_types'] = chord_types
            if self.save_config():
                return True
            else:
                bank['chord_types'] = previous
                return False
        return False
    
    def get_arp_potentiometer_functions(self, bank_index=None):
        """Retorna les funcions configurades per als potenciòmetres de l'arpegiador del banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            # Retornar funcions configurades o valors per defecte
            return bank.get('arp_potentiometer_functions', {
                'arp_pot_x': 'Arp Speed (BPM)',
                'arp_pot_y': 'Arp Pattern Selector',
                'arp_pot_z': 'Gate Length'
            })
        # Fallback per defecte
        return {
            'arp_pot_x': 'Arp Speed (BPM)',
            'arp_pot_y': 'Arp Pattern Selector',
            'arp_pot_z': 'Gate Length'
        }
    
    def set_arp_potentiometer_functions(self, arp_pot_x, arp_pot_y, arp_pot_z, bank_index=None):
        """Assigna les funcions dels potenciòmetres de l'arpegiador per al banc actual"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            # Guardar valors anteriors per restaurar si hi ha error
            previous_functions = bank.get('arp_potentiometer_functions', {})
            
            # Establir les noves funcions
            bank['arp_potentiometer_functions'] = {
                'arp_pot_x': arp_pot_x,
                'arp_pot_y': arp_pot_y,
                'arp_pot_z': arp_pot_z
            }
            
            # Intentar guardar la configuració
            if self.save_config():
                return True
            else:
                # Restaurar valors anteriors si hi ha error
                bank['arp_potentiometer_functions'] = previous_functions
                return False
        return False
    
    def get_available_effects(self):
        """Obté la llista d'efectes disponibles per ciclar"""
        if 'available_effects' in self.config:
            return self.config['available_effects']
        # Valor per defecte si no existeix - Efectes seleccionats
        return ['Sustain', 'Pausa', 'Gate', 'Modulation', 'Pitch Bend']
    
    def set_available_effects(self, effects):
        """Estableix la llista d'efectes disponibles"""
        self.config['available_effects'] = effects
        return self.save_config()
    
    # ========== GESTIÓ D'EFECTES TEMPORALS GLOBALS ==========
    
    def get_global_temporal_effects(self):
        """Retorna els efectes temporals globals (botons 14 i 15)
        Aquests efectes s'apliquen a TOTS els bancs
        """
        return self.config.get('efectos_temporales', {
            '13': 'Sustain',
            '14': 'Pausa'
        })
    
    def set_global_temporal_effects(self, effects_dict):
        """Estableix els efectes temporals globals
        Args:
            effects_dict: Diccionari amb claus '13' i '14' i valors dels noms d'efectes
        """
        old_effects = self.config.get('efectos_temporales', {})
        
        # Actualitzar els efectes temporals globals
        self.config['efectos_temporales'] = effects_dict
        
        # Guardar
        if self.save_config():
            print(f"✓ Efectes temporals globals actualitzats: {effects_dict}")
            return True
        else:
            # Restaurar si falla
            self.config['efectos_temporales'] = old_effects
            print("Error: No s'han pogut guardar els efectes temporals globals")
            return False
    
    def set_temporal_effect_for_button(self, button_index, effect_name):
        """Estableix l'efecte temporal per a un botó específic (13 o 14)
        Args:
            button_index: 13 o 14 (botons 14 i 15 físicament)
            effect_name: Nom de l'efecte (ex: 'Sustain', 'Pausa', etc.)
        """
        if button_index not in [13, 14]:
            print(f"Error: El botó {button_index} no és un botó d'efecte temporal")
            return False
        
        effects = self.get_global_temporal_effects()
        effects[str(button_index)] = effect_name
        
        return self.set_global_temporal_effects(effects)

    def _bank_or_global(self, key, default=None):
        """Valor de configuració amb prioritat de CAPA: primer el banc actual
        (cada capa de teclat porta una còpia pròpia de la seva config), després
        la config global (fallback del firmware) i finalment `default`. És la
        peça que fa que cada capa de teclat soni amb la SEVA configuració."""
        try:
            bank = self.get_current_bank() or {}
            v = bank.get(key, None)
            if v not in (None, [], {}, ''):
                return v
        except Exception:
            pass
        v = self.config.get(key, None)
        return v if v not in (None, [], {}, '') else default

    def get_keyboard_button_functions(self):
        """Retorna les funcions assignades als 16 botons del mode teclat.
        Índexs 12 i 15 sempre retornen 'modes_layer' i 'stop' (blocats).
        Format: llista de 16 strings. Per-capa amb fallback global.
        """
        _default = (
            'note','note','note','note','note','note','note','note',
            'scale','tonality','chord','arp',
            'modes_layer','octave_down','octave_up','stop'
        )
        fns = self._bank_or_global('keyboard_button_functions', None)
        if not fns or len(fns) != 16:
            return list(_default)
        result = list(fns)
        result[12] = 'modes_layer'
        result[15] = 'stop'
        return result

    def get_neg_harmony_type(self):
        """Retorna el tipus d'eix per a l'harmonia negativa (0-7). Per-capa."""
        try:
            v = int(self._bank_or_global('neg_harmony_type', 0) or 0)
            return v if 0 <= v <= 7 else 0
        except (ValueError, TypeError):
            # Valor no numèric a la config: no fer petar el setup del teclat
            return 0

    def get_neg_harmony_axes(self):
        """Retorna la llista d'IDs d'eixos d'harmonia negativa activats.
        Per defecte retorna tots els eixos disponibles (0-7). Per-capa.
        """
        axes = self._bank_or_global('neg_harmony_axes', None)
        if axes and isinstance(axes, list):
            result = []
            for a in axes:
                try:
                    n = int(a)
                except (ValueError, TypeError):
                    continue
                if 0 <= n <= 7:
                    result.append(n)
            if result:
                return result
        return [0, 1, 2, 3, 4, 5, 6, 7]

    def get_midi_channel(self):
        """Retorna el canal MIDI del dispositiu (1-16)"""
        return self.config.get('midi_channel', 1)

    def set_midi_channel(self, channel):
        """Assigna el canal MIDI del dispositiu (1-16)"""
        if not 1 <= channel <= 16:
            return False
        self.config['midi_channel'] = channel
        return self.save_config()


    # (get_chord_potentiometer_functions i get_neg_potentiometer_functions
    #  retirats: les capes de potes d'acords i h.negativa ja no existeixen.)

    def get_audio_potentiometer_functions(self):
        """Mapatge dels 3 potes per cada tecla amb 'synth_cfg' (Config àudio).
        Clau = índex de tecla (string) → {x, y, z}. Per-capa."""
        return self._bank_or_global('audio_potentiometer_functions', {}) or {}

    def get_modes_audio_pot_functions(self):
        """Mapatge dels 3 potes per cada preset 'Àudio N' de la capa de modes
        (efectes tecles 14/15). Clau = nom del preset → {x, y, z}."""
        return self.config.get('modes_audio_pot_functions', {})

    def get_mode_pot_layers(self):
        """Capes de funcions de potes per a MODES en directe (tecla 'Config Modes'
        del firmware MIX). Llista de {name, x, y, z} amb el mateix vocabulari de
        funcions que la resta de potes. Es busca primer al banc actual i després
        a la config global; None si no n'hi ha (el firmware aplica les capes per
        defecte de mix_runner.DEFAULT_MODE_POT_LAYERS)."""
        try:
            bank = self.get_current_bank() or {}
            layers = bank.get('mode_pot_layers') or self.config.get('mode_pot_layers')
            if isinstance(layers, list) and layers:
                return layers
        except Exception:
            pass
        return None

    def get_diatonic_functions(self):
        """Retorna la llista de funcions harmòniques diatòniques activades.
        Per defecte retorna ['diatonic'].
        """
        fns = self._bank_or_global('diatonic_functions', None)
        if fns:
            return list(fns)
        return ['diatonic']

    def get_voice_lead_types(self):
        """Formes de conducció de veus activades (ids). Per defecte, totes. Per-capa."""
        t = self._bank_or_global('voice_lead_types', None)
        if t:
            return list(t)
        return ['proximitat', 'comu', 'baix', 'ascendent', 'obert']
