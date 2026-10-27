"""Audio: one streamed music track at a time plus any number of short sounds.

    audio = Audio()                      # after init_window
    audio.play_music("ambience.wav")     # file in Music/, loops
    audio.load_sound("walk.wav")         # file in SFX/, referred to as "walk"
    audio.play_sound("walk")
    ...
    audio.update()                       # every frame - feeds the music stream
    audio.unload()                       # before close_window
"""
from pathlib import Path

from pyray import *

from .config import MUSIC_DIR, MUSIC_VOLUME, SFX_DIR, SFX_VOLUME

SOUND_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac")


def _resolve(directory, name):
    path = Path(name)
    if not path.is_absolute():
        path = directory / name
    if not path.is_file():
        raise FileNotFoundError(f"audio file not found: {path}")
    return path


class Audio:
    def __init__(self, music_dir=MUSIC_DIR, sfx_dir=SFX_DIR):
        self.music_dir = Path(music_dir)
        self.sfx_dir = Path(sfx_dir)
        self.music = None
        self.sounds = {}
        self.music_volume = MUSIC_VOLUME
        self.sfx_volume = SFX_VOLUME
        init_audio_device()

    # ---------------- Music ----------------
    def play_music(self, name, volume=None, loop=True):
        """Start streaming a track from Music/, replacing the current one."""
        self.stop_music()
        path = _resolve(self.music_dir, name)
        self.music = load_music_stream(str(path))
        self.music.looping = loop
        if volume is not None:
            self.music_volume = volume
        set_music_volume(self.music, self.music_volume)
        play_music_stream(self.music)

    def stop_music(self):
        if self.music is not None:
            stop_music_stream(self.music)
            unload_music_stream(self.music)
            self.music = None

    def pause_music(self):
        if self.music is not None:
            pause_music_stream(self.music)

    def resume_music(self):
        if self.music is not None:
            resume_music_stream(self.music)

    def set_music_volume(self, volume):
        self.music_volume = volume
        if self.music is not None:
            set_music_volume(self.music, volume)

    def update(self):
        """Call once per frame; without it the music stops after the first buffer."""
        if self.music is not None:
            update_music_stream(self.music)

    # ---------------- Sounds ----------------
    def load_sound(self, filename, name=None):
        """Load SFX/<filename>. Referred to by name, default = file name without extension."""
        key = name or Path(filename).stem
        if key in self.sounds:
            return key
        path = _resolve(self.sfx_dir, filename)
        self.sounds[key] = load_sound(str(path))
        return key

    def load_all_sounds(self):
        """Load every audio file in SFX/. Returns the list of names."""
        for path in sorted(self.sfx_dir.iterdir()):
            if path.suffix.lower() in SOUND_EXTENSIONS:
                self.load_sound(path.name)
        return list(self.sounds)

    def play_sound(self, name, volume=None, pitch=1.0, pan=0.5):
        """Play a loaded sound (pan: 0 = left, 0.5 = centre, 1 = right)."""
        sound = self.sounds[name]
        set_sound_volume(sound, self.sfx_volume if volume is None else volume)
        set_sound_pitch(sound, pitch)
        set_sound_pan(sound, pan)
        play_sound(sound)

    def stop_sound(self, name):
        stop_sound(self.sounds[name])

    def is_sound_playing(self, name):
        return is_sound_playing(self.sounds[name])

    # ---------------- Cleanup ----------------
    def unload(self):
        self.stop_music()
        for sound in self.sounds.values():
            unload_sound(sound)
        self.sounds.clear()
        close_audio_device()
