"""
Mode Tempesta (LITE)
"""
import time
import random
from modes.base_mode import BaseMode

class ModeTormenta(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Tempesta"
        self.lt = 0 # last_thunder
        self.ll = 0 # last_lightning
        self.np = set() # notes_playing
        self.bg = {24:0, 28:0, 32:0, 36:0} # background notes: vel
        self.ti = 0; self.li = 0; self.bi = 0 # intensities
        
        # Pre-load MIDI
        try:
            from adafruit_midi.note_on import NoteOn
            from adafruit_midi.note_off import NoteOff
            self._NoteOn = NoteOn
            self._NoteOff = NoteOff
        except: pass

    def setup(self):
        self.initialized = True
        self.lt=0; self.ll=0; self.np.clear()
        
    def cleanup(self):
        if hasattr(self, '_NoteOff'):
            try:
                for n in self.np: self.midi_out.send(self._NoteOff(n,0))
                for n in self.bg: self.midi_out.send(self._NoteOff(n,0))
            except: pass
        self.np.clear()

    def update(self, pots, btns):
        ct = time.monotonic()
        x, y, z = pots
        
        self.ti = x / 127.0 # Thunder
        self.li = y / 127.0 # Lightning
        self.bi = z / 127.0 # Background
        
        # 1. Background
        if hasattr(self, '_NoteOn') and hasattr(self, '_NoteOff'):
            try:
                # Target velocities
                tv = {
                    24: int(40 + self.bi * 40),
                    28: int(30 + self.ti * 50),
                    32: int(20 + self.bi * 40),
                    36: int(15 + self.bi * 35)
                }
                for n, v in tv.items():
                    if v > 10:
                        if self.bg[n] != v: # Update if changed
                            self.midi_out.send(self._NoteOn(n, v))
                            self.bg[n] = v
                    elif self.bg[n] > 0: # Turn off
                         self.midi_out.send(self._NoteOff(n, 0))
                         self.bg[n] = 0
            except: pass

        # 2. Thunder (Random Low)
        if (ct - self.lt) > (3.0 - self.ti*2.5) and random.random() < (self.ti * 0.7):
            self.tx(random.randint(22, 40), random.randint(40, 100))
            self.lt = ct

        # 3. Lightning (High cascade)
        if (ct - self.ll) > max(0.1, 2.0 - self.li*1.9):
            cnt = 1 + int(self.li*5) if self.li>0.3 else 1
            for i in range(cnt):
                n = random.randint(90, 108) - (i*2)
                v = int(90 + 35*self.li * (0.9 - i*0.1))
                self.tx(n, v)
            self.ll = ct
            
        return {}

    def tx(self, n, v):
        if hasattr(self, '_NoteOn'):
            try:
                self.midi_out.send(self._NoteOn(n, v))
                # Auto-off logic handled by external cleanup or short decay for FX?
                # For tempesta bursts, we usually want NoteOff after short duration.
                # Since we don't have async scheduler, we rely on "stateless" bursts 
                # or we track them. For LITE, we just fire NoteOn. 
                # Ideally we need NoteOff. Let's just track and clear randomly or immediately?
                # Immediate NoteOff is too short. 
                # Compromise: Add to self.np and clear old ones randomly.
                self.np.add(n)
                
                # Cleanup old notes randomly to prevent stuck notes
                if len(self.np) > 10:
                    rem = list(self.np)[:5]
                    if hasattr(self, '_NoteOff'):
                        for r in rem:
                            self.midi_out.send(self._NoteOff(r,0))
                            self.np.discard(r)
            except: pass
