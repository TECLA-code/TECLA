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


@pytest.fixture(scope='module')
def generats():
    return _genera(CASOS)


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
        assert spec['cat'] == 'melodic'
        assert spec['nom'] == CASOS[clau]['nom']


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
         'try { generateMode({cat:"ritmic"}); } catch (e) { process.stdout.write(e.message); }'],
        capture_output=True, text=True)
    assert 'ritmic' in res.stdout and 'implementada' in res.stdout


# ── Els modes, corrent ────────────────────────────────────────────────────

def _fes_sonar(cls, potes=(64, 64, 64), voltes=800, dt=0.01):
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


@pytest.mark.parametrize('clau', list(CASOS))
def test_el_mode_generat_corre_sense_petar(modes_importats, clau):
    midi, mode = _fes_sonar(modes_importats[clau])
    assert mode.initialized


@pytest.mark.parametrize('clau', list(CASOS))
def test_el_mode_generat_no_deixa_notes_penjades(modes_importats, clau):
    """El pecat capital d'un mode: quedar-se sonant en marxar-ne."""
    midi, mode = _fes_sonar(modes_importats[clau])
    assert not _balanc(midi), f'{clau}: notes vives després de cleanup'


@pytest.mark.parametrize('clau', list(CASOS))
def test_les_notes_queden_dins_del_rang_midi(modes_importats, clau):
    midi, mode = _fes_sonar(modes_importats[clau])
    for m in midi.sent:
        if type(m).__name__.endswith(('NoteOn', 'NoteOff')):
            assert 0 <= m.note <= 127, f'{clau}: nota {m.note}'
            assert 0 <= m.velocity <= 127, f'{clau}: velocity {m.velocity}'


@pytest.mark.parametrize('clau', list(CASOS))
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
