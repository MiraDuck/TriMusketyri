"""Head bob (from bob_example.c).

Purely visual: apply() returns a copy of the camera for drawing, so the
player's real position (and therefore collision / y) is never affected.
"""
import math

from pyray import *

from .config import BOB_SIDE, STEP_ROTATION, WALK_FOV_DELTA


def smooth(rate, dt):
    """Frame-rate independent lerp factor (same easing at any FPS)."""
    return 1.0 - math.exp(-rate * dt)


class HeadBob:
    def __init__(self):
        self.head_timer = 0.0
        self.walk_lerp = 0.0
        self.fov_offset = 0.0
        self.lean_x = 0.0
        self.lean_y = 0.0

    def update(self, moving, sideway, forward, dt):
        if moving:
            self.head_timer += dt * 3.0
            self.walk_lerp += (1.0 - self.walk_lerp) * smooth(10.0, dt)
            self.fov_offset += (WALK_FOV_DELTA - self.fov_offset) * smooth(5.0, dt)
        else:
            self.walk_lerp += (0.0 - self.walk_lerp) * smooth(10.0, dt)
            self.fov_offset += (0.0 - self.fov_offset) * smooth(5.0, dt)
        self.lean_x += (sideway * 0.02 - self.lean_x) * smooth(10.0, dt)
        self.lean_y += (forward * 0.015 - self.lean_y) * smooth(10.0, dt)

    def apply(self, cam):
        """Return a copy of cam with the bob effects applied (y is left untouched)."""
        fwd = vector3_normalize(vector3_subtract(cam.target, cam.position))
        right = vector3_normalize(vector3_cross_product(fwd, Vector3(0, 1, 0)))
        head_sin = math.sin(self.head_timer * math.pi)

        # sway sideways only; no vertical offset
        sway = vector3_scale(right, head_sin * BOB_SIDE * self.walk_lerp)
        pos = vector3_add(cam.position, sway)

        look = vector3_rotate_by_axis_angle(fwd, right, -self.lean_y)
        up = vector3_rotate_by_axis_angle(
            Vector3(0, 1, 0), look, head_sin * STEP_ROTATION + self.lean_x)

        fovy = cam.fovy
        if cam.projection == CameraProjection.CAMERA_PERSPECTIVE:
            fovy += self.fov_offset
        return Camera3D(pos, vector3_add(pos, look), up, fovy, cam.projection)
