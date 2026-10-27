"""Debug switches. Toggled from controls.handle_hotkeys, read by render."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DebugOptions:
    hitboxes: bool = False          # F1: bounding box of every entity (+ the player box outside first person)
    wireframes: bool = False        # F2: wireframe over every model
    collision_meshes: bool = False  # C:  draw each solid entity's collision mesh instead of its visible model
