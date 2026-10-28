"""Dial: a gauge needle that points at a value (temperature, pressure...).

    dial = Dial("oxygen_pressure", "Models/Oxygen_Pressure.glb", car.pos, low=0, high=100, sweep=360)
    dial.value = 42.0    # the game sets what it should show
    dial.update(dt)      # every frame: the needle swings there

The model is just the needle (the face is part of the room), a rigged .glb modelled in place in its car (see
entity.py): the bone's head at the centre of the face, its Y axis pointing out of the face, towards the player.
The needle turns about that bone, clockwise as you look at the face, like the Spin360 animation (which we don't
play; turning it in code lets it stop at any value).

A sliding dial (`slide` > 0: Oxygen_Level, the marker in a straight scale) moves `slide` units along the bone's -X
instead, like its Move animation.
"""
from __future__ import annotations

from pathlib import Path

import pyray as pr

from .config import DIAL_NEEDLE_SPEED
from .entity import Entity, bone_pivot_axis, bone_x, rotation_about


class Dial(Entity):
    """`value` is clamped to low..high and shown as `sweep` degrees of needle travel (or `slide` units of marker
    travel); the modelled pose is `low`, unless `start` (degrees) turns the needle's `low` away from it. `shown` is where the needle actually is: it follows `value` with a short
    lag instead of jumping."""

    def __init__(self, name: str, model_path: str | Path, pos: pr.Vector3,
                 low: float = 0.0, high: float = 1.0, sweep: float = 270.0, slide: float = 0.0) -> None:
        super().__init__(name, model_path, pos)
        self.pivot, y = bone_pivot_axis(self.model)
        # positive angles about -Y turn clockwise when you look at the face down the bone's Y axis
        self.axis: pr.Vector3 = pr.vector3_negate(y)
        self.low: float = low
        self.high: float = high
        self.sweep: float = sweep
        self.start: float = 0.0
        self.slide: float = slide
        self.slide_dir: pr.Vector3 = pr.vector3_negate(bone_x(self.model))
        self.value: float = low
        self.shown: float = low

    def update(self, dt: float) -> None:
        target = min(max(self.value, self.low), self.high)
        # ease towards the target: covers DIAL_NEEDLE_SPEED * dt of the remaining distance each frame
        self.shown += (target - self.shown) * min(DIAL_NEEDLE_SPEED * dt, 1.0)
        fraction = (self.shown - self.low) / (self.high - self.low)
        if self.slide:
            d = pr.vector3_scale(self.slide_dir, fraction * self.slide)
            self.set_transform(pr.matrix_translate(d.x, d.y, d.z))
        else:
            self.set_transform(rotation_about(self.pivot, self.axis, self.start + fraction * self.sweep))

    def debug_lines(self) -> list[str]:
        travel = f"slides {self.slide:g}" if self.slide else f"sweep {self.sweep:g} deg from {self.start:g}"
        return super().debug_lines() + [
            f"value: {self.value:.1f} (needle at {self.shown:.1f}), range {self.low:g}..{self.high:g}, {travel}"
        ]
