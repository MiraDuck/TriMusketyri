"""Collision: ray casts against a mesh placed in the world."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable

import pyray as pr

NormalTest = Callable[[pr.Vector3], bool]


def is_floor(n: pr.Vector3) -> bool:   return n.y > 0.5            # faces up
def is_ceiling(n: pr.Vector3) -> bool: return n.y < -0.5           # faces down
def is_wall(n: pr.Vector3) -> bool:    return abs(n.y) < 0.5       # steep


def world_bounds(model: pr.Model, pos: pr.Vector3) -> pr.BoundingBox:
    """A model's bounding box moved to where the model sits in the world."""
    bb = pr.get_model_bounding_box(model)
    return pr.BoundingBox(
        pr.Vector3(bb.min.x + pos.x, bb.min.y + pos.y, bb.min.z + pos.z),
        pr.Vector3(bb.max.x + pos.x, bb.max.y + pos.y, bb.max.z + pos.z),
    )


def load_geometry(path: str | Path) -> pr.Model:
    """Load an .obj without its materials (no mtllib / usemtl). Collision only needs the triangles, it skips loading
    textures, and raylib can hang forever on an .mtl with 10+ materials (DEVNOTES, Assets)."""
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    kept = [line for line in lines if not line.startswith(("mtllib", "usemtl"))]
    # raylib only loads models from a file path, so write the stripped copy to a temporary file
    fd, tmp = tempfile.mkstemp(suffix=".obj")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(kept))
    try:
        return pr.load_model(tmp)
    finally:
        os.remove(tmp)


class MeshCollider:
    """A collision mesh placed in the world. Needs an open window (load_model needs a GL context)."""

    def __init__(self, path: str | Path, pos: pr.Vector3) -> None:
        self.pos: pr.Vector3 = pos
        self.model: pr.Model = load_geometry(path)
        self.bounds: pr.BoundingBox = world_bounds(self.model, pos)

    def unload(self) -> None:
        pr.unload_model(self.model)

    def cast(
        self,
        origin: pr.Vector3,
        direction: pr.Vector3,
        accept: NormalTest,
        max_skips: int = 4,
    ) -> pr.Vector3 | None:
        """
        Closest hit on the model whose triangle normal passes accept(normal).
        Returns the hit point in world space, or None.

        raylib only reports the single closest triangle per mesh. If that triangle
        is the wrong kind (e.g. the underside of a floor), we restart the ray just
        past it and try again, so the right triangle can still be found.
        """
        ox = origin.x - self.pos.x   # world -> model space
        oy = origin.y - self.pos.y
        oz = origin.z - self.pos.z

        for _ in range(max_skips + 1):
            ray = pr.Ray(pr.Vector3(ox, oy, oz), direction)
            best = None
            for i in range(self.model.meshCount):
                hit = pr.get_ray_collision_mesh(ray, self.model.meshes[i], pr.matrix_identity())
                if hit.hit and (best is None or hit.distance < best.distance):
                    best = hit
            if best is None:
                return None
            if accept(best.normal):
                p = best.point
                return pr.Vector3(p.x + self.pos.x, p.y + self.pos.y, p.z + self.pos.z)
            # wrong kind of triangle: continue from just past it
            ox = best.point.x + direction.x * 0.01
            oy = best.point.y + direction.y * 0.01
            oz = best.point.z + direction.z * 0.01
        return None
