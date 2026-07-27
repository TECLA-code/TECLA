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


TOTS = dict(CASOS, **CASOS_RIT, **CASOS_DRONE)


@pytest.fixture(scope='module')
def generats():
    return _genera(TOTS)


@pytest.fixture(scope='module')
def modes_importats(generats, tmp_path_factory):
    """Escriu els modes generats a un paquet 'modes' temporal i els importa."""
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                        'codi', 'device_files', 'modes')
    dest = os.path.abspath(dest)
    escrits = []
    classes = {}
    try:
        for clau, g in generats.items():
            ruta = os.path.join(dest, g['file'])
            assert not os.path.exists(ruta), f'{g["file"]} xocaria amb un mode existent'
            with open(ruta, 'w') as f:
                f.write(g['source'])
            escrits.append(ruta)
        for clau, g in generats.items():
            mod = importlib.import_module('modes.' + g['file'][:-3])
            importlib.reload(mod)
            classes[clau] = getattr(mod, g['cls'])
        yield classes
    finally:
        for r in escrits:
            try:
                os.remove(r)
            except OSError:
                pass
            for c in (r + 'c', r.replace('.py', '.pyc')):
                if os.path.exists(c):
                    os.remove(c)
        cache = os.path.join(dest, '__pycache__')
        if os.path.isdir(cache):
            for f in os.listdir(cache):
                if any(os.path.basename(r)[:-3] in f for r in escrits):
                    try:
                        os.remove(os.path.join(cache, f))
                    except OSError:
                        pass


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
         'try { generateMode({cat:"textura"}); } catch (e) { process.stdout.write(e.message); }'],
        capture_output=True, text=True)
    assert 'textura' in res.stdout and 'implementada' in res.stdout


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
    midi, _ = _fes_sonar(modes_importats['quatre_per_quatre'])
    vels = {}
    for m in midi.sent:
        if type(m).__name__.endswith('NoteOn') and m.velocity > 0 and getattr(m, 'channel', 0) == 9:
            vels[m.note] = m.velocity
    assert vels.get(36) == 105 and vels.get(42) == 70


def test_el_pot_de_capes_retira_pistes(modes_importats):
    """Amb el breakdown al mínim només ha de quedar la capa 0 (el bombo)."""
    cls = modes_importats['quatre_per_quatre']
    ple, _ = _fes_sonar(cls, potes=(64, 64, 127))
    nu, mode = _fes_sonar(cls, potes=(64, 64, 0))
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
            mode.update([0, 64, 64], [False] * 16)
        ons = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
        offs = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOff')]
        assert len(ons) == 2, f'C i la seva quinta: {ons}'
        assert not offs, 'el drone no ha de tallar les notes mentre sona'
    finally:
        _t.monotonic = real
        mode.cleanup()


def test_les_veus_son_els_intervals_configurats(modes_importats):
    """Octava 3, C, intervals 0 i 7 → notes 36 i 43."""
    midi, _ = _fes_sonar(modes_importats['arc'], potes=(0, 64, 64), voltes=50)
    ons = {m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0}
    assert ons == {36, 43}, ons


def test_les_veus_repetides_es_fonen(modes_importats):
    """[0,0,7,7,7] és un acord de dues veus, no de cinc."""
    midi, _ = _fes_sonar(modes_importats['veus_repetides'], voltes=50)
    ons = [m.note for m in midi.sent if type(m).__name__.endswith('NoteOn') and m.velocity > 0]
    assert len(ons) == 2, ons


def test_un_acord_buit_cau_a_la_fonamental(modes_importats):
    midi, _ = _fes_sonar(modes_importats['acord_buit'], voltes=50)
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
    greu, _ = _fes_sonar(cls, potes=(64, 64, 0), voltes=40)
    agut, _ = _fes_sonar(cls, potes=(64, 64, 127), voltes=40)
    baix = lambda midi: min(m.note for m in midi.sent
                            if type(m).__name__.endswith('NoteOn') and m.velocity > 0)
    assert baix(agut) > baix(greu)


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
