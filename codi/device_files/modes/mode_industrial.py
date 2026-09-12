"""
Mode Industrial - Maquines, vapor, repeticio mecanica
"""
import time
from modes.base_mode import BaseMode

class ModeIndustrial(BaseMode):
    PARAMS = ('Tempo', 'Vapor', 'Engranatges', 'Força', 'Registre')
    POTS = ('Tempo', 'Vapor', 'Engranatges')

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Industrial"
        self.machine_step = 0
        self.steam_phase = 0
        self.machine_bpm = 150
        self.steam_pressure = 0.5
        self.num_gears = 4
        self.forca = 1.0
        self.registre = 0             # semitons

    def set_param(self, nom, v):
        f = v / 127.0
        if nom == 'Tempo':
            self.machine_bpm = 60 + int(f * 180)
        elif nom == 'Vapor':
            self.steam_pressure = f
        elif nom == 'Engranatges':
            self.num_gears = 1 + int(f * 7)
        elif nom == 'Força':
            self.forca = 0.3 + f * 0.7
        elif nom == 'Registre':
            self.registre = (min(2, int(f * 3)) - 1) * 12
        else:
            return False
        return True

    def _nota(self, n, vel):
        n = n + self.registre
        if 0 <= n <= 127:
            self.midi_out.send(self.note_on(n, max(1, min(127, int(vel * self.forca)))))
            self.midi_out.send(self.note_off(n, 0))

    def setup(self):
        self.initialized = True
        self.resincronitza()
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        self.potes(pot_values)
        machine_bpm = self.machine_bpm
        step_interval = 60.0 / (machine_bpm * 4)  # 16ths
        steam_pressure = self.steam_pressure
        num_gears = self.num_gears
        
        if self.toca('step', step_interval):
            # Màquina base (pols mecànic molt regular)
            if self.machine_step % 4 == 0:
                # Beat principal (fort)
                machine_note = 36
                machine_vel = 100
            elif self.machine_step % 2 == 0:
                # Beat secundari
                machine_note = 40
                machine_vel = 80
            else:
                # Tick mecànic
                machine_note = 48
                machine_vel = 60
            
            self._nota(machine_note, machine_vel)
            
            # Engranatges (notes repetitives)
            for i in range(num_gears):
                if (self.machine_step + i) % (2 + i) == 0:
                    gear_note = 52 + (i * 4)
                    gear_vel = 70 - i * 5
                    self._nota(gear_note, max(40, gear_vel))
            
            # Vapor (xiulet ocasional)
            if steam_pressure > 0.5:
                self.steam_phase += steam_pressure * 0.1
                if int(self.steam_phase) % int(10 / steam_pressure) == 0:
                    # Xiulet de vapor (agut)
                    steam_note = 84 + int(steam_pressure * 12)
                    steam_note = min(96, steam_note)
                    steam_vel = int(80 + steam_pressure * 40)
                    self._nota(steam_note, steam_vel)
            
            self.machine_step += 1

        return {
            'machine': f"{machine_bpm} BPM",
            'steam': f"{int(steam_pressure * 100)}%",
            'gears': num_gears
        }
    
    def cleanup(self):
        return []
