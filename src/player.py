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

# Down-rays for the floor: the centre + 4 points at 80 % towards the box corners (x, z offsets)
FLOOR_SAMPLES: list[tuple[float, float]] = [(0.0, 0.0)] + [
    (sx * PLAYER_HALF.x * 0.8, sz * PLAYER_HALF.z * 0.8) for sx in (1, -1) for sz in (1, -1)
]

AXES: list[pr.Vector3] = [pr.Vector3(1, 0, 0), pr.Vector3(-1, 0, 0), pr.Vector3(0, 0, 1), pr.Vector3(0, 0, -1)]
# Wall rays go out through each side of the box at its middle and at these fractions of the half size towards both
# edges. Spacing (0.13 with PLAYER_HALF 0.4) must stay below the thinnest wall edge, e.g. the 0.2 deep door frames,
# or the box can slide onto it between two rays.
EDGE_OFFSETS: list[float] = [0.95 * k / 3 for k in (1, 2, 3)]
# Overlaps smaller than this are just touching. Without it, a wall you were just pushed out of still reads as a
# ~0 overlap, wins "shallowest first" again, and a real overlap elsewhere is never fixed.
WALL_SKIN: float = 0.001


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
        push_y = 0.0
        touched = False

        # --- Floor: rays down from STEP_UP above the feet, keep the HIGHEST floor ---
        # Starting above the feet finds a floor we have sunk into (gravity this frame) or a ledge up to STEP_UP high,
        # which we then step onto. Several rays so standing half over an edge still counts.
        floor_y = None
        for ox, oz in FLOOR_SAMPLES:
            o = pr.Vector3(c.x + ox, feet + STEP_UP, c.z + oz)
            p = world.cast(o, DOWN, is_floor)
            if p is not None and (floor_y is None or p.y > floor_y):
                floor_y = p.y
        if floor_y is not None:
            if floor_y > feet:
                push_y += floor_y - feet
                touched = True
            if floor_y >= feet - 0.05:   # a little tolerance so walking down a slope stays "on ground"
                self.on_ground = True

        # --- Ceiling ---
        p = world.cast(c, UP, is_ceiling)
        if p is not None and p.y < head:
            push_y -= head - p.y
            touched = True

        if touched:
            self._shift(0.0, push_y, 0.0)

        # --- Walls: push out along the SHALLOWEST overlap only, then measure again ---
        # When a corner of the box clips a wall edge (e.g. beside a door), the overlap is small from the side but
        # large from the front; pushing along both would shove you through the wall. More passes handle a real
        # corner where two walls touch you at once.
        for _ in range(3):
            depth = self._wall_depths(world)
            if not depth:
                break
            (dx, dz), pen = min(depth.items(), key=lambda kv: kv[1])
            self._shift(-dx * pen, 0.0, -dz * pen)
            touched = True
        return touched

    def _wall_depths(self, world: MeshCollider) -> dict[tuple[float, float], float]:
        """How far a wall reaches into the box, per direction (x, z) it is in. Rays at two heights, ignoring
        floor-like triangles, out through each side of the box at several points across it (EDGE_OFFSETS), so a wall
        touching only a corner of the box is found too. Per direction only the deepest hit counts: several rays (and
        both heights) usually see the same wall."""
        c, _ = self.box()
        feet = c.y - PLAYER_HALF.y
        head = c.y + PLAYER_HALF.y
        depth: dict[tuple[float, float], float] = {}

        def hit(o: pr.Vector3, d: pr.Vector3) -> float:
            """Distance from o to the nearest wall along d (inf if none)."""
            p = world.cast(o, d, is_wall)
            return float("inf") if p is None else (p.x - o.x) * d.x + (p.z - o.z) * d.z

        # knee height (just above anything we could step onto) and head height
        for h in (feet + STEP_UP + 0.1, head - 0.2):
            centre = pr.Vector3(c.x, h, c.z)
            reach = {(d.x, d.z): hit(centre, d) for d in AXES}   # straight out from the centre
            for d in AXES:
                half, side_half = (PLAYER_HALF.x, PLAYER_HALF.z) if d.x else (PLAYER_HALF.z, PLAYER_HALF.x)
                dists = [reach[(d.x, d.z)]]
                for s in (1, -1):
                    side = (d.z * s, d.x * s)   # direction from the centre towards this edge
                    for f in EDGE_OFFSETS:
                        off = f * side_half
                        # the ray would start inside a wall if the centre ray towards this edge hits one first;
                        # it would then hit that wall from inside and push you the wrong way, so stop here
                        if reach[side] <= off:
                            break
                        dists.append(hit(pr.Vector3(c.x + side[0] * off, h, c.z + side[1] * off), d))
                dist = min(dists)
                if dist < half - WALL_SKIN:
                    key = (d.x, d.z)
                    depth[key] = max(depth.get(key, 0.0), half - dist)
        return depth

    def update(self, dt: float, colliders: Iterable[MeshCollider]) -> bool:
        """One physics step: gravity, then collision, then fallback floor."""
        self.apply_gravity(dt)
        self.colliding = self.resolve_collision(colliders)
        self.land_on_world_floor()
        if self.on_ground:
            self.vel_y = 0.0
        return self.colliding
