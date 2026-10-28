"""Keyboard / mouse input."""
from __future__ import annotations

from typing import Iterable

import pyray as pr

from .config import MOUSE_SENSITIVITY, PLAYER_SPEED, ZOOM_SPEED
from .debug import DebugOptions
from .interactable import Interactable

UP_VECTOR: pr.Vector3 = pr.Vector3(0.0, 1.0, 0.0)

MODE_KEYS: dict[int, int] = {
    pr.KeyboardKey.KEY_ONE: pr.CameraMode.CAMERA_FREE,
    pr.KeyboardKey.KEY_TWO: pr.CameraMode.CAMERA_FIRST_PERSON,
}


def _any_down(*keys: int) -> bool:
    return any(pr.is_key_down(k) for k in keys)


def move_axes() -> tuple[int, int]:
    """Returns (forward, sideway), each -1, 0 or 1."""
    K = pr.KeyboardKey
    forward = _any_down(K.KEY_W, K.KEY_UP) - _any_down(K.KEY_S, K.KEY_DOWN)
    sideway = _any_down(K.KEY_D, K.KEY_RIGHT) - _any_down(K.KEY_A, K.KEY_LEFT)
    return forward, sideway


def handle_hotkeys(camera: pr.Camera3D, camera_mode: int, debug: DebugOptions) -> int:
    """Mode keys, debug toggles, fullscreen. Returns camera_mode; `debug` is changed in place."""
    for key, mode in MODE_KEYS.items():
        if pr.is_key_pressed(key):
            camera_mode = mode
            camera.up = UP_VECTOR
    if pr.is_key_pressed(pr.KeyboardKey.KEY_F1):
        debug.hitboxes = not debug.hitboxes
    if pr.is_key_pressed(pr.KeyboardKey.KEY_F2):
        debug.wireframes = not debug.wireframes
    if pr.is_key_pressed(pr.KeyboardKey.KEY_C):
        debug.collision_meshes = not debug.collision_meshes
    if pr.is_key_pressed(pr.KeyboardKey.KEY_L):
        debug.unlit = not debug.unlit
    if pr.is_key_pressed(pr.KeyboardKey.KEY_V):
        debug.no_vignette = not debug.no_vignette
    if pr.is_key_pressed(pr.KeyboardKey.KEY_F11):
        pr.toggle_fullscreen()
    return camera_mode


def handle_interaction(
    camera: pr.Camera3D,
    interactables: Iterable[Interactable],
    held: Interactable | None,
) -> Interactable | None:
    """Left click uses the interactable you are looking at (the nearest, if several).
    A grabbable one stays held while the button is down and gets the mouse movement.
    Returns what is held now (None = nothing, mouse look is on)."""
    left = pr.MouseButton.MOUSE_BUTTON_LEFT
    if held is not None:
        # keep holding while the button is down and you still look at it; walking / looking away lets go
        if pr.is_mouse_button_down(left) and held.is_targeted(camera):
            held.drag(pr.get_mouse_delta())
            return held
        held.release()
        return None

    if not pr.is_mouse_button_pressed(left):
        return None
    # the first hitbox the view ray hits (parts modelled in place all share their car's pos, so not by pos)
    hits = [(d, i) for i in interactables if (d := i.target_distance(camera)) is not None]
    if not hits:
        return None
    target = min(hits, key=lambda hit: hit[0])[1]
    if target.grabbable:
        target.grab(camera)
        return target
    target.interact()
    return None


def move_camera(camera: pr.Camera3D, camera_mode: int, dt: float, look: bool = True) -> None:
    """Apply movement + mouse look. Space/Shift move vertically and the mouse wheel zooms, free camera only.
    look=False ignores the mouse (it is turning something you hold)."""
    step = PLAYER_SPEED * dt    # distance moved this frame
    forward, sideway = move_axes()
    free = camera_mode == pr.CameraMode.CAMERA_FREE
    K = pr.KeyboardKey
    vertical = (_any_down(K.KEY_SPACE) - _any_down(K.KEY_LEFT_SHIFT)) * step if free else 0.0
    # raylib's "zoom" moves the camera along the view direction (towards its target), which in first person would
    # move the player 2 units per wheel notch, straight through walls
    zoom = pr.get_mouse_wheel_move() * ZOOM_SPEED if free else 0.0

    mouse = pr.get_mouse_delta() if look else pr.Vector2(0.0, 0.0)
    pr.update_camera_pro(
        camera,
        (forward * step, sideway * step, vertical),
        (mouse.x * MOUSE_SENSITIVITY, mouse.y * MOUSE_SENSITIVITY, 0.0),
        zoom,
    )
