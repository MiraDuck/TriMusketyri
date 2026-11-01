"""Flicker: the lights in the cars next to you stutter for a moment, while your own stays on. Nothing is broken, you
just see it through the doors and hear it buzz.

    flicker = Flicker(lamps, audio)   # after the lamps; lamps in car order
    flicker.start(camera)             # True if it started (the faults do this; F6 in the debug menu)
    flicker.update(dt)                # every frame

A lamp that is off stays off. `Light.flickered` makes a lamp go dark without touching `on`, which the breakers set
every frame. The pattern (FLICKER_BLINKS times off and on, random lengths) is made once per game and the sound is built
from it, so every click lands on a change of the light.

The sound is not a recording: no file in audio/ fits. `flicker_wave` builds it like the computer's Morse: a mains hum
(FLICKER_HUM and its overtones) while the light is on, a faint one while off, a burst of noise on every change.
"""
from __future__ import annotations

import math
import random
from array import array

import pyray as pr

from .audio import Audio
from .config import (
    FLICKER_BLINKS, FLICKER_FAR, FLICKER_HUM, FLICKER_NEAR, FLICKER_OFF, FLICKER_ON, FLICKER_RATE, FLICKER_VOLUME,
)
from .lighting import Lamp

SOUND_NAME: str = "lights_flicker"


def flicker_wave(pattern: list[float]) -> tuple[pr.Wave, array]:
    """The sound of `pattern` (seconds off, on, off, on...). Returns the wave and the samples it points into (keep them
    until the sound is loaded)."""
    rate = FLICKER_RATE
    samples = array("h")
    for i, seconds in enumerate(pattern):
        lit = i % 2 == 1
        for n in range(int(rate * seconds)):
            t = len(samples) / rate
            hum = sum(math.sin(2 * math.pi * FLICKER_HUM * k * t) / k for k in (1, 2, 3, 5))
            click = math.exp(-n / (rate * 0.004)) * random.uniform(-1.0, 1.0)
            tone = hum * (0.5 if lit else 0.06) + click
            samples.append(int(32767 * FLICKER_VOLUME * min(max(tone, -1.0), 1.0)))
    data = pr.ffi.from_buffer("short[]", samples)
    return pr.Wave(len(samples), rate, 16, 1, pr.ffi.cast("void *", data)), samples


class Flicker:
    def __init__(self, lamps: list[Lamp], audio: Audio) -> None:
        self.lamps: list[Lamp] = lamps
        self.audio: Audio = audio
        self.pattern: list[float] = [random.uniform(*(FLICKER_ON if i % 2 else FLICKER_OFF))
                                     for i in range(2 * FLICKER_BLINKS)]
        self.active: list[Lamp] = []
        self.time: float = 0.0
        wave, _samples = flicker_wave(self.pattern)   # _samples holds the data until the sound has copied it
        audio.add_sound(SOUND_NAME, pr.load_sound_from_wave(wave))

    def _neighbours(self, z: float) -> list[Lamp]:
        """The lamps of the cars next to the one at `z` that are on."""
        for i, lamp in enumerate(self.lamps):
            low, high = lamp.light.zone
            if low <= z < high:
                return [self.lamps[j] for j in (i - 1, i + 1) if 0 <= j < len(self.lamps) and self.lamps[j].light.on]
        return []

    def start(self, camera: pr.Camera3D) -> bool:
        """The lights next to you stutter; False if they already do, or none of them is on."""
        lamps = self._neighbours(camera.position.z)
        if self.active or not lamps:
            return False
        self.active, self.time = lamps, 0.0
        nearest = min(lamps, key=lambda lamp: pr.vector3_distance(lamp.light.pos, camera.position))
        self.audio.play_sound_at(SOUND_NAME, nearest.light.pos, camera, FLICKER_NEAR, FLICKER_FAR)
        print(f"FAULT: lights flicker: {', '.join(lamp.name for lamp in lamps)}")
        return True

    def _dark(self) -> bool:
        """Is the pattern in one of its off parts now?"""
        t = self.time
        for i, seconds in enumerate(self.pattern):
            if t < seconds:
                return i % 2 == 0
            t -= seconds
        return False

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self.time += dt
        dark = self._dark()
        for lamp in self.active:
            lamp.light.flickered = dark
        if self.time >= sum(self.pattern):
            self.active = []
