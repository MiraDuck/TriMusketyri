"""Computer: the rest room's terminal that reports the drill's status. Collect, then send.

    computer = Computer(lever, car_pos, audio)
    computer.update(dt, camera, status, depth)   # every frame, after the lever; status() = the report text
    computer.draw()                       # inside 3D mode (a draw_scene overlay): its screen
    computer.unload()

It collects data ("Sbírání dat...", COMPUTER_SCREENS[0]) for COMPUTER_COOLDOWN, then the data is ready ("Data
připravena", COMPUTER_SCREENS[1]). Pull its lever (a Button: it swings down and back) while it's ready to send the
drill's status: it beeps the depth in Morse code from the computer, prints the report (`COMPUTER: sent ...`) and
starts collecting again. Pulling it while it collects does nothing. `sent` counts the reports.

The Morse signal is not a recording: `morse_wave` builds it as a raylib Wave (sine tone, COMPUTER_MORSE_TONE Hz,
COMPUTER_MORSE_UNIT s per dot) and it is loaded as a sound for each report.

The screen is a quad just in front of the model's own (COMPUTER_SCREEN_CORNERS), unlit like the console screens.
"""
from __future__ import annotations

import math
from array import array
from typing import Callable

import pyray as pr

from .audio import Audio
from .config import (
    COMPUTER_COOLDOWN, COMPUTER_MORSE_RATE, COMPUTER_MORSE_TONE, COMPUTER_MORSE_UNIT, COMPUTER_MORSE_VOLUME,
    COMPUTER_SCREEN_CORNERS, COMPUTER_SCREEN_WIDTH, COMPUTER_SCREENS, SFX_FAR, SFX_NEAR,
)
from .interactable import Lever
from .screens import draw_quad


MORSE: dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....", "I": "..",
    "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...",
    "8": "---..", "9": "----.",
}
SOUND_NAME: str = "computer_morse"   # the report's sound in Audio


def morse_wave(message: str) -> tuple[pr.Wave, array]:
    """`message` in Morse code as a raylib Wave: a dot is one COMPUTER_MORSE_UNIT of tone, a dash three, with one
    unit of silence between them, three between letters and seven between words (characters without a code are
    skipped). Returns the wave and the samples it points into (keep them until the sound is loaded)."""
    rate, unit = COMPUTER_MORSE_RATE, COMPUTER_MORSE_UNIT

    def tone(units: int) -> array:
        n = int(rate * unit * units)
        fade = int(rate * 0.005)   # 5 ms in and out, so it doesn't click
        return array("h", (int(32767 * COMPUTER_MORSE_VOLUME * min(1.0, i / fade, (n - i) / fade)
                               * math.sin(2 * math.pi * COMPUTER_MORSE_TONE * i / rate)) for i in range(n)))

    def silence(units: int) -> array:
        return array("h", bytes(2 * int(rate * unit * units)))

    dot, dash = tone(1), tone(3)
    samples = array("h")
    for word in message.upper().split():
        for letter in word:
            for symbol in MORSE.get(letter, ""):
                samples += (dot if symbol == "." else dash) + silence(1)
            samples += silence(2)   # 3 after a letter
        samples += silence(4)       # 7 after a word
    data = pr.ffi.from_buffer("short[]", samples)
    return pr.Wave(len(samples), rate, 16, 1, pr.ffi.cast("void *", data)), samples


def _load_scaled(path) -> pr.Texture:
    """The picture at COMPUTER_SCREEN_WIDTH wide (they are drawn small; full size would waste ~35 MB each)."""
    image = pr.load_image(str(path))
    pr.image_resize(image, COMPUTER_SCREEN_WIDTH, round(image.height * COMPUTER_SCREEN_WIDTH / image.width))
    texture = pr.load_texture_from_image(image)
    pr.unload_image(image)
    pr.set_texture_filter(texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
    return texture


class Computer:
    def __init__(self, lever: Lever, car_pos: pr.Vector3, audio: Audio) -> None:
        self.lever: Lever = lever
        self.audio: Audio = audio
        self.screens: list[pr.Texture] = [_load_scaled(path) for path in COMPUTER_SCREENS]
        self.corners: list[pr.Vector3] = [pr.vector3_add(car_pos, c) for c in COMPUTER_SCREEN_CORNERS]
        self.collecting: float = COMPUTER_COOLDOWN   # seconds until the data is ready (0 = ready)
        self.sent: int = 0
        lever.debug_extra = self.debug_lines

    @property
    def ready(self) -> bool:
        return self.collecting <= 0

    def update(self, dt: float, camera: pr.Camera3D, status: Callable[[], str], depth: float) -> None:
        if self.lever.flipped and self.ready:
            self.sent += 1
            print(f"COMPUTER: sent report {self.sent}: {status()}")
            message = f"{depth:.0f} M"   # the depth, in Morse
            wave, samples = morse_wave(message)
            self.audio.add_sound(SOUND_NAME, pr.load_sound_from_wave(wave))   # copies the samples
            self.audio.play_sound_at(SOUND_NAME, self.lever.center, camera, SFX_NEAR, SFX_FAR)
            self.collecting = COMPUTER_COOLDOWN
        self.collecting = max(self.collecting - dt, 0.0)

    def draw(self) -> None:
        texture = self.screens[1 if self.ready else 0]
        draw_quad(self.corners, texture.id, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)))

    def debug_lines(self) -> list[str]:
        state = "ready to send" if self.ready else f"collecting, ready in {self.collecting:.0f} s"
        return [f"computer: {state}, {self.sent} sent"]

    def unload(self) -> None:
        for texture in self.screens:
            pr.unload_texture(texture)
