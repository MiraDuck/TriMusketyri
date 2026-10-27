import math
from pyray import *

SCREEN_W = 1600
SCREEN_H = 900

set_trace_log_level(TraceLogLevel.LOG_WARNING)
init_window(SCREEN_W, SCREEN_H, "raylib [core] example - 3d camera first person")

toggle_fullscreen()

camera = Camera3D(
    Vector3(0.0, 2.5, 4.0),
    Vector3(0.0, 2.5, 0.0),
    Vector3(0.0, 1.0, 0.0),
    60.0,
    CameraProjection.CAMERA_PERSPECTIVE,
)

camera_mode = CameraMode.CAMERA_FIRST_PERSON

disable_cursor()
TARGET_FPS = 0          # 0 = uncapped; everything below scales with frame time
set_target_fps(TARGET_FPS)

mode_names = {
    CameraMode.CAMERA_FREE: "FREE",
    CameraMode.CAMERA_FIRST_PERSON: "FIRST_PERSON",
    CameraMode.CAMERA_THIRD_PERSON: "THIRD_PERSON",
    CameraMode.CAMERA_ORBITAL: "ORBITAL",
}

player_speed = 3.6      # units / second (was 0.06 per frame at 60 FPS)
MAX_DT = 0.05           # clamp long frames (window drag, load hitch) so physics can't tunnel

# ---------------- Models ----------------
MODEL_POS = Vector3(0, 1, 0)

model = load_model("Models/test.obj")                 # what you see
col_model = load_model("Models/navmesh.obj")   # what you hit

col_bb = get_model_bounding_box(col_model)
world_bb = BoundingBox(
    Vector3(col_bb.min.x + MODEL_POS.x, col_bb.min.y + MODEL_POS.y, col_bb.min.z + MODEL_POS.z),
    Vector3(col_bb.max.x + MODEL_POS.x, col_bb.max.y + MODEL_POS.y, col_bb.max.z + MODEL_POS.z),
)

# ---------------- Player cuboid ----------------
PLAYER_HALF = Vector3(0.4, 0.75, 0.4)
EYE_TO_CENTER = 1.0
STEP_UP = 0.6          # how high a ledge/sunken amount we can recover from

# Down-rays for the floor: center + 4 points inside the box corners
_f = 0.8
FLOOR_SAMPLES = [
    (0.0, 0.0),
    (PLAYER_HALF.x * _f, PLAYER_HALF.z * _f),
    (-PLAYER_HALF.x * _f, PLAYER_HALF.z * _f),
    (PLAYER_HALF.x * _f, -PLAYER_HALF.z * _f),
    (-PLAYER_HALF.x * _f, -PLAYER_HALF.z * _f),
]

WALL_DIRS = [
    (Vector3(1, 0, 0),  PLAYER_HALF.x),
    (Vector3(-1, 0, 0), PLAYER_HALF.x),
    (Vector3(0, 0, 1),  PLAYER_HALF.z),
    (Vector3(0, 0, -1), PLAYER_HALF.z),
]

DOWN = Vector3(0, -1, 0)
UP = Vector3(0, 1, 0)


def is_floor(n):   return n.y > 0.5            # faces up
def is_ceiling(n): return n.y < -0.5           # faces down
def is_wall(n):    return abs(n.y) < 0.5       # steep


def player_box(cam):
    c = Vector3(cam.position.x, cam.position.y - EYE_TO_CENTER, cam.position.z)
    box = BoundingBox(
        Vector3(c.x - PLAYER_HALF.x, c.y - PLAYER_HALF.y, c.z - PLAYER_HALF.z),
        Vector3(c.x + PLAYER_HALF.x, c.y + PLAYER_HALF.y, c.z + PLAYER_HALF.z),
    )
    return c, box


def cast_model(origin, direction, accept, max_skips=4):
    """
    Closest hit on col_model whose triangle normal passes accept(normal).
    Returns the hit point in world space, or None.

    raylib only reports the single closest triangle per mesh. If that triangle
    is the wrong kind (e.g. the underside of a floor), we restart the ray just
    past it and try again, so the right triangle can still be found.
    """
    ox = origin.x - MODEL_POS.x   # world -> model space
    oy = origin.y - MODEL_POS.y
    oz = origin.z - MODEL_POS.z

    for _ in range(max_skips + 1):
        ray = Ray(Vector3(ox, oy, oz), direction)
        best = None
        for i in range(col_model.meshCount):
            hit = get_ray_collision_mesh(ray, col_model.meshes[i], matrix_identity())
            if hit.hit and (best is None or hit.distance < best.distance):
                best = hit
        if best is None:
            return None
        if accept(best.normal):
            p = best.point
            return Vector3(p.x + MODEL_POS.x, p.y + MODEL_POS.y, p.z + MODEL_POS.z)
        # wrong kind of triangle: continue from just past it
        ox = best.point.x + direction.x * 0.01
        oy = best.point.y + direction.y * 0.01
        oz = best.point.z + direction.z * 0.01
    return None


on_ground = False

GRAVITY = 25.0         # units / s^2
MAX_FALL_SPEED = 15.0  # kept below STEP_UP per frame so we can't tunnel through floors
WORLD_FLOOR_Y = 0.0    # fallback floor (the drawn plane) outside the collision model
vel_y = 0.0


def apply_gravity(cam, dt):
    """Pull the player down; resolve_collision() then pushes them back onto the floor."""
    global vel_y
    vel_y = max(vel_y - GRAVITY * dt, -MAX_FALL_SPEED)
    dy = vel_y * dt
    cam.position = Vector3(cam.position.x, cam.position.y + dy, cam.position.z)
    cam.target = Vector3(cam.target.x, cam.target.y + dy, cam.target.z)


def land_on_world_floor(cam):
    """Stop the player at WORLD_FLOOR_Y if the collision model didn't catch them."""
    global on_ground
    feet = cam.position.y - EYE_TO_CENTER - PLAYER_HALF.y
    if feet < WORLD_FLOOR_Y:
        lift = WORLD_FLOOR_Y - feet
        cam.position = Vector3(cam.position.x, cam.position.y + lift, cam.position.z)
        cam.target = Vector3(cam.target.x, cam.target.y + lift, cam.target.z)
        on_ground = True


def resolve_collision(cam):
    """Push the camera out of the collision model. Returns True if touching it."""
    global on_ground
    on_ground = False

    c, box = player_box(cam)
    if not check_collision_boxes(box, world_bb):   # broadphase
        return False

    feet = c.y - PLAYER_HALF.y
    head = c.y + PLAYER_HALF.y
    push = Vector3(0, 0, 0)
    touched = False

    # --- Floor: several rays from just above the feet, keep the HIGHEST floor ---
    floor_y = None
    for ox, oz in FLOOR_SAMPLES:
        o = Vector3(c.x + ox, feet + STEP_UP, c.z + oz)
        p = cast_model(o, DOWN, is_floor)
        if p is not None and (floor_y is None or p.y > floor_y):
            floor_y = p.y
    if floor_y is not None:
        if floor_y > feet:
            push.y += floor_y - feet
            touched = True
        if floor_y >= feet - 0.05:
            on_ground = True

    # --- Ceiling ---
    p = cast_model(c, UP, is_ceiling)
    if p is not None and p.y < head:
        push.y -= head - p.y
        touched = True

    # --- Walls: rays at two heights, ignoring floor-like triangles ---
    for h in (feet + STEP_UP + 0.1, head - 0.2):
        o = Vector3(c.x, h, c.z)
        for d, half in WALL_DIRS:
            p = cast_model(o, d, is_wall)
            if p is None:
                continue
            dist = (p.x - o.x) * d.x + (p.z - o.z) * d.z
            if dist < half:
                push.x -= d.x * (half - dist)
                push.z -= d.z * (half - dist)
                touched = True

    if touched:
        # Move position AND target together so the view direction doesn't change
        cam.position = Vector3(cam.position.x + push.x, cam.position.y + push.y, cam.position.z + push.z)
        cam.target = Vector3(cam.target.x + push.x, cam.target.y + push.y, cam.target.z + push.z)
    return touched


# ---------------- Head bob (from bob_example.c) ----------------
# Purely visual: applied to a copy of the camera used for drawing, so the
# player's real position (and therefore collision / y) is never affected.
BOB_SIDE = 0.01          # sideways sway
STEP_ROTATION = 0.0075    # roll while walking
WALK_FOV_DELTA = -5.0   # fov change while walking

head_timer = 0.0
walk_lerp = 0.0
fov_offset = 0.0
lean_x = 0.0
lean_y = 0.0


def smooth(rate, dt):
    """Frame-rate independent lerp factor (same easing at any FPS)."""
    return 1.0 - math.exp(-rate * dt)


def update_bob(moving, sideway, forward, dt):
    global head_timer, walk_lerp, fov_offset, lean_x, lean_y
    if moving:
        head_timer += dt * 3.0
        walk_lerp += (1.0 - walk_lerp) * smooth(10.0, dt)
        fov_offset += (WALK_FOV_DELTA - fov_offset) * smooth(5.0, dt)
    else:
        walk_lerp += (0.0 - walk_lerp) * smooth(10.0, dt)
        fov_offset += (0.0 - fov_offset) * smooth(5.0, dt)
    lean_x += (sideway * 0.02 - lean_x) * smooth(10.0, dt)
    lean_y += (forward * 0.015 - lean_y) * smooth(10.0, dt)


def bob_camera(cam):
    """Return a copy of cam with the bob effects applied (y is left untouched)."""
    fwd = vector3_normalize(vector3_subtract(cam.target, cam.position))
    right = vector3_normalize(vector3_cross_product(fwd, Vector3(0, 1, 0)))
    head_sin = math.sin(head_timer * math.pi)

    # sway sideways only; no vertical offset
    sway = vector3_scale(right, head_sin * BOB_SIDE * walk_lerp)
    pos = vector3_add(cam.position, sway)

    look = vector3_rotate_by_axis_angle(fwd, right, -lean_y)
    up = vector3_rotate_by_axis_angle(Vector3(0, 1, 0), look, head_sin * STEP_ROTATION + lean_x)

    fovy = cam.fovy
    if cam.projection == CameraProjection.CAMERA_PERSPECTIVE:
        fovy += fov_offset
    return Camera3D(pos, vector3_add(pos, look), up, fovy, cam.projection)


rl_set_line_width(2)
colliding = False
show_col = False

while not window_should_close():
    dt = min(get_frame_time(), MAX_DT)
    step = player_speed * dt    # distance moved this frame

    if is_key_pressed(KeyboardKey.KEY_ONE):
        camera_mode = CameraMode.CAMERA_FREE
        camera.up = Vector3(0.0, 1.0, 0.0)
    if is_key_pressed(KeyboardKey.KEY_TWO):
        camera_mode = CameraMode.CAMERA_FIRST_PERSON
        camera.up = Vector3(0.0, 1.0, 0.0)
    if is_key_pressed(KeyboardKey.KEY_THREE):
        camera_mode = CameraMode.CAMERA_THIRD_PERSON
        camera.up = Vector3(0.0, 1.0, 0.0)
    if is_key_pressed(KeyboardKey.KEY_FOUR):
        camera_mode = CameraMode.CAMERA_ORBITAL
        camera.up = Vector3(0.0, 1.0, 0.0)
    if is_key_pressed(KeyboardKey.KEY_C):
        show_col = not show_col

    if is_key_pressed(KeyboardKey.KEY_P):
        if camera.projection == CameraProjection.CAMERA_PERSPECTIVE:
            camera_mode = CameraMode.CAMERA_THIRD_PERSON
            camera.target = Vector3(0.0, 2.0, 0.0)
            camera.position = Vector3(50.0, 2.0 + 100.0 * math.sin(math.radians(45)), 50.0)
            camera.up = Vector3(0.0, 1.0, 0.0)
            camera.projection = CameraProjection.CAMERA_ORTHOGRAPHIC
            camera.fovy = 20.0
        elif camera.projection == CameraProjection.CAMERA_ORTHOGRAPHIC:
            camera_mode = CameraMode.CAMERA_THIRD_PERSON
            camera.position = Vector3(0.0, 2.0, 10.0)
            camera.target = Vector3(0.0, 2.0, 0.0)
            camera.up = Vector3(0.0, 1.0, 0.0)
            camera.projection = CameraProjection.CAMERA_PERSPECTIVE
            camera.fovy = 60.0

    # update_camera(camera, camera_mode)
    update_camera_pro(camera,
            (
                (is_key_down(KeyboardKey.KEY_W) or is_key_down(KeyboardKey.KEY_UP))*step -
                (is_key_down(KeyboardKey.KEY_S) or is_key_down(KeyboardKey.KEY_DOWN))*step,
                (is_key_down(KeyboardKey.KEY_D) or is_key_down(KeyboardKey.KEY_RIGHT))*step -
                (is_key_down(KeyboardKey.KEY_A) or is_key_down(KeyboardKey.KEY_LEFT))*step,
                0.0 if camera_mode == CameraMode.CAMERA_FIRST_PERSON else
                (is_key_down(KeyboardKey.KEY_SPACE) - is_key_down(KeyboardKey.KEY_LEFT_SHIFT))*step
            ),
            (
                get_mouse_delta().x*0.05,
                get_mouse_delta().y*0.05,
                0.0
            ),
            get_mouse_wheel_move()*2.0)

    if camera_mode == CameraMode.CAMERA_FIRST_PERSON:
        apply_gravity(camera, dt)
        colliding = resolve_collision(camera)
        land_on_world_floor(camera)
        if on_ground:
            vel_y = 0.0
        sideway = (is_key_down(KeyboardKey.KEY_D) or is_key_down(KeyboardKey.KEY_RIGHT)) - \
                  (is_key_down(KeyboardKey.KEY_A) or is_key_down(KeyboardKey.KEY_LEFT))
        forward = (is_key_down(KeyboardKey.KEY_W) or is_key_down(KeyboardKey.KEY_UP)) - \
                  (is_key_down(KeyboardKey.KEY_S) or is_key_down(KeyboardKey.KEY_DOWN))
        update_bob(sideway != 0 or forward != 0, sideway, forward, dt)
        view_camera = bob_camera(camera)
    else:
        colliding = False
        view_camera = camera

    begin_drawing()
    clear_background(RAYWHITE)

    begin_mode_3d(view_camera)

    draw_plane(Vector3(0.0, 0.0, 0.0), Vector2(32.0, 32.0), LIGHTGRAY)
    draw_cube(Vector3(-16.0, 2.5, 0.0), 1.0, 5.0, 32.0, BLUE)
    draw_cube(Vector3(16.0, 2.5, 0.0), 1.0, 5.0, 32.0, LIME)
    draw_cube(Vector3(0.0, 2.5, 16.0), 32.0, 5.0, 1.0, GOLD)
    draw_cube(Vector3(0.0, 2.5, -16.0), 32.0, 5.0, 1.0, RED)

    if camera_mode == CameraMode.CAMERA_THIRD_PERSON:
        draw_cube(camera.target, 0.5, 0.5, 0.5, PURPLE)
        draw_cube_wires(camera.target, 0.5, 0.5, 0.5, DARKPURPLE)

    if not show_col:
        draw_model(model, MODEL_POS, 1.0, WHITE)
        draw_model_wires(model, MODEL_POS, 1.0, BLACK)
        draw_bounding_box(world_bb, GREEN)
    else:
        draw_model(col_model, MODEL_POS, 1.0, WHITE)
        draw_model_wires(col_model, MODEL_POS, 1.0, RED)

    if camera_mode != CameraMode.CAMERA_FIRST_PERSON:
        _, pbox = player_box(camera)
        draw_bounding_box(pbox, ORANGE)

    end_mode_3d()

    draw_rectangle(5, 5, 330, 100, fade(SKYBLUE, 0.5))
    draw_rectangle_lines(5, 5, 330, 100, BLUE)

    draw_text("Camera controls:", 15, 15, 10, BLACK)
    draw_text("- Move keys: W, A, S, D, Space, Left-Ctrl", 15, 30, 10, BLACK)
    draw_text("- Look around: arrow keys or mouse", 15, 45, 10, BLACK)
    draw_text("- Camera mode keys: 1, 2, 3, 4   |   C: show collision model", 15, 60, 10, BLACK)
    draw_text("- Zoom keys: num-plus, num-minus or mouse scroll", 15, 75, 10, BLACK)
    draw_text("- Camera projection key: P", 15, 90, 10, BLACK)

    draw_rectangle(600, 5, 195, 130, fade(SKYBLUE, 0.5))
    draw_rectangle_lines(600, 5, 195, 130, BLUE)

    proj = "PERSPECTIVE" if camera.projection == CameraProjection.CAMERA_PERSPECTIVE else \
           "ORTHOGRAPHIC" if camera.projection == CameraProjection.CAMERA_ORTHOGRAPHIC else "CUSTOM"
    p, t, u = camera.position, camera.target, camera.up

    draw_text("Camera status:", 610, 15, 10, BLACK)
    draw_text(f"- Mode: {mode_names.get(camera_mode, 'CUSTOM')}", 610, 30, 10, BLACK)
    draw_text(f"- Projection: {proj}", 610, 45, 10, BLACK)
    draw_text(f"- Position: ({p.x:06.3f}, {p.y:06.3f}, {p.z:06.3f})", 610, 60, 10, BLACK)
    draw_text(f"- Target: ({t.x:06.3f}, {t.y:06.3f}, {t.z:06.3f})", 610, 75, 10, BLACK)
    draw_text(f"- Up: ({u.x:06.3f}, {u.y:06.3f}, {u.z:06.3f})", 610, 90, 10, BLACK)
    draw_text(f"- Colliding: {colliding}", 610, 105, 10, RED if colliding else BLACK)
    draw_text(f"- On ground: {on_ground}", 610, 120, 10, BLACK)

    draw_fps(10, 145)

    end_drawing()

unload_model(model)
unload_model(col_model)
close_window()