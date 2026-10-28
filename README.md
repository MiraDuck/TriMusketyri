# Projekt C.O.R.E.
centrum obnovení rudných energií

A first-person horror game on a drill digging down. Keep the engine running, the oxygen and the temperature in
range, and fix what breaks.

## Run
Needs Python 3.12+ and raylib for Python.
```
pip install raylib
python main.py
```

## Controls
| Key | |
| --- | --- |
| W A S D | walk |
| Mouse | look |
| Left click | use (levers, buttons, coal, the furnace hatch); hold on a valve and move the mouse to turn it |
| E (hold) | repair a burst pipe |
| Esc | pause / back |
| F11 | fullscreen |
| F3 | debug menu (while `DEBUG_MENU` is on in `src/config.py`) |

## Files
- `main.py` + `src/`: the game; every setting is in `src/config.py`.
- `Models/`, `audio/` (`SFX/`, `ambience/`, `Music/`, `voices/`), `Shaders/`: assets. Blender sources are in `_Blender/`.
- An audio file starting with `_` isn't used by the game yet.

## Compile
Custom compilation into an exe
```
python -m nuitka --standalone --include-package=raylib --include-package=pyray --include-data-dir=Models=Models --include-data-dir=audio=audio --include-data-dir=Shaders=Shaders --windows-console-mode=disable main.py
```
