"""Dial: a gauge needle that points at a value (temperature, pressure...).

    dial = Dial("temp_pressure", config.TEMP_PRESSURE_DIAL_MODEL, car.pos, low=0, high=100, sweep=270)
    dial.value = 42.0    # the game sets what it should show
    dial.update(dt)      # every frame: the needle swings there

The model is just the needle (the face is part of the room), exported from Blender as .glb with the same origin as
its room and rigged with one bone: its head at the centre of the face, its Y axis pointing out of the face, towards
the player (Temperature_Pressure.glb). The needle turns about that bone, clockwise as you look at the face, like
the Spin360 animation (which we don't play; turning it in code lets it stop at any value).
"""
from __future__ import annotations

from pathlib import Path

import pyray as pr

from .config import DIAL_NEEDLE_SPEED
from .entity import Entity, rotation_about


class Dial(Entity):
    """`value` is clamped to low..high and shown as `sweep` degrees of needle travel; the modelled pose is `low`.
    `shown` is where the needle actually is: it follows `value` with a short lag instead of jumping."""

    def __init__(self, name: str, model_path: str | Path, pos: pr.Vector3,
                 low: float = 0.0, high: float = 1.0, sweep: float = 360.0) -> None:
        super().__init__(name, model_path, pos)
        if self.model.skeleton.boneCount < 1:
            raise ValueError(f"{model_path}: a dial needs a bone at the needle's centre")
        bone = self.model.skeleton.bindPose[0]   # where the bone sits in Blender (model space)
        self.pivot: pr.Vector3 = pr.Vector3(bone.translation.x, bone.translation.y, bone.translation.z)
        # positive angles about -Y turn clockwise when you look at the face down the bone's Y axis
        self.axis: pr.Vector3 = pr.vector3_rotate_by_quaternion(pr.Vector3(0.0, -1.0, 0.0), bone.rotation)
        self.low: float = low
        self.high: float = high
        self.sweep: float = sweep
        self.value: float = low
        self.shown: float = low

    def update(self, dt: float) -> None:
        target = min(max(self.value, self.low), self.high)
        # ease towards the target: covers DIAL_NEEDLE_SPEED * dt of the remaining distance each frame
        self.shown += (target - self.shown) * min(DIAL_NEEDLE_SPEED * dt, 1.0)
        fraction = (self.shown - self.low) / (self.high - self.low)
        self.model.transform = rotation_about(self.pivot, self.axis, fraction * self.sweep)
