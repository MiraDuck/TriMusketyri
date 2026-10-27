import math
from pyray import *

MAX_COLUMNS = 20

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

model = load_model("test.obj")
print(is_model_valid(model))   # older raylib versions: is_model_ready

print("meshes:", model.meshCount, "materials:", model.materialCount)
for i in range(model.meshCount):
    m = model.meshes[i]
    print(i, "verts:", m.vertexCount, "tris:", m.triangleCount)

bb = get_model_bounding_box(model)
print("min:", bb.min.x, bb.min.y, bb.min.z)
print("max:", bb.max.x, bb.max.y, bb.max.z)

rl_set_line_width(2)

while not window_should_close():
    # ---- Update ----
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

    update_camera(camera, camera_mode)

    # ---- Draw ----
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

    draw_model(model, Vector3(0, 1, 0), 1.0, WHITE)
    draw_model_wires(model, Vector3(0, 1, 0), 1.0, BLACK)
    draw_bounding_box(bb, GREEN)

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

    draw_rectangle(600, 5, 195, 100, fade(SKYBLUE, 0.5))
    draw_rectangle_lines(600, 5, 195, 100, BLUE)

    proj = "PERSPECTIVE" if camera.projection == CameraProjection.CAMERA_PERSPECTIVE else \
           "ORTHOGRAPHIC" if camera.projection == CameraProjection.CAMERA_ORTHOGRAPHIC else "CUSTOM"
    p, t, u = camera.position, camera.target, camera.up

    draw_text("Camera status:", 610, 15, 10, BLACK)
    draw_text(f"- Mode: {mode_names.get(camera_mode, 'CUSTOM')}", 610, 30, 10, BLACK)
    draw_text(f"- Projection: {proj}", 610, 45, 10, BLACK)
    draw_text(f"- Position: ({p.x:06.3f}, {p.y:06.3f}, {p.z:06.3f})", 610, 60, 10, BLACK)
    draw_text(f"- Target: ({t.x:06.3f}, {t.y:06.3f}, {t.z:06.3f})", 610, 75, 10, BLACK)
    draw_text(f"- Up: ({u.x:06.3f}, {u.y:06.3f}, {u.z:06.3f})", 610, 90, 10, BLACK)

    end_drawing()

close_window()