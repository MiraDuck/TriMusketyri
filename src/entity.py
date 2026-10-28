"""Entity: one thing in the world = a visible model + its own hitbox.

    room = Entity("room", "Models/Room.obj", Vector3(0, 1, 0), collision_path="Models/Room_Navmesh.obj")
    lever = Entity("lever", "Models/lever.obj", Vector3(0, 2, 0))     # no collision mesh: not solid

Moving parts (dials, valves, switches, the engine) are rigged .glb files, modelled in place in their car (same
origin as the car) with one bone: the part turns about the bone's Y axis through its head (`bone_pivot_axis`).

Hitbox:
  - `bounds` is always there (world-space box, used for debug drawing and for "am I looking at it").
  - `collider` is optional. If given, the player is stopped by it (solid). Without it the entity is
    only a visual / interactable and the player walks through.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path
from typing import Callable

import pyray as pr

from .collision import MeshCollider, world_bounds

MTL_HANG_RISK: int = 10   # raylib's OBJ loader can hang forever on an .mtl with this many materials or more


def warn_big_mtl(model_path: str | Path) -> None:
    """Print a warning before loading an .obj whose .mtl could hang raylib, so a frozen start names the file."""
    path = Path(model_path)
    if path.suffix.lower() != ".obj":
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("mtllib"):
            mtl = path.parent / line.split(maxsplit=1)[1].strip()
            if mtl.exists():
                count = sum(1 for m in mtl.read_text(encoding="utf-8", errors="replace").splitlines()
                            if m.startswith("newmtl"))
                if count >= MTL_HANG_RISK:
                    print(f"WARNING: {mtl.name} ({path.name}) has {count} materials; raylib may hang on "
                          f"{MTL_HANG_RISK}+. Remove the unused ones in Blender.", flush=True)
            return


def warn_glb_rig(model_path: str | Path) -> None:
    """Print a warning before loading a .glb whose rig raylib can't use as one moving part, naming the file:
    raylib only reads the first armature (a second one's mesh gets moved by the first one's bone), and a part with
    no armature can't turn (Dial / Lever / Spinner then stop with "the model has no bone")."""
    path = Path(model_path)
    if path.suffix.lower() != ".glb":
        return
    with path.open("rb") as f:
        f.seek(12)   # the .glb header, then the JSON chunk: its length, its type, the JSON
        length = struct.unpack("<I", f.read(4))[0]
        f.seek(20)
        skins = len(json.loads(f.read(length)).get("skins", []))
    if skins > 1:
        print(f"WARNING: {path.name} has {skins} armatures; only the first one is used. Export just the part and "
              f"its armature (Limit to: Selected Objects).", flush=True)
    elif skins == 0:
        print(f"WARNING: {path.name} has no armature; export the part together with its armature to move it.",
              flush=True)


def rotation_about(pivot: pr.Vector3, axis: pr.Vector3, degrees: float) -> pr.Matrix:
    """A model.transform turning a model `degrees` about `axis` through `pivot` (model space) instead of its origin:
    move the pivot to the origin, rotate, move it back. raylib's matrix_multiply(a, b) applies a first, then b;
    draw_model applies model.transform before the entity's `pos`."""
    p = pivot
    return pr.matrix_multiply(
        pr.matrix_multiply(pr.matrix_translate(-p.x, -p.y, -p.z), pr.matrix_rotate(axis, math.radians(degrees))),
        pr.matrix_translate(p.x, p.y, p.z),
    )


def load_unicode_textures(model: pr.Model, model_path: str | Path) -> None:
    """Load the .obj's textures whose file name isn't plain ASCII (Textures/kyslík.png) ourselves: raylib can't open
    those on Windows ("Failed to open file") and leaves the material untextured. Python reads the file, raylib
    decodes it from memory. raylib keeps the .mtl's materials in order, so the n-th newmtl is model.materials[n]."""
    path = Path(model_path)
    if path.suffix.lower() != ".obj":
        return
    mtl = next((path.parent / line.split(maxsplit=1)[1].strip()
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.startswith("mtllib")), None)
    if mtl is None or not mtl.exists():
        return
    index = -1
    for line in mtl.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("newmtl"):
            index += 1
        elif line.startswith("map_Kd") and 0 <= index < model.materialCount:
            texture_path = mtl.parent / line.split(maxsplit=1)[1].strip()
            if texture_path.name.isascii() or not texture_path.exists():
                continue
            data = texture_path.read_bytes()
            image = pr.load_image_from_memory(texture_path.suffix, data, len(data))
            # unload_model frees it with the material
            model.materials[index].maps[pr.MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = (
                pr.load_texture_from_image(image))
            pr.unload_image(image)


def keep_rigged_meshes(model: pr.Model) -> None:
    """Drop the meshes no bone moves, so a rigged .glb is only its moving part (Engine_Spin.glb also holds an old
    copy of the engine room). Unloads them and shifts the rest down; unload_model then frees only what is left."""
    keep = [i for i in range(model.meshCount) if model.meshes[i].boneIndices != pr.ffi.NULL]
    if not keep or len(keep) == model.meshCount:
        return
    for i in range(model.meshCount):
        if i not in keep:
            pr.unload_mesh(model.meshes[i])
    for k, i in enumerate(keep):   # k <= i, so nothing is overwritten before it is moved
        model.meshes[k] = model.meshes[i]
        model.meshMaterial[k] = model.meshMaterial[i]
    model.meshCount = len(keep)


def _bone(model: pr.Model) -> pr.Transform:
    if model.skeleton.boneCount < 1:
        raise ValueError("the model has no bone to move it by (export it rigged, as .glb)")
    return model.skeleton.bindPose[0]   # where the bone sits in Blender


def bone_pivot_axis(model: pr.Model) -> tuple[pr.Vector3, pr.Vector3]:
    """Head and Y axis (model space) of a rigged model's first bone: what its moving part turns about."""
    bone = _bone(model)
    pivot = pr.Vector3(bone.translation.x, bone.translation.y, bone.translation.z)
    return pivot, pr.vector3_rotate_by_quaternion(pr.Vector3(0.0, 1.0, 0.0), bone.rotation)


def bone_x(model: pr.Model) -> pr.Vector3:
    """X axis (model space) of a rigged model's first bone: the `Move` animations slide along -X."""
    return pr.vector3_rotate_by_quaternion(pr.Vector3(1.0, 0.0, 0.0), _bone(model).rotation)


def vec(v: pr.Vector3) -> str:
    """A Vector3 for the debug panel."""
    return f"({v.x:.2f}, {v.y:.2f}, {v.z:.2f})"


class Entity:
    """Needs an open window (load_model needs a GL context)."""

    # moving parts set these: what they turn about (model space), shown in the debug panel
    pivot: pr.Vector3 | None = None
    axis: pr.Vector3 | None = None
    # more debug panel lines from whatever this part belongs to (the engine adds its state to its parts)
    debug_extra: Callable[[], list[str]] | None = None

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
        self.model_path: Path = Path(model_path)
        self.collision_path: Path | None = Path(collision_path) if collision_path else None
        warn_big_mtl(model_path)
        warn_glb_rig(model_path)
        self.model: pr.Model = pr.load_model(str(model_path))
        load_unicode_textures(self.model, model_path)
        if self.model.skeleton.boneCount:
            keep_rigged_meshes(self.model)
        self.collider: MeshCollider | None = (
            MeshCollider(collision_path, pos) if collision_path else None
        )
        # the collider's box if it has one, otherwise the visible model's box
        self.bounds: pr.BoundingBox = (
            self.collider.bounds if self.collider else world_bounds(self.model, pos)
        )
        self._model_box: pr.BoundingBox = pr.get_model_bounding_box(self.model)   # as modelled, model space

    def set_transform(self, transform: pr.Matrix) -> None:
        """Move / turn the model (moving parts) and its hitbox with it, so you click it where you see it.
        The box is the one around the modelled box's 8 corners after the transform (raylib's own
        get_model_bounding_box only transforms min and max, which is wrong once it turns)."""
        self.model.transform = transform
        if self.collider is not None:
            return
        lo, hi = self._model_box.min, self._model_box.max
        corners = [pr.vector3_transform(pr.Vector3(x, y, z), transform)
                   for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        xs, ys, zs = [c.x for c in corners], [c.y for c in corners], [c.z for c in corners]
        p = self.pos
        self.bounds = pr.BoundingBox(
            pr.Vector3(min(xs) + p.x, min(ys) + p.y, min(zs) + p.z),
            pr.Vector3(max(xs) + p.x, max(ys) + p.y, max(zs) + p.z),
        )

    @property
    def center(self) -> pr.Vector3:
        """Middle of the hitbox, in the world (where its sounds come from)."""
        return pr.vector3_lerp(self.bounds.min, self.bounds.max, 0.5)

    @property
    def solid(self) -> bool:
        return self.collider is not None

    def target_distance(self, camera: pr.Camera3D, reach: float = 2.5) -> float | None:
        """How far the camera's view ray hits the hitbox, or None if it misses or is further than `reach`."""
        direction = pr.vector3_normalize(pr.vector3_subtract(camera.target, camera.position))
        hit = pr.get_ray_collision_box(pr.Ray(camera.position, direction), self.bounds)
        return hit.distance if hit.hit and hit.distance <= reach else None

    def is_targeted(self, camera: pr.Camera3D, reach: float = 2.5) -> bool:
        """True if the camera is looking at the hitbox from within `reach`."""
        return self.target_distance(camera, reach) is not None

    def debug_lines(self) -> list[str]:
        """What the debug panel shows while you look at this with hitboxes on (F1). Subclasses add their state."""
        b = self.bounds
        lines = [
            f"{self.name} ({type(self).__name__})",
            f"model: {self.model_path.name}" + (f", solid: {self.collision_path.name}" if self.collision_path else ""),
            f"pos: {vec(self.pos)}",
            f"box: {vec(b.min)} .. {vec(b.max)}",
        ]
        if self.pivot is not None and self.axis is not None:
            lines.append(f"pivot: {vec(pr.vector3_add(self.pos, self.pivot))}  axis: {vec(self.axis)}")
        if self.debug_extra is not None:
            lines += self.debug_extra()
        return lines

    def unload(self) -> None:
        pr.unload_model(self.model)
        if self.collider is not None:
            self.collider.unload()
