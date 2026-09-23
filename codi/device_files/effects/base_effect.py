"""
BaseEffect - Interfície comuna per a tots els efectes temporals del TECLA
"""
from adafruit_midi.control_change import ControlChange
try:
    from motor.modeloop import canals_auxiliars as _canals_auxiliars
except Exception:
    def _canals_auxiliars(midi_out):
        return (1, 2, 3)

class BaseEffect:
    def __init__(self, midi_out):
        self.midi = midi_out
        self.name = self.__class__.__name__.replace('Effect', '')
        # Cache de valors per CC: update_params s'executa a CADA cicle del
        # bucle (~2ms) — sense cache, cada efecte inundava l'USB amb 16
        # missatges per cicle (8000 msg/s) i el MIDI deixava d'anar "al toc".
        self._cc_cache = {}
        # Els canals dels loops (segons el canal de sortida): un efecte en viu
        # no hi envia res, el que un loop té gravat no s'ha de torçar.
        self._salta = _canals_auxiliars(midi_out)[1:]

    def _cc_all(self, control, value, force=False, loops=False):
        """Envia un CC a tots els canals, NOMÉS si el valor ha canviat (o
        force=True per a on_activate/on_deactivate). Missatge únic reutilitzat:
        zero al·locacions al camí calent.

        Tots els canals MENYS els dels loops (com el pitch bend): un efecte en
        viu no ha d'alterar el que un loop ja té gravat. El Sustain al canal
        del loop feia que el synth ignorés els seus NoteOff i cada volta
        apilés veus. `loops=True` és per als efectes que són de mescla global
        (Pausa: abaixar-ho tot, loops inclosos)."""
        value = max(0, min(127, int(value)))
        if not force and self._cc_cache.get(control) == value:
            return
        self._cc_cache[control] = value
        msg = ControlChange(control, value, channel=0)
        for ch in range(16):
            if not loops and ch in self._salta:
                continue
            msg.channel = ch
            try:
                self.midi.send(msg)
            except Exception:
                pass

    def on_activate(self):
        """S'executa quan l'efecte s'activa"""
        pass

    def on_deactivate(self):
        """S'executa quan l'efecte es desactiva"""
        pass

    def update_params(self, x=0, y=0, z=0):
        """Actualitza paràmetres de l'efecte en temps real"""
        pass
