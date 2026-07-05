"""
negharm.py - Harmonia negativa compartida entre modes.

Reflexio de la classe de to d'una nota al voltant d'un eix, tal com ho fa
el mode teclat (modes/kbd_notes.reflect_note), pero com a funcio pura
reutilitzable per qualsevol mode melodic.

Eix per defecte = 3.5 semitons sobre la tonica (eix de Levy / quinta),
que es l'harmonia negativa "canonica": converteix una progressio major en
la seva imatge menor mantenint la mateixa funcio tonal.
"""

# Eixos en semitons respecte la tonica (mateixa taula que el mode teclat)
NEG_HARM_AXES = (3.5, 0.0, 2.0, 1.5, 6.0, 2.5, 4.5, 5.5)
NEG_HARM_NAMES = ('Quinta', 'Unisonant', 'Tercera M', 'Tercera m',
                  'Trito', 'Quarta', 'Sexta M', 'Septima m')


def reflect_note(note, tonic_pc, axis_id=0):
    """Reflecteix una nota MIDI en harmonia negativa.

    note     : nota MIDI (0-127).
    tonic_pc : classe de to de la tonica del mode (0-11).
    axis_id  : index a NEG_HARM_AXES (0 = eix de Levy/quinta, l'estandard).

    Retorna la nota reflectida, plegada a l'octava mes propera i limitada a
    l'interval MIDI valid. Identica en semantica a kbd_notes.reflect_note.
    """
    axis = tonic_pc + NEG_HARM_AXES[axis_id % len(NEG_HARM_AXES)]
    note_pc = note % 12
    reflected_pc = int(round(2.0 * axis - note_pc)) % 12
    new_note = (note // 12) * 12 + reflected_pc
    if new_note - note > 6:
        new_note -= 12
    elif note - new_note > 6:
        new_note += 12
    return max(0, min(127, new_note))
