"""Conducció de veus (voice leading) per al Mode Teclat.

Quan està activa, cada acord nou es re-voiceja (provant inversions i canvis
d'octava) segons la FORMA triada respecte de l'acord anterior — les progressions
sonen lligades. Les classes d'altura (pitch classes) es conserven sempre.

Formes (mateixos ids i ordre que VL_TYPES a tecla-music-data.js):
  proximitat  — mínim moviment total (el voicing més proper; pianístic)
  comu        — manté els tons comuns amb l'acord anterior
  baix        — prioritza un baix llis (poc salt al greu)
  ascendent   — les veus tendeixen a pujar
  descendent  — les veus tendeixen a baixar
  obert       — distribució oberta (veus separades)
  tancat      — posició tancada (les veus tan juntes com es pugui)
  fonamental  — el baix sempre a la FONAMENTAL de l'acord
  inv1        — el baix a la TERCERA (1a inversió preferida)
  inv2        — el baix a la QUINTA (2a inversió preferida)
  drop2       — la 2a veu des de dalt baixa una octava (voicing jazzístic)
  pendol      — alterna pujar/baixar a cada acord (moviment pendular)

Les inversions harmòniques viuen AQUÍ (formes fonamental/inv1/inv2): l'antic
apartat "Inversions Harmòniques" + pot "Inversió d'Acord" s'han retirat.

Gest del botó 'voice_lead': tap = activa / cicla la forma · premuda llarga =
desactiva (vegeu kbd_buttons.py). Mòdul amb càrrega lazy.
"""

VL_TYPE_IDS = ('proximitat', 'comu', 'baix', 'ascendent', 'descendent',
               'obert', 'tancat', 'fonamental', 'inv1', 'inv2', 'drop2', 'pendol')


def _cost(cand, prev, vltype, bass_target_pc, is_drop2, updir):
    """Cost d'un voicing candidat segons la forma. Mirall de _vlCost (index.html)."""
    total = 0
    for n in cand:
        best = 128
        for p in prev:
            d = abs(n - p)
            if d < best:
                best = d
        total += best
    lo = min(cand)
    bass = abs(lo - min(prev))
    if vltype == 'comu':
        common = 0
        for n in cand:
            if n in prev:
                common += 1
        return -4 * common + total
    if vltype == 'baix':
        return 3 * bass + total
    if vltype == 'ascendent':
        return (60 if lo < min(prev) else 0) + total
    if vltype == 'descendent':
        return (60 if lo > min(prev) else 0) + total
    if vltype == 'obert':
        return -(max(cand) - lo) + total
    if vltype == 'tancat':
        return (max(cand) - lo) * 2 + total
    if vltype in ('fonamental', 'inv1', 'inv2'):
        # Inversió preferida: el baix ha de caure a la classe d'altura triada
        # (fonamental/3a/5a). Penalització forta si no hi és; proximitat decideix
        # entre les octaves possibles d'aquella inversió.
        return (0 if lo % 12 == bass_target_pc else 80) + total + bass // 2
    if vltype == 'drop2':
        return (0 if is_drop2 else 80) + total
    if vltype == 'pendol':
        # Alterna: en fase amunt es penalitza baixar, i al revés.
        if updir:
            return (60 if lo < min(prev) else 0) + total
        return (60 if lo > min(prev) else 0) + total
    return total + bass // 2   # proximitat (per defecte)


def _candidates(notes, want_open, want_drop2):
    """(voicing, is_drop2) candidats: inversions × (-1/0/+1 octaves), més
    variants obertes (per a 'obert') i drop-2 (per a 'drop2')."""
    base = sorted(notes)
    n = len(base)
    cands = []
    for inv in range(n):
        v = sorted(base[inv:] + [x + 12 for x in base[:inv]])
        variants = [(v, False)]
        if want_open and n >= 3:
            variants.append((sorted([(x + 12) if (i % 2 == 1) else x for i, x in enumerate(v)]), False))
        if want_drop2 and n >= 3:
            # Drop 2: la segona veu des de DALT baixa una octava
            d2 = list(v)
            d2[-2] -= 12
            variants.append((sorted(d2), True))
        for vv, isd2 in variants:
            for shift in (-12, 0, 12):
                cand = [x + shift for x in vv]
                if all(0 <= x <= 127 for x in cand):
                    cands.append((cand, isd2))
    return cands or [(base, False)]


def apply_voice_leading(kbd, notes):
    """Retorna el voicing de `notes` segons la forma activa (kbd._vl_type).

    IMPORTANT: `notes` arriba en ordre d'intervals (notes[0] = FONAMENTAL,
    notes[1] = 3a, notes[2] = 5a) — les formes d'inversió en depenen."""
    if not notes:
        return notes
    prev = getattr(kbd, '_vl_prev_chord', None)
    vltype = getattr(kbd, '_vl_type', 'proximitat')
    # Fase del pèndol: alterna a cada acord NOU (també al primer)
    updir = True
    if vltype == 'pendol':
        updir = not getattr(kbd, '_vl_pendol_up', False)
        kbd._vl_pendol_up = updir
    if not prev:
        kbd._vl_prev_chord = sorted(notes)
        return notes
    # Classe d'altura del baix objectiu per a les formes d'inversió
    if vltype == 'inv1' and len(notes) > 1:
        bass_pc = notes[1] % 12
    elif vltype == 'inv2' and len(notes) > 2:
        bass_pc = notes[2] % 12
    else:
        bass_pc = notes[0] % 12
    best = None
    best_cost = 1 << 30
    for cand, isd2 in _candidates(notes, vltype == 'obert', vltype == 'drop2'):
        c = _cost(cand, prev, vltype, bass_pc, isd2, updir)
        if c < best_cost:
            best_cost = c
            best = cand
    kbd._vl_prev_chord = best
    return best
