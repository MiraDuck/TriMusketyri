"""Death: mission failed. Either the motor stopped for good (the lights die, the engine fails and the drill
explodes) or you passed out (life support).

    death = Death(audio, "engine-faliure-explosion")   # a loaded sound, for the explosion
    death.start(text, depth, explode=True)   # what happened and how deep you got (does nothing if already started)
    death.update(dt)               # every frame
    view = death.shake(view)       # the drill shakes harder and harder until it blows
    death.draw()                   # every frame after the HUD: the fade / flash, then the death screen
    if death.over: ...             # the screen is covered: draw only death.draw() from now on
    if death.finished: ...         # the player clicked through the death screen: back to the menu

Explosion (seconds from start): the failure sound rumbles and the view shakes more and more (the player can still
move, in the dark); at DEATH_EXPLOSION_AT (where the bang is in the sound) every looping sound and the music stop,
the screen flashes DEATH_FLASH_COLOR and fades to black.
Passing out: the screen fades to black over PASS_OUT_FADE (the eyes closing, more to come), then the sounds stop.
Then the same death screen: DEATH_TITLE, what happened and the depth reached fade in DEATH_TEXT_AT later, and from
DEATH_CONTINUE_AT a click or key ends it. The texts are Czech: they use the first font in DEATH_FONTS that exists
(raylib's own has no Czech letters), or lose their accents without one.
"""
from __future__ import annotations

import random
import unicodedata

import pyray as pr

from .audio import Audio
from .config import (
    DEATH_CONTINUE_AT, DEATH_EXPLOSION_AT, DEATH_FLASH_COLOR, DEATH_FLASH_TIME, DEATH_FONTS, DEATH_SHAKE,
    DEATH_TEXT_AT, DEATH_TITLE, PASS_OUT_FADE, SCREEN_H,
)

CZECH: str = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
FONT_SIZE: int = 48   # loaded at; drawn smaller


def _plain(text: str) -> str:
    """`text` without accents (for raylib's own font, and the console, which may not take UTF-8)."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


def _load_font() -> pr.Font | None:
    """The first of DEATH_FONTS that exists, with ASCII and the Czech letters; None if there is none."""
    for path in DEATH_FONTS:
        if path.is_file():
            # ASCII but "|" (too tall in Consolas: raylib warns) + the Czech letters
            codepoints = [c for c in range(32, 127) if c != ord("|")] + [ord(c) for c in CZECH]
            array = pr.ffi.new("int[]", codepoints)   # pyray wants a plain int *, kept alive while it loads
            font = pr.load_font_ex(str(path), FONT_SIZE, pr.ffi.cast("int *", array), len(codepoints))
            pr.set_texture_filter(font.texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
            return font
    return None


class Death:
    def __init__(self, audio: Audio, sound: str) -> None:
        self.audio: Audio = audio
        self.sound: str = sound
        self.active: bool = False
        self.explode: bool = False
        self.text: str = ""
        self.depth: float = 0.0
        self.time: float = 0.0       # since start()
        self.finished: bool = False
        self.font: pr.Font | None = _load_font()

    def start(self, text: str, depth: float, explode: bool = False) -> None:
        if self.active:
            return
        self.active, self.text, self.depth, self.explode = True, text, depth, explode
        if explode:
            self.audio.play_sound(self.sound)
        print(f"DEATH: {_plain(text)} ({depth:.0f} m)")

    @property
    def _cover_at(self) -> float:
        """Seconds after start when the screen is all black."""
        return DEATH_EXPLOSION_AT if self.explode else PASS_OUT_FADE

    @property
    def over(self) -> bool:
        return self.active and self.time >= self._cover_at

    @property
    def since_over(self) -> float:
        return self.time - self._cover_at

    def update(self, dt: float) -> None:
        if not self.active:
            return
        was_over = self.over
        self.time += dt
        if self.over and not was_over:   # the drill is gone / you are out: only the bang is left
            for source in self.audio.sources.values():
                source.volume = 0.0
            self.audio.stop_music()
        if self.over and self.since_over >= DEATH_CONTINUE_AT and (
                pr.get_key_pressed() or pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT)):
            self.finished = True

    def shake(self, camera: pr.Camera3D) -> pr.Camera3D:
        """A copy of `camera` shaken by how close the explosion is (unchanged unless the drill is going to blow)."""
        if not (self.active and self.explode):
            return camera
        amount = DEATH_SHAKE * min(self.time / DEATH_EXPLOSION_AT, 1.0) ** 2
        d = pr.Vector3(*(random.uniform(-amount, amount) for _ in range(3)))
        return pr.Camera3D(pr.vector3_add(camera.position, d), pr.vector3_add(camera.target, d), camera.up,
                           camera.fovy, camera.projection)

    def draw(self) -> None:
        if not self.active:
            return
        w, h = pr.get_screen_width(), pr.get_screen_height()
        if not self.over:   # passing out: the screen goes dark over the game
            if not self.explode:
                pr.draw_rectangle(0, 0, w, h, pr.fade(pr.BLACK, self.time / PASS_OUT_FADE))
            return
        s = h / SCREEN_H
        t = self.since_over

        def centered(msg: str, y: float, size: float, color: pr.Color, czech: bool = False) -> None:
            size = int(size * s)
            if czech and self.font is not None:
                width = pr.measure_text_ex(self.font, msg, size, 1).x
                pr.draw_text_ex(self.font, msg, pr.Vector2((w - width) / 2, y * s), size, 1, color)
                return
            if czech:   # no font with the Czech letters: drop the accents
                msg = _plain(msg)
            pr.draw_text(msg, int((w - pr.measure_text(msg, size)) / 2), int(y * s), size, color)

        pr.draw_rectangle(0, 0, w, h, pr.BLACK)
        flash = max(0.0, 1.0 - t / DEATH_FLASH_TIME) if self.explode else 0.0
        if flash > 0:
            pr.draw_rectangle(0, 0, w, h, pr.fade(DEATH_FLASH_COLOR, flash))
        text = min(max(t - DEATH_TEXT_AT, 0.0), 1.0)   # fades in over 1 s
        if text > 0:
            centered(DEATH_TITLE, SCREEN_H / 2 - 60, 60, pr.fade(pr.RED, text))
            centered(self.text, SCREEN_H / 2 + 8, 22, pr.fade(pr.LIGHTGRAY, text), czech=True)
            centered(f"Depth reached: {self.depth:.0f} m", SCREEN_H / 2 + 40, 20, pr.fade(pr.RAYWHITE, text))
        if t >= DEATH_CONTINUE_AT and int(pr.get_time() * 2) % 2 == 0:   # blinks
            centered("Click to continue", SCREEN_H / 2 + 90, 15, pr.GRAY)

    def unload(self) -> None:
        if self.font is not None:
            pr.unload_font(self.font)
