"""Audio: one streamed music track at a time, any number of short sounds, and looping sounds placed in the world.

    audio = Audio()                      # after init_window
    audio.play_music("ambience.wav")     # file in Music/, loops
    audio.load_sound("walk.wav")         # file in SFX/, referred to as "walk"
    audio.play_sound("walk")
    audio.add_source("engine.wav", pr.Vector3(0, 3, 8), near=6, far=14)   # loops at that spot
    audio.play_sound_at("valve-turn", pos, camera)   # a loaded sound, from a spot in the world
    ...
    audio.update(camera)                 # every frame - feeds the streams, places the sources around the camera
    audio.unload()                       # before close_window

Pan in raylib 6: -1 = left, 0 = centre, 1 = right.
"""
from __future__ import annotations

import math
from pathlib import Path

import pyray as pr

from .config import MUSIC_DIR, MUSIC_VOLUME, SFX_DIR, SFX_VOLUME

SOUND_EXTENSIONS: tuple[str, ...] = (".wav", ".mp3", ".ogg", ".flac")
SOURCE_PAN: float = 0.7   # how far a sound beside you pans (1 = only in one ear, which sounds unnatural)


def _resolve(directory: Path, name: str | Path) -> Path:
    path = Path(name)
    if not path.is_absolute():
        path = directory / name
    if not path.is_file():
        raise FileNotFoundError(f"audio file not found: {path}")
    return path


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    """0 below edge0, 1 above edge1, an S-curve between (no sudden jumps in volume)."""
    t = min(max((x - edge0) / (edge1 - edge0), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def _gain(pos: pr.Vector3, listener: pr.Vector3, near: float, far: float, floor: float = 0.0) -> float:
    """floor..1 from the distance alone: 1 within `near`, fading smoothly to `floor` at `far`."""
    fade = 1.0 - _smoothstep(near, far, pr.vector3_distance(listener, pos))
    return floor + (1.0 - floor) * fade


def _pan(pos: pr.Vector3, camera: pr.Camera3D) -> float:
    """-SOURCE_PAN (left) .. SOURCE_PAN (right): how much `pos` is to the right of the view, i.e. dot(direction to
    the sound, camera right), flattened to the horizontal plane so looking up or down doesn't swap the ears."""
    forward = pr.vector3_subtract(camera.target, camera.position)
    right = pr.vector3_normalize(pr.Vector3(-forward.z, 0.0, forward.x))
    to = pr.Vector3(pos.x - camera.position.x, 0.0, pos.z - camera.position.z)
    flat = math.hypot(to.x, to.z)
    return SOURCE_PAN * (pr.vector3_dot_product(right, to) / flat if flat > 0.01 else 0.0)


class SoundSource:
    """A looping sound at a point in the world (streamed, so long files are fine).

    Full `volume` within `near` units of the listener, fading smoothly to `floor` (a fraction of `volume`; 0 =
    silent) at `far` and staying there however far away you are; panned left / right by where it is relative to the
    listener's view. Walls don't block it, so pick `far` to be silent by where it should no longer be heard (e.g. a
    little into the next car), or give it a floor to be heard everywhere (the drill engine).
    `volume` and `pitch` (1 = as recorded, lower = slower and deeper) can be changed while it plays (the motor).
    """

    def __init__(self, path: Path, pos: pr.Vector3, volume: float, near: float, far: float,
                 floor: float = 0.0) -> None:
        self.pos: pr.Vector3 = pos
        self.volume: float = volume
        self.near: float = near
        self.far: float = far
        self.floor: float = floor
        self.pitch: float = 1.0
        self.music: pr.Music = pr.load_music_stream(str(path))
        self.music.looping = True
        pr.set_music_volume(self.music, 0.0)   # silent until the first update() places it
        pr.play_music_stream(self.music)

    def gain(self, listener: pr.Vector3) -> float:
        """floor..1 from the distance alone."""
        return _gain(self.pos, listener, self.near, self.far, self.floor)

    def update(self, camera: pr.Camera3D, master: float) -> None:
        pr.set_music_volume(self.music, master * self.volume * self.gain(camera.position))
        pr.set_music_pan(self.music, _pan(self.pos, camera))
        pr.set_music_pitch(self.music, self.pitch)
        pr.update_music_stream(self.music)

    def unload(self) -> None:
        pr.stop_music_stream(self.music)
        pr.unload_music_stream(self.music)


class Audio:
    def __init__(self, music_dir: str | Path = MUSIC_DIR, sfx_dir: str | Path = SFX_DIR) -> None:
        self.music_dir: Path = Path(music_dir)
        self.sfx_dir: Path = Path(sfx_dir)
        self.music: pr.Music | None = None
        self.sounds: dict[str, pr.Sound] = {}
        self.sources: dict[str, SoundSource] = {}
        self.music_volume: float = MUSIC_VOLUME
        self.sfx_volume: float = SFX_VOLUME
        pr.init_audio_device()

    # ---------------- Music ----------------
    def play_music(self, name: str | Path, volume: float | None = None, loop: bool = True) -> None:
        """Start streaming a track from Music/, replacing the current one."""
        self.stop_music()
        path = _resolve(self.music_dir, name)
        self.music = pr.load_music_stream(str(path))
        self.music.looping = loop
        if volume is not None:
            self.music_volume = volume
        pr.set_music_volume(self.music, self.music_volume)
        pr.play_music_stream(self.music)

    def stop_music(self) -> None:
        if self.music is not None:
            pr.stop_music_stream(self.music)
            pr.unload_music_stream(self.music)
            self.music = None

    def pause_music(self) -> None:
        if self.music is not None:
            pr.pause_music_stream(self.music)

    def resume_music(self) -> None:
        if self.music is not None:
            pr.resume_music_stream(self.music)

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = volume
        if self.music is not None:
            pr.set_music_volume(self.music, volume)

    def update(self, listener: pr.Camera3D | None = None) -> None:
        """Call once per frame; without it the streams stop after the first buffer.
        `listener` (the player's camera) sets each source's volume and pan; without one they are silent."""
        if self.music is not None:
            pr.update_music_stream(self.music)
        for source in self.sources.values():
            if listener is not None:
                source.update(listener, self.sfx_volume)
            else:
                pr.update_music_stream(source.music)

    # ---------------- Sounds in the world ----------------
    def add_source(
        self, filename: str | Path, pos: pr.Vector3, volume: float = 1.0, near: float = 6.0, far: float = 14.0,
        floor: float = 0.0, name: str | None = None,
    ) -> str:
        """Loop SFX/<filename> at `pos`, see SoundSource. Referred to by name, default = file name without extension."""
        key = name or Path(filename).stem
        if key in self.sources:
            self.sources[key].unload()
        self.sources[key] = SoundSource(_resolve(self.sfx_dir, filename), pos, volume, near, far, floor)
        return key

    def remove_source(self, name: str) -> None:
        self.sources.pop(name).unload()

    # ---------------- Sounds ----------------
    def load_sound(self, filename: str | Path, name: str | None = None) -> str:
        """Load SFX/<filename>. Referred to by name, default = file name without extension."""
        key = name or Path(filename).stem
        if key in self.sounds:
            return key
        path = _resolve(self.sfx_dir, filename)
        self.sounds[key] = pr.load_sound(str(path))
        return key

    def load_all_sounds(self) -> list[str]:
        """Load every audio file in SFX/. Returns the list of names."""
        for path in sorted(self.sfx_dir.iterdir()):
            if path.suffix.lower() in SOUND_EXTENSIONS:
                self.load_sound(path.name)
        return list(self.sounds)

    def play_sound(
        self, name: str, volume: float | None = None, pitch: float = 1.0, pan: float = 0.0
    ) -> None:
        """Play a loaded sound (pan: -1 = left, 0 = centre, 1 = right)."""
        sound = self.sounds[name]
        pr.set_sound_volume(sound, self.sfx_volume if volume is None else volume)
        pr.set_sound_pitch(sound, pitch)
        pr.set_sound_pan(sound, pan)
        pr.play_sound(sound)

    def play_sound_at(
        self, name: str, pos: pr.Vector3, listener: pr.Camera3D, near: float = 3.0, far: float = 14.0
    ) -> None:
        """Play a loaded sound as if it came from `pos`: full volume within `near` units of the listener, silent
        from `far`, panned by where it is (it doesn't move with you while it plays; fine for short sounds)."""
        gain = _gain(pos, listener.position, near, far)
        if gain > 0.0:
            self.play_sound(name, self.sfx_volume * gain, pan=_pan(pos, listener))

    def stop_sound(self, name: str) -> None:
        pr.stop_sound(self.sounds[name])

    def is_sound_playing(self, name: str) -> bool:
        return pr.is_sound_playing(self.sounds[name])

    # ---------------- Cleanup ----------------
    def unload(self) -> None:
        self.stop_music()
        for source in self.sources.values():
            source.unload()
        self.sources.clear()
        for sound in self.sounds.values():
            pr.unload_sound(sound)
        self.sounds.clear()
        pr.close_audio_device()
