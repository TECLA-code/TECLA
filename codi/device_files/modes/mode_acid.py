"""
Mode Acid - Linia de baix estil TB-303 amb slides i accents.
La sequencia de 16 passos es genera sola i muta a poc a poc; els slides
lliguen notes (legato + portamento) i els accents les ressalten. Z obre
el filtre (CC74). Mono, canal 0. Sonoritat acid iconica, molt diferent
dels patrons de bateria existents.
X: Tempo (120-160 BPM)
Y: Mutacio (probabilitat que la sequencia canvii sola)
Z: Cutoff del filtre (brillantor)
Doble clic: regenera la sequencia i puja la tonica
"""
import time, random
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# Reservori d'intervals tipic d'una linia acid (tonica, oct, 5a, b3, b7, 4a)
_POOL = (0, 12, 7, 3, 10, 5, -12, 0, 0, 12)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')


class ModeAcid(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Acid"
        self.key = 0
        self.octave = 2
        self.bpm = 135.0
        self.step = 0
        self.step_dur = 0.1
        self.last_step_t = 0.0
        self.seq = []          # (interval, gate, accent, slide)
        self.cur = -1
        self.slide_prev = False
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self._last_cut = -1
        self._regen()

    def _regen(self):
        seq = []
        for _ in range(16):
            iv = _POOL[random.randint(0, len(_POOL) - 1)]
            gate = 1 if random.random() < 0.75 else 0
            accent = 1 if random.random() < 0.25 else 0
            slide = 1 if random.random() < 0.20 else 0
            seq.append((iv, gate, accent, slide))
        self.seq = seq

    def setup(self):
        self.initialized = True
        self.step = 0
        self._calc()
        self.last_step_t = time.monotonic()
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self._cc(65, 127)   # portamento ON
        self._cc(5, 28)     # temps de portamento
        print("Acid: %s" % _KEYS[self.key])

    def _calc(self):
        self.step_dur = 60.0 / self.bpm / 4.0

    def _cc(self, c, v):
        try:
            self.midi_out.send(ControlChange(c, max(0, min(127, int(v)))))
        except Exception:
            pass

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        nb = 120.0 + (x / 127.0) * 40.0
        if abs(nb - self.bpm) > 0.4:
            self.bpm = nb; self._calc()
        cut = int((z / 127.0) * 127)
        if cut != self._last_cut:                # cutoff del filtre (nomes si canvia)
            self._cc(74, cut); self._last_cut = cut
        mut = (y / 127.0) * 0.12                 # prob. de mutar un pas per tick

        if now - self.last_step_t >= self.step_dur:
            self.last_step_t = now
            # Mutacio esporadica d'un pas
            if mut > 0 and random.random() < mut:
                j = random.randint(0, 15)
                iv = _POOL[random.randint(0, len(_POOL) - 1)]
                old = self.seq[j]
                self.seq[j] = (iv, old[1], old[2], old[3])

            iv, gate, accent, slide = self.seq[self.step]
            prev_slide = self.slide_prev
            if gate:
                note = max(24, min(96, self.octave * 12 + self.key + iv))
                vel = 118 if accent else 80
                if self.cur >= 0 and not prev_slide:
                    self.send_note_off(self.cur, 0, 0)
                self.send_note_on(note, vel, 0)
                if self.cur >= 0 and prev_slide:
                    # solapament breu -> el porta glissa cap a la nova nota
                    self.send_note_off(self.cur, 0, 0)
                self.cur = note
                self.slide_prev = bool(slide)
            else:
                if self.cur >= 0:
                    self.send_note_off(self.cur, 0, 0)
                    self.cur = -1
                self.slide_prev = False
            self.step = (self.step + 1) % 16

        # Doble clic: regenerar + pujar tonica
        for i in range(min(len(button_states), 16)):
            curb = bool(button_states[i])
            if self.last_btn[i] and not curb:
                gap = now - self.last_release[i]
                if 0.05 < gap < 0.4:
                    self.last_release[i] = 0.0
                    self.key = (self.key + 1) % 12
                    self._regen()
                    print("Acid: %s" % _KEYS[self.key])
                else:
                    self.last_release[i] = now
            self.last_btn[i] = curb

        return {'key': _KEYS[self.key], 'bpm': int(self.bpm),
                'cut': int((z / 127.0) * 127)}

    def stop(self):
        self.cleanup()

    def cleanup(self):
        if self.cur >= 0:
            self.send_note_off(self.cur, 0, 0)
            self.cur = -1
        self.slide_prev = False
        self._cc(65, 0)     # portamento OFF
        self._cc(123, 0)    # all notes off
        self._cc(120, 0)    # all sound off
        self.stop_tracked_notes()
