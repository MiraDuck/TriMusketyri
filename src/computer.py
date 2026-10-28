"""Computer: the rest room's terminal that reports the drill's status. Collect, then send.

    computer = Computer(lever, car_pos, audio, send_sound)
    computer.update(dt, camera, status)   # every frame, after the lever; status() = the report text when it sends
    computer.draw()                       # inside 3D mode (a draw_scene overlay): its screen
    computer.unload()

It collects data ("Sbírání dat...", COMPUTER_SCREENS[0]) for COMPUTER_COOLDOWN, then the data is ready ("Data
připravena", COMPUTER_SCREENS[1]). Pull its lever (a Button: it swings down and back) while it's ready to send the
drill's status: it plays COMPUTER_SEND_SOUND, prints the report (`COMPUTER: sent ...`) and starts collecting again.
Pulling it while it collects does nothing. `sent` counts the reports.

The screen is a quad just in front of the model's own (COMPUTER_SCREEN_CORNERS), unlit like the console screens.
"""
from __future__ import annotations

from typing import Callable

import pyray as pr

from .audio import Audio
from .config import (
    COMPUTER_COOLDOWN, COMPUTER_SCREEN_CORNERS, COMPUTER_SCREEN_WIDTH, COMPUTER_SCREENS, SFX_FAR, SFX_NEAR,
)
from .interactable import Lever
from .screens import draw_quad


def _load_scaled(path) -> pr.Texture:
    """The picture at COMPUTER_SCREEN_WIDTH wide (they are drawn small; full size would waste ~35 MB each)."""
    image = pr.load_image(str(path))
    pr.image_resize(image, COMPUTER_SCREEN_WIDTH, round(image.height * COMPUTER_SCREEN_WIDTH / image.width))
    texture = pr.load_texture_from_image(image)
    pr.unload_image(image)
    pr.set_texture_filter(texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
    return texture


class Computer:
    def __init__(self, lever: Lever, car_pos: pr.Vector3, audio: Audio, send_sound: str) -> None:
        self.lever: Lever = lever
        self.audio: Audio = audio
        self.send_sound: str = send_sound
        self.screens: list[pr.Texture] = [_load_scaled(path) for path in COMPUTER_SCREENS]
        self.corners: list[pr.Vector3] = [pr.vector3_add(car_pos, c) for c in COMPUTER_SCREEN_CORNERS]
        self.collecting: float = COMPUTER_COOLDOWN   # seconds until the data is ready (0 = ready)
        self.sent: int = 0
        lever.debug_extra = self.debug_lines

    @property
    def ready(self) -> bool:
        return self.collecting <= 0

    def update(self, dt: float, camera: pr.Camera3D, status: Callable[[], str]) -> None:
        if self.lever.flipped and self.ready:
            self.sent += 1
            print(f"COMPUTER: sent report {self.sent}: {status()}")
            self.audio.play_sound_at(self.send_sound, self.lever.center, camera, SFX_NEAR, SFX_FAR)
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
