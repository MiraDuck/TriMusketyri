"""Pipes: the oxygen and cooling pipes, one of each in every car. They burst under pressure; you fix them by hand.

    pipes = Pipes([Pipe(...), ...], audio, repair_sound)   # see main.py
    pipes.update(dt, camera, pr.is_key_down(KEY_E))         # every frame, after life support
    pipes.draw(camera, brightness)                          # inside 3D mode: the steam (brightness(pipe): 0..1)
    pipes.draw_smoke(camera.position.z)                     # after the HUD: the smoke of the car you are in
    pipes.draw_hud()                                        # then the repair ring and the blink

- Bursting: every PIPE_CHECK_INTERVAL each whole pipe rolls PIPE_BURST_CHANCE * pressure^2 of its system (life
  support), so the more pressure, the likelier (full pressure: about once a minute, half: every ~4 min).
- A burst pipe swaps to its broken model, shoots steam out of the crack (Steam: particles, STEAM_*), loops
  PIPE_LEAK_SOUND there and its system loses PIPE_LEAK of its pressure (`regulator.leak`; each more burst pipe of
  it loses PIPE_LEAK of what is left): turn the red valve up to make up for it, and back down once it's fixed. Its
  car fills with smoke (SMOKE_*), drawn over the whole screen while you are in it, and clears slowly after.
- Fixing: look at it from within PIPE_REPAIR_REACH and hold E. A ring round the crosshair fills in PIPE_REPAIR_TIME
  (letting go or looking away starts it over), then you blink (BLINK_TIME): while your eyes are shut it is fixed.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pyray as pr

from .audio import Audio
from .config import (
    BLINK_TIME, PIPE_BURST_CHANCE, PIPE_CHECK_INTERVAL, PIPE_LEAK, PIPE_LEAK_SOUND, PIPE_REPAIR_REACH,
    PIPE_REPAIR_TIME, SCREEN_H, SMOKE_CLEAR, SMOKE_COLOR, SMOKE_MAX, SMOKE_RISE, STEAM_COLOR, STEAM_LIFE, STEAM_RATE,
    STEAM_SIZE, STEAM_SPEED, STEAM_SPREAD,
)
from .entity import Entity
from .life_support import Regulator


@dataclass
class _Particle:
    pos: pr.Vector3
    vel: pr.Vector3
    age: float = 0.0


class Steam:
    """Particles shot from `origin` along `direction` (+ STEAM_SPREAD sideways), slowing down and rising a little,
    growing and fading over STEAM_LIFE. `on` makes new ones; the old ones live out their time."""

    def __init__(self, origin: pr.Vector3, direction: pr.Vector3) -> None:
        self.origin: pr.Vector3 = origin
        self.direction: pr.Vector3 = pr.vector3_normalize(direction)
        # two directions across it, for the spread
        side = pr.vector3_normalize(pr.vector3_cross_product(self.direction, pr.Vector3(0.0, 1.0, 0.0)))
        self._across = (side, pr.vector3_cross_product(side, self.direction))
        self.particles: list[_Particle] = []
        self.on: bool = False
        self._due: float = 0.0   # particles owed (STEAM_RATE * dt is rarely whole)

    def update(self, dt: float) -> None:
        if self.on:
            self._due += STEAM_RATE * dt
            while self._due >= 1.0:
                self._due -= 1.0
                speed = random.uniform(*STEAM_SPEED)
                a, b = (random.uniform(-STEAM_SPREAD, STEAM_SPREAD) * speed for _ in range(2))
                vel = pr.vector3_add(pr.vector3_scale(self.direction, speed),
                                     pr.vector3_add(pr.vector3_scale(self._across[0], a),
                                                    pr.vector3_scale(self._across[1], b)))
                self.particles.append(_Particle(self.origin, vel))
        drag = math.exp(-2.5 * dt)
        for p in self.particles:
            p.age += dt
            p.pos = pr.vector3_add(p.pos, pr.vector3_scale(p.vel, dt))
            p.vel = pr.Vector3(p.vel.x * drag, p.vel.y * drag + 0.6 * dt, p.vel.z * drag)   # slows, rises
        self.particles = [p for p in self.particles if p.age < STEAM_LIFE]

    def draw(self, camera: pr.Camera3D, texture: pr.Texture, brightness: float) -> None:
        small, big = STEAM_SIZE
        for p in self.particles:
            t = p.age / STEAM_LIFE
            alpha = int(200 * (1.0 - t) ** 0.6 * min(t * 8.0, 1.0))   # fades in quickly, out slowly
            c = STEAM_COLOR
            color = pr.Color(int(c.r * brightness), int(c.g * brightness), int(c.b * brightness), alpha)
            pr.draw_billboard(camera, texture, p.pos, small + (big - small) * t, color)


class Pipe(Entity):
    """A pipe of one life-support system. Solid (its own mesh). `burst` swaps to the broken model."""

    def __init__(self, name: str, model_path: str | Path, burst_path: str | Path, pos: pr.Vector3,
                 system: Regulator, crack: pr.Vector3, zone: tuple[float, float]) -> None:
        super().__init__(name, model_path, pos, collision_path=model_path)
        self.whole_model: pr.Model = self.model
        self.burst_model: pr.Model = Entity(f"{name}_burst", burst_path, pos).model
        self.system: Regulator = system
        self.zone: tuple[float, float] = zone   # its car's z range (the steam fog)
        self.burst: bool = False
        self.steam: Steam = Steam(pr.vector3_add(pos, crack), pr.Vector3(0.0, 0.0, -1.0))   # into the room
        self.until_check: float = random.uniform(*PIPE_CHECK_INTERVAL)

    def set_burst(self, burst: bool) -> None:
        self.burst = burst
        self.model = self.burst_model if burst else self.whole_model
        self.steam.on = burst
        print(f"PIPE: {self.name} {'burst' if burst else 'fixed'}")

    def debug_lines(self) -> list[str]:
        chance = PIPE_BURST_CHANCE * self.system.pressure ** 2
        return super().debug_lines() + [
            f"burst: {self.burst}, {self.system.name} pressure {self.system.pressure:.0%} "
            f"(burst chance {chance:.0%} every ~{sum(PIPE_CHECK_INTERVAL) / 2:.0f} s), "
            f"{len(self.steam.particles)} steam particles"]

    def unload(self) -> None:
        self.model = self.whole_model
        super().unload()
        pr.unload_model(self.burst_model)


class Pipes:
    def __init__(self, pipes: list[Pipe], audio: Audio, repair_sound: str) -> None:
        self.pipes: list[Pipe] = pipes
        self.audio: Audio = audio
        self.repair_sound: str = repair_sound
        self.smoke: dict[tuple[float, float], float] = {pipe.zone: 0.0 for pipe in pipes}   # per car, 0..1
        self.target: Pipe | None = None   # the burst pipe you look at (within reach)
        self.progress: float = 0.0        # 0..1 of the repair
        self.blink: float = -1.0          # seconds into a blink, -1 = not blinking
        self._fixing: Pipe | None = None  # fixed when the eyes are shut
        image = pr.gen_image_gradient_radial(64, 64, 0.0, pr.WHITE, pr.BLANK)   # a soft round puff
        self.puff: pr.Texture = pr.load_texture_from_image(image)
        pr.unload_image(image)

    def burst(self, pipe: Pipe) -> None:
        if pipe.burst:
            return
        pipe.set_burst(True)
        self._leak(pipe.system)
        self.audio.add_source(PIPE_LEAK_SOUND, pipe.steam.origin, 1.0, 3.0, 12.0, name=f"leak_{pipe.name}")

    def fix(self, pipe: Pipe) -> None:
        pipe.set_burst(False)
        self._leak(pipe.system)
        self.audio.remove_source(f"leak_{pipe.name}")
        self.audio.play_sound(self.repair_sound)

    def _leak(self, system: Regulator) -> None:
        """Each burst pipe of `system` loses PIPE_LEAK of the pressure the others leave."""
        burst = sum(1 for pipe in self.pipes if pipe.system is system and pipe.burst)
        system.leak = 1.0 - (1.0 - PIPE_LEAK) ** burst

    def update(self, dt: float, camera: pr.Camera3D, repairing: bool) -> None:
        for pipe in self.pipes:
            pipe.until_check -= dt
            if pipe.until_check <= 0:
                pipe.until_check = random.uniform(*PIPE_CHECK_INTERVAL)
                if not pipe.burst and random.random() < PIPE_BURST_CHANCE * pipe.system.pressure ** 2:
                    self.burst(pipe)
            pipe.steam.update(dt)
        for zone in self.smoke:
            steaming = any(p.burst for p in self.pipes if p.zone == zone)
            rate = SMOKE_RISE if steaming else -SMOKE_CLEAR
            self.smoke[zone] = min(max(self.smoke[zone] + rate * dt, 0.0), 1.0)

        if self.blink >= 0:   # eyes closing / shut / opening; it gets fixed while they are shut
            self.blink += dt
            close, shut, _ = BLINK_TIME
            if self._fixing is not None and self.blink >= close:
                self.fix(self._fixing)
                self._fixing = None
            if self.blink >= sum(BLINK_TIME):
                self.blink = -1.0
            return
        hits = [(d, p) for p in self.pipes
                if p.burst and (d := p.target_distance(camera, PIPE_REPAIR_REACH)) is not None]
        self.target = min(hits, key=lambda hit: hit[0])[1] if hits else None
        if self.target is not None and repairing:
            self.progress += dt / PIPE_REPAIR_TIME
            if self.progress >= 1.0:
                self.progress = 0.0
                self._fixing = self.target
                self.blink = 0.0
        else:
            self.progress = 0.0

    def smoke_at(self, z: float) -> float:
        """0..1: how much smoke there is in the car at `z`."""
        return next((amount for (low, high), amount in self.smoke.items() if low <= z < high), 0.0)

    def draw_smoke(self, z: float) -> None:
        """Over the whole screen, HUD included: the smoke of the car you are in (at `z`), with a few big soft
        puffs drifting through it so it doesn't look like a flat filter."""
        amount = self.smoke_at(z) * SMOKE_MAX
        if amount <= 0:
            return
        w, h = pr.get_screen_width(), pr.get_screen_height()
        pr.draw_rectangle(0, 0, w, h, pr.fade(SMOKE_COLOR, amount * 0.8))
        t = pr.get_time()
        for i in range(6):   # each drifts sideways and wobbles, wrapping round the screen
            x = ((i * 0.37 + t * (0.02 + 0.01 * i)) % 1.4 - 0.2) * w
            y = (0.2 + 0.6 * ((i * 0.53) % 1.0) + 0.05 * math.sin(t * 0.7 + i)) * h
            size = h * (0.6 + 0.15 * math.sin(t * 0.3 + i * 2.0))
            pr.draw_texture_pro(self.puff, pr.Rectangle(0, 0, self.puff.width, self.puff.height),
                                pr.Rectangle(x - size / 2, y - size / 2, size, size), pr.Vector2(0, 0), 0.0,
                                pr.fade(SMOKE_COLOR, amount * 0.6))

    def draw(self, camera: pr.Camera3D, brightness: Callable[[Pipe], float] = lambda pipe: 1.0) -> None:
        """The steam (inside 3D mode, after the scene), as bright as `brightness(pipe)` says (dark in a dark car).
        Transparent: it doesn't write depth."""
        pr.rl_disable_depth_mask()
        for pipe in self.pipes:
            if pipe.steam.particles:
                pipe.steam.draw(camera, self.puff, brightness(pipe))
        pr.rl_enable_depth_mask()

    def draw_hud(self) -> None:
        w, h = pr.get_screen_width(), pr.get_screen_height()
        s = h / SCREEN_H
        if self.target is not None and self.blink < 0:   # a ring round the crosshair; fills while you hold E
            center = pr.Vector2(w / 2, h / 2)
            pr.draw_ring(center, 14 * s, 18 * s, 0, 360, 48, pr.fade(pr.WHITE, 0.3))
            if self.progress > 0:
                pr.draw_ring(center, 14 * s, 18 * s, -90, -90 + 360 * self.progress, 48, pr.WHITE)
            else:
                pr.draw_text("E", int(w / 2 + 24 * s), int(h / 2 - 8 * s), int(16 * s), pr.fade(pr.WHITE, 0.7))
        if self.blink >= 0:
            close, shut, opening = BLINK_TIME
            t = self.blink
            dark = t / close if t < close else 1.0 if t < close + shut else 1.0 - (t - close - shut) / opening
            pr.draw_rectangle(0, 0, w, h, pr.fade(pr.BLACK, min(max(dark, 0.0), 1.0)))

    def unload(self) -> None:
        pr.unload_texture(self.puff)
