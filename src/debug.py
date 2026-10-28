"""Debug switches. Toggled from controls.handle_hotkeys, read by render."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

import pyray as pr

from .config import DEBUG_REACH

if TYPE_CHECKING:
    from .entity import Entity


@dataclass
class DebugOptions:
    hitboxes: bool = False          # F1: bounding box of every entity, the player box and the lights
    wireframes: bool = False        # F2: wireframe over every model
    collision_meshes: bool = False  # C:  draw each solid entity's collision mesh instead of its visible model
    unlit: bool = False             # L:  turn the lighting shader off (everything full bright)
    no_vignette: bool = False       # V:  turn the vignette off


def looked_at(camera: pr.Camera3D, entities: Iterable[Entity], reach: float = DEBUG_REACH) -> Entity | None:
    """The entity whose hitbox the view ray hits first, for the debug panel. The cars (solid) only count if nothing
    else is hit: their boxes overlap the next car's and reach past the parts on their walls."""
    hits = [(d, e) for e in entities if (d := e.target_distance(camera, reach)) is not None]
    parts = [hit for hit in hits if not hit[1].solid]
    return min(parts or hits, key=lambda hit: hit[0])[1] if hits else None
