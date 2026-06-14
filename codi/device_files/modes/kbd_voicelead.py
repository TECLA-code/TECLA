"""Conducció de veus (voice leading) per al Mode Teclat.

Quan està activa, cada acord nou es re-voiceja (provant inversions i canvis
d'octava) per minimitzar el moviment total de les veus respecte de l'acord
anterior — les progressions sonen lligades, com les tocaria un pianista:
    C (do-mi-sol) -> G no salta a sol-si-re; es queda a si-re-sol.

Funció de botó 'voice_lead' (toggle). Les classes de altura (pitch classes)
de l'acord es conserven sempre: només canvia la distribució per octaves.

Mòdul amb càrrega lazy: només s'importa si la funció 'voice_lead' s'usa.
"""


def _cost(candidate, prev):
    """Moviment total: cada veu del candidat busca la veu anterior més propera."""
    total = 0
    for n in candidate:
        best = 128
        for p in prev:
            d = abs(n - p)
            if d < best:
                best = d
        total += best
    # Penalització suau del salt del baix (evita inversions amb greus erràtics)
    total += abs(min(candidate) - min(prev)) // 2
    return total


def _candidates(notes):
    """Voicings candidats: totes les inversions, cadascuna a -1/0/+1 octaves."""
    base = sorted(notes)
    n = len(base)
    cands = []
    for inv in range(n):
        v = sorted(base[inv:] + [x + 12 for x in base[:inv]])
        for shift in (-12, 0, 12):
            cand = [x + shift for x in v]
            if all(0 <= x <= 127 for x in cand):
                cands.append(cand)
    return cands or [base]


def apply_voice_leading(kbd, notes):
    """Retorna el voicing de `notes` més proper a l'acord anterior tocat."""
    if not notes:
        return notes
    prev = getattr(kbd, '_vl_prev_chord', None)
    if not prev:
        kbd._vl_prev_chord = sorted(notes)
        return notes
    best = None
    best_cost = 1 << 30
    for cand in _candidates(notes):
        c = _cost(cand, prev)
        if c < best_cost:
            best_cost = c
            best = cand
    kbd._vl_prev_chord = best
    return best
