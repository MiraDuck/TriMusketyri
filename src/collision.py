"""Collision model: ray casts against a mesh placed in the world."""
from pyray import *


def is_floor(n):   return n.y > 0.5            # faces up
def is_ceiling(n): return n.y < -0.5           # faces down
def is_wall(n):    return abs(n.y) < 0.5       # steep


class CollisionWorld:
    """Needs an open window (load_model requires a GL context)."""

    def __init__(self, path, pos):
        self.pos = pos
        self.model = load_model(str(path))

        bb = get_model_bounding_box(self.model)
        self.bounds = BoundingBox(
            Vector3(bb.min.x + pos.x, bb.min.y + pos.y, bb.min.z + pos.z),
            Vector3(bb.max.x + pos.x, bb.max.y + pos.y, bb.max.z + pos.z),
        )

    def unload(self):
        unload_model(self.model)

    def cast(self, origin, direction, accept, max_skips=4):
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
            ray = Ray(Vector3(ox, oy, oz), direction)
            best = None
            for i in range(self.model.meshCount):
                hit = get_ray_collision_mesh(ray, self.model.meshes[i], matrix_identity())
                if hit.hit and (best is None or hit.distance < best.distance):
                    best = hit
            if best is None:
                return None
            if accept(best.normal):
                p = best.point
                return Vector3(p.x + self.pos.x, p.y + self.pos.y, p.z + self.pos.z)
            # wrong kind of triangle: continue from just past it
            ox = best.point.x + direction.x * 0.01
            oy = best.point.y + direction.y * 0.01
            oz = best.point.z + direction.z * 0.01
        return None
