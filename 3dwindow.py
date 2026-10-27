import math
from pyray import *

SCREEN_W = 1600
SCREEN_H = 900

set_trace_log_level(TraceLogLevel.LOG_WARNING)
init_window(SCREEN_W, SCREEN_H, "raylib [core] example - 3d camera first person")

toggle_fullscreen()

camera = Camera3D(
    Vector3(0.0, 2.5, 4.0),   # position
    Vector3(0.0, 2.5, 0.0),   # target
    Vector3(0.0, 1.0, 0.0),   # up
    60.0,                     # fovy
    CameraProjection.CAMERA_PERSPECTIVE,       # projection
)

camera_mode = CameraMode.CAMERA_FIRST_PERSON

disable_cursor()
set_target_fps(60)

mode_names = {
    CameraMode.CAMERA_FREE: "FREE",
    CameraMode.CAMERA_FIRST_PERSON: "FIRST_PERSON",
    CameraMode.CAMERA_THIRD_PERSON: "THIRD_PERSON",
    CameraMode.CAMERA_ORBITAL: "ORBITAL",
}

# ---------------- Model ----------------
MODEL_POS = Vector3(0, 1, 0)

model = load_model("test.obj")
print(is_model_valid(model))

print("meshes:", model.meshCount, "materials:", model.materialCount)
for i in range(model.meshCount):
    m = model.meshes[i]
    print(i, "verts:", m.vertexCount, "tris:", m.triangleCount)

bb = get_model_bounding_box(model)
print("min:", bb.min.x, bb.min.y, bb.min.z)
print("max:", bb.max.x, bb.max.y, bb.max.z)

# Bounding box moved to where the model is actually drawn
world_bb = BoundingBox(
    Vector3(bb.min.x + MODEL_POS.x, bb.min.y + MODEL_POS.y, bb.min.z + MODEL_POS.z),
    Vector3(bb.max.x + MODEL_POS.x, bb.max.y + MODEL_POS.y, bb.max.z + MODEL_POS.z),
)

# # ---------------- Player cuboid ----------------
# PLAYER_HALF = Vector3(0.4, 1.25, 0.4)   # half-size of the cuboid on each axis
# EYE_TO_CENTER = 1.0                      # box center sits this far below the camera

# # Directions we probe from the box center, with the box half-size on that axis
# PROBES = [
#     (Vector3(1, 0, 0),  PLAYER_HALF.x),
#     (Vector3(-1, 0, 0), PLAYER_HALF.x),
#     (Vector3(0, 0, 1),  PLAYER_HALF.z),
#     (Vector3(0, 0, -1), PLAYER_HALF.z),
#     (Vector3(0, 1, 0),  PLAYER_HALF.y),
#     (Vector3(0, -1, 0), PLAYER_HALF.y),
# ]


# def player_box(cam):
#     c = Vector3(cam.position.x, cam.position.y - EYE_TO_CENTER, cam.position.z)
#     box = BoundingBox(
#         Vector3(c.x - PLAYER_HALF.x, c.y - PLAYER_HALF.y, c.z - PLAYER_HALF.z),
#         Vector3(c.x + PLAYER_HALF.x, c.y + PLAYER_HALF.y, c.z + PLAYER_HALF.z),
#     )
#     return c, box


# def distance_to_model(origin, direction):
#     """Closest hit distance of a ray against the model, or None."""
#     # The model is drawn at MODEL_POS, so shift the ray into model space
#     ray = Ray(
#         Vector3(origin.x - MODEL_POS.x, origin.y - MODEL_POS.y, origin.z - MODEL_POS.z),
#         direction,
#     )
#     best = None
#     for i in range(model.meshCount):
#         hit = get_ray_collision_mesh(ray, model.meshes[i], matrix_identity())
#         if hit.hit and (best is None or hit.distance < best):
#             best = hit.distance
#     return best


# def resolve_collision(cam):
#     """Push the camera out of the model. Returns True if we were touching it."""
#     c, box = player_box(cam)

#     # Broadphase: skip all triangle tests if we're nowhere near the model
#     if not check_collision_boxes(box, world_bb):
#         return False

#     push = Vector3(0, 0, 0)
#     touched = False
#     for d, half in PROBES:
#         dist = distance_to_model(c, d)
#         if dist is not None and dist < half:
#             depth = half - dist
#             push.x -= d.x * depth
#             push.y -= d.y * depth
#             push.z -= d.z * depth
#             touched = True

#     if touched:
#         # Move position AND target together so the view direction doesn't change
#         cam.position = Vector3(cam.position.x + push.x, cam.position.y + push.y, cam.position.z + push.z)
#         cam.target = Vector3(cam.target.x + push.x, cam.target.y + push.y, cam.target.z + push.z)
#     return touched


rl_set_line_width(2)
# colliding = False

while not window_should_close():
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

    if is_key_pressed(KeyboardKey.KEY_P):
        if camera.projection == CameraProjection.CAMERA_PERSPECTIVE:
            # Isometric view (placed manually: 45 deg diagonal, 45 deg down, distance 100)
            camera_mode = CameraMode.CAMERA_THIRD_PERSON
            camera.target = Vector3(0.0, 2.0, 0.0)
            camera.position = Vector3(50.0, 2.0 + 100.0 * math.sin(math.radians(45)), 50.0)
            camera.up = Vector3(0.0, 1.0, 0.0)
            camera.projection = CameraProjection.CAMERA_ORTHOGRAPHIC
            camera.fovy = 20.0
        elif camera.projection == CameraProjection.CAMERA_ORTHOGRAPHIC:
            # Back to default view
            camera_mode = CameraMode.CAMERA_THIRD_PERSON
            camera.position = Vector3(0.0, 2.0, 10.0)
            camera.target = Vector3(0.0, 2.0, 0.0)
            camera.up = Vector3(0.0, 1.0, 0.0)
            camera.projection = CameraProjection.CAMERA_PERSPECTIVE
            camera.fovy = 60.0

    # update_camera(camera, camera_mode)
    update_camera_pro(camera,
            (
                (is_key_down(KeyboardKey.KEY_W) or is_key_down(KeyboardKey.KEY_UP))*0.1 -
                (is_key_down(KeyboardKey.KEY_S) or is_key_down(KeyboardKey.KEY_DOWN))*0.1,
                (is_key_down(KeyboardKey.KEY_D) or is_key_down(KeyboardKey.KEY_RIGHT))*0.1 -
                (is_key_down(KeyboardKey.KEY_A) or is_key_down(KeyboardKey.KEY_LEFT))*0.1,
                0.0
            ),
            (
                get_mouse_delta().x*0.05,
                get_mouse_delta().y*0.05,
                0.0
            ),
            get_mouse_wheel_move()*2.0)

    # # Collision only makes sense where the camera IS the player
    # if camera_mode == CameraMode.CAMERA_FIRST_PERSON:
    #     colliding = resolve_collision(camera)
    # else:
    #     colliding = False

    begin_drawing()
    clear_background(RAYWHITE)

    begin_mode_3d(camera)

    draw_plane(Vector3(0.0, 0.0, 0.0), Vector2(32.0, 32.0), LIGHTGRAY)
    draw_cube(Vector3(-16.0, 2.5, 0.0), 1.0, 5.0, 32.0, BLUE)
    draw_cube(Vector3(16.0, 2.5, 0.0), 1.0, 5.0, 32.0, LIME)
    draw_cube(Vector3(0.0, 2.5, 16.0), 32.0, 5.0, 1.0, GOLD)
    draw_cube(Vector3(0.0, 2.5, -16.0), 32.0, 5.0, 1.0, RED)

    if camera_mode == CameraMode.CAMERA_THIRD_PERSON:
        draw_cube(camera.target, 0.5, 0.5, 0.5, PURPLE)
        draw_cube_wires(camera.target, 0.5, 0.5, 0.5, DARKPURPLE)

    draw_model(model, MODEL_POS, 1.0, WHITE)
    draw_model_wires(model, MODEL_POS, 1.0, BLACK)
    draw_bounding_box(world_bb, GREEN)

    # Debug: show the player cuboid (visible when you leave first person)
    # if camera_mode != CameraMode.CAMERA_FIRST_PERSON:
    #     _, pbox = player_box(camera)
    #     draw_bounding_box(pbox, ORANGE)

    end_mode_3d()

    # Info boxes
    draw_rectangle(5, 5, 330, 100, fade(SKYBLUE, 0.5))
    draw_rectangle_lines(5, 5, 330, 100, BLUE)

    draw_text("Camera controls:", 15, 15, 10, BLACK)
    draw_text("- Move keys: W, A, S, D, Space, Left-Ctrl", 15, 30, 10, BLACK)
    draw_text("- Look around: arrow keys or mouse", 15, 45, 10, BLACK)
    draw_text("- Camera mode keys: 1, 2, 3, 4", 15, 60, 10, BLACK)
    draw_text("- Zoom keys: num-plus, num-minus or mouse scroll", 15, 75, 10, BLACK)
    draw_text("- Camera projection key: P", 15, 90, 10, BLACK)

    draw_rectangle(600, 5, 195, 115, fade(SKYBLUE, 0.5))
    draw_rectangle_lines(600, 5, 195, 115, BLUE)

    proj = "PERSPECTIVE" if camera.projection == CameraProjection.CAMERA_PERSPECTIVE else \
           "ORTHOGRAPHIC" if camera.projection == CameraProjection.CAMERA_ORTHOGRAPHIC else "CUSTOM"
    p, t, u = camera.position, camera.target, camera.up

    draw_text("Camera status:", 610, 15, 10, BLACK)
    draw_text(f"- Mode: {mode_names.get(camera_mode, 'CUSTOM')}", 610, 30, 10, BLACK)
    draw_text(f"- Projection: {proj}", 610, 45, 10, BLACK)
    draw_text(f"- Position: ({p.x:06.3f}, {p.y:06.3f}, {p.z:06.3f})", 610, 60, 10, BLACK)
    draw_text(f"- Target: ({t.x:06.3f}, {t.y:06.3f}, {t.z:06.3f})", 610, 75, 10, BLACK)
    draw_text(f"- Up: ({u.x:06.3f}, {u.y:06.3f}, {u.z:06.3f})", 610, 90, 10, BLACK)
    # draw_text(f"- Colliding: {colliding}", 610, 105, 10, RED if colliding else BLACK)

    draw_fps(10, 120)

    end_drawing()

unload_model(model)
close_window()