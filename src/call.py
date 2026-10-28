"""Call: the phone call at the start of a game (INTRO_CALL), heard everywhere at INTRO_CALL_VOLUME. Nothing happens
in the drill until it ends: the main loop freezes the world while `call.active` (no digging, no faults, no burning).
The computer's lever skips it.

    call = Call(audio, audio.load_sound(INTRO_CALL))   # starts it
    call.update(dt)          # every frame (not while paused)
    call.active              # still talking
    call.skip()              # the computer's lever
    call.pause() / call.resume()   # the pause menu
"""
from __future__ import annotations

import pyray as pr

from .audio import Audio
from .config import INTRO_CALL_VOLUME


class Call:
    def __init__(self, audio: Audio, sound: str) -> None:
        self.audio: Audio = audio
        self.sound: str = sound
        clip = audio.sounds[sound]
        self.length: float = clip.frameCount / clip.stream.sampleRate   # seconds
        self.elapsed: float = 0.0
        self.active: bool = True
        self.skipped: bool = False
        self._paused: bool = False
        audio.play_sound(sound, audio.sfx_volume * INTRO_CALL_VOLUME)
        print(f"CALL: started ({self.length:.0f} s)")

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self.elapsed += dt
        if not self._paused and not self.audio.is_sound_playing(self.sound):
            self.active = False
            print("CALL: ended")

    def skip(self) -> None:
        if self.active:
            self.audio.stop_sound(self.sound)
            self.active, self.skipped = False, True
            print(f"CALL: skipped at {self.elapsed:.0f} s")

    def pause(self) -> None:
        if self.active:
            pr.pause_sound(self.audio.sounds[self.sound])
            self._paused = True

    def resume(self) -> None:
        if self.active:
            pr.resume_sound(self.audio.sounds[self.sound])
            self._paused = False
