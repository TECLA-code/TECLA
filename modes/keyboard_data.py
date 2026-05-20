"""
Data Lite (Emergency Fix)
"""
# Només escales bàsiques
SCALE_MODES = {
    0: ([0, 2, 4, 5, 7, 9, 11], 'Jonic'),
    1: ([0, 2, 3, 5, 7, 9, 10], 'Doric'),
    5: ([0, 2, 3, 5, 7, 8, 10], 'Eolic'),
    7: ([0, 2, 4, 7, 9], 'PentMaj'),
    8: ([0, 3, 5, 7, 10], 'PentMin')
}
KEY_CIRCLE = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'Ab', 'Eb', 'Bb', 'F']
KEY_OFFSETS = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]

# Només arpegiadors bàsics
ARP_MODES = {
    0: ('up', 'Amunt'),
    1: ('down', 'Avall'),
    2: ('pingpong', 'PingPong'),
    3: ('random', 'Aleatori'),
    4: ('order', 'Ordre')
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NOTE_OFFSETS = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}

# Només acords bàsics
CHORD_TYPES = {
    'Major': [0, 4, 7],           
    'm': [0, 3, 7],
    '7': [0, 4, 7, 10]
}
