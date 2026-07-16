"""So intern de TECLA: to PWM monofònic a GP22.

Mòdul mínim i AÏLLAT expressament: abans el singleton PWM vivia com a atribut
del mòdul 'main', i el primer `import main` des de mode_keyboard recompilava
main.py sencer al primer toc (centenars de ms de lag + pic de RAM). Aquí només
hi ha el pin i dues funcions; a l'escriptori (simulador/tests) pwmio no
existeix i tot queda en no-op silenciós.
"""

pwm = None


def midi_to_frequency(midi_note):
    """Converteix una nota MIDI a freqüència en Hz (enter)."""
    return round(440 * (2 ** ((midi_note - 69) / 12)))


def play(midi_note):
    """Fa sonar la nota pel PWM (crea el pin al primer ús)."""
    global pwm
    try:
        freq = midi_to_frequency(midi_note)
        if pwm is None:
            import pwmio
            import board
            pwm = pwmio.PWMOut(board.GP22, frequency=freq, duty_cycle=32767,
                               variable_frequency=True)
        else:
            pwm.frequency = freq
            pwm.duty_cycle = 32767
    except Exception:
        pass  # sense so intern el MIDI ha de continuar igualment


def off():
    """Silencia el PWM (les notes MIDI no es toquen)."""
    if pwm is not None:
        try:
            pwm.duty_cycle = 0
        except Exception:
            pass
