"""Billar - Pilotes físiques que reboten i generen notes. X:velocitat Y:to Z:rebost"""
import time, random, math
from modes.base_mode import BaseMode

_SCALE = [0, 3, 5, 7, 10]  # pentatònica menor


class ModeBillar(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Billar"
        self.t = time.monotonic()
        self.balls = []
        self.notes_on = []    # [(note, off_time)]
        self._cooldowns = []  # segon per pilota

    def _init_balls(self):
        self.balls = []
        self._cooldowns = []
        for i in range(4):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.15, 0.35)
            self.balls.append({
                'x':  random.uniform(0.15, 0.85),
                'y':  random.uniform(0.15, 0.85),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'r':  0.07,
                'si': i % len(_SCALE),  # scale index
            })
            self._cooldowns.append(0.0)

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.notes_on = []
        self._init_balls()

    def update(self, pot_values, button_states):
        now = time.monotonic()
        dt = min(now - self.t, 0.05)
        self.t = now
        x, y, z = pot_values

        # X = velocitat global  (0.3× – 3.0×)
        speed_mult = 0.3 + (x / 127.0) * 2.7
        # Y = nota base  (C2=36 – C5=72)
        base_note = 36 + int((y / 127.0) * 36)
        # Z = restitució / rebost  (0.30 – 0.95)
        restitution = 0.30 + (z / 127.0) * 0.65

        step = dt * speed_mult

        # --- Apagar notes expirades ---
        still = []
        for (note, off_t) in self.notes_on:
            if now >= off_t:
                self.midi_out.send(self.note_off(note, 0))
            else:
                still.append((note, off_t))
        self.notes_on = still

        # --- Decréixer cooldowns ---
        for i in range(len(self._cooldowns)):
            if self._cooldowns[i] > 0.0:
                self._cooldowns[i] = max(0.0, self._cooldowns[i] - dt)

        # --- Moure pilotes ---
        for b in self.balls:
            b['x'] += b['vx'] * step
            b['y'] += b['vy'] * step

        # --- Col·lisions amb les parets ---
        events = []
        for i, b in enumerate(self.balls):
            r = b['r']
            hit = False
            if b['x'] - r < 0.0:
                b['x'] = r
                b['vx'] = abs(b['vx']) * restitution
                hit = True
            elif b['x'] + r > 1.0:
                b['x'] = 1.0 - r
                b['vx'] = -abs(b['vx']) * restitution
                hit = True
            if b['y'] - r < 0.0:
                b['y'] = r
                b['vy'] = abs(b['vy']) * restitution
                hit = True
            elif b['y'] + r > 1.0:
                b['y'] = 1.0 - r
                b['vy'] = -abs(b['vy']) * restitution
                hit = True
            if hit and self._cooldowns[i] <= 0.0:
                spd = math.sqrt(b['vx'] ** 2 + b['vy'] ** 2)
                if spd > 0.02:
                    events.append((i, spd))
                    self._cooldowns[i] = 0.10

        # --- Col·lisions entre pilotes ---
        n = len(self.balls)
        for ai in range(n):
            for bi in range(ai + 1, n):
                a = self.balls[ai]
                b = self.balls[bi]
                dx = b['x'] - a['x']
                dy = b['y'] - a['y']
                dist = math.sqrt(dx * dx + dy * dy)
                min_d = a['r'] + b['r']
                if dist < min_d and dist > 1e-6:
                    nx = dx / dist
                    ny = dy / dist
                    # Separar
                    ov = (min_d - dist) * 0.5
                    a['x'] -= nx * ov
                    a['y'] -= ny * ov
                    b['x'] += nx * ov
                    b['y'] += ny * ov
                    # Impulse
                    rvx = b['vx'] - a['vx']
                    rvy = b['vy'] - a['vy']
                    vel_n = rvx * nx + rvy * ny
                    if vel_n < 0:
                        imp = -(1.0 + restitution) * vel_n * 0.5
                        a['vx'] -= imp * nx
                        a['vy'] -= imp * ny
                        b['vx'] += imp * nx
                        b['vy'] += imp * ny
                        rel = math.sqrt(rvx * rvx + rvy * rvy)
                        if rel > 0.03:
                            if self._cooldowns[ai] <= 0.0:
                                events.append((ai, rel))
                                self._cooldowns[ai] = 0.12
                            if self._cooldowns[bi] <= 0.0:
                                events.append((bi, rel))
                                self._cooldowns[bi] = 0.12

        # --- Emetre notes ---
        for (ball_idx, spd) in events:
            b = self.balls[ball_idx]
            note = base_note + _SCALE[b['si']]
            note = max(0, min(127, note))
            vel = int(min(127, max(20, spd * 200)))
            dur = 0.04 + spd * 0.07
            self.midi_out.send(self.note_on(note, vel))
            self.notes_on.append((note, now + dur))

        return {'balls': n, 'events': len(events)}

    def cleanup(self):
        for (note, _) in self.notes_on:
            self.midi_out.send(self.note_off(note, 0))
        self.notes_on = []
        return []
