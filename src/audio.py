"""Audio: one streamed music track at a time plus any number of short sounds.

    audio = Audio()                      # after init_window
    audio.play_music("ambience.wav")     # file in Music/, loops
    audio.load_sound("walk.wav")         # file in SFX/, referred to as "walk"
    audio.play_sound("walk")
    ...
    audio.update()                       # every frame - feeds the music stream
    audio.unload()                       # before close_window
"""
from __future__ import annotations

from pathlib import Path

import pyray as pr

from .config import MUSIC_DIR, MUSIC_VOLUME, SFX_DIR, SFX_VOLUME

SOUND_EXTENSIONS: tuple[str, ...] = (".wav", ".mp3", ".ogg", ".flac")


def _resolve(directory: Path, name: str | Path) -> Path:
    path = Path(name)
    if not path.is_absolute():
        path = directory / name
    if not path.is_file():
        raise FileNotFoundError(f"audio file not found: {path}")
    return path


class Audio:
    def __init__(self, music_dir: str | Path = MUSIC_DIR, sfx_dir: str | Path = SFX_DIR) -> None:
        self.music_dir: Path = Path(music_dir)
        self.sfx_dir: Path = Path(sfx_dir)
        self.music: pr.Music | None = None
        self.sounds: dict[str, pr.Sound] = {}
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

    def update(self) -> None:
        """Call once per frame; without it the music stops after the first buffer."""
        if self.music is not None:
            pr.update_music_stream(self.music)

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
        self, name: str, volume: float | None = None, pitch: float = 1.0, pan: float = 0.5
    ) -> None:
        """Play a loaded sound (pan: 0 = left, 0.5 = centre, 1 = right)."""
        sound = self.sounds[name]
        pr.set_sound_volume(sound, self.sfx_volume if volume is None else volume)
        pr.set_sound_pitch(sound, pitch)
        pr.set_sound_pan(sound, pan)
        pr.play_sound(sound)

    def stop_sound(self, name: str) -> None:
        pr.stop_sound(self.sounds[name])

    def is_sound_playing(self, name: str) -> bool:
        return pr.is_sound_playing(self.sounds[name])

    # ---------------- Cleanup ----------------
    def unload(self) -> None:
        self.stop_music()
        for sound in self.sounds.values():
            pr.unload_sound(sound)
        self.sounds.clear()
        pr.close_audio_device()
