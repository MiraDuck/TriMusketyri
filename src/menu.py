"""Main menu: drawn in the game window before play starts.

    menu = MainMenu()           # after init_window (loads the background textures)
    choice = menu.run(audio)    # returns when the player picks something; keeps audio's music playing
    if choice == MenuChoice.STATS:
        StatsScreen().run(audio, menu.draw_background)   # stats.py, over the same background
    menu.unload()

The background cycles through config.MENU_BACKGROUNDS, scaled to cover the window (cropping the edges that don't
fit). The title "PROJEKT C.O.R.E." is part of those images, so the buttons are placed in image pixels, under it.

Mouse: hover a button to highlight it, click to pick it. Esc or closing the window counts as Quit (Konec). The
labels are Czech: drawn with ui's font.
"""
from __future__ import annotations

from enum import Enum

import pyray as pr

from . import config, ui
from .audio import Audio


class MenuChoice(Enum):
    PLAY = "Hrát"
    STATS = "Statistiky"
    QUIT = "Konec"


# In pixels of the background images (1500 x 1000), so the buttons stay under the title at any window size.
BUTTONS_CENTER_X: float = 1080   # middle of the C.O.R.E. sign
BUTTONS_TOP: float = 620         # just below it
BUTTON_W: float = 380
BUTTON_H: float = 60
BUTTON_GAP: float = 20
BUTTON_BORDER: float = 5
BUTTON_TEXT_SIZE: int = 30

BACKGROUND: pr.Color = pr.Color(18, 18, 18, 255)   # behind the image, only seen while the textures are missing


class MainMenu:
    """Needs an open window (load_texture needs a GL context)."""

    def __init__(self, options: tuple[MenuChoice, ...] = (MenuChoice.PLAY, MenuChoice.STATS, MenuChoice.QUIT)) -> None:
        self.options: tuple[MenuChoice, ...] = options
        self.hovered: int | None = None   # index of the button under the mouse
        self.backgrounds: list[pr.Texture] = [pr.load_texture(str(path)) for path in config.MENU_BACKGROUNDS]
        for texture in self.backgrounds:
            pr.set_texture_filter(texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)

    def _image_rect(self) -> tuple[float, float, float]:
        """(x, y, scale): where the background's top-left lands on screen and how much it is scaled to cover it."""
        w, h = pr.get_screen_width(), pr.get_screen_height()
        image = self.backgrounds[0]
        scale = max(w / image.width, h / image.height)
        return (w - image.width * scale) / 2, (h - image.height * scale) / 2, scale

    def _buttons(self) -> list[pr.Rectangle]:
        """Screen-space rectangle of each option, top to bottom."""
        x, y, s = self._image_rect()
        left = x + (BUTTONS_CENTER_X - BUTTON_W / 2) * s
        return [pr.Rectangle(left, y + (BUTTONS_TOP + i * (BUTTON_H + BUTTON_GAP)) * s, BUTTON_W * s, BUTTON_H * s)
                for i in range(len(self.options))]

    def update(self) -> MenuChoice | None:
        """Handle the mouse; returns the clicked option, or None while still choosing."""
        mouse = pr.get_mouse_position()
        self.hovered = None
        for i, rect in enumerate(self._buttons()):
            if pr.check_collision_point_rec(mouse, rect):
                self.hovered = i
                if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
                    return self.options[i]
        if pr.is_key_pressed(pr.KeyboardKey.KEY_F11):
            pr.toggle_fullscreen()
        if pr.is_key_pressed(pr.KeyboardKey.KEY_ESCAPE):   # not raylib's exit key any more (main.py): the game pauses
            return MenuChoice.QUIT
        return None

    def draw_background(self) -> None:
        """The cycling pictures, covering the window (also behind the statistics)."""
        x, y, s = self._image_rect()
        pr.clear_background(BACKGROUND)
        frame = int(pr.get_time() / config.MENU_FRAME_TIME) % len(self.backgrounds)
        pr.draw_texture_ex(self.backgrounds[frame], pr.Vector2(x, y), 0.0, s, pr.WHITE)

    def draw(self) -> None:
        self.draw_background()
        _, _, s = self._image_rect()
        for i, (option, rect) in enumerate(zip(self.options, self._buttons())):
            on = i == self.hovered
            pr.draw_rectangle_rec(rect, ui.GREEN if on else ui.BUTTON_FILL)
            pr.draw_rectangle_lines_ex(rect, max(2.0, BUTTON_BORDER * s), ui.DARK_GREEN if on else ui.DIM)
            size = BUTTON_TEXT_SIZE * s
            ui.draw_centered(option.value, rect.x + rect.width / 2, rect.y + (rect.height - size) / 2, size,
                             ui.DARK_GREEN if on else ui.GREEN)

    def run(self, audio: Audio | None = None) -> MenuChoice:
        """Show the menu until a button is clicked (Esc or closing the window counts as Quit). Leaves the cursor
        visible; the game disables it again. `audio` is updated every frame so its music keeps playing."""
        pr.enable_cursor()
        while not pr.window_should_close():
            if audio is not None:
                audio.update()
            choice = self.update()
            pr.begin_drawing()
            self.draw()
            pr.end_drawing()
            if choice is not None:
                return choice
        return MenuChoice.QUIT

    def unload(self) -> None:
        for texture in self.backgrounds:
            pr.unload_texture(texture)
