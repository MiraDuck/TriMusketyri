"""Death: mission failed. Either the motor stopped for good (the lights die, the engine fails and the drill
explodes) or you passed out (life support). The death screen shows the run's report; type your name and save it.

    death = Death(audio, "engine-faliure-explosion", "EarsRinging-YoPhoneLinging")   # loaded sounds: the
                                                    # explosion, the ringing after the bang
    death.start(cause, depth, time, explode=True)   # what failed and the last reported depth (None: no report
                                                    # sent), how long you survived (does nothing if started)
    death.update(dt)               # every frame
    view = death.shake(view)       # the drill shakes harder and harder until it blows
    death.draw()                   # every frame after the HUD: the fade / flash, then the death screen
    if death.over: ...             # the screen is covered: draw only death.draw() from now on
    if death.finished: ...         # saved (Enter) or skipped (Esc): back to the menu

Explosion (seconds from start): the failure sound rumbles and the view shakes more and more (the player can still
move, in the dark); at DEATH_EXPLOSION_AT (where the bang is in the sound) every looping sound and the music stop,
the screen flashes DEATH_FLASH_COLOR and fades to black, and your ears ring (quietly, EARS_RINGING_VOLUME).
Passing out: the screen fades to black over PASS_OUT_FADE (the eyes closing, more to come), then the sounds stop.
Then the same death screen: DEATH_TITLE and the run's report (records.py: name, time survived, the last reported
depth, the expected cause; both unknown without a report) fade in DEATH_TEXT_AT later. The name starts as the last saved run's; type to change it (Backspace deletes). From
DEATH_CONTINUE_AT, Enter saves the run (records.save_run) and Esc leaves without saving.
"""
from __future__ import annotations

import random

import pyray as pr

from . import ui
from .audio import Audio
from .config import (
    DEATH_CONTINUE_AT, DEATH_EXPLOSION_AT, DEATH_FLASH_COLOR, DEATH_FLASH_TIME, DEATH_NAME_LENGTH, DEATH_NO_REPORT,
    DEATH_SHAKE,
    DEATH_TEXT_AT, DEATH_TITLE, DEATH_UNNAMED, EARS_RINGING_VOLUME, PASS_OUT_FADE, SCREEN_H,
)
from .records import Run, draw_record, last_name, save_run


class Death:
    def __init__(self, audio: Audio, sound: str, ringing: str) -> None:
        self.audio: Audio = audio
        self.sound: str = sound
        self.ringing: str = ringing
        self.active: bool = False
        self.explode: bool = False
        self.run: Run | None = None   # the report, once started
        self.time: float = 0.0       # since start()
        self.finished: bool = False
        self.saved: bool = False

    def start(self, cause: str | None, depth: float | None, time: float, explode: bool = False) -> None:
        if self.active:
            return
        self.active, self.explode = True, explode
        self.run = Run(last_name(), time, depth, cause, Run.now())
        if explode:
            self.audio.play_sound(self.sound)
        print(f"DEATH: {ui.plain(self.run.cause_text)} ({ui.plain(self.run.depth_text)}, {time:.0f} s)")

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
            if self.explode:
                self.audio.play_sound(self.ringing, self.audio.sfx_volume * EARS_RINGING_VOLUME)
        if not self.over or self.since_over < DEATH_TEXT_AT or self.finished:
            return
        self._type_name()
        if self.since_over >= DEATH_CONTINUE_AT:
            if pr.is_key_pressed(pr.KeyboardKey.KEY_ENTER) or pr.is_key_pressed(pr.KeyboardKey.KEY_KP_ENTER):
                self.run.name = self.run.name.strip() or DEATH_UNNAMED
                save_run(self.run)
                self.saved = self.finished = True
            elif pr.is_key_pressed(pr.KeyboardKey.KEY_ESCAPE):
                self.finished = True

    def _type_name(self) -> None:
        """The keys typed this frame go into the name (only letters the font has); Backspace deletes."""
        while (code := pr.get_char_pressed()) > 0:
            if chr(code) in ui.CHARS and len(self.run.name) < DEATH_NAME_LENGTH:
                self.run.name += chr(code)
        if pr.is_key_pressed(pr.KeyboardKey.KEY_BACKSPACE) or pr.is_key_pressed_repeat(
                pr.KeyboardKey.KEY_BACKSPACE):
            self.run.name = self.run.name[:-1]

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
        pr.draw_rectangle(0, 0, w, h, pr.BLACK)
        flash = max(0.0, 1.0 - t / DEATH_FLASH_TIME) if self.explode else 0.0
        if flash > 0:
            pr.draw_rectangle(0, 0, w, h, pr.fade(DEATH_FLASH_COLOR, flash))
        text = min(max(t - DEATH_TEXT_AT, 0.0), 1.0)   # fades in over 1 s
        if text > 0:
            ui.draw_centered(DEATH_TITLE, w / 2, (SCREEN_H / 2 - 250) * s, 60 * s, pr.fade(pr.RED, text))
            draw_record(self.run, w / 2, (SCREEN_H / 2 - 160) * s, s, text, caret=not self.finished)
        if text > 0 and self.run.depth is None:
            ui.draw_centered(DEATH_NO_REPORT, w / 2, (SCREEN_H / 2 + 145) * s, 22 * s, pr.fade(pr.RED, text))
        if t >= DEATH_CONTINUE_AT:
            ui.draw_centered("Napište své jméno.   Enter: uložit záznam   Esc: neukládat", w / 2,
                             (SCREEN_H / 2 + 185) * s, 20 * s, pr.GRAY)
