"""Keyboard / mouse input."""
import math

from pyray import *

from .config import MOUSE_SENSITIVITY, PLAYER_SPEED, ZOOM_SPEED

UP_VECTOR = Vector3(0.0, 1.0, 0.0)

MODE_KEYS = {
    KeyboardKey.KEY_ONE: CameraMode.CAMERA_FREE,
    KeyboardKey.KEY_TWO: CameraMode.CAMERA_FIRST_PERSON,
    # KeyboardKey.KEY_THREE: CameraMode.CAMERA_THIRD_PERSON,
    # KeyboardKey.KEY_FOUR: CameraMode.CAMERA_ORBITAL,
}


def _any_down(*keys):
    return any(is_key_down(k) for k in keys)


def move_axes():
    """Returns (forward, sideway), each -1, 0 or 1."""
    K = KeyboardKey
    forward = _any_down(K.KEY_W, K.KEY_UP) - _any_down(K.KEY_S, K.KEY_DOWN)
    sideway = _any_down(K.KEY_D, K.KEY_RIGHT) - _any_down(K.KEY_A, K.KEY_LEFT)
    return forward, sideway


def handle_hotkeys(camera, camera_mode, show_col):
    """Mode keys, collision toggle. Returns (camera_mode, show_col)."""
    for key, mode in MODE_KEYS.items():
        if is_key_pressed(key):
            camera_mode = mode
            camera.up = UP_VECTOR
    if is_key_pressed(KeyboardKey.KEY_C):
        show_col = not show_col
    if is_key_pressed(KeyboardKey.KEY_F11):
        toggle_fullscreen()

    # if is_key_pressed(KeyboardKey.KEY_P):
    #     if camera.projection == CameraProjection.CAMERA_PERSPECTIVE:
    #         camera_mode = CameraMode.CAMERA_THIRD_PERSON
    #         camera.target = Vector3(0.0, 2.0, 0.0)
    #         camera.position = Vector3(50.0, 2.0 + 100.0 * math.sin(math.radians(45)), 50.0)
    #         camera.up = UP_VECTOR
    #         camera.projection = CameraProjection.CAMERA_ORTHOGRAPHIC
    #         camera.fovy = 20.0
    #     elif camera.projection == CameraProjection.CAMERA_ORTHOGRAPHIC:
    #         camera_mode = CameraMode.CAMERA_THIRD_PERSON
    #         camera.position = Vector3(0.0, 2.0, 10.0)
    #         camera.target = Vector3(0.0, 2.0, 0.0)
    #         camera.up = UP_VECTOR
    #         camera.projection = CameraProjection.CAMERA_PERSPECTIVE
    #         camera.fovy = 60.0
    return camera_mode, show_col


def move_camera(camera, camera_mode, dt):
    """Apply movement + mouse look. Space/Shift move vertically except in first person (gravity)."""
    step = PLAYER_SPEED * dt    # distance moved this frame
    forward, sideway = move_axes()
    if camera_mode == CameraMode.CAMERA_FIRST_PERSON:
        vertical = 0.0
    else:
        vertical = (is_key_down(KeyboardKey.KEY_SPACE) - is_key_down(KeyboardKey.KEY_LEFT_SHIFT)) * step

    mouse = get_mouse_delta()
    update_camera_pro(
        camera,
        (forward * step, sideway * step, vertical),
        (mouse.x * MOUSE_SENSITIVITY, mouse.y * MOUSE_SENSITIVITY, 0.0),
        get_mouse_wheel_move() * ZOOM_SPEED,
    )
