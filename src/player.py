"""Player body: cuboid around the camera, gravity and collision response."""
from pyray import *

from .collision import is_ceiling, is_floor, is_wall
from .config import (
    EYE_TO_CENTER, GRAVITY, MAX_FALL_SPEED, PLAYER_HALF, STEP_UP, WORLD_FLOOR_Y,
)

DOWN = Vector3(0, -1, 0)
UP = Vector3(0, 1, 0)

# Down-rays for the floor: center + 4 points inside the box corners
_f = 0.8
FLOOR_SAMPLES = [
    (0.0, 0.0),
    (PLAYER_HALF.x * _f, PLAYER_HALF.z * _f),
    (-PLAYER_HALF.x * _f, PLAYER_HALF.z * _f),
    (PLAYER_HALF.x * _f, -PLAYER_HALF.z * _f),
    (-PLAYER_HALF.x * _f, -PLAYER_HALF.z * _f),
]

WALL_DIRS = [
    (Vector3(1, 0, 0),  PLAYER_HALF.x),
    (Vector3(-1, 0, 0), PLAYER_HALF.x),
    (Vector3(0, 0, 1),  PLAYER_HALF.z),
    (Vector3(0, 0, -1), PLAYER_HALF.z),
]


class Player:
    """The real camera is the player's position; this adds a body around it."""

    def __init__(self, camera):
        self.camera = camera
        self.vel_y = 0.0
        self.on_ground = False
        self.colliding = False

    # ---- helpers ----
    def box(self):
        """Returns (center, BoundingBox) of the player cuboid."""
        p = self.camera.position
        c = Vector3(p.x, p.y - EYE_TO_CENTER, p.z)
        box = BoundingBox(
            Vector3(c.x - PLAYER_HALF.x, c.y - PLAYER_HALF.y, c.z - PLAYER_HALF.z),
            Vector3(c.x + PLAYER_HALF.x, c.y + PLAYER_HALF.y, c.z + PLAYER_HALF.z),
        )
        return c, box

    def _shift(self, dx, dy, dz):
        """Move position AND target together so the view direction doesn't change."""
        cam = self.camera
        cam.position = Vector3(cam.position.x + dx, cam.position.y + dy, cam.position.z + dz)
        cam.target = Vector3(cam.target.x + dx, cam.target.y + dy, cam.target.z + dz)

    # ---- physics ----
    def apply_gravity(self, dt):
        """Pull the player down; resolve_collision() then pushes them back onto the floor."""
        self.vel_y = max(self.vel_y - GRAVITY * dt, -MAX_FALL_SPEED)
        self._shift(0, self.vel_y * dt, 0)

    def land_on_world_floor(self):
        """Stop the player at WORLD_FLOOR_Y if the collision model didn't catch them."""
        feet = self.camera.position.y - EYE_TO_CENTER - PLAYER_HALF.y
        if feet < WORLD_FLOOR_Y:
            self._shift(0, WORLD_FLOOR_Y - feet, 0)
            self.on_ground = True

    def resolve_collision(self, world):
        """Push the player out of the collision model. Returns True if touching it."""
        self.on_ground = False

        c, box = self.box()
        if not check_collision_boxes(box, world.bounds):   # broadphase
            return False

        feet = c.y - PLAYER_HALF.y
        head = c.y + PLAYER_HALF.y
        push = Vector3(0, 0, 0)
        touched = False

        # --- Floor: several rays from just above the feet, keep the HIGHEST floor ---
        floor_y = None
        for ox, oz in FLOOR_SAMPLES:
            o = Vector3(c.x + ox, feet + STEP_UP, c.z + oz)
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
            o = Vector3(c.x, h, c.z)
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

    def update(self, dt, world):
        """One physics step: gravity, then collision, then fallback floor."""
        self.apply_gravity(dt)
        self.colliding = self.resolve_collision(world)
        self.land_on_world_floor()
        if self.on_ground:
            self.vel_y = 0.0
        return self.colliding
