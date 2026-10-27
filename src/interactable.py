"""Interactable: an Entity the player can use (lever, valve, button...).

    lever = Lever("lever", config.LEVER_MODEL, config.LEVER_POS)
    lever.interact()    # flips it and prints the new state

Subclasses override `interact()` (what a click does) and `update(dt)` (animation).
Grabbable ones (valve) instead get `grab(camera)` on click, `drag(mouse_delta)` every frame while the
button is held (mouse look is off meanwhile) and `release()`.
"""
from __future__ import annotations

import math

import pyray as pr

from .config import VALVE_TURN_SPEED
from .entity import Entity


class Interactable(Entity):
    grabbable: bool = False

    def interact(self) -> None:
        """Called once when the player clicks while looking at it."""

    def grab(self, camera: pr.Camera3D) -> None:
        """Grabbable only: the player clicked on it and is now holding it."""

    def drag(self, delta: pr.Vector2) -> None:
        """Grabbable only: mouse movement (pixels) this frame while held."""

    def release(self) -> None:
        """Grabbable only: the player let go (or walked / looked away)."""

    def update(self, dt: float) -> None:
        """Called every frame (animation)."""


class Lever(Interactable):
    """Two states: up (False) and down (True)."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.down: bool = False

    def interact(self) -> None:
        self.down = not self.down
        print(f"{self.name}: {'down' if self.down else 'up'}")


class Valve(Interactable):
    """A wheel you grab and turn by moving the mouse left / right, like pulling the top of its rim.
    Right turns it clockwise as you see it (closes), left counter-clockwise (opens).

    `angle` (degrees, 0 = closed, no upper limit) is kept between grabs.
    `spin` (degrees / s) turns it on its own for emergencies: positive opens, negative closes (and stops at 0),
    0 stops it. It keeps going while held, so the player has to fight it.

        valve.spin = VALVE_BREAK_SPIN    # broken: starts opening by itself
        valve.spin = 0.0                 # repaired

    The model rotates about `axis` (model space) through the centre of its box.
    """

    grabbable = True

    def __init__(self, *args, axis: pr.Vector3 = pr.Vector3(0.0, 0.0, 1.0), **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.axis: pr.Vector3 = axis
        self.angle: float = 0.0
        self.spin: float = 0.0
        bb = pr.get_model_bounding_box(self.model)
        self.pivot: pr.Vector3 = pr.Vector3(
            (bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2, (bb.min.z + bb.max.z) / 2
        )
        self._facing: float = 1.0   # -1 if the axis points at the player (flips the turn direction)

    @property
    def turns(self) -> float:
        return self.angle / 360.0

    def turn(self, degrees: float) -> None:
        self.angle = max(self.angle + degrees, 0.0)

    def grab(self, camera: pr.Camera3D) -> None:
        forward = pr.vector3_subtract(camera.target, camera.position)
        self._facing = -1.0 if pr.vector3_dot_product(self.axis, forward) < 0 else 1.0

    def drag(self, delta: pr.Vector2) -> None:
        # a positive angle is counter-clockwise when the axis points at you, so mouse right (clockwise) subtracts
        self.turn(delta.x * VALVE_TURN_SPEED * self._facing)

    def release(self) -> None:
        print(f"{self.name}: {self.angle:.0f} deg ({self.turns:.2f} turns open)")

    def update(self, dt: float) -> None:
        if self.spin:
            self.turn(self.spin * dt)
        # Rotate about the pivot, not the model's origin: move the pivot to the origin, rotate, move it back.
        # raylib's matrix_multiply(a, b) applies a first, then b. draw_model applies model.transform before `pos`.
        p = self.pivot
        self.model.transform = pr.matrix_multiply(
            pr.matrix_multiply(pr.matrix_translate(-p.x, -p.y, -p.z),
                               pr.matrix_rotate(self.axis, math.radians(self.angle))),
            pr.matrix_translate(p.x, p.y, p.z),
        )
