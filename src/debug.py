"""Debug switches. Toggled from controls.handle_hotkeys, read by render.

F3 opens the debug menu (only with config.DEBUG_MENU): its box on the left of the HUD, and the debug keys work
only while it is open. Closing it turns every debug view off again and goes back to first person.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

import pyray as pr

from .config import DEBUG_REACH

if TYPE_CHECKING:
    from .entity import Entity


@dataclass
class DebugOptions:
    menu: bool = False              # F3: the debug menu is open (the keys below only work then)
    hitboxes: bool = False          # F1: bounding box of every entity, the player box and the lights
    wireframes: bool = False        # F2: wireframe over every model
    collision_meshes: bool = False  # C:  draw each solid entity's collision mesh instead of its visible model
    unlit: bool = False             # L:  turn the lighting shader off (everything full bright)
    no_vignette: bool = False       # V:  turn the vignette off

    def close(self) -> None:
        """Close the menu: every debug view off."""
        self.menu = self.hitboxes = self.wireframes = self.collision_meshes = self.unlit = self.no_vignette = False


def looked_at(camera: pr.Camera3D, entities: Iterable[Entity], reach: float = DEBUG_REACH) -> list[Entity]:
    """Every entity whose hitbox the view ray hits, nearest first, for the debug panel (boxes overlap: posters
    cover the parts in front of them). The cars (solid) only count if nothing else is hit: their boxes overlap the
    next car's and reach past the parts on their walls."""
    hits = [(d, e) for e in entities if (d := e.target_distance(camera, reach)) is not None]
    parts = [hit for hit in hits if not hit[1].solid]
    return [e for _, e in sorted(parts or hits, key=lambda hit: hit[0])]
