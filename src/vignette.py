"""Vignette: darkens the edges of the screen (Shaders/vignette.fs).

    vignette = Vignette()   # after init_window
    vignette.draw()         # every frame, after the 3D scene and before the HUD
    vignette.draw(pr.Color(120, 0, 0, 255), strength=1.0)   # e.g. a red flash, or stronger as sanity drops

Drawn as a full-screen rectangle with the shader on top of what is already drawn, so no render texture is needed.
"""
from __future__ import annotations

import pyray as pr

from .config import SHADERS_DIR, VIGNETTE_COLOR, VIGNETTE_RADIUS, VIGNETTE_SOFTNESS, VIGNETTE_STRENGTH


class Vignette:
    """Needs an open window (load_shader needs a GL context)."""

    def __init__(self) -> None:
        # no vertex shader (NULL; pyray doesn't take None): raylib's default one passes the rectangle's colour
        # through as fragColor
        self.shader: pr.Shader = pr.load_shader(pr.ffi.NULL, str(SHADERS_DIR / "vignette.fs"))
        self._resolution_loc: int = pr.get_shader_location(self.shader, "resolution")
        for name, value in (("radius", VIGNETTE_RADIUS), ("softness", VIGNETTE_SOFTNESS)):
            pr.set_shader_value(self.shader, pr.get_shader_location(self.shader, name), pr.ffi.new("float *", value),
                                pr.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)

    def draw(self, color: pr.Color = VIGNETTE_COLOR, strength: float = VIGNETTE_STRENGTH) -> None:
        """Darken the edges towards `color`; strength 0 = nothing, 1 = full colour at the corners."""
        if strength <= 0:
            return
        # gl_FragCoord counts framebuffer pixels, which can differ from the screen size (fullscreen, high DPI)
        w, h = pr.get_render_width(), pr.get_render_height()
        pr.set_shader_value(self.shader, self._resolution_loc, pr.ffi.new("float[2]", [w, h]),
                            pr.ShaderUniformDataType.SHADER_UNIFORM_VEC2)
        r, g, b = (color.r, color.g, color.b) if hasattr(color, "r") else tuple(color)[:3]
        pr.begin_shader_mode(self.shader)
        pr.draw_rectangle(0, 0, pr.get_screen_width(), pr.get_screen_height(),
                          pr.Color(r, g, b, int(255 * min(strength, 1.0))))
        pr.end_shader_mode()

    def unload(self) -> None:
        pr.unload_shader(self.shader)
