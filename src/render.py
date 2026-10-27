"""Drawing: the 3D scene and the HUD."""
from __future__ import annotations

import pyray as pr

from typing import Iterable

from . import config
from .debug import DebugOptions
from .entity import Entity
from .player import Player

MODE_NAMES: dict[int, str] = {
    pr.CameraMode.CAMERA_FREE: "FREE",
    pr.CameraMode.CAMERA_FIRST_PERSON: "FIRST_PERSON",
    pr.CameraMode.CAMERA_THIRD_PERSON: "THIRD_PERSON",
    pr.CameraMode.CAMERA_ORBITAL: "ORBITAL",
}

def draw_entity(entity: Entity, camera: pr.Camera3D, debug: DebugOptions) -> None:
    """Visible model (or its collision mesh in debug), then the optional wireframe and hitbox."""
    collider = entity.collider
    show_mesh = debug.collision_meshes and collider is not None
    model = collider.model if show_mesh and collider else entity.model

    pr.draw_model(model, entity.pos, 1.0, pr.WHITE)
    if debug.wireframes:
        pr.draw_model_wires(model, entity.pos, 1.0, pr.RED if show_mesh else pr.BLACK)
    if debug.hitboxes:
        # solid things are always green; non-solid ones go red until you look at them
        ok = entity.solid or entity.is_targeted(camera)
        pr.draw_bounding_box(entity.bounds, pr.GREEN if ok else pr.RED)


def draw_scene(
    view_camera: pr.Camera3D,
    camera: pr.Camera3D,
    camera_mode: int,
    player: Player,
    entities: Iterable[Entity],
    debug: DebugOptions,
) -> None:
    """view_camera is what we render from; camera is the player's real camera."""
    pr.begin_mode_3d(view_camera)

    pr.draw_plane(pr.Vector3(0.0, 0.0, 0.0), pr.Vector2(32.0, 32.0), pr.LIGHTGRAY)
    pr.draw_cube(pr.Vector3(-16.0, 2.5, 0.0), 1.0, 5.0, 32.0, pr.BLUE)
    pr.draw_cube(pr.Vector3(16.0, 2.5, 0.0), 1.0, 5.0, 32.0, pr.LIME)
    pr.draw_cube(pr.Vector3(0.0, 2.5, 16.0), 32.0, 5.0, 1.0, pr.GOLD)
    pr.draw_cube(pr.Vector3(0.0, 2.5, -16.0), 32.0, 5.0, 1.0, pr.RED)


    if camera_mode == pr.CameraMode.CAMERA_THIRD_PERSON:
        pr.draw_cube(camera.target, 0.5, 0.5, 0.5, pr.PURPLE)
        pr.draw_cube_wires(camera.target, 0.5, 0.5, 0.5, pr.DARKPURPLE)

    for entity in entities:
        draw_entity(entity, camera, debug)

    if debug.hitboxes and camera_mode != pr.CameraMode.CAMERA_FIRST_PERSON:
        _, pbox = player.box()
        pr.draw_bounding_box(pbox, pr.ORANGE)

    pr.end_mode_3d()


def draw_hud(camera: pr.Camera3D, camera_mode: int, player: Player, debug: DebugOptions) -> None:
    # pr.draw_rectangle(5, 5, 330, 100, pr.fade(pr.SKYBLUE, 0.5))
    # pr.draw_rectangle_lines(5, 5, 330, 100, pr.BLUE)

    # pr.draw_text("Camera controls:", 15, 15, 10, pr.BLACK)
    # pr.draw_text("- Move keys: W, A, S, D, Space, Left-Ctrl", 15, 30, 10, pr.BLACK)
    # pr.draw_text("- Look around: arrow keys or mouse", 15, 45, 10, pr.BLACK)
    # pr.draw_text("- Camera mode keys: 1, 2, 3, 4   |   C: show collision model", 15, 60, 10, pr.BLACK)
    # pr.draw_text("- Zoom keys: num-plus, num-minus or mouse scroll", 15, 75, 10, pr.BLACK)
    # pr.draw_text("- Camera projection key: P", 15, 90, 10, pr.BLACK)

    pr.draw_rectangle(600, 5, 195, 130, pr.fade(pr.SKYBLUE, 0.5))
    pr.draw_rectangle_lines(600, 5, 195, 130, pr.BLUE)

    proj = "PERSPECTIVE" if camera.projection == pr.CameraProjection.CAMERA_PERSPECTIVE else \
           "ORTHOGRAPHIC" if camera.projection == pr.CameraProjection.CAMERA_ORTHOGRAPHIC else "CUSTOM"
    p, t, u = camera.position, camera.target, camera.up

    pr.draw_text("Camera status:", 610, 15, 10, pr.BLACK)
    pr.draw_text(f"- Mode: {MODE_NAMES.get(camera_mode, 'CUSTOM')}", 610, 30, 10, pr.BLACK)
    pr.draw_text(f"- Projection: {proj}", 610, 45, 10, pr.BLACK)
    pr.draw_text(f"- Position: ({p.x:06.3f}, {p.y:06.3f}, {p.z:06.3f})", 610, 60, 10, pr.BLACK)
    pr.draw_text(f"- Target: ({t.x:06.3f}, {t.y:06.3f}, {t.z:06.3f})", 610, 75, 10, pr.BLACK)
    pr.draw_text(f"- Up: ({u.x:06.3f}, {u.y:06.3f}, {u.z:06.3f})", 610, 90, 10, pr.BLACK)
    pr.draw_text(f"- Colliding: {player.colliding}", 610, 105, 10, pr.RED if player.colliding else pr.BLACK)
    pr.draw_text(f"- On ground: {player.on_ground}", 610, 120, 10, pr.BLACK)

    if debug.hitboxes or debug.wireframes or debug.collision_meshes:
        flags = [n for n, on in (("HITBOXES", debug.hitboxes), ("WIRES", debug.wireframes),
                                 ("COLLISION MESH", debug.collision_meshes)) if on]
        pr.draw_text("DEBUG: " + " + ".join(flags), 10, 165, 10, pr.RED)

    pr.draw_circle(config.SCREEN_W//2, config.SCREEN_H//2, 4, pr.WHITE)

    pr.draw_fps(10, 145)
