import pyray as pr
import math

pr.init_window(800, 450, "Camera Bobbing")
pr.set_target_fps(60)

camera = pr.Camera3D(
    (0.0, 2.0, 0.0),  # Position
    (0.0, 2.0, 1.0),  # Target
    (0.0, 1.0, 0.0),  # Up
    60.0,
    pr.CAMERA_PERSPECTIVE
)

timer = 0.0

bob_up = 0.1        # const
side_bob = 0.05     # const

while not pr.window_should_close():
    delta = pr.get_frame_time()

    # Update timer while holding W
    if pr.is_key_down(pr.KeyboardKey.KEY_W):
        timer += delta * 4.0

    # Calculate bobbing
    bob_y = abs(math.cos(timer * math.pi)) * bob_up
    bob_x = math.sin(timer * math.pi) * side_bob

    # Apply bobbing
    camera.position.x = bob_x
    camera.position.y = 2.0 + bob_y

    camera.target.x = bob_x
    camera.target.y = 2.0 + bob_y

    pr.begin_drawing()
    pr.clear_background(pr.RAYWHITE)

    pr.begin_mode_3d(camera)

    pr.draw_plane(
        (0.0, 0.0, 0.0),
        (20.0, 20.0),
        pr.LIGHTGRAY
    )

    pr.draw_cube(
        (0.0, 1.0, 5.0),
        2.0, 2.0, 2.0,
        pr.RED
    )

    pr.end_mode_3d()

    pr.draw_text(
        "Hold W to bob the camera",
        10, 10, 20, pr.DARKGRAY
    )

    pr.end_drawing()

pr.close_window()