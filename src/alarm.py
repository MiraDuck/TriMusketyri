"""Alarm: red flashing lamps and a warning beep while something is badly wrong (the motor died).

    alarm = Alarm(lamps, audio, "error-warning")   # a loaded sound
    alarm.active = True / False
    alarm.update(time, camera)                     # every frame, after the breakers switched the lamps

Every lamp goes into its alarm mode (lighting.Lamp.set_alarm): it flashes red and tints its car red, but only while
it is on, so a car whose breaker is down stays dark. Each flash beeps once, from the nearest lamp that is on: in a
lit car it is loud, from a dark car you only hear the next lit car's alarm, quietly (ALARM_NEAR / ALARM_FAR).
"""
from __future__ import annotations

import math

import pyray as pr

from .audio import Audio
from .config import ALARM_BLINK, ALARM_FAR, ALARM_NEAR
from .lighting import Lamp


class Alarm:
    def __init__(self, lamps: list[Lamp], audio: Audio, sound: str) -> None:
        self.lamps: list[Lamp] = lamps
        self.audio: Audio = audio
        self.sound: str = sound
        self.active: bool = False
        self._flash: int = -1   # number of the last flash that beeped

    def update(self, time: float, camera: pr.Camera3D) -> None:
        for lamp in self.lamps:
            lamp.set_alarm(self.active)
        if not self.active:
            return
        # the lamps all flash together (Light.strength: on for the first half of each 1 / ALARM_BLINK s), so a new
        # flash starts whenever time * ALARM_BLINK passes a whole number
        flash = math.floor(time * ALARM_BLINK)
        if flash == self._flash:
            return
        self._flash = flash
        lit = [lamp for lamp in self.lamps if lamp.light.on]
        if lit:
            nearest = min(lit, key=lambda lamp: pr.vector3_distance(lamp.light.pos, camera.position))
            self.audio.play_sound_at(self.sound, nearest.light.pos, camera, ALARM_NEAR, ALARM_FAR)
