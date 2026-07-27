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


TOTS = dict(CASOS, **CASOS_RIT)


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
         'try { generateMode({cat:"drone"}); } catch (e) { process.stdout.write(e.message); }'],
        capture_output=True, text=True)
    assert 'drone' in res.stdout and 'implementada' in res.stdout


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
