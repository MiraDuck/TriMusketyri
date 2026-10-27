"""Drawing: the 3D scene and the HUD."""
from pyray import *

MODE_NAMES = {
    CameraMode.CAMERA_FREE: "FREE",
    CameraMode.CAMERA_FIRST_PERSON: "FIRST_PERSON",
    CameraMode.CAMERA_THIRD_PERSON: "THIRD_PERSON",
    CameraMode.CAMERA_ORBITAL: "ORBITAL",
}

def draw_scene(view_camera, camera, camera_mode, player, model, world, show_col):
    """view_camera is what we render from; camera is the player's real camera."""
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
        draw_model(model, world.pos, 1.0, WHITE)
        draw_model_wires(model, world.pos, 1.0, BLACK)
        draw_bounding_box(world.bounds, GREEN)
    else:
        draw_model(world.model, world.pos, 1.0, WHITE)
        draw_model_wires(world.model, world.pos, 1.0, RED)

    if camera_mode != CameraMode.CAMERA_FIRST_PERSON:
        _, pbox = player.box()
        draw_bounding_box(pbox, ORANGE)

    end_mode_3d()


def draw_hud(camera, camera_mode, player):
    # draw_rectangle(5, 5, 330, 100, fade(SKYBLUE, 0.5))
    # draw_rectangle_lines(5, 5, 330, 100, BLUE)

    # draw_text("Camera controls:", 15, 15, 10, BLACK)
    # draw_text("- Move keys: W, A, S, D, Space, Left-Ctrl", 15, 30, 10, BLACK)
    # draw_text("- Look around: arrow keys or mouse", 15, 45, 10, BLACK)
    # draw_text("- Camera mode keys: 1, 2, 3, 4   |   C: show collision model", 15, 60, 10, BLACK)
    # draw_text("- Zoom keys: num-plus, num-minus or mouse scroll", 15, 75, 10, BLACK)
    # draw_text("- Camera projection key: P", 15, 90, 10, BLACK)

    draw_rectangle(600, 5, 195, 130, fade(SKYBLUE, 0.5))
    draw_rectangle_lines(600, 5, 195, 130, BLUE)

    proj = "PERSPECTIVE" if camera.projection == CameraProjection.CAMERA_PERSPECTIVE else \
           "ORTHOGRAPHIC" if camera.projection == CameraProjection.CAMERA_ORTHOGRAPHIC else "CUSTOM"
    p, t, u = camera.position, camera.target, camera.up

    draw_text("Camera status:", 610, 15, 10, BLACK)
    draw_text(f"- Mode: {MODE_NAMES.get(camera_mode, 'CUSTOM')}", 610, 30, 10, BLACK)
    draw_text(f"- Projection: {proj}", 610, 45, 10, BLACK)
    draw_text(f"- Position: ({p.x:06.3f}, {p.y:06.3f}, {p.z:06.3f})", 610, 60, 10, BLACK)
    draw_text(f"- Target: ({t.x:06.3f}, {t.y:06.3f}, {t.z:06.3f})", 610, 75, 10, BLACK)
    draw_text(f"- Up: ({u.x:06.3f}, {u.y:06.3f}, {u.z:06.3f})", 610, 90, 10, BLACK)
    draw_text(f"- Colliding: {player.colliding}", 610, 105, 10, RED if player.colliding else BLACK)
    draw_text(f"- On ground: {player.on_ground}", 610, 120, 10, BLACK)

    draw_fps(10, 145)
