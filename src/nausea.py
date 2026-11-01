"""Nausea: the view sways and the picture warps while the oxygen or the temperature is off. Only what you see: the
real camera (aiming, collision) isn't touched.

    nausea = Nausea()                   # after init_window
    nausea.update(dt, life.sickness)    # every frame
    view = nausea.apply(view)           # a copy of the camera, swaying (like HeadBob.apply)
    nausea.begin()                      # after begin_drawing, before the scene
    nausea.end()                        # after the scene: draws it warped (Shaders/nausea.fs)
    nausea.unload()

While you feel fine `begin` and `end` do nothing and the scene goes straight to the screen. While you are sick it
goes into a render texture of the screen's size, which `end` draws through the shader.
"""
from __future__ import annotations

import math

import pyray as pr

from .config import (
    NAUSEA_CURVE, NAUSEA_DOUBLE, NAUSEA_FALL, NAUSEA_FOV, NAUSEA_LOOK, NAUSEA_RISE, NAUSEA_ROLL, NAUSEA_SPEED,
    NAUSEA_SWAY, NAUSEA_WARP, SHADERS_DIR,
)
from .head_bob import smooth

FEELS_FINE: float = 0.01   # below this nothing is drawn differently


class Nausea:
    """Needs an open window (load_shader needs a GL context)."""

    def __init__(self) -> None:
        self.amount: float = 0.0   # 0..1, eases towards the sickness ^ NAUSEA_CURVE
        self.forced: bool = False
        self.clock: float = 0.0
        self.target: pr.RenderTexture | None = None
        self._warping: bool = False
        self.shader: pr.Shader = pr.load_shader(pr.ffi.NULL, str(SHADERS_DIR / "nausea.fs"))
        self._time_loc: int = pr.get_shader_location(self.shader, "time")
        self._amount_loc: int = pr.get_shader_location(self.shader, "amount")
        for name, value in (("warp", NAUSEA_WARP), ("ghosting", NAUSEA_DOUBLE)):
            self._set(pr.get_shader_location(self.shader, name), value)

    def _set(self, location: int, value: float) -> None:
        pr.set_shader_value(self.shader, location, pr.ffi.new("float *", value),
                            pr.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)

    def update(self, dt: float, sickness: float) -> None:
        self.clock += dt
        goal = 1.0 if self.forced else sickness ** NAUSEA_CURVE
        self.amount += (goal - self.amount) * smooth(NAUSEA_RISE if goal > self.amount else NAUSEA_FALL, dt)

    def apply(self, cam: pr.Camera3D) -> pr.Camera3D:
        """A copy of `cam`, swaying: slow swings that never quite repeat, so your eyes can't settle on them."""
        if self.amount < FEELS_FINE:
            return cam
        t, a = self.clock * NAUSEA_SPEED, self.amount
        fwd = pr.vector3_normalize(pr.vector3_subtract(cam.target, cam.position))
        right = pr.vector3_normalize(pr.vector3_cross_product(fwd, pr.Vector3(0, 1, 0)))
        look = pr.vector3_rotate_by_axis_angle(fwd, right, math.radians(NAUSEA_LOOK) * a * math.sin(t * 1.37))
        look = pr.vector3_rotate_by_axis_angle(look, pr.Vector3(0, 1, 0), math.radians(NAUSEA_LOOK) * a * math.sin(t * 0.73))
        roll = math.radians(NAUSEA_ROLL) * a * (0.7 * math.sin(t) + 0.3 * math.sin(t * 2.3))
        up = pr.vector3_rotate_by_axis_angle(cam.up, look, roll)
        pos = pr.vector3_add(cam.position, pr.vector3_scale(right, NAUSEA_SWAY * a * math.sin(t * 0.91)))
        fovy = cam.fovy + NAUSEA_FOV * a * math.sin(t * 0.61)
        return pr.Camera3D(pos, pr.vector3_add(pos, look), up, fovy, cam.projection)

    def begin(self) -> None:
        """The scene goes into the texture from here, while you are sick."""
        self._warping = self.amount >= FEELS_FINE
        if not self._warping:
            return
        # framebuffer pixels, like the vignette (it can differ from the screen size); F11 changes them
        w, h = pr.get_render_width(), pr.get_render_height()
        if self.target is None or (self.target.texture.width, self.target.texture.height) != (w, h):
            if self.target is not None:
                pr.unload_render_texture(self.target)
            self.target = pr.load_render_texture(w, h)
            pr.set_texture_filter(self.target.texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
            pr.set_texture_wrap(self.target.texture, pr.TextureWrap.TEXTURE_WRAP_CLAMP)   # bent past the edge
        pr.begin_texture_mode(self.target)

    def end(self) -> None:
        if not self._warping:
            return
        pr.end_texture_mode()
        self._set(self._time_loc, self.clock)
        self._set(self._amount_loc, self.amount)
        texture = self.target.texture
        pr.begin_shader_mode(self.shader)
        # a render texture is stored upside down
        pr.draw_texture_pro(texture, pr.Rectangle(0, 0, texture.width, -texture.height),
                            pr.Rectangle(0, 0, pr.get_screen_width(), pr.get_screen_height()),
                            pr.Vector2(0, 0), 0.0, pr.WHITE)
        pr.end_shader_mode()

    def unload(self) -> None:
        if self.target is not None:
            pr.unload_render_texture(self.target)
        pr.unload_shader(self.shader)
