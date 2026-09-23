"""La funció 'progression' de la capa teclat: una progressió sencera en UNA tecla.

Les progressions són les de l'app («Progressions i escales pròpies»:
`custom_chord_progressions`, vuit acords cadascuna). Quina toca cada tecla ho
diu `bank['progs'][tecla]` = {'id': id de la progressió, 'temps': negres per
acord, 'bpm': tempo}. Gest, en PRÉMER (resposta immediata, com el latch):

    tecla aturada      → engega la seva progressió des del primer acord
    tecla que sona     → l'atura
    una altra tecla    → canvia a la progressió d'aquella (des del principi)

Els acords sonen sostinguts pel canal de la base, una octava per sota de com
sonen a les tecles de nota, i el teclat queda lliure per tocar-hi a sobre. Si
la base (funció 'accomp') també sona, segueix la fonamental de cada acord.
El rellotge és el de l'acompanyament (motor/accompaniment.py) en una
instància pròpia: la base i la progressió conviuen. Mòdul mandrós.
"""
try:
    from core.pantalla import diu
except Exception:                       # simulador i proves sense core/
    def diu(text):
        print(text)
        return True

TEMPS_DEF = 4
BPM_DEF = 100


def _prog_de_tecla(kbd, btn_idx):
    """(progressió, temps, bpm) de la tecla, o (None, …) si no en té."""
    cm = getattr(kbd, 'config_manager', None)
    if cm is None:
        return None, TEMPS_DEF, BPM_DEF
    try:
        bank = cm.get_current_bank() or {}
        progs = bank.get('progs') or []
        p = progs[btn_idx] if btn_idx < len(progs) else None
    except Exception:
        p = None
    if not isinstance(p, dict) or not p.get('id'):
        return None, TEMPS_DEF, BPM_DEF
    try:
        prog = cm.get_progression_by_id(p.get('id'))
    except Exception:
        prog = None
    try:
        temps = max(1, min(16, int(p.get('temps', TEMPS_DEF))))
    except Exception:
        temps = TEMPS_DEF
    try:
        bpm = max(40, min(240, int(p.get('bpm', BPM_DEF))))
    except Exception:
        bpm = BPM_DEF
    return prog, temps, bpm


def acords(prog, octava):
    """Les notes de cada acord, en l'ordre de les tecles (0..7). Una octava per
    sota de com les toca la tecla de nota amb aquesta progressió."""
    from motor.kbd_notes import get_chord, note_offset
    llista = sorted(prog.get('chords') or [], key=lambda c: c.get('button', 0))
    fora = []
    for c in llista:
        try:
            base = (octava + int(c.get('octave', 4)) - 4) * 12 + note_offset(c.get('root_note', 'C')) - 12
        except Exception:
            continue
        notes = tuple(max(0, min(127, base + i)) for i in get_chord(c.get('chord_type', 'Major')))
        if notes:
            fora.append(notes)
    return fora


def _patro(kbd, notes_acords, temps):
    passos = temps * 4                  # setzens per acord

    def pat(n, ctx, rng):
        if n % passos:
            return ()
        ac = notes_acords[(n // passos) % len(notes_acords)]
        # La base, si sona, segueix la fonamental de l'acord
        base = getattr(kbd, '_accomp', None)
        if base is not None and getattr(kbd, '_accomp_active', False):
            try:
                base.ctx = {'root': max(24, min(96, ac[0] + 12)), 'scale': base.ctx['scale']}
            except Exception:
                pass
        return tuple((x, passos, 80) for x in ac)

    return pat


def handle_button(kbd, btn_idx, now):
    """Gest de la tecla 'progression' (en prémer)."""
    if getattr(kbd, '_prog_btn', -1) == btn_idx:
        atura(kbd)
        diu("Progressio OFF")
        return
    prog, temps, bpm = _prog_de_tecla(kbd, btn_idx)
    if not prog:
        diu("Progressio: tria-la a l'app")
        return
    ac = acords(prog, getattr(kbd, 'octave', 4))
    if not ac:
        return
    from motor.accompaniment import Accompaniment, _canal
    eng = getattr(kbd, '_prog', None)
    if eng is None:
        eng = Accompaniment(kbd.midi)
        kbd._prog = eng
    eng.clear()
    eng.set_tempo(bpm)
    eng.add_fn(_patro(kbd, ac, temps), _canal(kbd), now, 'progressio')
    kbd._prog_btn = btn_idx
    diu("Progressio: %s" % prog.get('name', ''))


def atura(kbd):
    """Atura la progressió (tecla, STOP, canvi de capa). Mai llança."""
    eng = getattr(kbd, '_prog', None)
    if eng is not None:
        try:
            eng.clear()
        except Exception:
            pass
    kbd._prog_btn = -1
