"""Player body: cuboid around the camera, gravity and collision response."""
from __future__ import annotations

from typing import Iterable

import pyray as pr

from .collision import MeshCollider, is_ceiling, is_floor, is_wall
from .config import (
    EYE_TO_CENTER, GRAVITY, MAX_FALL_SPEED, PLAYER_HALF, STEP_UP, WORLD_FLOOR_Y,
)

DOWN: pr.Vector3 = pr.Vector3(0, -1, 0)
UP: pr.Vector3 = pr.Vector3(0, 1, 0)

# Down-rays for the floor: center + 4 points inside the box corners
_f = 0.8
FLOOR_SAMPLES: list[tuple[float, float]] = [
    (0.0, 0.0),
    (PLAYER_HALF.x * _f, PLAYER_HALF.z * _f),
    (-PLAYER_HALF.x * _f, PLAYER_HALF.z * _f),
    (PLAYER_HALF.x * _f, -PLAYER_HALF.z * _f),
    (-PLAYER_HALF.x * _f, -PLAYER_HALF.z * _f),
]

WALL_DIRS: list[tuple[pr.Vector3, float]] = [
    (pr.Vector3(1, 0, 0),  PLAYER_HALF.x),
    (pr.Vector3(-1, 0, 0), PLAYER_HALF.x),
    (pr.Vector3(0, 0, 1),  PLAYER_HALF.z),
    (pr.Vector3(0, 0, -1), PLAYER_HALF.z),
]


class Player:
    """The real camera is the player's position; this adds a body around it."""

    def __init__(self, camera: pr.Camera3D) -> None:
        self.camera: pr.Camera3D = camera
        self.vel_y: float = 0.0
        self.on_ground: bool = False
        self.colliding: bool = False

    # ---- helpers ----
    def box(self) -> tuple[pr.Vector3, pr.BoundingBox]:
        """Returns (center, BoundingBox) of the player cuboid."""
        p = self.camera.position
        c = pr.Vector3(p.x, p.y - EYE_TO_CENTER, p.z)
        box = pr.BoundingBox(
            pr.Vector3(c.x - PLAYER_HALF.x, c.y - PLAYER_HALF.y, c.z - PLAYER_HALF.z),
            pr.Vector3(c.x + PLAYER_HALF.x, c.y + PLAYER_HALF.y, c.z + PLAYER_HALF.z),
        )
        return c, box

    def _shift(self, dx: float, dy: float, dz: float) -> None:
        """Move position AND target together so the view direction doesn't change."""
        cam = self.camera
        cam.position = pr.Vector3(cam.position.x + dx, cam.position.y + dy, cam.position.z + dz)
        cam.target = pr.Vector3(cam.target.x + dx, cam.target.y + dy, cam.target.z + dz)

    # ---- physics ----
    def apply_gravity(self, dt: float) -> None:
        """Pull the player down; resolve_collision() then pushes them back onto the floor."""
        self.vel_y = max(self.vel_y - GRAVITY * dt, -MAX_FALL_SPEED)
        self._shift(0, self.vel_y * dt, 0)

    def land_on_world_floor(self) -> None:
        """Stop the player at WORLD_FLOOR_Y if the collision model didn't catch them."""
        feet = self.camera.position.y - EYE_TO_CENTER - PLAYER_HALF.y
        if feet < WORLD_FLOOR_Y:
            self._shift(0, WORLD_FLOOR_Y - feet, 0)
            self.on_ground = True

    def resolve_collision(self, colliders: Iterable[MeshCollider]) -> bool:
        """Push the player out of every collider. Returns True if touching any of them."""
        self.on_ground = False
        touched = False
        for world in colliders:
            touched |= self._resolve_one(world)
        return touched

    def _resolve_one(self, world: MeshCollider) -> bool:
        """Push the player out of one collider; sets on_ground if standing on it."""
        c, box = self.box()
        if not pr.check_collision_boxes(box, world.bounds):   # broadphase
            return False

        feet = c.y - PLAYER_HALF.y
        head = c.y + PLAYER_HALF.y
        push = pr.Vector3(0, 0, 0)
        touched = False

        # --- Floor: several rays from just above the feet, keep the HIGHEST floor ---
        floor_y = None
        for ox, oz in FLOOR_SAMPLES:
            o = pr.Vector3(c.x + ox, feet + STEP_UP, c.z + oz)
            p = world.cast(o, DOWN, is_floor)
            if p is not None and (floor_y is None or p.y > floor_y):
                floor_y = p.y
        if floor_y is not None:
            if floor_y > feet:
                push.y += floor_y - feet
                touched = True
            if floor_y >= feet - 0.05:
                self.on_ground = True

        # --- Ceiling ---
        p = world.cast(c, UP, is_ceiling)
        if p is not None and p.y < head:
            push.y -= head - p.y
            touched = True

        # --- Walls: rays at two heights, ignoring floor-like triangles ---
        for h in (feet + STEP_UP + 0.1, head - 0.2):
            o = pr.Vector3(c.x, h, c.z)
            for d, half in WALL_DIRS:
                p = world.cast(o, d, is_wall)
                if p is None:
                    continue
                dist = (p.x - o.x) * d.x + (p.z - o.z) * d.z
                if dist < half:
                    push.x -= d.x * (half - dist)
                    push.z -= d.z * (half - dist)
                    touched = True

        if touched:
            self._shift(push.x, push.y, push.z)
        return touched

    def update(self, dt: float, colliders: Iterable[MeshCollider]) -> bool:
        """One physics step: gravity, then collision, then fallback floor."""
        self.apply_gravity(dt)
        self.colliding = self.resolve_collision(colliders)
        self.land_on_world_floor()
        if self.on_ground:
            self.vel_y = 0.0
        return self.colliding
