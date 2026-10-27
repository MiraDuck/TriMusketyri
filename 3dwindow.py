"""Entry point. Run from anywhere: python 3dwindow.py"""
from __future__ import annotations

import pyray as pr

from src import config
from src.audio import Audio
from src.controls import handle_hotkeys, move_axes, move_camera
from src.debug import DebugOptions
from src.entity import Entity
from src.head_bob import HeadBob
from src.player import Player
from src.render import draw_hud, draw_scene


def main() -> None:
    pr.set_trace_log_level(pr.TraceLogLevel.LOG_WARNING)
    pr.init_window(config.SCREEN_W, config.SCREEN_H, config.WINDOW_TITLE)
    # pr.toggle_fullscreen()
    pr.disable_cursor()
    pr.set_target_fps(config.TARGET_FPS)

    camera: pr.Camera3D = pr.Camera3D(
        config.START_POSITION,
        config.START_TARGET,
        pr.Vector3(0.0, 1.0, 0.0),
        config.CAMERA_FOVY,
        pr.CameraProjection.CAMERA_PERSPECTIVE,
    )
    camera_mode: int = pr.CameraMode.CAMERA_FIRST_PERSON

    audio = Audio()
    if config.START_MUSIC:
        audio.play_music(config.START_MUSIC)

    entities: list[Entity] = [
        Entity("level", config.VISIBLE_MODEL, config.MODEL_POS, collision_path=config.COLLISION_MODEL),
        Entity("lever", config.LEVER_MODEL, config.LEVER_POS),
    ]
    colliders = [e.collider for e in entities if e.collider is not None]
    player = Player(camera)
    bob = HeadBob()
    debug = DebugOptions()

    pr.rl_set_line_width(2)

    while not pr.window_should_close():
        dt: float = min(pr.get_frame_time(), config.MAX_DT)

        audio.update()
        camera_mode = handle_hotkeys(camera, camera_mode, debug)
        move_camera(camera, camera_mode, dt)

        if camera_mode == pr.CameraMode.CAMERA_FIRST_PERSON:
            player.update(dt, colliders)
            forward, sideway = move_axes()
            bob.update(forward != 0 or sideway != 0, sideway, forward, dt)
            view_camera = bob.apply(camera)
        else:
            player.colliding = False
            view_camera = camera

        pr.begin_drawing()
        pr.clear_background(pr.RAYWHITE)
        draw_scene(view_camera, camera, camera_mode, player, entities, debug)
        draw_hud(camera, camera_mode, player, debug)
        pr.end_drawing()

    for entity in entities:
        entity.unload()
    audio.unload()
    pr.close_window()


if __name__ == "__main__":
    main()
