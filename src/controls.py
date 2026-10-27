"""Keyboard / mouse input."""
from __future__ import annotations

import pyray as pr

from .config import MOUSE_SENSITIVITY, PLAYER_SPEED, ZOOM_SPEED
from .debug import DebugOptions

UP_VECTOR: pr.Vector3 = pr.Vector3(0.0, 1.0, 0.0)

MODE_KEYS: dict[int, int] = {
    pr.KeyboardKey.KEY_ONE: pr.CameraMode.CAMERA_FREE,
    pr.KeyboardKey.KEY_TWO: pr.CameraMode.CAMERA_FIRST_PERSON,
    # pr.KeyboardKey.KEY_THREE: pr.CameraMode.CAMERA_THIRD_PERSON,
    # pr.KeyboardKey.KEY_FOUR: pr.CameraMode.CAMERA_ORBITAL,
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
    if pr.is_key_pressed(pr.KeyboardKey.KEY_F11):
        pr.toggle_fullscreen()

    # if pr.is_key_pressed(pr.KeyboardKey.KEY_P):
    #     if camera.projection == pr.CameraProjection.CAMERA_PERSPECTIVE:
    #         camera_mode = pr.CameraMode.CAMERA_THIRD_PERSON
    #         camera.target = pr.Vector3(0.0, 2.0, 0.0)
    #         camera.position = pr.Vector3(50.0, 2.0 + 100.0 * math.sin(math.radians(45)), 50.0)
    #         camera.up = UP_VECTOR
    #         camera.projection = pr.CameraProjection.CAMERA_ORTHOGRAPHIC
    #         camera.fovy = 20.0
    #     elif camera.projection == pr.CameraProjection.CAMERA_ORTHOGRAPHIC:
    #         camera_mode = pr.CameraMode.CAMERA_THIRD_PERSON
    #         camera.position = pr.Vector3(0.0, 2.0, 10.0)
    #         camera.target = pr.Vector3(0.0, 2.0, 0.0)
    #         camera.up = UP_VECTOR
    #         camera.projection = pr.CameraProjection.CAMERA_PERSPECTIVE
    #         camera.fovy = 60.0
    return camera_mode


def move_camera(camera: pr.Camera3D, camera_mode: int, dt: float) -> None:
    """Apply movement + mouse look. Space/Shift move vertically except in first person (gravity)."""
    step = PLAYER_SPEED * dt    # distance moved this frame
    forward, sideway = move_axes()
    if camera_mode == pr.CameraMode.CAMERA_FIRST_PERSON:
        vertical = 0.0
    else:
        vertical = (pr.is_key_down(pr.KeyboardKey.KEY_SPACE) - pr.is_key_down(pr.KeyboardKey.KEY_LEFT_SHIFT)) * step

    mouse = pr.get_mouse_delta()
    pr.update_camera_pro(
        camera,
        (forward * step, sideway * step, vertical),
        (mouse.x * MOUSE_SENSITIVITY, mouse.y * MOUSE_SENSITIVITY, 0.0),
        pr.get_mouse_wheel_move() * ZOOM_SPEED,
    )
