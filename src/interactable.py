"""Interactable: an Entity the player can use (lever, valve, button...).

    lever = Lever("lever", config.LEVER_MODEL, config.LEVER_POS)
    lever.interact()    # flips it and prints the new state
    button = Button("power_button", "Models/Control_Rooms/Power_Lever.glb", car.pos, throw=-90)

Subclasses override `interact()` (what a click does) and `update(dt)` (animation).
Grabbable ones (valve) instead get `grab(camera)` on click, `drag(mouse_delta)` every frame while the
button is held (mouse look is off meanwhile) and `release()`.
"""
from __future__ import annotations

import pyray as pr

from .config import LEVER_FLIP_TIME, VALVE_FIX_TIME, VALVE_TURN_SPEED
from .entity import Entity, bone_pivot_axis, bone_x, rotation_about


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
    """Two states: up (False, as modelled) and down (True). Breakers and switches are levers too.

    A rigged one (.glb) swings `throw` degrees about its bone's Y axis (`bone_axis="x"`: its X axis) when pulled
    down (negative = the other way), taking `flip_time` (LEVER_FLIP_TIME); `angle` is where it is on the way. Without a bone (lever.obj) it doesn't move.
    `flipped` is True for the one frame (after update) in which `down` changed, by a click or by a fault.
    """

    def __init__(self, *args, throw: float = 0.0, bone_axis: str = "y", flip_time: float = LEVER_FLIP_TIME,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.down: bool = False
        self.throw: float = throw
        self.flip_time: float = flip_time
        self.angle: float = 0.0
        self.flipped: bool = False
        self._was_down: bool = False
        self.pivot, self.axis = bone_pivot_axis(self.model) if throw else (None, None)
        if throw and bone_axis == "x":
            self.axis = bone_x(self.model)

    @property
    def thrown(self) -> bool:
        """True once the handle has swung past halfway down: what a switch acts on (`down` flips on the click)."""
        if self.pivot is None:
            return self.down
        return abs(self.angle) > abs(self.throw) / 2

    def interact(self) -> None:
        self.down = not self.down
        print(f"{self.name}: {'down' if self.down else 'up'}")

    def update(self, dt: float) -> None:
        self.flipped = self.down != self._was_down
        self._was_down = self.down
        self._swing(dt)

    def _swing(self, dt: float) -> None:
        """Move the handle towards `down` / up."""
        if self.pivot is None:
            return
        target = self.throw if self.down else 0.0
        step = abs(self.throw) / self.flip_time * dt
        self.angle = min(self.angle + step, target) if self.angle < target else max(self.angle - step, target)
        self.set_transform(rotation_about(self.pivot, self.axis, self.angle))

    def debug_lines(self) -> list[str]:
        moving = f", angle {self.angle:.0f} of {self.throw:.0f} deg" if self.pivot is not None else ""
        return super().debug_lines() + [f"down: {self.down}{moving}"]


class Button(Lever):
    """A press button: a click plays its swing (`throw` degrees about its bone, like a lever) there and back again,
    and `flipped` is True for the one frame (after update) the press starts in. `down` is True on the way there."""

    def interact(self) -> None:
        self.down = True
        print(f"{self.name}: pressed")

    def update(self, dt: float) -> None:
        self.flipped = self.down and not self._was_down
        self._was_down = self.down
        self._swing(dt)
        if self.down and self.angle == self.throw:   # all the way over: come back
            self.down = False


class Valve(Interactable):
    """A wheel you grab and turn by moving the mouse left / right, like pulling the top of its rim.
    Right turns it clockwise as you see it (closes), left counter-clockwise (opens).

    `angle` (degrees, 0 = closed, up to `max_angle`; None = no upper limit) is kept between grabs.
    `turning` is True while it moved this frame (by hand, `spin` or `drift`).
    `spin` (degrees / s) turns it on its own, for the game (the engine opens its valve after a restart): positive
    opens, negative closes (and stops at 0), 0 stops it.
    `drift` (degrees / s) is the same for a fault (faults.py), started by `start_drift(speed, degrees)`: it creeps
    `degrees` by itself, then stops; the player turns it back. Holding it for VALVE_FIX_TIME stops it sooner.

    A rigged one (.glb) turns about its bone's Y axis through its head; otherwise about `axis` (model space)
    through the centre of its box.
    """

    grabbable = True

    def __init__(self, *args, axis: pr.Vector3 = pr.Vector3(0.0, 0.0, 1.0), **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.angle: float = 0.0
        self.max_angle: float | None = None
        self.spin: float = 0.0
        self.drift: float = 0.0
        self._drift_left: float = 0.0   # degrees it still creeps
        self.held: bool = False
        self._held_for: float = 0.0   # while drifting: how long it has been held
        self.turning: bool = False
        self._last_angle: float = 0.0
        if self.model.skeleton.boneCount:
            self.pivot, self.axis = bone_pivot_axis(self.model)
        else:
            bb = pr.get_model_bounding_box(self.model)
            self.pivot = pr.Vector3((bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2, (bb.min.z + bb.max.z) / 2)
            self.axis = axis
        self._facing: float = 1.0   # -1 if the axis points at the player (flips the turn direction)

    @property
    def turns(self) -> float:
        return self.angle / 360.0

    def turn(self, degrees: float) -> None:
        self.angle = max(self.angle + degrees, 0.0)
        if self.max_angle is not None:
            self.angle = min(self.angle, self.max_angle)

    def start_drift(self, speed: float, degrees: float) -> None:
        """A fault: creep `degrees` at `speed` deg/s (negative = shut) by itself, then stop."""
        self.drift, self._drift_left = speed, degrees

    def set_angle(self, degrees: float) -> None:
        """Put it at `degrees` straight away (a start setting): not a turn, so `turning` stays False."""
        self.angle = self._last_angle = degrees

    def grab(self, camera: pr.Camera3D) -> None:
        forward = pr.vector3_subtract(camera.target, camera.position)
        self._facing = -1.0 if pr.vector3_dot_product(self.axis, forward) < 0 else 1.0
        self.held = True

    def drag(self, delta: pr.Vector2) -> None:
        # a positive angle is counter-clockwise when the axis points at you, so mouse right (clockwise) subtracts
        self.turn(delta.x * VALVE_TURN_SPEED * self._facing)

    def release(self) -> None:
        self.held = False
        print(f"{self.name}: {self.angle:.0f} deg ({self.turns:.2f} turns open)")

    def debug_lines(self) -> list[str]:
        state = (f"angle: {self.angle:.1f} deg ({self.turns:.2f} turns), spin {self.spin:g}, "
                 f"drift {self.drift:.1f} deg/s")
        return super().debug_lines() + [state]

    def update(self, dt: float) -> None:
        creep = 0.0
        if self.drift:   # a fault: it creeps until it has gone its distance, or it was held long enough
            creep = min(abs(self.drift) * dt, self._drift_left)
            self._drift_left -= creep
            creep = creep if self.drift > 0 else -creep
            self._held_for = self._held_for + dt if self.held else 0.0
            if self._held_for >= VALVE_FIX_TIME or self._drift_left <= 0:
                print(f"{self.name}: {'stabilized' if self._drift_left > 0 else 'stopped drifting'}")
                self.drift = 0.0
        if self.spin or creep:
            self.turn(self.spin * dt + creep)
        self.turning = self.angle != self._last_angle
        self._last_angle = self.angle
        self.set_transform(rotation_about(self.pivot, self.axis, self.angle))
