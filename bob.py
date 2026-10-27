import pyray as pr
import math

pr.init_window(800, 450, "FPS Camera Bobbing")
pr.set_target_fps(60)
pr.disable_cursor()

# Player position
player_x = 0.0
player_y = 0.0
player_z = 0.0

# Movement
speed = 5.0

# Camera rotation
yaw = 0.0
pitch = 0.0
sensitivity = 0.001

# Camera height
camera_height = 1.5

# Camera bobbing
head_timer = 0.0
walk_lerp = 0.0

bob_up = 0.15
side_bob = 0.1

# Camera
camera = pr.Camera3D(
    (player_x, camera_height, player_z),
    (player_x, camera_height, player_z + 1.0),
    (0.0, 1.0, 0.0),
    60.0,
    pr.CAMERA_PERSPECTIVE
)

while not pr.window_should_close():

    delta = pr.get_frame_time()

    # -------------------------
    # 1. Mouse look
    # -------------------------

    mouse = pr.get_mouse_delta()

    yaw -= mouse.x * sensitivity
    pitch -= mouse.y * sensitivity

    pitch = max(
        -math.pi / 2 + 0.01,
        min(math.pi / 2 - 0.01, pitch)
    )

    # -------------------------
    # 2. WASD movement
    # -------------------------

    forward_input = (
        int(pr.is_key_down(pr.KeyboardKey.KEY_W))
        - int(pr.is_key_down(pr.KeyboardKey.KEY_S))
    )

    side_input = (
        int(pr.is_key_down(pr.KeyboardKey.KEY_A))
        - int(pr.is_key_down(pr.KeyboardKey.KEY_D))
    )

    moving = forward_input != 0 or side_input != 0

    # Movement directions
    forward_x = math.sin(yaw)
    forward_z = math.cos(yaw)

    right_x = math.cos(yaw)
    right_z = -math.sin(yaw)

    move_x = right_x * side_input + forward_x * forward_input
    move_z = right_z * side_input + forward_z * forward_input

    # Normalize diagonal movement
    length = math.sqrt(move_x**2 + move_z**2)

    if length > 0:
        move_x /= length
        move_z /= length

    player_x += move_x * speed * delta
    player_z += move_z * speed * delta

    # -------------------------
    # 3. Calculate base position
    # -------------------------

    # Never include bobbing in the player's position
    base_x = player_x
    base_y = player_y + camera_height
    base_z = player_z

    # -------------------------
    # 4. Camera bobbing
    # -------------------------

    if moving:
        head_timer += delta * 3.0

        walk_lerp += (
            1.0 - walk_lerp
        ) * min(1.0, 10.0 * delta)

    else:
        walk_lerp += (
            0.0 - walk_lerp
        ) * min(1.0, 10.0 * delta)

    head_sin = math.sin(head_timer * math.pi)
    head_cos = math.cos(head_timer * math.pi)

    bob_x = head_sin * side_bob * walk_lerp
    bob_y = abs(head_cos) * bob_up * walk_lerp

    # -------------------------
    # 5. Final camera position
    # -------------------------

    camera_x = base_x + right_x * bob_x
    camera_y = base_y + bob_y
    camera_z = base_z + right_z * bob_x

    # Viewing direction
    direction_x = math.sin(yaw) * math.cos(pitch)
    direction_y = math.sin(pitch)
    direction_z = math.cos(yaw) * math.cos(pitch)

    camera.position = pr.Vector3(
        camera_x,
        camera_y,
        camera_z
    )

    camera.target = pr.Vector3(
        camera_x + direction_x,
        camera_y + direction_y,
        camera_z + direction_z
    )

    # -------------------------
    # 6. Drawing
    # -------------------------

    pr.begin_drawing()
    pr.clear_background(pr.RAYWHITE)

    pr.begin_mode_3d(camera)

    pr.draw_plane(
        (0.0, 0.0, 0.0),
        (100.0, 100.0),
        pr.LIGHTGRAY
    )

    pr.draw_cube(
        (0.0, 1.0, 5.0),
        2.0, 2.0, 2.0,
        pr.RED
    )

    pr.draw_cube(
        (5.0, 1.0, 5.0),
        2.0, 2.0, 2.0,
        pr.BLUE
    )

    pr.end_mode_3d()

    pr.draw_text(
        "WASD: Move | Mouse: Look",
        10, 10, 20, pr.DARKGRAY
    )

    pr.end_drawing()

pr.close_window()