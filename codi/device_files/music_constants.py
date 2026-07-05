"""
Constants musicals compartides per estalviar RAM
Utilitzar tuples (immutables) en lloc de llistes per reduir memòria
"""

# Escales: només intervals (sense noms per estalviar RAM)
# Accés: SCALES[scale_id]
SCALES = (
    (0, 2, 4, 5, 7, 9, 11),      # 0: Jònic (Major)
    (0, 2, 3, 5, 7, 9, 10),      # 1: Dòric
    (0, 1, 3, 5, 7, 8, 10),      # 2: Frigi
    (0, 2, 4, 6, 7, 9, 11),      # 3: Lidi
    (0, 2, 4, 5, 7, 9, 10),      # 4: Mixolidi
    (0, 2, 3, 5, 7, 8, 10),      # 5: Eòlic (Minor)
    (0, 1, 3, 5, 6, 8, 10),      # 6: Locri
    (0, 2, 4, 7, 9),             # 7: Pentatònica Major
    (0, 3, 5, 7, 10),            # 8: Pentatònica Menor
    (0, 1, 4, 6, 7),             # 9: Japonesa
    (0, 2, 5, 7, 9),             # 10: Egípcia
    (0, 1, 4, 5, 7, 8, 11),      # 11: Aràbiga
    (0, 2, 3, 6, 7, 9, 10),      # 12: Hongaresa Menor
    (0, 2, 4, 6, 7, 9, 10),      # 13: Lídia Dominant
    (0, 1, 3, 4, 6, 8, 10),      # 14: Alterada
    (0, 2, 3, 5, 7, 9, 11),      # 15: Menor Melòdica
    (0, 1, 4, 5, 7, 8, 11),      # 16: Raga Bhairav
    (0, 1, 3, 6, 7, 8, 11),      # 17: Raga Todi
    (0, 1, 4, 5, 7, 8, 10),      # 18: Flamenca
    (0, 1, 4, 5, 7, 9, 11),      # 19: Catalana
    (0, 1, 3, 5, 7, 8, 10),      # 20: Frígia
    (0, 1, 4, 5, 7, 8, 11),      # 21: Balcànica
    (0, 2, 4, 6, 8, 10),         # 22: Tons Sencers
    (0, 2, 4, 5, 7, 8, 11),      # 23: Harmònica Major
)


# Modes d'arpegiador: només direcció (sense noms)
# Strings curts per estalviar memòria
ARP_DIRS = (
    'up', 'down', 'pingpong', 'random', 'order',
    'alberti', 'alberti_alt', 'waltz', 'broken', 'tremolo',
    'zigzag', 'block', 'rolled', 'octaves', 'contrary', 'spread', 'custom'
)

# Tonalitats
KEYS = (0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5)  # Offsets en semitons

# Notes musicals
NOTES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')

# Acords: intervals per tipologia (31 tipologies)
# Tuples en lloc de dict per estalviar ~40% de RAM (sense hash-table overhead)
_CHORD_NAMES = (
    'Major', 'm', '7', 'maj7', 'm7', 'dim', 'aug', 'sus4', 'sus2',
    'm7b5', 'add9', '6', 'add11', 'add13', '9', '9#5', '9b5', '9#11',
    '11', '13', '13b9', '13#9', '7b9', '7#9', '7sus4', '7b13',
    '69', 'm9', 'm11', 'm13', 'm69',
)
_CHORD_INTERVALS = (
    (0, 4, 7), (0, 3, 7), (0, 4, 7, 10), (0, 4, 7, 11), (0, 3, 7, 10),
    (0, 3, 6), (0, 4, 8), (0, 5, 7), (0, 2, 7), (0, 3, 6, 10),
    (0, 4, 7, 14), (0, 4, 7, 9), (0, 4, 7, 17), (0, 4, 7, 21),
    (0, 4, 7, 10, 14), (0, 4, 8, 10, 14), (0, 4, 6, 10, 14),
    (0, 4, 7, 10, 14, 18), (0, 4, 7, 10, 14, 17), (0, 4, 7, 10, 14, 21),
    (0, 4, 7, 10, 13, 21), (0, 4, 7, 10, 15, 21),
    (0, 4, 7, 10, 13), (0, 4, 7, 10, 15), (0, 5, 7, 10), (0, 4, 7, 10, 20),
    (0, 4, 7, 9, 14), (0, 3, 7, 10, 14), (0, 3, 7, 10, 14, 17),
    (0, 3, 7, 10, 14, 21), (0, 3, 7, 9, 14),
)

def get_chord(name):
    """Retorna els intervals d'un acord per nom. Default: Major (0,4,7)"""
    try:
        return _CHORD_INTERVALS[_CHORD_NAMES.index(name)]
    except (ValueError, IndexError):
        return (0, 4, 7)

# Mapatge notes → offset (generat dinàmicament per estalviar RAM)
def note_offset(note_name):
    """Retorna l'offset MIDI d'una nota"""
    try:
        return NOTES.index(note_name)
    except ValueError:
        return 0
