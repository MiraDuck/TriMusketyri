"""Entity: one thing in the world = a visible model + its own hitbox.

    level = Entity("level", "Models/test.obj", Vector3(0, 1, 0), collision_path="Models/navmesh.obj")
    lever = Entity("lever", "Models/lever.obj", Vector3(0, 2, 0))     # no collision mesh: not solid

Hitbox:
  - `bounds` is always there (world-space box, used for debug drawing and for "am I looking at it").
  - `collider` is optional. If given, the player is stopped by it (solid). Without it the entity is
    only a visual / interactable and the player walks through.
"""
from __future__ import annotations

from pathlib import Path

import pyray as pr

from .collision import MeshCollider, world_bounds


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
