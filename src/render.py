"""Drawing: the 3D scene and the HUD."""
from __future__ import annotations

from typing import Callable, Iterable

import pyray as pr

from . import config
from .debug import DebugOptions
from .entity import Entity
from .lighting import Light
from .player import Player

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
    overlays: Iterable[Callable[[], None]] = (),
) -> None:
    """view_camera (with head bob) is what we render from; camera is the player's real camera, used for targeting.
    With hitboxes on, also the player box and each light as a small sphere in its colour; `inspected` (what you
    look at) get a yellow box. `overlays` (the console's screens, the steam) are drawn after the entities, in the same 3D mode."""
    pr.begin_mode_3d(view_camera)

    for entity in entities:
        draw_entity(entity, camera, debug, entity in (inspected or ()))
    for overlay in overlays:
        overlay()

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
    """The crosshair, and while the debug menu is open (F3) its box on the left: FPS, the camera, the debug keys
    (lit up while on), then a panel for each thing you look at with hitboxes on."""
    # Laid out for a SCREEN_H tall window and scaled by s, so it keeps its size and place in fullscreen.
    w, h = pr.get_screen_width(), pr.get_screen_height()
    s = h / config.SCREEN_H
    if debug.menu:
        _draw_debug_menu(camera, camera_mode, player, debug, inspected or [], s, h)
    pr.draw_circle(w // 2, h // 2, 4 * s, pr.WHITE)   # crosshair


def _draw_debug_menu(camera: pr.Camera3D, camera_mode: int, player: Player, debug: DebugOptions,
                     inspected: list[Entity], s: float, h: int) -> None:
    size, line = 16, 21   # text size and line height, in SCREEN_H pixels

    def rect(x: float, y: float, rw: float, rh: float, color: pr.Color, lines: bool = False) -> None:
        if lines:
            pr.draw_rectangle_lines_ex(pr.Rectangle(x * s, y * s, rw * s, rh * s), max(1.0, 2 * s), color)
        else:
            pr.draw_rectangle(int(x * s), int(y * s), int(rw * s), int(rh * s), color)

    def text(msg: str, x: float, y: float, color: pr.Color = pr.RAYWHITE, text_size: float = size) -> None:
        pr.draw_text(msg, int(x * s), int(y * s), int(text_size * s), color)

    p, t = camera.position, camera.target
    off, on = pr.GRAY, pr.LIME
    keys = [("1 / 2", f"camera: {MODE_NAMES.get(camera_mode, 'CUSTOM')}", None),
            ("F1", "hitboxes + details", debug.hitboxes), ("F2", "wireframes", debug.wireframes),
            ("C", "collision meshes", debug.collision_meshes), ("L", "lighting off", debug.unlit),
            ("V", "vignette off", debug.no_vignette), ("F4", "burst a pipe", None), ("F5", "a fault now", None),
            ("F3", "close (all off)", None)]
    width, height = 360, 16 + line * (4.5 + len(keys))   # the title, 3 lines about the camera, a gap, the keys
    rect(10, 10, width, height, pr.fade(pr.BLACK, 0.7))
    rect(10, 10, width, height, pr.LIME, lines=True)
    x, y = 22, 20
    text("DEBUG", x, y, pr.LIME)
    fps = f"{pr.get_fps()} FPS"
    text(fps, 10 + width - 12 - pr.measure_text(fps, int(size * s)) / s, y, pr.LIME)
    y += line
    text(f"pos    ({p.x:7.2f}, {p.y:6.2f}, {p.z:7.2f})", x, y)
    text(f"target ({t.x:7.2f}, {t.y:6.2f}, {t.z:7.2f})", x, y + line)
    text(f"colliding: {player.colliding}", x, y + 2 * line, pr.RED if player.colliding else pr.RAYWHITE)
    text(f"on ground: {player.on_ground}", x + 180, y + 2 * line)
    y += 3 * line + line // 2
    pr.draw_line_ex(pr.Vector2((x - 4) * s, (y - 8) * s), pr.Vector2((10 + width - 8) * s, (y - 8) * s),
                    max(1.0, s), pr.fade(pr.LIME, 0.5))
    for key, what, state in keys:
        color = pr.RAYWHITE if state is None else on if state else off
        text(key, x, y, pr.YELLOW)
        text(what + ("" if state is None else "  [ON]" if state else "  [off]"), x + 60, y, color)
        y += line

    # with hitboxes on: details of everything you look at, nearest first, one panel each (as many as fit)
    y = 10 + height + 8
    small, small_line = 14, 18
    for entity in inspected:
        lines = entity.debug_lines()
        panel = small_line * len(lines) + 12
        if y + panel > h / s:
            break
        panel_w = max(pr.measure_text(row, int(small * s)) for row in lines) / s + 24   # as drawn (scaled)
        rect(10, y, panel_w, panel, pr.fade(pr.BLACK, 0.7))
        for i, row in enumerate(lines):
            text(row, 22, y + 7 + small_line * i, pr.YELLOW if i == 0 else pr.RAYWHITE, small)
        y += panel + 6
