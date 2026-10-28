"""Computer: the rest room's terminal that reports the drill's status to the surface. Collect, then send.

    computer = Computer(lever, car_pos, audio, call)
    computer.update(dt, camera, status)   # every frame, after the lever, before begin_drawing (renders its screen);
                                          # status: the drill's readings now (Status)
    computer.draw()                       # inside 3D mode (a draw_scene overlay): its screen
    computer.unload()

What it does, in turn (`phase`):
- "call": the phone call at the start (call.py) is on; pulling the lever skips it.
- "luck": the call is over: it beeps HODNĚ ŠTĚSTÍ in Morse code and shows it for COMPUTER_LUCK_TIME.
- "collecting": it collects data for COMPUTER_COOLDOWN, then
- "ready": DATA PŘIPRAVENA. Pull the lever (a Button: it swings down and back) to send the drill's status: it beeps
  the depth in Morse code from the computer, prints the report (`COMPUTER: sent ...`) and collects again.
  Pulling it while it collects does nothing. `sent` counts the reports, `last_depth` is the depth in the last one
  (the run's record only knows that).
- "report": for COMPUTER_REPORT_TIME after sending, the screen shows what was sent (it keeps collecting meanwhile).

The screen is drawn in code into a render texture every frame, like the console's depth panel, in big letters and
only what matters now: during the call the call (PŘÍCHOZÍ HOVOR, how far it is, "Páka = přeskočit"), then HODNĚ
ŠTĚSTÍ!, then SBÍRÁNÍ DAT and the time left / DATA PŘIPRAVENA, "Páka = odeslat"; right after sending, the report's
readings (depth, engine, fuel, oxygen, temperature) under ODESÍLÁNÍ... / ODESLÁNO. A quad just in front of the
model's own (COMPUTER_SCREEN_CORNERS), unlit like the console screens.

The Morse signal is not a recording: `morse_wave` builds it as a raylib Wave (sine tone, COMPUTER_MORSE_TONE Hz,
COMPUTER_MORSE_UNIT s per dot) and it is loaded as a sound for each message.
"""
from __future__ import annotations

import math
from array import array
from dataclasses import dataclass

import pyray as pr

from . import ui
from .audio import Audio
from .call import Call
from .config import (
    COMPUTER_COOLDOWN, COMPUTER_LUCK, COMPUTER_LUCK_TIME, COMPUTER_REPORT_TIME, COMPUTER_MORSE_RATE, COMPUTER_MORSE_TONE,
    COMPUTER_MORSE_UNIT, COMPUTER_MORSE_VOLUME, COMPUTER_SCREEN_CORNERS, COMPUTER_SCREEN_SIZE, SCREEN_BLACK,
    SCREEN_GREEN, SFX_FAR, SFX_NEAR,
)
from .interactable import Lever
from .records import format_time
from .screens import draw_quad


MORSE: dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....", "I": "..",
    "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...",
    "8": "---..", "9": "----.",
}
SOUND_NAME: str = "computer_morse"   # the message's sound in Audio
ENGINE_STATES: dict[str, str] = {"running": "běží", "dying": "umírá", "starting": "start", "dead": "stojí"}


@dataclass
class Status:
    """The drill's readings: what the computer collects and sends."""
    depth: float         # metres
    engine: float        # speed, 0..1 (more when overclocked)
    engine_state: str    # EngineState.value
    fuel: float          # 0..1
    oxygen: float        # level, 0..1
    temperature: float   # level, 0..1

    def __str__(self) -> str:
        return (f"depth {self.depth:.0f} m, engine {self.engine:.0%} ({self.engine_state}), fuel {self.fuel:.0%}, "
                f"oxygen {self.oxygen:.0%}, temperature {self.temperature:.0%}")


def morse_wave(message: str) -> tuple[pr.Wave, array]:
    """`message` in Morse code as a raylib Wave: a dot is one COMPUTER_MORSE_UNIT of tone, a dash three, with one
    unit of silence between them, three between letters and seven between words (accents are dropped, characters
    without a code skipped). Returns the wave and the samples it points into (keep them until the sound is loaded)."""
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
    for word in ui.plain(message).upper().split():
        for letter in word:
            for symbol in MORSE.get(letter, ""):
                samples += (dot if symbol == "." else dash) + silence(1)
            samples += silence(2)   # 3 after a letter
        samples += silence(4)       # 7 after a word
    data = pr.ffi.from_buffer("short[]", samples)
    return pr.Wave(len(samples), rate, 16, 1, pr.ffi.cast("void *", data)), samples


class Computer:
    def __init__(self, lever: Lever, car_pos: pr.Vector3, audio: Audio, call: Call) -> None:
        self.lever: Lever = lever
        self.audio: Audio = audio
        self.call: Call = call
        self.corners: list[pr.Vector3] = [pr.vector3_add(car_pos, c) for c in COMPUTER_SCREEN_CORNERS]
        self.screen: pr.RenderTexture = pr.load_render_texture(*COMPUTER_SCREEN_SIZE)
        pr.set_texture_filter(self.screen.texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
        self.luck: float = 0.0                       # seconds of HODNĚ ŠTĚSTÍ left, once the call is over
        self.collecting: float = COMPUTER_COOLDOWN   # seconds until the data is ready (0 = ready)
        self.sent: int = 0
        self.last_depth: float | None = None   # in the last report sent: what the run's record shows
        self.report: Status | None = None      # the last report sent, shown for COMPUTER_REPORT_TIME
        self.report_left: float = 0.0
        self.clock: float = 0.0
        self._call_was_active: bool = call.active
        lever.debug_extra = self.debug_lines

    @property
    def phase(self) -> str:
        if self.call.active:
            return "call"
        if self.luck > 0:
            return "luck"
        if self.report_left > 0:
            return "report"
        return "ready" if self.collecting <= 0 else "collecting"

    @property
    def ready(self) -> bool:
        return self.phase == "ready"

    def _beep(self, message: str, camera: pr.Camera3D) -> None:
        """Beep `message` in Morse code from the computer."""
        wave, _samples = morse_wave(message)   # _samples holds the data until the sound has copied it
        self.audio.add_sound(SOUND_NAME, pr.load_sound_from_wave(wave))
        self.audio.play_sound_at(SOUND_NAME, self.lever.center, camera, SFX_NEAR, SFX_FAR)

    def update(self, dt: float, camera: pr.Camera3D, status: Status) -> None:
        self.clock += dt
        if self.lever.flipped and self.call.active:
            self.call.skip()
        if self._call_was_active and not self.call.active:   # the call is over (or skipped): wish them luck
            self.luck = COMPUTER_LUCK_TIME
            self._beep(COMPUTER_LUCK, camera)
        self._call_was_active = self.call.active
        if self.lever.flipped and self.ready:
            self.sent += 1
            self.last_depth = status.depth
            self.report, self.report_left = status, COMPUTER_REPORT_TIME
            print(f"COMPUTER: sent report {self.sent}: {status}")
            self._beep(f"{status.depth:.0f} M", camera)   # the depth, in Morse
            self.collecting = COMPUTER_COOLDOWN
        if self.phase == "luck":
            self.luck = max(self.luck - dt, 0.0)
        elif self.phase in ("report", "collecting"):
            self.report_left = max(self.report_left - dt, 0.0)
            self.collecting = max(self.collecting - dt, 0.0)
        self._render()

    def _render(self) -> None:
        """The screen, into its render texture: big text, only what matters now."""
        w, h = COMPUTER_SCREEN_SIZE
        green = SCREEN_GREEN
        blink = int(self.clock * 2) % 2 == 0
        phase = self.phase
        pr.begin_texture_mode(self.screen)
        pr.clear_background(SCREEN_BLACK)
        for x in range(0, w, 32):   # the grid of the other screens
            pr.draw_line(x, 0, x, h, pr.fade(green, 0.12))
        for y in range(0, h, 32):
            pr.draw_line(0, y, w, y, pr.fade(green, 0.12))

        if phase == "call":
            if blink:
                ui.draw_centered("PŘÍCHOZÍ HOVOR", w / 2, 60, 76, green)
            pr.draw_rectangle_lines_ex(pr.Rectangle(40, 190, w - 80, 60), 3, green)
            fraction = min(self.call.elapsed / self.call.length, 1.0)
            pr.draw_rectangle(46, 196, int((w - 92) * fraction), 48, pr.fade(green, 0.7))
            ui.draw_centered(f"{format_time(self.call.elapsed)} / {format_time(self.call.length)}", w / 2, 270, 48,
                             green)
            ui.draw_centered("Páka = přeskočit", w / 2, 380, 48, green)
        elif phase == "luck":
            ui.draw_centered(COMPUTER_LUCK, w / 2, (h - 84) / 2, 84, green)
        elif phase == "report":   # what was just sent
            r = self.report
            sending = self.audio.is_sound_playing(SOUND_NAME)
            ui.draw_centered("ODESÍLÁNÍ" + "." * (int(self.clock * 3) % 4) if sending else "ODESLÁNO", w / 2, 22, 50,
                             green)
            pr.draw_line_ex(pr.Vector2(16, 90), pr.Vector2(w - 16, 90), 3, green)
            engine = f"{r.engine:.0%} ({ENGINE_STATES.get(r.engine_state, r.engine_state)})"
            rows = [("HLOUBKA", f"{r.depth:.0f} m"), ("MOTOR", engine), ("PALIVO", f"{r.fuel:.0%}"),
                    ("KYSLÍK", f"{r.oxygen:.0%}"), ("TEPLOTA", f"{r.temperature:.0%}")]
            for i, (label, value) in enumerate(rows):
                y = 108 + i * 76
                ui.draw_text(label, 36, y, 50, green)
                ui.draw_text(value, 290, y, 50, green)
        elif phase == "collecting":
            ui.draw_centered("SBÍRÁNÍ DAT" + "." * (int(self.clock * 2) % 4), w / 2, 130, 68, green)
            ui.draw_centered(format_time(self.collecting + 0.99), w / 2, 260, 68, green)
        else:   # ready
            if blink:
                ui.draw_centered("DATA PŘIPRAVENA", w / 2, 130, 68, green)
            ui.draw_centered("Páka = odeslat", w / 2, 280, 48, green)
        pr.end_texture_mode()

    def draw(self) -> None:
        # a render texture is stored upside down
        draw_quad(self.corners, self.screen.texture.id, ((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)))

    def debug_lines(self) -> list[str]:
        return [f"computer: {self.phase}, ready in {self.collecting:.0f} s, {self.sent} sent"]

    def unload(self) -> None:
        pr.unload_render_texture(self.screen)
