"""Entry point. Run from anywhere: python 3dwindow.py"""
from __future__ import annotations

import pyray as pr

from src import config
from src.audio import Audio
from src.controls import handle_hotkeys, handle_interaction, move_axes, move_camera
from src.debug import DebugOptions
from src.entity import Entity
from src.head_bob import HeadBob
from src.interactable import Interactable, Lever, Valve
from src.lighting import Light, Lighting
from src.player import Player
from src.render import draw_hud, draw_scene


def drill_cars() -> list[Entity]:
    """The cars from config.DRILL_CARS, the first at DRILL_POS and each next one CAR_LENGTH further along -z."""
    d = config.DRILL_POS
    return [
        Entity(name, model, pr.Vector3(d.x, d.y, d.z - i * config.CAR_LENGTH), collision_path=collision)
        for i, (name, model, collision) in enumerate(config.DRILL_CARS)
    ]


def main() -> None:
    pr.set_trace_log_level(pr.TraceLogLevel.LOG_WARNING)
    pr.init_window(config.SCREEN_W, config.SCREEN_H, config.WINDOW_TITLE)
    pr.disable_cursor()
    pr.set_target_fps(config.TARGET_FPS)

    # `camera` is the player's real position (input and physics move it); what we draw from is a copy of it
    # with head bob added (view_camera below), so the bob can never affect collision.
    camera = pr.Camera3D(
        config.START_POSITION,
        config.START_TARGET,
        pr.Vector3(0.0, 1.0, 0.0),
        config.CAMERA_FOVY,
        pr.CameraProjection.CAMERA_PERSPECTIVE,
    )
    camera_mode: int = pr.CameraMode.CAMERA_FIRST_PERSON

    audio = Audio(config.AMBIENCE_DIR)
    if config.START_MUSIC:
        audio.play_music(config.START_MUSIC)

    valve = Valve("valve", config.VALVE_MODEL, config.VALVE_POS)
    entities: list[Entity] = drill_cars() + [Lever("lever", config.LEVER_MODEL, config.LEVER_POS), valve]
    colliders = [e.collider for e in entities if e.collider is not None]
    interactables = [e for e in entities if isinstance(e, Interactable)]
    held: Interactable | None = None   # what the player is holding (a valve), None = mouse look is on

    lighting = Lighting([Light(*light) for light in config.LIGHTS])
    for entity in entities:
        if entity.name in config.LIT_ENTITIES:
            lighting.add(entity.model)

    player = Player(camera)
    bob = HeadBob()
    debug = DebugOptions()
    valve_break_at = config.VALVE_BREAK_TEST_AT

    pr.rl_set_line_width(2)

    while not pr.window_should_close():
        dt: float = min(pr.get_frame_time(), config.MAX_DT)
        audio.update()

        # ---- input ----
        camera_mode = handle_hotkeys(camera, camera_mode, debug)
        held = handle_interaction(camera, interactables, held)
        move_camera(camera, camera_mode, dt, look=held is None)

        # ---- world ----
        # Emergency example: set VALVE_BREAK_TEST_AT in config and the valve starts turning by itself then.
        # Real faults will do the same from the fault director: valve.spin = speed (0 = repaired).
        if valve_break_at is not None and pr.get_time() >= valve_break_at:
            valve.spin = config.VALVE_BREAK_SPIN   # degrees / s; positive opens, negative closes
            valve_break_at = None
        for interactable in interactables:
            interactable.update(dt)

        # ---- player ----
        if camera_mode == pr.CameraMode.CAMERA_FIRST_PERSON:
            player.update(dt, colliders)
            forward, sideway = move_axes()
            bob.update(forward != 0 or sideway != 0, sideway, forward, dt)
            view_camera = bob.apply(camera)
        else:
            player.colliding = False
            view_camera = camera

        # ---- draw ----
        lighting.set_enabled(not debug.unlit)
        lighting.update(pr.get_time())
        pr.begin_drawing()
        pr.clear_background(pr.RAYWHITE)
        draw_scene(view_camera, camera, player, entities, lighting.lights, debug)
        draw_hud(camera, camera_mode, player, debug)
        pr.end_drawing()

    for entity in entities:
        entity.unload()
    lighting.unload()
    audio.unload()
    pr.close_window()


if __name__ == "__main__":
    main()
