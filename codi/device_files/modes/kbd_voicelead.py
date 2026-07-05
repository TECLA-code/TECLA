"""Conducció de veus (voice leading) per al Mode Teclat.

Quan està activa, cada acord nou es re-voiceja (provant inversions i canvis
d'octava) segons la FORMA triada respecte de l'acord anterior — les progressions
sonen lligades. Les classes d'altura (pitch classes) es conserven sempre.

Formes (mateixos ids i ordre que VL_TYPES a tecla-music-data.js):
  proximitat  — mínim moviment total (el voicing més proper; pianístic)
  comu        — manté els tons comuns amb l'acord anterior
  baix        — prioritza un baix llis (poc salt al greu)
  ascendent   — les veus tendeixen a pujar
  obert       — distribució oberta (veus separades)

Gest del botó 'voice_lead': tap = activa / cicla la forma · premuda llarga =
desactiva (vegeu kbd_buttons.py). Mòdul amb càrrega lazy.
"""

VL_TYPE_IDS = ('proximitat', 'comu', 'baix', 'ascendent', 'obert')


def _cost(cand, prev, vltype):
    """Cost d'un voicing candidat segons la forma. Mirall de _vlCost (index.html)."""
    total = 0
    for n in cand:
        best = 128
        for p in prev:
            d = abs(n - p)
            if d < best:
                best = d
        total += best
    bass = abs(min(cand) - min(prev))
    if vltype == 'comu':
        common = 0
        for n in cand:
            if n in prev:
                common += 1
        return -4 * common + total
    if vltype == 'baix':
        return 3 * bass + total
    if vltype == 'ascendent':
        return (60 if min(cand) < min(prev) else 0) + total
    if vltype == 'obert':
        return -(max(cand) - min(cand)) + total
    return total + bass // 2   # proximitat (per defecte)


def _candidates(notes, open_voicing):
    """Voicings candidats: inversions × (-1/0/+1 octaves). Si open_voicing, també
    versions obertes (puja una octava les veus en posició senar)."""
    base = sorted(notes)
    n = len(base)
    cands = []
    for inv in range(n):
        v = sorted(base[inv:] + [x + 12 for x in base[:inv]])
        variants = [v]
        if open_voicing and n >= 3:
            variants.append(sorted([(x + 12) if (i % 2 == 1) else x for i, x in enumerate(v)]))
        for vv in variants:
            for shift in (-12, 0, 12):
                cand = [x + shift for x in vv]
                if all(0 <= x <= 127 for x in cand):
                    cands.append(cand)
    return cands or [base]


def apply_voice_leading(kbd, notes):
    """Retorna el voicing de `notes` segons la forma activa (kbd._vl_type)."""
    if not notes:
        return notes
    prev = getattr(kbd, '_vl_prev_chord', None)
    if not prev:
        kbd._vl_prev_chord = sorted(notes)
        return notes
    vltype = getattr(kbd, '_vl_type', 'proximitat')
    best = None
    best_cost = 1 << 30
    for cand in _candidates(notes, vltype == 'obert'):
        c = _cost(cand, prev, vltype)
        if c < best_cost:
            best_cost = c
            best = cand
    kbd._vl_prev_chord = best
    return best
