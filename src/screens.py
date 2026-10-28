"""Screens: the control room console's displays.

    screens = Screens(control_room.pos)          # after init_window
    screens.update(dt, depth, rate, speed, on)   # every frame, before begin_drawing (renders the depth panel)
    screens.draw()                               # inside 3D mode, after the scene
    screens.unload()

Each is a quad drawn just in front of the room model's own panel (DRILL_SCREEN_CORNERS / DEPTH_PANEL_CORNERS), not
lit by the lamps: they glow on their own, also in a dark car. Off (black) once the engine is dead.
- Drill screen (the green grid left of the vertical depth gauge): drill_1..4 cycled, as fast as the engine turns
  (DRILL_SCREEN_FPS at full speed, standing still when it stops). Cropped to the screen's proportions.
- Depth panel (the black panel right of the gauge): "HLOUBKA", the depth in metres and how fast it digs, drawn into
  a render texture.
"""
from __future__ import annotations

import pyray as pr

from .config import (
    DEPTH_PANEL_CORNERS, DEPTH_PANEL_SIZE, DRILL_SCREEN_CORNERS, DRILL_SCREEN_FPS, DRILL_SCREEN_FRAMES, SCREEN_BLACK,
    SCREEN_GREEN,
)


def _quad(corners: list[pr.Vector3], texture_id: int, uvs: tuple[tuple[float, float], ...],
          color: pr.Color = pr.WHITE) -> None:
    """corners: top left, top right, bottom right, bottom left; uvs the same corners' texture coordinates."""
    pr.rl_disable_backface_culling()
    pr.rl_set_texture(texture_id)
    pr.rl_begin(pr.RL_QUADS)
    r, g, b, alpha = (color.r, color.g, color.b, color.a) if hasattr(color, "r") else color   # pr.WHITE is a tuple
    pr.rl_color4ub(r, g, b, alpha)
    for i in (0, 3, 2, 1):   # counter-clockwise as you look at it
        pr.rl_tex_coord2f(*uvs[i])
        pr.rl_vertex3f(corners[i].x, corners[i].y, corners[i].z)
    pr.rl_end()
    pr.rl_set_texture(0)
    pr.rl_enable_backface_culling()


class Screens:
    def __init__(self, car_pos: pr.Vector3) -> None:
        self.frames: list[pr.Texture] = [pr.load_texture(str(path)) for path in DRILL_SCREEN_FRAMES]
        self.panel: pr.RenderTexture = pr.load_render_texture(*DEPTH_PANEL_SIZE)
        for texture in [*self.frames, self.panel.texture]:
            pr.set_texture_filter(texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
        self.drill_corners = [pr.vector3_add(car_pos, c) for c in DRILL_SCREEN_CORNERS]
        self.panel_corners = [pr.vector3_add(car_pos, c) for c in DEPTH_PANEL_CORNERS]
        self.frame: float = 0.0
        self.on: bool = True
        # crop the frames to the screen's proportions (top / bottom cut off evenly)
        width = pr.vector3_distance(self.drill_corners[0], self.drill_corners[1])
        height = pr.vector3_distance(self.drill_corners[0], self.drill_corners[3])
        image = self.frames[0]
        keep = min(1.0, (image.width / image.height) / (width / height))
        top, bottom = (1 - keep) / 2, (1 + keep) / 2
        self._drill_uvs = ((0.0, top), (1.0, top), (1.0, bottom), (0.0, bottom))

    def update(self, dt: float, depth: float, rate: float, speed: float, on: bool) -> None:
        """`rate`: metres / s it digs now; `speed`: the engine's (0..1) runs the drill animation."""
        self.on = on
        self.frame = (self.frame + DRILL_SCREEN_FPS * speed * dt) % len(self.frames)
        w, h = DEPTH_PANEL_SIZE

        def centered(msg: str, y: float, size: int, color: pr.Color = SCREEN_GREEN) -> None:
            while size > 10 and pr.measure_text(msg, size) > w - 20:   # shrink a long number to fit
                size -= 2
            pr.draw_text(msg, (w - pr.measure_text(msg, size)) // 2, int(y - size / 2), size, color)

        pr.begin_texture_mode(self.panel)
        pr.clear_background(SCREEN_BLACK)
        dim = pr.fade(SCREEN_GREEN, 0.25)
        for x in range(0, w, 31):   # the grid of the other screen
            pr.draw_line(x, 0, x, h, dim)
        for y in range(0, h, 31):
            pr.draw_line(0, y, w, y, dim)
        centered("HLOUBKA", 45, 36)
        centered(f"{depth:.0f}", h / 2, 80)
        centered("m", h / 2 + 65, 36)
        centered(f"{rate:.1f} m/s", h - 45, 28)
        pr.end_texture_mode()

    def draw(self) -> None:
        if not self.on:
            for corners in (self.drill_corners, self.panel_corners):
                _quad(corners, 0, ((0, 0),) * 4, pr.BLACK)
            return
        _quad(self.drill_corners, self.frames[int(self.frame)].id, self._drill_uvs)
        # a render texture is stored upside down
        _quad(self.panel_corners, self.panel.texture.id, ((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)))

    def unload(self) -> None:
        for texture in self.frames:
            pr.unload_texture(texture)
        pr.unload_render_texture(self.panel)
