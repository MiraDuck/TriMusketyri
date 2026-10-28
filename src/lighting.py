"""Lighting: dynamic cel-shaded point lights (Shaders/lit.vs + lit.fs) and the lamps they hang in.

    lamp = Lamp("lamp_control_room", pr.Vector3(0, 4.16, 0), zone=(-4, 4))   # lamp model + its Light
    lamp.light.on = False           # its car goes dark (LIGHT_DARK)
    lighting = Lighting([lamp.light])
    lighting.add(entity.model)      # this model is now lit
    lamp.update(pr.get_time())      # every frame: lamp glows while its light is on
    lighting.update(pr.get_time())  # every frame, before drawing

Only models passed to `add()` are lit; everything else draws with raylib's default (unlit) shader.
`set_enabled(False)` puts the default shaders back.

Each light only lights its `zone` (a z range: its car), since there are no shadows to stop it at the walls.
A lamp's light also has `fill`: it lifts its whole car from LIGHT_DARK to LIGHT_AMBIENT while it is on (tinted by
`fill_color`, white normally). `lamp.set_alarm(True)` makes a lamp flash red and its car with it.
"""
from __future__ import annotations

import pyray as pr

from .config import (
    ALARM_BLINK, ALARM_COLOR, ALARM_FILL_COLOR, FOG_COLOR, FOG_DENSITY, LAMP_COLOR, LAMP_INTENSITY, LAMP_LIGHT_DROP,
    LAMP_MODEL, LAMP_RANGE, LIGHT_AMBIENT, LIGHT_BANDS, LIGHT_DARK, SHADERS_DIR,
)
from .entity import Entity

MAX_LIGHTS: int = 8   # keep in sync with MAX_LIGHTS in lit.fs
LAMP_ON_TINT: pr.Color = pr.WHITE      # a shining lamp is drawn full bright, brighter than the lit room around it
_DARK = round(255 * LIGHT_DARK)
LAMP_OFF_TINT: pr.Color = pr.Color(_DARK, _DARK, _DARK, 255)   # as dark as the unlit car around it
EVERYWHERE: tuple[float, float] = (-1e9, 1e9)


class Light:
    """A point light. `blink` = blinks per second (0 = steady). Switch it with `on`.
    It only lights `zone` (z from .. to, its car), and adds `fill` (times `fill_color`) to all of it while on."""

    def __init__(
        self,
        pos: pr.Vector3,
        color: pr.Color | tuple[int, int, int, int],
        intensity: float = 1.0,
        range: float = 8.0,
        blink: float = 0.0,
        zone: tuple[float, float] = EVERYWHERE,
        fill: float = 0.0,
    ) -> None:
        self.pos: pr.Vector3 = pos
        # pyray's named colours (pr.RED) are tuples, pr.Color(...) is a struct: keep it as a tuple either way
        self.color: tuple[int, int, int, int] = (
            (color.r, color.g, color.b, color.a) if hasattr(color, "r") else tuple(color)
        )
        self.intensity: float = intensity
        self.range: float = range
        self.blink: float = blink
        self.zone: tuple[float, float] = zone
        self.fill: float = fill
        self.fill_color: tuple[float, float, float] = (1.0, 1.0, 1.0)
        self.on: bool = True

    def strength(self, time: float) -> float:
        # blinking: (time * blink) % 1 runs 0..1 once per blink; the light is off for the second half
        if not self.on or (self.blink and (time * self.blink) % 1.0 >= 0.5):
            return 0.0
        return self.intensity


class Lamp(Entity):
    """A ceiling lamp: the lamp model hanging from `pos` with its Light inside the shade (`.light`).
    Don't add the lamp model to Lighting: it is the light source, so it is drawn unlit, full bright while its light
    shines and dark while it is off (switched off, or the dark half of a blink). Not solid.
    `zone` is its car's z range: the light fills it (LIGHT_AMBIENT) and doesn't reach past it.
    `set_alarm(True)`: the light flashes red (ALARM_COLOR, ALARM_BLINK times / s) and tints its car red, while it is
    on (a lamp switched off by its breaker stays dark); `set_alarm(False)` puts its own colour back."""

    def __init__(
        self,
        name: str,
        pos: pr.Vector3,
        color: pr.Color | tuple[int, int, int, int] = LAMP_COLOR,
        intensity: float = LAMP_INTENSITY,
        range: float = LAMP_RANGE,
        blink: float = 0.0,
        zone: tuple[float, float] = EVERYWHERE,
    ) -> None:
        super().__init__(name, LAMP_MODEL, pos)
        self.light: Light = Light(pr.Vector3(pos.x, pos.y - LAMP_LIGHT_DROP, pos.z), color, intensity, range, blink,
                                  zone, fill=LIGHT_AMBIENT - LIGHT_DARK)
        self.alarm: bool = False
        self._normal: tuple[tuple[int, int, int, int], float] = (self.light.color, self.light.blink)

    def set_alarm(self, on: bool) -> None:
        if on == self.alarm:
            return
        self.alarm = on
        light = self.light
        if on:
            self._normal = (light.color, light.blink)
            light.color = (ALARM_COLOR.r, ALARM_COLOR.g, ALARM_COLOR.b, ALARM_COLOR.a)
            light.blink = ALARM_BLINK
            light.fill_color = ALARM_FILL_COLOR
        else:
            light.color, light.blink = self._normal
            light.fill_color = (1.0, 1.0, 1.0)

    def update(self, time: float) -> None:
        if self.light.strength(time) <= 0:
            self.tint = LAMP_OFF_TINT
        else:   # glows in its light's colour while in an alarm
            self.tint = pr.Color(*self.light.color) if self.alarm else LAMP_ON_TINT

    def debug_lines(self) -> list[str]:
        light = self.light
        return super().debug_lines() + [
            f"light: {'on' if light.on else 'off'}, colour {light.color}, intensity {light.intensity:g}, "
            f"range {light.range:g}, blink {light.blink:g}/s",
            f"lights z {light.zone[0]:g} .. {light.zone[1]:g}, fill {light.fill:g}" + (", ALARM" if self.alarm else ""),
        ]


class Lighting:
    """Needs an open window (load_shader needs a GL context)."""

    def __init__(self, lights: list[Light]) -> None:
        if len(lights) > MAX_LIGHTS:
            raise ValueError(f"at most {MAX_LIGHTS} lights, got {len(lights)}")
        self.lights: list[Light] = lights
        self.enabled: bool = True
        self.shader: pr.Shader = pr.load_shader(str(SHADERS_DIR / "lit.vs"), str(SHADERS_DIR / "lit.fs"))
        # where each uniform lives in the shader; for an array (lightPos[8]) it is the location of element 0
        self._loc: dict[str, int] = {
            name: pr.get_shader_location(self.shader, name)
            for name in ("lightCount", "lightPos", "lightColor", "lightRange", "lightZone", "lightFill", "ambient",
                         "bands", "viewPos", "fogColor", "fogDensity")
        }
        self._set_float("ambient", LIGHT_DARK)   # the lamps' fill brings their cars up to LIGHT_AMBIENT
        self._set_float("bands", LIGHT_BANDS)
        self._set_float("fogDensity", FOG_DENSITY)
        self._set_vec("fogColor", FOG_COLOR)
        self.set_fog(pr.Vector3(0.0, 0.0, 0.0))
        # each lit model with copies of its original shaders, to put back when disabled
        self._models: list[tuple[pr.Model, list[pr.Shader]]] = []

    def _set_float(self, name: str, value: float) -> None:
        pr.set_shader_value(self.shader, self._loc[name], pr.ffi.new("float *", value),
                            pr.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)

    def _set_vec(self, name: str, value: tuple[float, ...]) -> None:
        kind = {2: pr.ShaderUniformDataType.SHADER_UNIFORM_VEC2, 3: pr.ShaderUniformDataType.SHADER_UNIFORM_VEC3}
        pr.set_shader_value(self.shader, self._loc[name], pr.ffi.new("float[]", list(value)), kind[len(value)])

    def set_fog(self, view_pos: pr.Vector3) -> None:
        """Every frame: where the camera is (the fog grows with distance from it)."""
        self._set_vec("viewPos", (view_pos.x, view_pos.y, view_pos.z))

    def _set_shaders(self, model: pr.Model, shaders: list[pr.Shader]) -> None:
        for i, shader in enumerate(shaders):
            model.materials[i].shader = shader

    def add(self, model: pr.Model) -> None:
        # A model draws each material with that material's shader, so "lit" = our shader on every material.
        # Copy the originals: model.materials[i].shader is a view into the model and would change with it.
        defaults = [pr.Shader(m.shader.id, m.shader.locs) for m in model.materials[0:model.materialCount]]
        self._models.append((model, defaults))
        if self.enabled:
            self._set_shaders(model, [self.shader] * model.materialCount)

    def set_enabled(self, enabled: bool) -> None:
        if enabled == self.enabled:
            return
        self.enabled = enabled
        for model, defaults in self._models:
            self._set_shaders(model, [self.shader] * model.materialCount if enabled else defaults)

    def update(self, time: float) -> None:
        """Send the lights to the shader (positions, colours, blinking)."""
        if not self.enabled:
            return
        positions, colors, ranges, zones, fills = [], [], [], [], []
        for light in self.lights:
            strength = light.strength(time)
            positions += [light.pos.x, light.pos.y, light.pos.z]
            colors += [c * strength / 255.0 for c in light.color[:3]]
            ranges.append(light.range)
            zones += list(light.zone)
            fills += [c * light.fill if strength > 0 else 0.0 for c in light.fill_color]
        n = len(self.lights)
        vec3 = pr.ShaderUniformDataType.SHADER_UNIFORM_VEC3
        pr.set_shader_value(self.shader, self._loc["lightCount"], pr.ffi.new("int *", n),
                            pr.ShaderUniformDataType.SHADER_UNIFORM_INT)
        if n:
            pr.set_shader_value_v(self.shader, self._loc["lightPos"], pr.ffi.new("float[]", positions), vec3, n)
            pr.set_shader_value_v(self.shader, self._loc["lightColor"], pr.ffi.new("float[]", colors), vec3, n)
            floats = pr.ShaderUniformDataType.SHADER_UNIFORM_FLOAT
            pr.set_shader_value_v(self.shader, self._loc["lightRange"], pr.ffi.new("float[]", ranges), floats, n)
            pr.set_shader_value_v(self.shader, self._loc["lightZone"], pr.ffi.new("float[]", zones),
                                  pr.ShaderUniformDataType.SHADER_UNIFORM_VEC2, n)
            pr.set_shader_value_v(self.shader, self._loc["lightFill"], pr.ffi.new("float[]", fills), vec3, n)

    def unload(self) -> None:
        """Safe before or after the models are unloaded (raylib's unload_model leaves material shaders alone)."""
        pr.unload_shader(self.shader)
