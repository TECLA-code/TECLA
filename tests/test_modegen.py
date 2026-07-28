"""El generador de modes: del formulari a un mode que sona.

Aquests tests criden el generador REAL (codi/js/tecla-modegen.js, amb node) i
després fan córrer els modes que en surten amb els mocks de maquinari, com
faria el dispositiu. Així una especificació que generi codi trencat, que deixi
notes penjades o que es surti del rang MIDI no arriba mai a l'usuari.
"""
import ast
import importlib
import json
import os
import shutil
import subprocess
import sys
import textwrap

import pytest

from conftest import FakeMidiOut

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN_JS = os.path.join(ROOT, 'codi', 'js', 'tecla-modegen.js')

pytestmark = pytest.mark.skipif(shutil.which('node') is None,
                                reason='cal node per cridar el generador')


# ── Especificacions de prova: els extrems del formulari ────────────────────

def _spec(**canvis):
    base = {
        'cat': 'melodic', 'nom': 'El meu mode', 'escalaIntervals': [0, 2, 4, 5, 7, 9, 11],
        'tonalitat': 0, 'octava': 4, 'passos': 8,
        'patrons': [
            {'graus': [0, 4, 7, 11, 7, 4, 0, 7], 'din': [2, 1, 1, 2, 1, 1, 0, 1]},
            {'graus': [0, 2, 4, 2, 0, -1, 4, 2], 'din': [2, 1, 1, 1, 2, 0, 1, 1]},
        ],
        'articulacio': 55, 'tempoMin': 40, 'tempoMax': 150,
        'veu2': {'on': False, 'interval': -12, 'cada': 3, 'retard': 45},
        'pots': {'x': 'Tempo', 'y': 'Patró', 'z': 'Octava'},
    }
    base.update(canvis)
    return base


CASOS = {
    'senzill': _spec(),
    'veu2': _spec(nom='Contrapunt', veu2={'on': True, 'interval': -12, 'cada': 2, 'retard': 50}),
    'tot_silenci': _spec(nom='Silenci total', patrons=[{'graus': [-1] * 8, 'din': [1] * 8}]),
    'graus_alts': _spec(nom='Graus alts', patrons=[{'graus': [7, 7, 7, 7, 7, 7, 7, 7], 'din': [2] * 8}],
                        octava=7),                       # ha de quedar dins del rang MIDI
    'octava_baixa': _spec(nom='Greu', octava=1, patrons=[{'graus': [0, 1, 2, 3], 'din': [0] * 4}], passos=4),
    'setze_passos': _spec(nom='Setze', passos=16,
                          patrons=[{'graus': list(range(8)) + list(range(8)), 'din': [1] * 16}]),
    'escala_pentatonica': _spec(nom='Penta', escalaIntervals=[0, 2, 4, 7, 9]),
    'tempo_invertit': _spec(nom='Invertit', tempoMin=200, tempoMax=60),   # l'usuari els pot posar del revés
    'articulacio_curta': _spec(nom='Picada', articulacio=15),
    'articulacio_lligada': _spec(nom='Lligada', articulacio=100),
    'pots_cc': _spec(nom='Amb CC', pots={'x': 'Brillantor (CC74)', 'y': 'Modulació (CC1)', 'z': 'Tonalitat'}),
    'pots_buits': _spec(nom='Sense potes', pots={'x': '—', 'y': '—', 'z': '—'}),
    'pots_dinamica': _spec(nom='Dinamic', pots={'x': 'Dinàmica', 'y': 'Articulació', 'z': 'Octava'}),
    'nom_amb_accents': _spec(nom='Cançó de l’Àvia'),
    'nom_rar': _spec(nom='  42 !!  '),
}


# ── Especificacions rítmiques ─────────────────────────────────────────────

_PISTES = [
    {'id': 'bombo', 'nom': 'Bombo', 'nota': 36, 'capa': 0, 'vel': 105},
    {'id': 'caixa', 'nom': 'Caixa', 'nota': 38, 'capa': 1, 'vel': 92},
    {'id': 'charles', 'nom': 'Charles', 'nota': 42, 'capa': 2, 'vel': 70},
    {'id': 'obert', 'nom': 'Obert', 'nota': 46, 'capa': 2, 'vel': 78},
    {'id': 'perc', 'nom': 'Percussió', 'nota': 39, 'capa': 3, 'vel': 85},
]


def _patro(bombo, caixa, charles, obert, perc, baix):
    return {'graella': {'bombo': bombo, 'caixa': caixa, 'charles': charles,
                        'obert': obert, 'perc': perc}, 'baix': baix}


_QUATRE = _patro(
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, -1, -1, -1, 0, -1, -1, -1, 4, -1, -1, -1, 0, -1, -1, -1])
_BUIT = _patro(*([[0] * 16] * 5), [-1] * 16)


def _specr(**canvis):
    base = {
        'cat': 'ritmic', 'nom': 'El meu ritme', 'passos': 16,
        'escalaIntervals': [0, 2, 4, 5, 7, 9, 11], 'tonalitat': 0,
        'pistes': [dict(p) for p in _PISTES], 'patrons': [_QUATRE],
        'baixOn': True, 'baixOctava': 2,
        'bpmMin': 110, 'bpmMax': 150, 'swing': 0,
        'pots': {'x': 'Tempo', 'y': 'Patró', 'z': 'Capes (breakdown)'},
    }
    base.update(canvis)
    return base


CASOS_RIT = {
    'quatre_per_quatre': _specr(),
    'sense_baix': _specr(nom='Sec', baixOn=False),
    'buit': _specr(nom='Buit', patrons=[_BUIT]),
    'swing': _specr(nom='Swing', swing=30),
    'vuit_passos': _specr(nom='Vuit', passos=8,
                          patrons=[_patro([1, 0, 0, 0, 1, 0, 0, 0], [0, 0, 1, 0, 0, 0, 1, 0],
                                          [1, 1, 1, 1, 1, 1, 1, 1], [0] * 8, [0] * 8,
                                          [0, -1, 4, -1, 0, -1, 2, -1])]),
    'trenta_dos': _specr(nom='Trenta-dos', passos=32,
                         patrons=[_patro(*([[1] * 32] * 5), list(range(8)) * 4)]),
    'tot_ple': _specr(nom='Ple', patrons=[_patro(*([[1] * 16] * 5), [0] * 16)]),
    'una_pista': _specr(nom='Nomes bombo', pistes=[dict(_PISTES[0])],
                        patrons=[{'graella': {'bombo': [1, 0, 0, 0] * 4}, 'baix': [-1] * 16}]),
    'dos_patrons': _specr(nom='Dos', patrons=[_QUATRE, _BUIT]),
    'baix_greu': _specr(nom='Baix greu', baixOctava=0, patrons=[_patro(*([[0] * 16] * 5), [0] * 16)]),
    'baix_agut': _specr(nom='Baix agut', baixOctava=4,
                        patrons=[_patro(*([[0] * 16] * 5), [7] * 16)]),
    'bpm_invertit': _specr(nom='Bpm invers', bpmMin=200, bpmMax=60),
    'notes_extremes': _specr(nom='Extrems',
                             pistes=[{'id': 'bombo', 'nom': 'B', 'nota': 0, 'capa': 0, 'vel': 1},
                                     {'id': 'caixa', 'nom': 'C', 'nota': 127, 'capa': 0, 'vel': 127}],
                             patrons=[{'graella': {'bombo': [1] * 16, 'caixa': [1] * 16}, 'baix': [-1] * 16}]),
    'pots_alternatius': _specr(nom='Altres potes',
                               pots={'x': 'Swing', 'y': 'Octava del baix', 'z': 'Brillantor (CC74)'}),
    'pots_buits_rit': _specr(nom='Sense potes rit', pots={'x': '—', 'y': '—', 'z': '—'}),
}


# ── Especificacions de drone ──────────────────────────────────────────────

def _specd(**canvis):
    base = {
        'cat': 'drone', 'nom': 'El meu drone', 'tonalitat': 0, 'octava': 3,
        'brillantor': 80, 'acords': [[0, 7], [0, 4, 7], [0, 3, 7], [0, 4, 7, 11]],
        'moviment': 'Arc', 'movCC': 11, 'movPeriode': 2,
        'movProfunditat': 100, 'movDuty': 50,
        'pots': {'x': 'Moviment (velocitat)', 'y': "Tipus d'acord", 'z': 'Octava'},
    }
    base.update(canvis)
    return base


CASOS_DRONE = {
    'arc': _specd(),
    'gate': _specd(nom='Gate drone', moviment='Gate', movDuty=25),
    'respiracio': _specd(nom='Respira', moviment='Respiració', movPeriode=6),
    'sense_moviment': _specd(nom='Quiet', moviment='Cap'),
    'una_veu': _specd(nom='Pedal', acords=[[0]]),
    'moltes_veus': _specd(nom='Catedral', acords=[[0, 7, 12, 16, 19, 24]]),
    'veus_repetides': _specd(nom='Repetit', acords=[[0, 0, 7, 7, 7]]),   # s'han de fondre
    'veus_desordenades': _specd(nom='Desordre', acords=[[19, 0, 7, 4]]),
    'acord_buit': _specd(nom='Buit drone', acords=[[]]),                 # cau a la fonamental
    'greu_extrem': _specd(nom='Abisme', octava=0, acords=[[0, 7]]),
    'agut_extrem': _specd(nom='Cim', octava=7, acords=[[0, 12, 24, 36]]),
    'profunditat_zero': _specd(nom='Pla', movProfunditat=0),
    'periode_curt': _specd(nom='Tremolo', movPeriode=0.05),
    'cc_brillantor': _specd(nom='Cap al filtre', movCC=74),
    'pots_alternatius_drone': _specd(nom='Potes drone',
                                     pots={'x': 'Brillantor', 'y': 'Profunditat', 'z': 'Tonalitat'}),
    'pots_buits_drone': _specd(nom='Sense potes drone', pots={'x': '—', 'y': '—', 'z': '—'}),
}


# ── Especificacions de textura ────────────────────────────────────────────

def _spect(**canvis):
    base = {
        'cat': 'textura', 'nom': 'La meva textura',
        'densitat': 8, 'jitter': 70, 'notaCentre': 78, 'notaDispersio': 18,
        'velMin': 40, 'velMax': 100, 'duradaMin': 20, 'duradaMax': 120,
        'rafegues': False, 'rafegaNotes': 4, 'rafegaPausa': 4,
        'fonsOn': True, 'fonsNota': 28, 'fonsIntervals': [0, 7], 'fonsVel': 45,
        'moviment': 'Arc', 'movCC': 74, 'movPeriode': 4, 'movProfunditat': 100,
        'pots': {'x': 'Densitat', 'y': 'Zona de notes', 'z': 'Filtre (velocitat)'},
    }
    base.update(canvis)
    return base


CASOS_TEX = {
    'gra': _spect(),
    'sense_fons': _spect(nom='Sense terra', fonsOn=False),
    'rafegues': _spect(nom='Rafegues', rafegues=True, rafegaNotes=6, rafegaPausa=8),
    'regular': _spect(nom='Rellotge', jitter=0),
    'clavat': _spect(nom='Clavat', notaDispersio=0),
    'escampat': _spect(nom='Escampat', notaDispersio=48, notaCentre=60),
    'zona_greu': _spect(nom='Zona greu', notaCentre=12, notaDispersio=24),   # no pot baixar de 0
    'zona_aguda': _spect(nom='Zona aguda', notaCentre=108, notaDispersio=30),  # ni passar de 127
    'densitat_alta': _spect(nom='Enxarxat', densitat=40),
    'densitat_baixa': _spect(nom='Gota a gota', densitat=0.3),
    'notes_llargues': _spect(nom='Nuvol', duradaMin=800, duradaMax=3000),
    'notes_curtissimes': _spect(nom='Espurna', duradaMin=5, duradaMax=8),
    'sense_filtre': _spect(nom='Sec textura', moviment='Cap'),
    'filtre_gate': _spect(nom='Filtre gate', moviment='Gate', movPeriode=0.5),
    'forca_plana': _spect(nom='Forca plana', velMin=90, velMax=90),
    'pots_alternatius_tex': _spect(nom='Potes textura',
                                   pots={'x': 'Dispersió', 'y': 'Atenuació', 'z': 'Fons greu'}),
    'pots_buits_tex': _spect(nom='Sense potes tex', pots={'x': '—', 'y': '—', 'z': '—'}),
}


# ── Especificacions d'ona ─────────────────────────────────────────────────

def _speco(**canvis):
    base = {
        'cat': 'ona', 'nom': 'Ona prova base', 'forma': 'Sinus', 'freq': 2, 'duty': 50,
        'notaBase': 48, 'amplitud': 12, 'desti': 'Nota', 'cc': 74, 'vel': 80,
        'lligat': True, 'durada': 150,
        'quantitza': True, 'escalaIntervals': [0, 2, 4, 5, 7, 9, 11], 'tonalitat': 0,
        'rCaos': 3.7, 'pasAtzar': 3,
        'pots': {'x': 'Freqüència', 'y': 'Nota base', 'z': 'Amplitud'},
    }
    base.update(canvis)
    return base


CASOS_ONA = {
    'sinus': _speco(),
    'quadrada': _speco(nom='Ona prova quadrada', forma='Quadrada', duty=25),
    'triangle': _speco(nom='Ona prova triangle', forma='Triangle'),
    'serra': _speco(nom='Ona prova serra', forma='Serra'),
    'respiracio_ona': _speco(nom='Ona prova respira', forma='Respiració'),
    'atzar': _speco(nom='Ona prova atzar', forma='Atzar', pasAtzar=5),
    'caos': _speco(nom='Ona prova caos', forma='Caos', rCaos=3.9),
    'cromatica': _speco(nom='Cromatica', quantitza=False),
    'pentatonica_ona': _speco(nom='Ona prova penta', escalaIntervals=[0, 2, 4, 7, 9]),
    'cap_a_cc': _speco(nom='Ona prova cc', desti='CC', cc=74),
    'picada': _speco(nom='Ona prova picada', lligat=False, durada=60),
    'molt_lenta': _speco(nom='Ona prova lenta', freq=0.05),
    'molt_rapida': _speco(nom='Ona prova rapida', freq=18),
    'amplitud_1': _speco(nom='Ona prova plana', amplitud=1),
    'amplitud_maxima': _speco(nom='Ona prova ampla', amplitud=48, notaBase=24),
    'base_aguda': _speco(nom='Ona prova aguda', notaBase=108, amplitud=36),   # no pot passar de 127
    'pots_alternatius_ona': _speco(nom='Potes ona',
                                   pots={'x': 'Duty', 'y': 'Força', 'z': 'Paràmetre del caos'}),
    'pots_buits_ona': _speco(nom='Sense potes ona', pots={'x': '—', 'y': '—', 'z': '—'}),
}


# ── Especificacions algorísmiques ─────────────────────────────────────────

def _speca(**canvis):
    base = {
        'cat': 'algoritmic', 'nom': 'El meu algorisme', 'algoritme': 'Euclidià',
        'escalaIntervals': [0, 2, 4, 7, 9], 'tonalitat': 0, 'octava': 4,
        'vel': 92, 'gate': 60, 'bpmMin': 80, 'bpmMax': 160,
        'veus': [
            {'n': 16, 'k': 4, 'rot': 0, 'perc': True, 'nota': 36, 'grau': 0, 'vel': 105},
            {'n': 8, 'k': 3, 'rot': 0, 'perc': True, 'nota': 38, 'grau': 0, 'vel': 92},
        ],
        'regla': 90, 'autN': 16, 'maxVeus': 5, 'llavorAut': None,
        'mkGraus': 5, 'matriu': None,
        'vidaW': 12, 'vidaH': 8, 'llavorVida': None,
        'cx': -0.4, 'cy': 0.6, 'iters': 1,
        'pots': {'x': 'Tempo', 'y': '—', 'z': 'Octava'},
    }
    base.update(canvis)
    return base


_CICLE5 = [[0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 0, 0, 1], [1, 0, 0, 0, 0]]
_GLIDER = [[0] * 12 for _ in range(8)]
for _y, _x in ((1, 2), (2, 3), (3, 1), (3, 2), (3, 3)):
    _GLIDER[_y][_x] = 1

CASOS_ALG = {
    'euclid': _speca(),
    'euclid_tresillo': _speca(nom='Tresillo', veus=[
        {'n': 8, 'k': 3, 'rot': 0, 'perc': True, 'nota': 36, 'grau': 0, 'vel': 100}]),
    'euclid_melodic': _speca(nom='Euclid melodic', veus=[
        {'n': 16, 'k': 5, 'rot': 0, 'perc': False, 'nota': 36, 'grau': 0, 'vel': 90},
        {'n': 12, 'k': 7, 'rot': 3, 'perc': False, 'nota': 36, 'grau': 2, 'vel': 80}]),
    'euclid_girat': _speca(nom='Euclid girat', veus=[
        {'n': 16, 'k': 4, 'rot': 2, 'perc': True, 'nota': 36, 'grau': 0, 'vel': 100}]),
    'euclid_buit': _speca(nom='Euclid buit', veus=[
        {'n': 16, 'k': 0, 'rot': 0, 'perc': True, 'nota': 36, 'grau': 0, 'vel': 100}]),
    'euclid_ple': _speca(nom='Euclid ple', veus=[
        {'n': 8, 'k': 8, 'rot': 0, 'perc': True, 'nota': 36, 'grau': 0, 'vel': 100}]),
    'euclid_quatre_veus': _speca(nom='Euclid quatre', veus=[
        {'n': 16, 'k': 4, 'rot': 0, 'perc': True, 'nota': 36, 'grau': 0, 'vel': 105},
        {'n': 12, 'k': 3, 'rot': 0, 'perc': True, 'nota': 38, 'grau': 0, 'vel': 92},
        {'n': 9, 'k': 5, 'rot': 0, 'perc': True, 'nota': 42, 'grau': 0, 'vel': 70},
        {'n': 7, 'k': 2, 'rot': 0, 'perc': False, 'nota': 36, 'grau': 4, 'vel': 80}]),
    'aut90': _speca(nom='Aut 90', algoritme='Autòmat', regla=90),
    'aut30': _speca(nom='Aut 30', algoritme='Autòmat', regla=30),
    'aut110': _speca(nom='Aut 110', algoritme='Autòmat', regla=110),
    'aut0': _speca(nom='Aut zero', algoritme='Autòmat', regla=0),      # s'extingeix sempre
    'aut255': _speca(nom='Aut ple', algoritme='Autòmat', regla=255),   # s'omple sempre
    'markov': _speca(nom='Markov prova', algoritme='Markov'),
    'markov_cicle': _speca(nom='Markov cicle', algoritme='Markov', mkGraus=5, matriu=_CICLE5),
    'markov_buit': _speca(nom='Markov buit', algoritme='Markov', mkGraus=4,
                          matriu=[[0] * 4 for _ in range(4)]),
    'vida': _speca(nom='Vida prova', algoritme='Joc de la vida', llavorVida=_GLIDER),
    'vida_buida': _speca(nom='Vida buida', algoritme='Joc de la vida',
                         llavorVida=[[0] * 12 for _ in range(8)]),
    'mandel_dins': _speca(nom='Mandel dins', algoritme='Mandelbrot', cx=-0.4, cy=0.0),
    'mandel_fora': _speca(nom='Mandel fora', algoritme='Mandelbrot', cx=1.5, cy=1.5),
    'mandel_iters': _speca(nom='Mandel iters', algoritme='Mandelbrot', cx=-0.75, cy=0.1, iters=5),
    'alg_pots': _speca(nom='Alg potes', pots={'x': 'Densitat', 'y': 'Rotació', 'z': 'Octava'}),
    'alg_pots_buits': _speca(nom='Alg sense potes', pots={'x': '—', 'y': '—', 'z': '—'}),
}


def _genera(specs):
    """Crida el generador amb node i torna {clau: {file, cls, source}}."""
    # Les especificacions entren per stdin: amb -e els arguments de node no són
    # de fiar i així tampoc no toquem el límit de llargada de la línia d'ordres.
    driver = textwrap.dedent(f"""
        import {{ generateMode }} from {json.dumps(GEN_JS)};
        let cru = '';
        process.stdin.on('data', d => cru += d);
        process.stdin.on('end', () => {{
            const out = {{}};
            for (const [k, spec] of Object.entries(JSON.parse(cru))) {{
                const r = generateMode(spec);
                out[k] = {{ file: r.file, cls: r.cls, nom: r.nom, source: r.source }};
            }}
            process.stdout.write(JSON.stringify(out));
        }});
    """)
    res = subprocess.run([shutil.which('node'), '--input-type=module', '-e', driver],
                         input=json.dumps(specs), capture_output=True, text=True)
    assert res.returncode == 0, f'el generador ha petat:\n{res.stderr}'
    return json.loads(res.stdout)


TOTS = dict(CASOS, **CASOS_RIT, **CASOS_DRONE, **CASOS_TEX, **CASOS_ONA, **CASOS_ALG)


@pytest.fixture(scope='module')
def generats():
    return _genera(TOTS)


@pytest.fixture(scope='module')
def modes_importats(generats, tmp_path_factory):
    """Escriu els modes generats FORA de l'arbre de codi i els fa importables.

    Un paquet de Python pot buscar a més d'un lloc: afegint el directori
    temporal al __path__ de 'modes', els modes generats s'importen com si hi
    fossin (i poden fer 'from modes.base_mode import BaseMode') sense deixar
    ni un fitxer dins de codi/device_files. Abans s'hi escrivien i s'hi
    esborraven ~90 fitxers a cada passada, i la sincronització del sistema
    n'anava deixant còpies pel mig.
    """
    import modes as paquet_modes

    tmp = tmp_path_factory.mktemp('modes_generats')
    reals = set(os.listdir(os.path.dirname(paquet_modes.__file__)))
    classes = {}
    paquet_modes.__path__.append(str(tmp))
    try:
        for clau, g in generats.items():
            assert g['file'] not in reals, f'{g["file"]} xocaria amb un mode del firmware'
            (tmp / g['file']).write_text(g['source'])
        importlib.invalidate_caches()
        for clau, g in generats.items():
            mod = importlib.import_module('modes.' + g['file'][:-3])
            classes[clau] = getattr(mod, g['cls'])
        yield classes
    finally:
        try:
            paquet_modes.__path__.remove(str(tmp))
        except ValueError:
            pass
        for clau, g in generats.items():
            sys.modules.pop('modes.' + g['file'][:-3], None)


# ── El codi generat ───────────────────────────────────────────────────────

def test_tots_els_casos_son_python_valid(generats):
    for clau, g in generats.items():
        ast.parse(g['source'])          # peta amb el nom del cas si no ho és


def test_els_noms_de_fitxer_segueixen_la_convencio(generats):
    for clau, g in generats.items():
        assert g['file'].startswith('mode_') and g['file'].endswith('.py'), (clau, g['file'])
        assert g['file'].replace('.py', '').replace('_', '').isalnum(), (clau, g['file'])
        assert g['cls'].startswith('Mode'), (clau, g['cls'])


def test_els_accents_del_nom_no_arriben_al_fitxer(generats):
    assert generats['nom_amb_accents']['file'] == 'mode_canco_de_l_avia.py'
    assert generats['nom_amb_accents']['cls'] == 'ModeCancoDeLAvia'
    # …però el nom que veu l'usuari sí que els conserva
    assert 'ç' in generats['nom_amb_accents']['nom']


def test_un_nom_que_comenca_amb_xifra_dona_un_identificador_valid(generats):
    g = generats['nom_rar']
    assert g['file'] == 'mode_m42.py'
    assert g['cls'].isidentifier()


def test_l_especificacio_viatja_dins_del_fitxer(generats):
    """Perquè el mode es pugui tornar a obrir a l'editor més endavant."""
    for clau, g in generats.items():
        linia = [l for l in g['source'].splitlines() if l.startswith('# TECLA-SPEC ')]
        assert linia, clau
        spec = json.loads(linia[0][len('# TECLA-SPEC '):])
        assert spec['cat'] == TOTS[clau]['cat']
        assert spec['nom'] == TOTS[clau]['nom']


def test_el_mode_passa_la_validacio_de_l_instal_lador(generats):
    """Mateixes condicions que validateModeFile de tecla-modes.js."""
    import re
    for clau, g in generats.items():
        assert re.search(r'class\s+\w+\s*\(\s*BaseMode\s*\)', g['source']), clau
        assert 'def update' in g['source'], clau
        assert 'def cleanup' in g['source'], clau


def test_una_familia_no_implementada_avisa_clarament():
    res = subprocess.run(
        [shutil.which('node'), '--input-type=module', '-e',
         f'import {{ generateMode }} from {json.dumps(GEN_JS)};'
         'try { generateMode({cat:"inventada"}); } catch (e) { process.stdout.write(e.message); }'],
        capture_output=True, text=True)
    assert 'inventada' in res.stdout and 'implementada' in res.stdout


# ── Els modes, corrent ────────────────────────────────────────────────────

def _fes_sonar(cls, potes=(64, 64, 64), voltes=800, dt=0.01, neteja=True):
    """Fa córrer un mode com el bucle del dispositiu, amb rellotge simulat."""
    import time as _t
    midi = FakeMidiOut()
    mode = cls(midi)
    mode.setup()
    real = _t.monotonic
    rellotge = [real()]
    _t.monotonic = lambda: rellotge[0]
    try:
        for _ in range(voltes):
            rellotge[0] += dt
            mode.update(list(potes), [False] * 16)
        if neteja:
            mode.cleanup()
    finally:
        _t.monotonic = real
    return midi, mode


def _balanc(midi):
    """Notes que han quedat sonant (NoteOn sense el seu NoteOff)."""
    vives = {}
    for m in midi.sent:
        t = type(m).__name__
        if t.endswith('NoteOn') and getattr(m, 'velocity', 0) > 0:
            vives[m.note] = vives.get(m.note, 0) + 1
        elif t.endswith('NoteOff') or (t.endswith('NoteOn') and getattr(m, 'velocity', 0) == 0):
            vives[m.note] = vives.get(m.note, 0) - 1
    return {n: c for n, c in vives.items() if c > 0}


@pytest.mark.parametrize('clau', list(TOTS))
def test_el_mode_generat_corre_sense_petar(modes_importats, clau):
    midi, mode = _fes_sonar(modes_importats[clau])
    assert mode.initialized


@pytest.mark.parametrize('clau', list(TOTS))
def test_el_mode_generat_no_deixa_notes_penjades(modes_importats, clau):
    """El pecat capital d'un mode: quedar-se sonant en marxar-ne."""
    midi, mode = _fes_sonar(modes_importats[clau])
    assert not _balanc(midi), f'{clau}: notes vives després de cleanup'


@pytest.mark.parametrize('clau', list(TOTS))
def test_les_notes_queden_dins_del_rang_midi(modes_importats, clau):
    midi, mode = _fes_sonar(modes_importats[clau])
    for m in midi.sent:
        if type(m).__name__.endswith(('NoteOn', 'NoteOff')):
            assert 0 <= m.note <= 127, f'{clau}: nota {m.note}'
            assert 0 <= m.velocity <= 127, f'{clau}: velocity {m.velocity}'


@pytest.mark.parametrize('clau', list(TOTS))
def test_el_mode_sobreviu_a_qualsevol_posicio_dels_potes(modes_importats, clau):
    for potes in ((0, 0, 0), (127, 127, 127), (0, 127, 64), (127, 0, 13)):
        midi, mode = _fes_sonar(modes_importats[clau], potes=potes, voltes=120)
        assert not _balanc(midi), f'{clau} amb potes {potes}'


def test_un_mode_de_silencis_no_envia_cap_nota(modes_importats):
    midi, mode = _fes_sonar(modes_importats['tot_silenci'])
    notes = [m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert not notes


def test_el_mode_sona_de_debo(modes_importats):
    midi, mode = _fes_sonar(modes_importats['senzill'])
    notes = [m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert len(notes) > 5, 'un mode melòdic ha de tocar notes'


def test_la_segona_veu_dobla_la_melodia(modes_importats):
    """Amb la veu secundària a una octava baixa i cada 2 notes, hi ha d'haver
    notes 12 semitons per sota de les de la melodia."""
    midi, _ = _fes_sonar(modes_importats['veu2'])
    notes = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert any((n + 12) in notes for n in notes), 'no hi ha cap octava inferior'


def test_el_pot_de_tempo_canvia_la_velocitat(modes_importats):
    cls = modes_importats['senzill']
    _, lent = _fes_sonar(cls, potes=(64, 0, 64), voltes=20)
    _, rapid = _fes_sonar(cls, potes=(64, 127, 64), voltes=20)
    assert rapid.speed < lent.speed


def test_el_tempo_generat_el_llegeix_la_pantalla(modes_importats):
    """El mode ha de desar el pols a self.speed: és el que llegeix la pantalla
    virtual per dir el tempo en BPM (vegeu mm_update.mode_tempo)."""
    from modes.mm_update import mode_tempo
    _, mode = _fes_sonar(modes_importats['senzill'], potes=(64, 64, 64), voltes=20)
    t = mode_tempo(mode)
    assert t is not None
    assert 20 <= t[0] <= 240, t


def test_el_pot_de_patro_canvia_de_patro(modes_importats):
    cls = modes_importats['senzill']
    _, a = _fes_sonar(cls, potes=(0, 64, 64), voltes=20)
    _, b = _fes_sonar(cls, potes=(127, 64, 64), voltes=20)
    assert a.pat != b.pat


# ── Família rítmica ───────────────────────────────────────────────────────

def _canals(midi):
    """Canal de cada NoteOn enviat."""
    return {getattr(m, 'channel', 0) for m in midi.sent
            if type(m).__name__.endswith('NoteOn') and m.velocity > 0}


def test_la_percussio_va_al_canal_de_bateria(modes_importats):
    """Percussió al canal 10 (índex 9, General MIDI) i baix al canal 1."""
    midi, _ = _fes_sonar(modes_importats['quatre_per_quatre'])
    assert 9 in _canals(midi), 'cap cop de percussió al canal de bateria'
    assert 0 in _canals(midi), 'el baix no ha sonat al canal 1'


def test_sense_baix_nomes_sona_la_percussio(modes_importats):
    midi, _ = _fes_sonar(modes_importats['sense_baix'])
    assert _canals(midi) == {9}


def test_un_patro_buit_no_envia_res(modes_importats):
    midi, _ = _fes_sonar(modes_importats['buit'])
    assert not [m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]


def test_les_notes_de_percussio_son_les_configurades(modes_importats):
    midi, _ = _fes_sonar(modes_importats['quatre_per_quatre'])
    notes = {m.note for m in midi.sent
             if type(m).__name__.endswith('NoteOn') and m.velocity > 0 and getattr(m, 'channel', 0) == 9}
    assert notes <= {36, 38, 42, 46, 39}, notes
    assert 36 in notes, 'el bombo hi ha de ser a totes les negres'


def test_la_dinamica_de_cada_pista_es_respecta(modes_importats):
    # Pot de capes en repòs = hi són totes les pistes
    midi, _ = _fes_sonar(modes_importats['quatre_per_quatre'], potes=(64, 64, 0))
    vels = {}
    for m in midi.sent:
        if type(m).__name__.endswith('NoteOn') and m.velocity > 0 and getattr(m, 'channel', 0) == 9:
            vels[m.note] = m.velocity
    assert vels.get(36) == 105 and vels.get(42) == 70


def test_el_pot_de_capes_retira_pistes(modes_importats):
    """Amb el breakdown al mínim només ha de quedar la capa 0 (el bombo)."""
    cls = modes_importats['quatre_per_quatre']
    ple, _ = _fes_sonar(cls, potes=(64, 64, 0))
    nu, mode = _fes_sonar(cls, potes=(64, 64, 127))
    perc = lambda midi: {m.note for m in midi.sent
                         if type(m).__name__.endswith('NoteOn') and m.velocity > 0
                         and getattr(m, 'channel', 0) == 9}
    assert mode.capa == 0
    assert perc(nu) == {36}, perc(nu)
    assert len(perc(ple)) > 1


def test_el_pot_de_tempo_ritmic_canvia_els_bpm(modes_importats):
    cls = modes_importats['quatre_per_quatre']
    _, lent = _fes_sonar(cls, potes=(64, 0, 64), voltes=30)
    _, rapid = _fes_sonar(cls, potes=(64, 127, 64), voltes=30)
    assert rapid.bpm > lent.bpm
    assert rapid.step_dur < lent.step_dur


def test_el_tempo_ritmic_es_el_que_diu_el_formulari(modes_importats):
    """El pot al màxim ha de donar exactament el BPM de dalt del rang."""
    _, mode = _fes_sonar(modes_importats['quatre_per_quatre'], potes=(64, 127, 64), voltes=30)
    assert round(mode.bpm) == 150
    _, mode = _fes_sonar(modes_importats['quatre_per_quatre'], potes=(64, 0, 64), voltes=30)
    assert round(mode.bpm) == 110


def test_el_swing_desplaça_els_passos_senars(modes_importats):
    """Amb swing, els passos parells duren més que els senars (i el compàs,
    en total, el mateix)."""
    import time as _t
    cls = modes_importats['swing']
    midi = FakeMidiOut()
    mode = cls(midi)
    mode.setup()
    real = _t.monotonic
    rellotge = [real()]
    _t.monotonic = lambda: rellotge[0]
    try:
        durades = []
        anterior = None
        for _ in range(4000):
            rellotge[0] += 0.001
            abans = mode.step
            mode.update([64, 64, 64], [False] * 16)
            if mode.step != abans:
                if anterior is not None:
                    durades.append(rellotge[0] - anterior)
                anterior = rellotge[0]
        parells = durades[0::2]
        senars = durades[1::2]
        assert sum(parells) / len(parells) > sum(senars) / len(senars)
    finally:
        _t.monotonic = real
        mode.cleanup()


def test_sense_swing_tots_els_passos_duren_igual(modes_importats):
    _, mode = _fes_sonar(modes_importats['quatre_per_quatre'], voltes=30)
    assert mode.swing == 0


def test_el_baix_segueix_l_escala_i_la_tonalitat(modes_importats):
    """Graus 0 i 4 de la major sobre C a l'octava 2 → C2 i G2 (24 i 31)."""
    midi, _ = _fes_sonar(modes_importats['quatre_per_quatre'])
    baix = {m.note for m in midi.sent
            if type(m).__name__.endswith('NoteOn') and m.velocity > 0 and getattr(m, 'channel', 0) == 0}
    assert 24 in baix and 31 in baix, baix


def test_el_pot_d_octava_del_baix_transporta(modes_importats):
    cls = modes_importats['pots_alternatius']
    greu, _ = _fes_sonar(cls, potes=(0, 64, 64))
    agut, _ = _fes_sonar(cls, potes=(127, 64, 64))
    b = lambda midi: min((m.note for m in midi.sent
                          if type(m).__name__.endswith('NoteOn') and m.velocity > 0
                          and getattr(m, 'channel', 0) == 0), default=None)
    assert b(greu) is not None and b(agut) is not None
    assert b(agut) > b(greu)


def test_el_ritme_no_deixa_percussio_sonant(modes_importats):
    """Els cops són curts: cap no pot quedar-se obert en marxar del mode."""
    for clau in CASOS_RIT:
        midi, _ = _fes_sonar(modes_importats[clau], voltes=200)
        assert not _balanc(midi), f'{clau}: cops oberts'


# ── Família drone ─────────────────────────────────────────────────────────

def _ccs(midi, cc=None):
    """Valors enviats d'un CC (o de tots)."""
    out = []
    for m in midi.sent:
        if type(m).__name__.endswith('ControlChange'):
            num = getattr(m, 'control', getattr(m, 'cc', None))
            if cc is None or num == cc:
                out.append((num, m.value))
    return out


def test_el_drone_sosté_l_acord(modes_importats):
    """Un drone toca les seves veus i les manté: cap note-off durant la marxa."""
    import time as _t
    midi = FakeMidiOut()
    mode = modes_importats['arc'](midi)
    mode.setup()
    real = _t.monotonic
    rellotge = [real()]
    _t.monotonic = lambda: rellotge[0]
    try:
        # Potes quiets a la posició que ja té el mode (banc 0, octava 3): així
        # no hi ha el remuntatge inicial amb què el drone es fa seu el pot.
        for _ in range(300):
            rellotge[0] += 0.01
            mode.update([0, 64, 0], [False] * 16)
        ons = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
        offs = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOff')]
        assert len(ons) == 2, f'C i la seva quinta: {ons}'
        assert not offs, 'el drone no ha de tallar les notes mentre sona'
    finally:
        _t.monotonic = real
        mode.cleanup()


def test_les_veus_son_els_intervals_configurats(modes_importats):
    """Octava 3, C, intervals 0 i 7 → notes 36 i 43."""
    midi, _ = _fes_sonar(modes_importats['arc'], potes=(0, 64, 0), voltes=50)
    ons = {m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0}
    assert ons == {36, 43}, ons


def test_les_veus_repetides_es_fonen(modes_importats):
    """[0,0,7,7,7] és un acord de dues veus, no de cinc."""
    midi, _ = _fes_sonar(modes_importats['veus_repetides'], potes=(64, 64, 0), voltes=50)
    ons = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert len(ons) == 2, ons


def test_un_acord_buit_cau_a_la_fonamental(modes_importats):
    midi, _ = _fes_sonar(modes_importats['acord_buit'], potes=(64, 64, 0), voltes=50)
    ons = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert len(ons) == 1


def test_les_veus_que_no_caben_no_s_envien(modes_importats):
    """A l'octava 7 amb intervals fins a 36 semitons, les que passen de 108
    s'han de quedar fora en lloc de sortir com a notes absurdes."""
    midi, mode = _fes_sonar(modes_importats['agut_extrem'], voltes=50)
    ons = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert ons, 'alguna veu hi ha de cabre'
    assert all(n <= 108 for n in ons), ons


def test_el_gate_es_una_ona_quadrada(modes_importats):
    """Amb gate i profunditat a fons, el CC només ha de valer 127 o 0."""
    midi, _ = _fes_sonar(modes_importats['gate'], voltes=1200)
    vals = {v for _, v in _ccs(midi, 11)}
    assert vals <= {0, 127}, vals
    assert vals == {0, 127}, 'el gate ha de bategar amunt i avall'


def test_l_arc_recorre_tot_el_camí(modes_importats):
    """El triangle passa per valors intermedis, no només pels extrems."""
    midi, _ = _fes_sonar(modes_importats['arc'], voltes=1200)
    vals = sorted({v for _, v in _ccs(midi, 11)})
    mitjans = [v for v in vals if 20 < v < 107]
    assert len(mitjans) > 10, f'el triangle no gradua: {vals[:20]}'
    assert max(vals) > 115 and min(vals) < 12


def test_la_respiracio_es_mes_suau_que_l_arc(modes_importats):
    """El suavitzat fa que passi més temps a prop dels extrems: hi ha d'haver
    menys valors distints al mig del recorregut que amb el triangle."""
    def mitjans(clau):
        midi, _ = _fes_sonar(modes_importats[clau], voltes=1500)
        return len([v for _, v in _ccs(midi, 11) if 50 < v < 78])
    assert mitjans('respiracio') < mitjans('arc')


def test_sense_moviment_no_s_envia_cap_cc_de_moviment(modes_importats):
    midi, _ = _fes_sonar(modes_importats['sense_moviment'], voltes=600, neteja=False)
    assert not _ccs(midi, 11), 'amb el moviment a Cap no s\'ha d\'enviar cap CC'


def test_la_profunditat_limita_fins_on_baixa(modes_importats):
    """Profunditat 0 = el moviment no s'aparta del màxim."""
    midi, _ = _fes_sonar(modes_importats['profunditat_zero'], voltes=800)
    vals = {v for _, v in _ccs(midi, 11)}
    assert vals <= {127}, vals


def test_el_moviment_pot_anar_a_un_altre_cc(modes_importats):
    midi, _ = _fes_sonar(modes_importats['cc_brillantor'], voltes=800)
    assert _ccs(midi, 74), 'no ha arribat res al CC74'


def test_el_pot_de_velocitat_del_moviment_el_canvia(modes_importats):
    cls = modes_importats['arc']
    _, lent = _fes_sonar(cls, potes=(64, 0, 64), voltes=30)
    _, rapid = _fes_sonar(cls, potes=(64, 127, 64), voltes=30)
    assert rapid.mov_per < lent.mov_per


def test_el_pot_de_tipus_d_acord_canvia_les_veus(modes_importats):
    cls = modes_importats['arc']
    a, ma = _fes_sonar(cls, potes=(0, 64, 64), voltes=40)
    b, mb = _fes_sonar(cls, potes=(127, 64, 64), voltes=40)
    veus = lambda midi: {m.note for m in midi.sent
                         if type(m).__name__.endswith('NoteOn') and m.velocity > 0}
    assert ma.acord != mb.acord
    assert veus(a) != veus(b)


def test_el_pot_d_octava_transporta_el_drone(modes_importats):
    cls = modes_importats['arc']
    greu, mg = _fes_sonar(cls, potes=(64, 64, 0), voltes=40)
    agut, ma = _fes_sonar(cls, potes=(64, 64, 127), voltes=40)
    alt = lambda midi: max(m.note for m in midi.sent
                           if type(m).__name__.endswith('NoteOn') and m.velocity > 0)
    assert mg.octave == 3, 'el pot en repòs ha de donar l\'octava configurada'
    assert ma.octave > mg.octave
    assert alt(agut) > alt(greu)


def test_el_drone_no_te_pols_per_a_la_pantalla(modes_importats):
    """Un drone no té tempo de notes: la pantalla no li ha de treure cap BPM
    del període del moviment (per això el camp no es diu 'speed')."""
    from modes.mm_update import mode_tempo
    for clau in ('arc', 'gate', 'sense_moviment'):
        _, mode = _fes_sonar(modes_importats[clau], voltes=40)
        assert mode_tempo(mode) is None, clau


def test_el_drone_calla_del_tot_en_marxar(modes_importats):
    for clau in CASOS_DRONE:
        midi, _ = _fes_sonar(modes_importats[clau], voltes=200)
        assert not _balanc(midi), f'{clau}: veus obertes'


# ── Família textura ───────────────────────────────────────────────────────

def _gra_notes(midi, fora=()):
    """Notes dels esdeveniments (excloent-ne les del fons sostingut)."""
    return [m.note for m in midi.sent
            if type(m).__name__.endswith('NoteOn') and m.velocity > 0 and m.note not in fora]


def test_la_textura_reparteix_les_notes_per_la_zona(modes_importats):
    """Centre 78 amb dispersió 18: totes entre 60 i 96, i no sempre la mateixa."""
    midi, mode = _fes_sonar(modes_importats['gra'], voltes=3000)
    notes = _gra_notes(midi, fora={28, 35})
    lo, hi = mode.centre - mode.disp, mode.centre + mode.disp
    assert len(notes) > 20, len(notes)
    assert all(lo <= n <= hi for n in notes), (lo, hi, min(notes), max(notes))
    assert len(set(notes)) > 8, 'una textura no pot repetir sempre la mateixa nota'


def test_sense_dispersio_totes_les_notes_son_la_mateixa(modes_importats):
    midi, mode = _fes_sonar(modes_importats['clavat'], voltes=2000)
    assert set(_gra_notes(midi, fora={28, 35})) == {mode.centre}


def test_la_zona_mai_no_surt_del_rang_midi(modes_importats):
    """Amb el centre als extrems i molta dispersió, res per sota de 0 ni per
    sobre de 127 (i els que no hi caben, simplement no sonen)."""
    for clau in ('zona_greu', 'zona_aguda'):
        midi, _ = _fes_sonar(modes_importats[clau], voltes=2000)
        for m in midi.sent:
            if type(m).__name__.endswith(('NoteOn', 'NoteOff')):
                assert 0 <= m.note <= 127, (clau, m.note)


def test_el_fons_greu_es_sosté(modes_importats):
    """El fons entra un cop i es queda: no s'ha de re-disparar cada volta."""
    midi, _ = _fes_sonar(modes_importats['gra'], voltes=1500, neteja=False)
    fons = [m for m in midi.sent
            if type(m).__name__.endswith('NoteOn') and m.velocity > 0 and m.note in (28, 35)]
    assert len(fons) == 2, f'el fons s\'ha re-disparat {len(fons)} cops'


def test_sense_fons_nomes_hi_ha_els_grans(modes_importats):
    midi, mode = _fes_sonar(modes_importats['sense_fons'], voltes=1500)
    ons = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert ons and all(n >= mode.centre - mode.disp for n in ons), 'no hi ha d\'haver res sota la zona'


def test_la_densitat_mana_quants_esdeveniments_hi_ha(modes_importats):
    poc, _ = _fes_sonar(modes_importats['densitat_baixa'], voltes=2000)
    molt, _ = _fes_sonar(modes_importats['densitat_alta'], voltes=2000)
    assert len(_gra_notes(molt, fora={28, 35})) > len(_gra_notes(poc, fora={28, 35})) * 5


def test_la_irregularitat_desiguala_els_intervals(modes_importats):
    """Amb jitter 0 els esdeveniments cauen clavats; amb jitter, no."""
    import time as _t

    def intervals(clau):
        midi = FakeMidiOut()
        mode = modes_importats[clau](midi)
        mode.setup()
        real = _t.monotonic
        rellotge = [real()]
        _t.monotonic = lambda: rellotge[0]
        try:
            quan = []
            vist = 0
            for _ in range(4000):
                rellotge[0] += 0.002
                mode.update([64, 64, 64], [False] * 16)
                ara = len([m for m in midi.sent
                           if type(m).__name__.endswith('NoteOn') and m.velocity > 0])
                if ara != vist:
                    vist = ara
                    quan.append(rellotge[0])
            return [round(b - a, 4) for a, b in zip(quan, quan[1:])]
        finally:
            _t.monotonic = real
            mode.cleanup()

    regulars = intervals('regular')
    irregulars = intervals('gra')
    assert len(set(regulars)) <= 2, f'sense atzar han de caure clavats: {set(regulars)}'
    assert len(set(irregulars)) > 4, f'amb atzar han de variar: {set(irregulars)}'


def test_les_rafegues_disparen_diverses_notes_alhora(modes_importats):
    """Cada dispar de la ràfega són 6 notes en el mateix instant."""
    import time as _t
    midi = FakeMidiOut()
    mode = modes_importats['rafegues'](midi)
    mode.setup()
    real = _t.monotonic
    rellotge = [real()]
    _t.monotonic = lambda: rellotge[0]
    try:
        # Es compten NOMÉS els grans: el fons greu ja sona des del setup i
        # entrava dins de la primera mesura.
        fons = set(mode.fons_notes)
        abans = 0
        maxim = 0
        for _ in range(3000):
            rellotge[0] += 0.002
            mode.update([64, 64, 64], [False] * 16)
            ara = len([m for m in midi.sent
                       if type(m).__name__.endswith('NoteOn') and m.velocity > 0
                       and m.note not in fons])
            maxim = max(maxim, ara - abans)
            abans = ara
        assert maxim == 6, f'la ràfega hauria de disparar 6 notes de cop, no {maxim}'
    finally:
        _t.monotonic = real
        mode.cleanup()


def test_la_forca_es_queda_dins_del_rang_demanat(modes_importats):
    midi, _ = _fes_sonar(modes_importats['forca_plana'], voltes=2000)
    vels = {m.velocity for m in midi.sent
            if type(m).__name__.endswith('NoteOn') and m.velocity > 0 and m.note not in (28, 35)}
    assert vels == {90}, vels


def test_les_notes_llargues_duren_mes(modes_importats):
    """La durada configurada mana quant triga a arribar el note-off."""
    curta, _ = _fes_sonar(modes_importats['notes_curtissimes'], voltes=600, neteja=False)
    llarga, _ = _fes_sonar(modes_importats['notes_llargues'], voltes=600, neteja=False)
    parell = lambda midi: (len([m for m in midi.sent if type(m).__name__.endswith('NoteOff')]),
                           len([m for m in midi.sent
                                if type(m).__name__.endswith('NoteOn') and m.velocity > 0]))
    offs_c, ons_c = parell(curta)
    offs_l, ons_l = parell(llarga)
    assert offs_c / max(1, ons_c) > offs_l / max(1, ons_l)


def test_el_filtre_de_la_textura_escombra(modes_importats):
    midi, _ = _fes_sonar(modes_importats['gra'], voltes=2000)
    vals = sorted({v for _, v in _ccs(midi, 74)})
    assert len([v for v in vals if 20 < v < 107]) > 8, vals[:20]


def test_sense_filtre_la_textura_no_envia_cc(modes_importats):
    midi, _ = _fes_sonar(modes_importats['sense_filtre'], voltes=800, neteja=False)
    assert not _ccs(midi, 74)


def test_el_pot_de_densitat_la_canvia(modes_importats):
    cls = modes_importats['gra']
    _, poc = _fes_sonar(cls, potes=(64, 0, 64), voltes=30)
    _, molt = _fes_sonar(cls, potes=(64, 127, 64), voltes=30)
    assert poc.dens == 8.0, 'el pot en repòs ha de donar la densitat configurada'
    assert molt.dens > poc.dens * 2


def test_el_pot_de_zona_mou_les_notes(modes_importats):
    cls = modes_importats['clavat']
    greu, _ = _fes_sonar(cls, potes=(0, 64, 64), voltes=600)
    agut, _ = _fes_sonar(cls, potes=(127, 64, 64), voltes=600)
    assert max(_gra_notes(agut, fora={28, 35})) > max(_gra_notes(greu, fora={28, 35}))


def test_la_textura_no_te_pols_per_a_la_pantalla(modes_importats):
    """Una textura és atzar, no un tempo: la pantalla no li ha de treure BPM."""
    from modes.mm_update import mode_tempo
    _, mode = _fes_sonar(modes_importats['gra'], voltes=40)
    assert mode_tempo(mode) is None


def test_la_textura_calla_del_tot_en_marxar(modes_importats):
    for clau in CASOS_TEX:
        midi, _ = _fes_sonar(modes_importats[clau], voltes=1500)
        assert not _balanc(midi), f'{clau}: notes obertes'


# ── Família ona ───────────────────────────────────────────────────────────

def _notes_de(midi):
    return [m.note for m in midi.sent
            if type(m).__name__.endswith('NoteOn') and m.velocity > 0]


def test_l_ona_recorre_el_seu_rang(modes_importats):
    """Sinus de C3 amb 12 semitons d'amplitud: hi ha d'haver el greu, l'agut
    i el que hi ha entremig."""
    midi, mode = _fes_sonar(modes_importats['sinus'], potes=(64, 64, 127), voltes=3000)
    notes = set(_notes_de(midi))
    assert len(notes) >= 5, notes
    assert max(notes) - min(notes) >= 10, notes


@pytest.mark.parametrize('clau', ['sinus', 'triangle', 'serra', 'respiracio_ona', 'quadrada'])
def test_cada_forma_dona_un_recorregut_diferent(modes_importats, clau):
    midi, _ = _fes_sonar(modes_importats[clau], potes=(64, 64, 127), voltes=2000)
    assert _notes_de(midi), f'{clau}: no ha tocat res'


def test_la_quadrada_només_té_dos_estats(modes_importats):
    midi, _ = _fes_sonar(modes_importats['quadrada'], potes=(64, 64, 127), voltes=2000)
    assert len(set(_notes_de(midi))) == 2


def test_la_quantitzacio_ajusta_les_notes_a_l_escala(modes_importats):
    """Amb l'escala major sobre C, cap nota pot caure fora dels seus graus."""
    midi, _ = _fes_sonar(modes_importats['sinus'], potes=(64, 64, 127), voltes=3000)
    major = {0, 2, 4, 5, 7, 9, 11}
    fora = {n for n in _notes_de(midi) if n % 12 not in major}
    assert not fora, f'notes fora de l\'escala: {sorted(fora)}'


def test_la_quantitzacio_pentatonica_deixa_menys_graus(modes_importats):
    penta = {0, 2, 4, 7, 9}
    midi, _ = _fes_sonar(modes_importats['pentatonica_ona'], potes=(64, 64, 127), voltes=3000)
    fora = {n for n in _notes_de(midi) if n % 12 not in penta}
    assert not fora, sorted(fora)


def test_sense_quantitzar_l_ona_passa_per_tots_els_semitons(modes_importats):
    """És la diferència entre música i sirena: sense escala hi surten notes
    que la major no té."""
    midi, _ = _fes_sonar(modes_importats['cromatica'], potes=(64, 64, 127), voltes=3000)
    major = {0, 2, 4, 5, 7, 9, 11}
    assert {n for n in _notes_de(midi) if n % 12 not in major}


def test_l_ona_cap_a_cc_no_toca_cap_nota(modes_importats):
    midi, _ = _fes_sonar(modes_importats['cap_a_cc'], voltes=2000)
    assert not _notes_de(midi)
    vals = sorted({v for _, v in _ccs(midi, 74)})
    assert len(vals) > 10, vals


def test_l_ona_no_repeteix_la_nota_a_cada_volta(modes_importats):
    """Només toca quan l'alçada canvia: si no, seria una allau de note-ons.
    Amb una ona lenta, 1500 voltes del bucle han de donar un grapat de notes
    (les alçades per on passa), no una per volta."""
    midi, _ = _fes_sonar(modes_importats['molt_lenta'], voltes=1500)
    n = len(_notes_de(midi))
    assert 0 < n < 75, n


def test_l_ona_lligada_manté_la_nota_fins_al_canvi(modes_importats):
    """Lligada: tants note-offs com canvis d'alçada, ni un més."""
    midi, _ = _fes_sonar(modes_importats['sinus'], potes=(64, 64, 127), voltes=2000, neteja=False)
    ons = len(_notes_de(midi))
    offs = len([m for m in midi.sent if type(m).__name__.endswith('NoteOff')])
    assert offs == ons - 1 or offs == ons, (ons, offs)


def test_l_ona_picada_apaga_la_nota_sola(modes_importats):
    """Sense lligat, la nota es tanca després de la durada encara que l'ona no
    hagi canviat: hi ha d'haver tants note-offs com note-ons."""
    midi, _ = _fes_sonar(modes_importats['picada'], potes=(64, 64, 127), voltes=2000, neteja=False)
    ons = len(_notes_de(midi))
    offs = len([m for m in midi.sent if type(m).__name__.endswith('NoteOff')])
    assert ons > 0 and offs >= ons - 1


def test_el_random_walk_passeja_sense_sortir_del_rang(modes_importats):
    midi, mode = _fes_sonar(modes_importats['atzar'], potes=(64, 64, 127), voltes=4000)
    notes = _notes_de(midi)
    assert len(set(notes)) > 3, 'un random walk ha de moure\'s'
    assert all(0 <= n <= 127 for n in notes)


def test_el_caos_no_es_repeteix(modes_importats):
    """Amb r = 3,9 el mapa logístic no cau mai en un cicle curt."""
    midi, _ = _fes_sonar(modes_importats['caos'], potes=(64, 64, 127), voltes=4000)
    notes = _notes_de(midi)
    assert len(set(notes)) > 4, set(notes)


def test_l_ona_mai_no_surt_del_rang_midi(modes_importats):
    for clau in ('base_aguda', 'amplitud_maxima'):
        midi, _ = _fes_sonar(modes_importats[clau], potes=(64, 64, 127), voltes=2000)
        for m in midi.sent:
            if type(m).__name__.endswith(('NoteOn', 'NoteOff')):
                assert 0 <= m.note <= 127, (clau, m.note)


def test_el_pot_de_frequencia_la_canvia(modes_importats):
    cls = modes_importats['sinus']
    _, lenta = _fes_sonar(cls, potes=(64, 0, 64), voltes=30)
    _, rapida = _fes_sonar(cls, potes=(64, 127, 64), voltes=30)
    assert lenta.freq == 2.0, 'el pot en repòs ha de donar la freqüència configurada'
    assert rapida.freq > lenta.freq * 3


def test_el_pot_d_amplitud_estreny_el_recorregut(modes_importats):
    cls = modes_importats['sinus']
    estret, _ = _fes_sonar(cls, potes=(64, 64, 0), voltes=2000)
    ample, _ = _fes_sonar(cls, potes=(64, 64, 127), voltes=2000)
    volta = lambda midi: max(_notes_de(midi)) - min(_notes_de(midi))
    assert volta(ample) > volta(estret)


def test_l_ona_no_te_pols_per_a_la_pantalla(modes_importats):
    from modes.mm_update import mode_tempo
    _, mode = _fes_sonar(modes_importats['sinus'], voltes=40)
    assert mode_tempo(mode) is None


def test_l_ona_calla_del_tot_en_marxar(modes_importats):
    for clau in CASOS_ONA:
        midi, _ = _fes_sonar(modes_importats[clau], potes=(64, 64, 127), voltes=2000)
        assert not _balanc(midi), f'{clau}: notes obertes'


# ── Família algorísmica ───────────────────────────────────────────────────

def _js(expr):
    """Avalua una expressió amb el generador carregat i torna el JSON."""
    driver = (f'import * as G from {json.dumps(GEN_JS)};'
              f'process.stdout.write(JSON.stringify({expr}));')
    res = subprocess.run([shutil.which('node'), '--input-type=module', '-e', driver],
                         capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_l_euclidia_reparteix_com_diu_la_teoria():
    """Els repartiments euclidians clàssics: E(3,8) és el tresillo cubà,
    E(5,8) el cinquillo i E(5,16) el bossa-nova."""
    assert _js('G.euclid(3, 8)') == [0, 0, 1, 0, 0, 1, 0, 1]
    assert sum(_js('G.euclid(5, 8)')) == 5
    assert sum(_js('G.euclid(5, 16)')) == 5
    assert _js('G.euclid(4, 16)') == [0, 0, 0, 1] * 4
    assert _js('G.euclid(0, 8)') == [0] * 8
    assert _js('G.euclid(8, 8)') == [1] * 8


def test_l_euclidia_del_python_i_el_del_javascript_diuen_el_mateix(modes_importats):
    """El dibuix del formulari surt del JS i el que sona, del Python: si
    divergissin, el collaret ensenyaria un ritme i en sonaria un altre."""
    midi = FakeMidiOut()
    mode = modes_importats['euclid'](midi)
    for k in range(0, 17):
        for n in (8, 12, 16):
            kk = min(k, n)
            assert list(mode._euclid(kk, n)) == _js(f'G.euclid({kk}, {n})'), (kk, n)


def test_el_tresillo_toca_on_toca(modes_importats):
    """E(3,8) al bombo: tres cops per cada vuit passos, sempre als mateixos."""
    midi, _ = _fes_sonar(modes_importats['euclid_tresillo'], potes=(64, 64, 64), voltes=2000)
    ons = [m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert ons and all(m.note == 36 for m in ons)
    assert all(getattr(m, 'channel', 0) == 9 for m in ons), 'ha d\'anar al canal de bateria'


def test_les_veus_euclidianes_fan_polirítmia(modes_importats):
    """Amb llargades diferents (16, 12, 9, 7) el conjunt no es repeteix fins
    al mínim comú múltiple: això és el que fa que no soni a bucle."""
    midi, mode = _fes_sonar(modes_importats['euclid_quatre_veus'], voltes=3000)
    ons = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert len(set(ons)) >= 3, set(ons)
    # Cada veu ha avançat pel seu compte
    assert len(set(mode.pas_veu)) > 1, mode.pas_veu


def test_una_veu_euclidiana_buida_no_toca(modes_importats):
    midi, _ = _fes_sonar(modes_importats['euclid_buit'], voltes=1500)
    assert not [m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]


def test_una_veu_euclidiana_plena_toca_cada_pas(modes_importats):
    midi, mode = _fes_sonar(modes_importats['euclid_ple'], voltes=800, neteja=False)
    ons = len([m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0])
    assert ons == mode.step, (ons, mode.step)


def test_el_gir_desplaça_el_ritme(modes_importats):
    """El mateix K/N girat ha de caure en passos diferents."""
    import time as _t

    def quan(clau):
        midi = FakeMidiOut()
        mode = modes_importats[clau](midi)
        mode.setup()
        real = _t.monotonic
        rell = [real()]
        _t.monotonic = lambda: rell[0]
        try:
            passos = []
            vist = 0
            for _ in range(600):
                rell[0] += 0.005
                mode.update([64, 64, 64], [False] * 16)
                ara = len([m for m in midi.sent
                           if type(m).__name__.endswith('NoteOn') and m.velocity > 0])
                if ara != vist:
                    vist = ara
                    passos.append(mode.step % 16)
            return passos[:4]
        finally:
            _t.monotonic = real
            mode.cleanup()

    assert quan('euclid_girat') != quan('euclid'), 'el gir no ha canviat res'


def test_la_veu_melodica_va_al_canal_de_notes(modes_importats):
    midi, _ = _fes_sonar(modes_importats['euclid_melodic'], voltes=1500)
    ons = [m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert ons and all(getattr(m, 'channel', 0) == 0 for m in ons)


def test_l_automat_del_python_i_el_del_javascript_diuen_el_mateix(modes_importats):
    """L'evolució que dibuixa el formulari ha de ser la que sonarà."""
    midi = FakeMidiOut()
    mode = modes_importats['aut90'](midi)
    mode.setup()
    fila = list(mode.fila)
    for regla in (90, 30, 110, 150, 22):
        mode.regla = regla
        mode.fila = list(fila)
        mode._generacio()
        esperat = _js(f'G.wolfram({json.dumps(fila)}, {regla})')
        assert list(mode.fila) == esperat, (regla, list(mode.fila), esperat)


def test_la_regla_90_dibuixa_sierpinski(modes_importats):
    """Des d'una sola cèl·lula, la regla 90 dona el triangle de Sierpinski:
    la segona generació té exactament dues cèl·lules, i la tercera, dues."""
    midi = FakeMidiOut()
    mode = modes_importats['aut90'](midi)
    mode.setup()
    assert sum(mode.fila) == 1, 'la llavor és una sola cèl·lula'
    mode._generacio()
    assert sum(mode.fila) == 2
    mode._generacio()
    assert sum(mode.fila) == 2      # 1 0 1 amb el buit al mig… i els extrems


def test_cada_regla_té_la_seva_densitat(modes_importats):
    """Les regles clàssiques han de sonar diferent les unes de les altres."""
    dens = {}
    for clau in ('aut90', 'aut30', 'aut110'):
        midi, _ = _fes_sonar(modes_importats[clau], voltes=2500)
        dens[clau] = len([m for m in midi.sent
                          if type(m).__name__.endswith('NoteOn') and m.velocity > 0])
    assert len(set(dens.values())) == 3, dens
    assert all(v > 0 for v in dens.values()), dens


def test_un_automat_que_s_extingeix_torna_a_sembrar(modes_importats):
    """La regla 0 mata tothom a la primera generació. En comptes de quedar-se
    mut per sempre, el mode torna a sembrar."""
    midi, mode = _fes_sonar(modes_importats['aut0'], voltes=2000)
    assert sum(mode.fila) > 0, 'ha quedat tot mort'
    assert [m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]


def test_l_automat_no_passa_del_maxim_de_veus(modes_importats):
    """La regla 255 omple la fila sencera: sense el límit, sonarien 16 notes
    de cop a cada generació."""
    import time as _t
    midi = FakeMidiOut()
    mode = modes_importats['aut255'](midi)
    mode.setup()
    real = _t.monotonic
    rell = [real()]
    _t.monotonic = lambda: rell[0]
    try:
        abans = 0
        maxim = 0
        for _ in range(2000):
            rell[0] += 0.005
            mode.update([64, 64, 64], [False] * 16)
            ara = len([m for m in midi.sent
                       if type(m).__name__.endswith('NoteOn') and m.velocity > 0])
            maxim = max(maxim, ara - abans)
            abans = ara
        assert maxim == 5, maxim
    finally:
        _t.monotonic = real
        mode.cleanup()


def test_markov_amb_una_matriu_de_cicle_fa_un_cicle(modes_importats):
    """Si de cada grau només s'hi pot anar al següent, la seqüència ha de ser
    exactament I-II-III-IV-V-I-… per molt atzar que hi hagi pel mig."""
    midi = FakeMidiOut()
    mode = modes_importats['markov_cicle'](midi)
    mode.setup()
    graus = [mode.grau]
    for _ in range(30):
        mode.grau = mode._tria()
        graus.append(mode.grau)
    esperat = [(graus[0] + i) % 5 for i in range(len(graus))]
    assert graus == esperat, graus


def test_markov_amb_una_matriu_buida_no_es_penja(modes_importats):
    """Tots els pesos a zero: ha de triar a l'atzar en lloc de dividir per zero."""
    midi = FakeMidiOut()
    mode = modes_importats['markov_buit'](midi)
    mode.setup()
    tries = {mode._tria() for _ in range(60)}
    assert len(tries) > 1
    assert all(0 <= g < 4 for g in tries)


def test_markov_es_queda_dins_dels_graus(modes_importats):
    midi, _ = _fes_sonar(modes_importats['markov'], voltes=2000)
    notes = [m.note for m in midi.sent
             if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    penta = {0, 2, 4, 7, 9}
    assert notes and all(n % 12 in penta for n in notes), sorted({n % 12 for n in notes})


def test_el_planador_es_mou(modes_importats):
    """El planador de Conway s'ha de desplaçar per la graella, no quedar-se
    quiet: quatre generacions després és el mateix dibuix però mogut."""
    midi = FakeMidiOut()
    mode = modes_importats['vida'](midi)
    mode.setup()
    inicial = [list(f) for f in mode.g]
    for _ in range(4):
        mode._generacio()
    assert mode.g != inicial, 'el planador no s\'ha mogut'
    assert mode._viva() == 5, 'un planador sempre té cinc cèl·lules'


def test_la_vida_del_python_i_la_del_javascript_diuen_el_mateix(modes_importats):
    midi = FakeMidiOut()
    mode = modes_importats['vida'](midi)
    mode.setup()
    g0 = [list(f) for f in mode.g]
    mode._generacio()
    assert [list(f) for f in mode.g] == _js(f'G.vida({json.dumps(g0)})')


def test_una_vida_extingida_torna_a_sembrar(modes_importats):
    midi, mode = _fes_sonar(modes_importats['vida_buida'], voltes=1500)
    assert mode._viva() > 0, 'ha quedat buida per sempre'


def test_la_vida_reparteix_la_forca_per_poblacio(modes_importats):
    """Com més poblada la columna, més fort sona: no totes les notes poden
    tenir la mateixa força."""
    midi, _ = _fes_sonar(modes_importats['vida'], voltes=2500)
    vels = {m.velocity for m in midi.sent
            if type(m).__name__.endswith('NoteOn') and m.velocity > 0}
    assert len(vels) > 1, vels


def test_l_orbita_de_mandelbrot_no_s_escapa_dins_del_conjunt(modes_importats):
    """c = −0,4 és dins del conjunt: l'òrbita no ha de fugir mai, i per tant
    el mode no s'ha de reiniciar."""
    midi = FakeMidiOut()
    mode = modes_importats['mandel_dins'](midi)
    mode.setup()
    for _ in range(400):
        mode._orbita()
        assert mode.zx * mode.zx + mode.zy * mode.zy <= 4.0


def test_l_orbita_de_fora_del_conjunt_es_reinicia(modes_importats):
    """c = 1,5 + 1,5i s'escapa de seguida: el mode ha de tornar a l'origen en
    lloc de desbordar amb números infinits."""
    midi, mode = _fes_sonar(modes_importats['mandel_fora'], voltes=1500)
    assert abs(mode.zx) < 1e6 and abs(mode.zy) < 1e6
    notes = [m.note for m in midi.sent
             if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert notes and all(0 <= n <= 127 for n in notes)


def test_mandelbrot_dona_una_seqüencia_que_no_es_repeteix_de_seguida(modes_importats):
    midi, _ = _fes_sonar(modes_importats['mandel_iters'], voltes=2500)
    notes = [m.note for m in midi.sent
             if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert len(set(notes)) >= 3, set(notes)


def test_el_pot_de_densitat_omple_l_euclidia(modes_importats):
    cls = modes_importats['alg_pots']
    poc, _ = _fes_sonar(cls, potes=(64, 0, 64), voltes=1500)
    molt, _ = _fes_sonar(cls, potes=(64, 127, 64), voltes=1500)
    n = lambda midi: len([m for m in midi.sent
                          if type(m).__name__.endswith('NoteOn') and m.velocity > 0])
    assert n(molt) > n(poc), (n(poc), n(molt))


def test_el_pot_de_regla_canvia_l_automat(modes_importats):
    cls = modes_importats['aut90']
    # amb la regla al pot Y (que aquí és '—'), la provem directament
    midi = FakeMidiOut()
    mode = cls(midi)
    mode.setup()
    mode.regla = 30
    mode._generacio()
    assert mode.regla == 30


def test_amb_els_potes_en_repos_l_automat_manté_la_regla_que_has_triat(modes_importats):
    """Regressió: amb el pot de regla mapejat a 0–255 en cru, un pot a zero
    et posava la regla 0 i la que havies configurat es perdia només d'engegar.
    La llista de regles comença per la teva."""
    spec = _speca(nom='Regla mantinguda', algoritme='Autòmat', regla=110,
                  pots={'x': 'Tempo', 'y': 'Regla', 'z': 'Octava'})
    g = _genera({'r': spec})['r']
    assert '_REGLES = (110,' in g['source'], g['source'][:400]


def test_amb_els_potes_en_repos_mandelbrot_manté_el_punt_que_has_triat(modes_importats):
    """Els potes de c hi SUMEN: el punt que has clicat es respecta."""
    spec = _speca(nom='Punt mantingut', algoritme='Mandelbrot', cx=-0.75, cy=0.1,
                  pots={'x': 'Part real de c', 'y': 'Part imaginària de c', 'z': 'Octava'})
    g = _genera({'m': spec})['m']
    assert '_CX = -0.75' in g['source']
    assert 'self.cx = _CX + (v / 127.0)' in g['source']


def test_amb_el_pot_de_densitat_al_minim_l_euclidia_toca_el_que_has_posat(tmp_path_factory):
    """Amb K=3 sobre 8 i el pot de densitat a zero han de sonar tres cops per
    compàs, no cap (abans el mapatge portava el mínim cap al silenci)."""
    import time as _t
    spec = _speca(nom='Densitat minima', veus=[
        {'n': 8, 'k': 3, 'rot': 0, 'perc': True, 'nota': 36, 'grau': 0, 'vel': 100}],
        pots={'x': 'Densitat', 'y': '—', 'z': '—'})
    g = _genera({'d': spec})['d']
    import modes as paquet_modes
    tmp = tmp_path_factory.mktemp('densitat')
    (tmp / g['file']).write_text(g['source'])
    paquet_modes.__path__.append(str(tmp))
    try:
        importlib.invalidate_caches()
        mod = importlib.import_module('modes.' + g['file'][:-3])
        midi = FakeMidiOut()
        mode = getattr(mod, g['cls'])(midi)
        mode.setup()
        real = _t.monotonic
        rell = [real()]
        _t.monotonic = lambda: rell[0]
        try:
            for _ in range(200):
                rell[0] += 0.01
                mode.update([0, 0, 0], [False] * 16)     # tots els potes al mínim
        finally:
            _t.monotonic = real
            mode.cleanup()
        assert sum(mode.patrons[0]) == 3, list(mode.patrons[0])
        ons = len([m for m in midi.sent
                   if type(m).__name__.endswith('NoteOn') and m.velocity > 0])
        assert ons > 0
    finally:
        try:
            paquet_modes.__path__.remove(str(tmp))
        except ValueError:
            pass
        sys.modules.pop('modes.' + g['file'][:-3], None)


def test_amb_els_potes_en_repos_els_modes_sonen_com_els_has_fet(modes_importats):
    """LA propietat del constructor: si dissenyes una cosa i la fas sonar, has
    de sentir ALLÒ. Els potes exploren a partir del que has configurat, no li
    imposen la seva posició.

    Trobat exportant modes de debò: el ritme sonava pelat (el breakdown en
    repòs retirava totes les pistes menys el bombo) i els drones sonaven una
    octava per sota de la triada.
    """
    ref = {
        # família        atribut      el que diu el formulari
        'senzill':      [('speed', 60 / 40), ('artic', 0.55), ('vel_k', 1.0), ('pat', 0)],
        'quatre_per_quatre': [('capa', 3), ('swing', 0.0), ('oct_baix', 2)],
        'arc':          [('octave', 3), ('acord', 0), ('vel', 80), ('mov_per', 2.0)],
        'gra':          [('dens', 8.0), ('centre', 78), ('disp', 18), ('vol', 1.0),
                         ('fons_vel', 45), ('mov_per', 4.0)],
        'sinus':        [('freq', 2.0), ('base', 48), ('amp', 1.0), ('duty', 0.5), ('vel', 80)],
        'euclid':       [('rot', 0), ('dens', 0.0), ('octave', 4)],
        'markov':       [('atzar', 0.0), ('abast', 2), ('octave', 4)],
    }
    dolents = []
    for clau, camps in ref.items():
        _, mode = _fes_sonar(modes_importats[clau], potes=(0, 0, 0), voltes=60)
        for camp, esperat in camps:
            real = getattr(mode, camp, '(no hi és)')
            if isinstance(esperat, float):
                if abs(real - esperat) > 1e-6:
                    dolents.append(f'{clau}.{camp}: {real} en lloc de {esperat}')
            elif real != esperat:
                dolents.append(f'{clau}.{camp}: {real} en lloc de {esperat}')
    assert not dolents, 'els potes en repòs canvien el disseny:\n  ' + '\n  '.join(dolents)


def test_tots_els_algorismes_toquen_alguna_cosa(modes_importats):
    for clau in CASOS_ALG:
        if clau in ('euclid_buit',):
            continue
        midi, _ = _fes_sonar(modes_importats[clau], voltes=1500)
        ons = [m for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
        assert ons, f'{clau}: no ha sonat res'


def test_cap_algorisme_deixa_notes_penjades(modes_importats):
    for clau in CASOS_ALG:
        midi, _ = _fes_sonar(modes_importats[clau], voltes=1500)
        assert not _balanc(midi), f'{clau}: notes obertes'


def test_el_doble_clic_canvia_la_tonalitat(modes_importats):
    import time as _t
    midi = FakeMidiOut()
    mode = modes_importats['senzill'](midi)
    mode.setup()
    real = _t.monotonic
    rellotge = [real()]
    _t.monotonic = lambda: rellotge[0]
    try:
        tonalitat = mode.key
        for estat in (True, False, True, False):      # dos tocs seguits
            rellotge[0] += 0.1
            estats = [False] * 16
            estats[0] = estat
            mode.update([64, 64, 64], estats)
        assert mode.key == (tonalitat + 1) % 12
    finally:
        _t.monotonic = real
        mode.cleanup()
