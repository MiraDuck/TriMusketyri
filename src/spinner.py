"""Spinner: a part that keeps turning on its own (the engine).

    engine = Spinner("engine", "Models/Engine_Spin.glb", car.pos, speed=180)
    engine.speed = 0.0   # stalled
    engine.update(dt)    # every frame

A rigged .glb modelled in place in its car (see entity.py). It turns about its bone's Y axis, the same way as its
Spin360 animation (positive speed = about -Y).
"""
from __future__ import annotations

from pathlib import Path

import pyray as pr

from .entity import Entity, bone_pivot_axis, rotation_about


class Spinner(Entity):
    """`speed` in degrees / s, 0 = stopped; `angle` is where it is now (0..360)."""

    def __init__(self, name: str, model_path: str | Path, pos: pr.Vector3, speed: float = 0.0) -> None:
        super().__init__(name, model_path, pos)
        self.pivot, y = bone_pivot_axis(self.model)
        self.axis: pr.Vector3 = pr.vector3_negate(y)
        self.speed: float = speed
        self.angle: float = 0.0

    def update(self, dt: float) -> None:
        self.angle = (self.angle + self.speed * dt) % 360.0
        self.set_transform(rotation_about(self.pivot, self.axis, self.angle))

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [f"speed: {self.speed:g} deg/s, angle {self.angle:.0f} deg"]
