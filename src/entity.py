"""Entity: one thing in the world = a visible model + its own hitbox.

    room = Entity("room", "Models/Room.obj", Vector3(0, 1, 0), collision_path="Models/Room_Navmesh.obj")
    lever = Entity("lever", "Models/lever.obj", Vector3(0, 2, 0))     # no collision mesh: not solid

Hitbox:
  - `bounds` is always there (world-space box, used for debug drawing and for "am I looking at it").
  - `collider` is optional. If given, the player is stopped by it (solid). Without it the entity is
    only a visual / interactable and the player walks through.
"""
from __future__ import annotations

import math
from pathlib import Path

import pyray as pr

from .collision import MeshCollider, world_bounds

MTL_HANG_RISK: int = 10   # raylib's OBJ loader can hang forever on an .mtl with this many materials or more


def warn_big_mtl(model_path: str | Path) -> None:
    """Print a warning before loading an .obj whose .mtl could hang raylib, so a frozen start names the file."""
    path = Path(model_path)
    if path.suffix.lower() != ".obj":
        return
    for line in path.read_text().splitlines():
        if line.startswith("mtllib"):
            mtl = path.parent / line.split(maxsplit=1)[1].strip()
            if mtl.exists():
                count = sum(1 for m in mtl.read_text().splitlines() if m.startswith("newmtl"))
                if count >= MTL_HANG_RISK:
                    print(f"WARNING: {mtl.name} ({path.name}) has {count} materials; raylib may hang on "
                          f"{MTL_HANG_RISK}+. Remove the unused ones in Blender.", flush=True)
            return


def rotation_about(pivot: pr.Vector3, axis: pr.Vector3, degrees: float) -> pr.Matrix:
    """A model.transform turning a model `degrees` about `axis` through `pivot` (model space) instead of its origin:
    move the pivot to the origin, rotate, move it back. raylib's matrix_multiply(a, b) applies a first, then b;
    draw_model applies model.transform before the entity's `pos`."""
    p = pivot
    return pr.matrix_multiply(
        pr.matrix_multiply(pr.matrix_translate(-p.x, -p.y, -p.z), pr.matrix_rotate(axis, math.radians(degrees))),
        pr.matrix_translate(p.x, p.y, p.z),
    )


class Entity:
    """Needs an open window (load_model needs a GL context)."""

    def __init__(
        self,
        name: str,
        model_path: str | Path,
        pos: pr.Vector3,
        collision_path: str | Path | None = None,
    ) -> None:
        self.name: str = name
        self.pos: pr.Vector3 = pos
        self.tint: pr.Color = pr.WHITE   # colour the model is drawn with (multiplies its texture)
        warn_big_mtl(model_path)
        self.model: pr.Model = pr.load_model(str(model_path))
        self.collider: MeshCollider | None = (
            MeshCollider(collision_path, pos) if collision_path else None
        )
        # the collider's box if it has one, otherwise the visible model's box
        self.bounds: pr.BoundingBox = (
            self.collider.bounds if self.collider else world_bounds(self.model, pos)
        )

    @property
    def solid(self) -> bool:
        return self.collider is not None

    def is_targeted(self, camera: pr.Camera3D, reach: float = 2.5) -> bool:
        """True if the camera is looking at the hitbox from within `reach`."""
        direction = pr.vector3_normalize(pr.vector3_subtract(camera.target, camera.position))
        hit = pr.get_ray_collision_box(pr.Ray(camera.position, direction), self.bounds)
        return bool(hit.hit and hit.distance <= reach)

    def unload(self) -> None:
        pr.unload_model(self.model)
        if self.collider is not None:
            self.collider.unload()
