"""Drawing: the 3D scene and the HUD."""
from __future__ import annotations

from typing import Iterable

import pyray as pr

from . import config
from .debug import DebugOptions
from .entity import Entity
from .lighting import Light
from .player import Player
from .screens import Screens

MODE_NAMES: dict[int, str] = {
    pr.CameraMode.CAMERA_FREE: "FREE",
    pr.CameraMode.CAMERA_FIRST_PERSON: "FIRST_PERSON",
}


def draw_entity(entity: Entity, camera: pr.Camera3D, debug: DebugOptions, inspected: bool = False) -> None:
    """Visible model (or its collision mesh in debug), then the optional wireframe and hitbox
    (yellow if its details are shown)."""
    collider = entity.collider
    show_mesh = debug.collision_meshes and collider is not None
    model = collider.model if show_mesh and collider else entity.model
    if show_mesh and collider:
        pr.draw_model(collider.model, entity.pos, 1.0, pr.DARKGRAY)
    else:
        pr.draw_model(entity.model, entity.pos, 1.0, entity.tint)
    if debug.wireframes:
        pr.draw_model_wires(model, entity.pos, 1.0, pr.WHITE if show_mesh else pr.BLACK)
    if debug.hitboxes:
        # solid things are always green; non-solid ones go red until you look at them
        ok = entity.solid or entity.is_targeted(camera)
        pr.draw_bounding_box(entity.bounds, pr.YELLOW if inspected else pr.GREEN if ok else pr.RED)


def draw_scene(
    view_camera: pr.Camera3D,
    camera: pr.Camera3D,
    player: Player,
    entities: Iterable[Entity],
    lights: Iterable[Light],
    debug: DebugOptions,
    inspected: list[Entity] | None = None,
    screens: Screens | None = None,
) -> None:
    """view_camera (with head bob) is what we render from; camera is the player's real camera, used for targeting.
    With hitboxes on, also the player box and each light as a small sphere in its colour; `inspected` (what you
    look at) get a yellow box. `screens` (the console's displays) are drawn after the entities."""
    pr.begin_mode_3d(view_camera)

    pr.draw_plane(pr.Vector3(0.0, 0.0, 0.0), pr.Vector2(32.0, 32.0), pr.LIGHTGRAY)
    for entity in entities:
        draw_entity(entity, camera, debug, entity in (inspected or ()))
    if screens is not None:
        screens.draw()

    if debug.hitboxes:
        for light in lights:
            pr.draw_sphere(light.pos, 0.1, light.color)
        _, pbox = player.box()
        pr.draw_bounding_box(pbox, pr.ORANGE)

    pr.end_mode_3d()


def draw_hud(
    camera: pr.Camera3D, camera_mode: int, player: Player, debug: DebugOptions,
    inspected: list[Entity] | None = None,
) -> None:
    # Laid out for a SCREEN_H tall window and scaled by s, so it keeps its size and place in fullscreen.
    w, h = pr.get_screen_width(), pr.get_screen_height()
    s = h / config.SCREEN_H
    right = w / s - 200   # left edge of the status panel, in unscaled units

    def rect(x: float, y: float, rw: float, rh: float, color: pr.Color, lines: bool = False) -> None:
        draw = pr.draw_rectangle_lines if lines else pr.draw_rectangle
        draw(int(x * s), int(y * s), int(rw * s), int(rh * s), color)

    def text(msg: str, x: float, y: float, size: float = 10, color: pr.Color = pr.BLACK) -> None:
        pr.draw_text(msg, int(x * s), int(y * s), int(size * s), color)

    rect(right, 5, 195, 130, pr.fade(pr.SKYBLUE, 0.5))
    rect(right, 5, 195, 130, pr.BLUE, lines=True)

    proj = "PERSPECTIVE" if camera.projection == pr.CameraProjection.CAMERA_PERSPECTIVE else "ORTHOGRAPHIC"
    p, t, u = camera.position, camera.target, camera.up

    text("Camera status:", right + 10, 15)
    text(f"- Mode: {MODE_NAMES.get(camera_mode, 'CUSTOM')}", right + 10, 30)
    text(f"- Projection: {proj}", right + 10, 45)
    text(f"- Position: ({p.x:06.3f}, {p.y:06.3f}, {p.z:06.3f})", right + 10, 60)
    text(f"- Target: ({t.x:06.3f}, {t.y:06.3f}, {t.z:06.3f})", right + 10, 75)
    text(f"- Up: ({u.x:06.3f}, {u.y:06.3f}, {u.z:06.3f})", right + 10, 90)
    text(f"- Colliding: {player.colliding}", right + 10, 105, color=pr.RED if player.colliding else pr.BLACK)
    text(f"- On ground: {player.on_ground}", right + 10, 120)

    text(f"{pr.get_fps()} FPS", 10, 145, size=20, color=pr.LIME)
    flags = [n for n, on in (("HITBOXES", debug.hitboxes), ("WIRES", debug.wireframes),
                             ("COLLISION MESH", debug.collision_meshes), ("UNLIT", debug.unlit),
                             ("NO VIGNETTE", debug.no_vignette)) if on]
    if flags:
        text("DEBUG: " + " + ".join(flags), 10, 165, color=pr.RED)

    # with hitboxes on: details of everything you look at, nearest first, one panel each (as many as fit)
    y = 185
    for entity in inspected or ():
        lines = entity.debug_lines()
        height = 15 * len(lines) + 10
        if y + height > h / s:
            break
        width = max(pr.measure_text(line, int(10 * s)) for line in lines) / s + 20   # as drawn (scaled)
        rect(5, y, width, height, pr.fade(pr.BLACK, 0.6))
        for i, line in enumerate(lines):
            text(line, 15, y + 7 + 15 * i, color=pr.YELLOW if i == 0 else pr.RAYWHITE)
        y += height + 5

    pr.draw_circle(w // 2, h // 2, 4 * s, pr.WHITE)   # crosshair
