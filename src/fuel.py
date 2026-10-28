"""Fuel: coal for the engine. Take a piece from the stockpile, carry it to the engine room, throw it into the furnace.

    fuel = Fuel(pile, hatch, coal, audio, take_sound, feed_sound, dial)
    fuel.update(dt, camera, engine.speed, engine.depth)   # every frame, after the pile and the hatch updated
    engine.update(dt, fuel.factor)                         # the fuel limits / boosts the engine
    life.update(dt, engine.depth, fuel.heat)               # overclocking heats the drill
    fuel.draw_held(view_camera)                            # inside 3D mode, last: the coal in your hand

- `level` 0..1: the engine burns FUEL_BURN (+ FUEL_BURN_PER_METRE * depth, at most FUEL_BURN_MAX) per s at full
  speed, times its speed. Each piece of coal adds FUEL_PER_COAL (at most up to full).
- `factor` multiplies the engine's power: below FUEL_LOW (30 %) it falls with the fuel, to 0 when empty (the engine
  dies on the way); above FUEL_OVERCLOCK (90 %) it rises to FUEL_OVERCLOCK_BOOST at full: the engine OVERCLOCKS,
  spinning faster than 100 % (digs faster, burns faster) and heating the drill (`heat`, added to the cooling's drift).
- Click the stockpile (CoalPile) with empty hands: you carry one piece (drawn in your hand). Click the furnace hatch
  (Hatch): it swings open / shut; click it while it is open and you carry coal: the coal goes in.
- The fuel bar on the console (Fuel_Level, a sliding dial: its marker is modelled at the top and slides down) shows
  the level: full at the top, empty at the bottom.
"""
from __future__ import annotations

import math

import pyray as pr

from .audio import Audio
from .config import (
    COAL_HELD_OFFSET, COAL_HELD_SCALE, FUEL_BURN, FUEL_BURN_MAX, FUEL_BURN_PER_METRE, FUEL_LOW, FUEL_OVERCLOCK,
    FUEL_OVERCLOCK_BOOST, FUEL_OVERCLOCK_HEAT, FUEL_PER_COAL, FUEL_START, SFX_FAR, SFX_NEAR,
)
from .dial import Dial
from .entity import Entity
from .interactable import Interactable, Lever


class CoalPile(Interactable):
    """The stockpile in the storage room. `clicked` is True for the one frame (after update) after a click: Fuel
    decides what it does."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.clicked: bool = False
        self._click: bool = False

    def interact(self) -> None:
        self._click = True

    def update(self, dt: float) -> None:
        self.clicked, self._click = self._click, False


class Hatch(Lever):
    """The furnace door on the engine, a rigged .glb: it swings `throw` degrees about its bone (upright, on the edge
    away from the handle) like a lever; `down` = open. A click only sets `clicked` (like CoalPile): Fuel decides
    whether it opens / shuts or takes the coal. You can click it where the door is shut or where it swung to."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.clicked: bool = False
        self._click: bool = False
        self._shut_bounds: pr.BoundingBox = self.bounds

    @property
    def open(self) -> bool:
        return self.thrown

    def interact(self) -> None:
        self._click = True

    def update(self, dt: float) -> None:
        self.clicked, self._click = self._click, False
        super().update(dt)

    def set_transform(self, transform: pr.Matrix) -> None:
        super().set_transform(transform)
        if hasattr(self, "_shut_bounds"):   # the box around the shut and the swung door: the opening stays clickable
            shut, now = self._shut_bounds, self.bounds
            self.bounds = pr.BoundingBox(pr.vector3_min(shut.min, now.min), pr.vector3_max(shut.max, now.max))


class Fuel:
    def __init__(self, pile: CoalPile, hatch: Hatch, coal: Entity, audio: Audio, take_sound: str,
                 feed_sound: str, dial: Dial | None = None) -> None:
        self.pile: CoalPile = pile
        self.hatch: Hatch = hatch
        self.coal: Entity = coal   # the piece you carry, modelled at its own origin
        self.audio: Audio = audio
        self.take_sound: str = take_sound
        self.feed_sound: str = feed_sound
        self.dial: Dial | None = dial   # the fuel bar on the console
        self.level: float = FUEL_START
        self.carrying: bool = False
        self.fed: int = 0   # pieces thrown in
        self.burn: float = 0.0   # fuel / s it burns now
        for part in (pile, hatch):
            part.debug_extra = self.debug_lines

    @property
    def overclock(self) -> float:
        """0..1: how far above FUEL_OVERCLOCK the fuel is (1 = full)."""
        return min(max((self.level - FUEL_OVERCLOCK) / (1.0 - FUEL_OVERCLOCK), 0.0), 1.0)

    @property
    def factor(self) -> float:
        """What the engine's power is multiplied by: 0..1 below FUEL_LOW, 1, up to FUEL_OVERCLOCK_BOOST at full."""
        if self.level < FUEL_LOW:
            return self.level / FUEL_LOW
        return 1.0 + (FUEL_OVERCLOCK_BOOST - 1.0) * self.overclock

    @property
    def heat(self) -> float:
        """Extra temperature / s while overclocking."""
        return FUEL_OVERCLOCK_HEAT * self.overclock

    def update(self, dt: float, camera: pr.Camera3D, speed: float, depth: float) -> None:
        if self.pile.clicked and not self.carrying:
            self.carrying = True
            self.audio.play_sound_at(self.take_sound, self.pile.center, camera, SFX_NEAR, SFX_FAR)
            print("FUEL: took a piece of coal")
        if self.hatch.clicked:
            if self.carrying and self.hatch.open:
                self.carrying = False
                self.fed += 1
                self.level = min(self.level + FUEL_PER_COAL, 1.0)
                self.audio.play_sound_at(self.feed_sound, self.hatch.center, camera, SFX_NEAR, SFX_FAR)
                print(f"FUEL: coal in, fuel {self.level:.0%}")
            else:   # it plays its sound as a switch (SWITCH_SOUNDS)
                self.hatch.down = not self.hatch.down
                print(f"{self.hatch.name}: {'opening' if self.hatch.down else 'shutting'}")
        self.burn = min(FUEL_BURN + FUEL_BURN_PER_METRE * depth, FUEL_BURN_MAX) * speed
        self.level = max(self.level - self.burn * dt, 0.0)
        if self.dial is not None:   # its marker is modelled at the top (its `low`) and slides down: full at the top
            self.dial.value = self.dial.high - (self.dial.high - self.dial.low) * self.level

    def draw_held(self, camera: pr.Camera3D) -> None:
        """The coal in your hand, low right in front of the eye, over everything (it never sinks into a wall)."""
        if not self.carrying:
            return
        forward = pr.vector3_normalize(pr.vector3_subtract(camera.target, camera.position))
        right = pr.vector3_normalize(pr.vector3_cross_product(forward, pr.Vector3(0.0, 1.0, 0.0)))
        up = pr.vector3_cross_product(right, forward)
        x, y, z = COAL_HELD_OFFSET
        pos = camera.position
        for axis, amount in ((right, x), (up, y), (forward, z)):
            pos = pr.vector3_add(pos, pr.vector3_scale(axis, amount))
        yaw = math.degrees(math.atan2(forward.x, forward.z))   # turns with you
        pr.rl_draw_render_batch_active()
        pr.rl_disable_depth_test()
        pr.draw_model_ex(self.coal.model, pos, pr.Vector3(0.0, 1.0, 0.0), yaw, pr.Vector3(*(COAL_HELD_SCALE,) * 3),
                         pr.WHITE)
        pr.rl_draw_render_batch_active()
        pr.rl_enable_depth_test()

    def debug_lines(self) -> list[str]:
        state = ", OVERCLOCKED" if self.overclock else ", LOW" if self.level < FUEL_LOW else ""
        return [f"fuel: {self.level:.0%}{state}, engine power x{self.factor:.2f}, burning {self.burn * 60:.1%}/min, "
                f"carrying: {self.carrying}, {self.fed} fed, hatch {'open' if self.hatch.open else 'closed'}"]
