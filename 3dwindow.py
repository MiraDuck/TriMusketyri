"""Entry point. Run from anywhere: python 3dwindow.py"""
from pyray import *

from src import config
from src.audio import Audio
from src.collision import CollisionWorld
from src.controls import handle_hotkeys, move_axes, move_camera
from src.head_bob import HeadBob
from src.player import Player
from src.render import draw_hud, draw_scene


def main():
    set_trace_log_level(TraceLogLevel.LOG_WARNING)
    init_window(config.SCREEN_W, config.SCREEN_H, config.WINDOW_TITLE)
    # toggle_fullscreen()
    disable_cursor()
    set_target_fps(config.TARGET_FPS)

    camera = Camera3D(
        config.START_POSITION,
        config.START_TARGET,
        Vector3(0.0, 1.0, 0.0),
        config.CAMERA_FOVY,
        CameraProjection.CAMERA_PERSPECTIVE,
    )
    camera_mode = CameraMode.CAMERA_FIRST_PERSON

    audio = Audio()
    if config.START_MUSIC:
        audio.play_music(config.START_MUSIC)

    model = load_model(str(config.VISIBLE_MODEL))
    world = CollisionWorld(config.COLLISION_MODEL, config.MODEL_POS)
    player = Player(camera)
    bob = HeadBob()
    show_col = False

    rl_set_line_width(2)

    while not window_should_close():
        dt = min(get_frame_time(), config.MAX_DT)

        audio.update()
        camera_mode, show_col = handle_hotkeys(camera, camera_mode, show_col)
        move_camera(camera, camera_mode, dt)

        if camera_mode == CameraMode.CAMERA_FIRST_PERSON:
            player.update(dt, world)
            forward, sideway = move_axes()
            bob.update(forward != 0 or sideway != 0, sideway, forward, dt)
            view_camera = bob.apply(camera)
        else:
            player.colliding = False
            view_camera = camera

        begin_drawing()
        clear_background(RAYWHITE)
        draw_scene(view_camera, camera, camera_mode, player, model, world, show_col)
        draw_hud(camera, camera_mode, player)
        end_drawing()

    unload_model(model)
    world.unload()
    audio.unload()
    close_window()


if __name__ == "__main__":
    main()
