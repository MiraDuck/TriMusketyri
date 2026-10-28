"""All tunable constants in one place."""
from pathlib import Path

import pyray as pr

ROOT: Path = Path(__file__).resolve().parent.parent
MODELS_DIR: Path = ROOT / "Models"
AMBIENCE_DIR: Path = ROOT / "ambience"
MUSIC_DIR: Path = ROOT / "Music"
SFX_DIR: Path = ROOT / "SFX"
SHADERS_DIR: Path = ROOT / "Shaders"

# ---------------- Audio ----------------
START_MUSIC: str = "ambience.wav"    # file in AMBIENCE_DIR played on launch ("" = none)
MUSIC_VOLUME: float = 1.0
SFX_VOLUME: float = 1.0
# Looping sounds placed in the world: (file in SFX/, position, volume, near, far, floor). Full volume within `near`
# units of the player, fading smoothly to `floor` (fraction of the volume that is always heard; 0 = silent) at
# `far`. Walls don't block sound, so set `far` to where it should be gone. Cars are 8 long: the control room is
# z -4..4, the next car z -4..-12, and so on.
SOUND_SOURCES: list[tuple[str, pr.Vector3, float, float, float, float]] = [
    # drill engine in front of the control room: loud there, then a steady 30 % through the whole drill
    ("DrillDoingWhateverDrillsDoButWithTheSoundOfEngine.wav", pr.Vector3(0, 3, 8), 1.0, 6.0, 14.0, 0.2),
]

# ---------------- Window / timing ----------------
SCREEN_W: int = 1600
SCREEN_H: int = 900
WINDOW_TITLE: str = "TriMusketyri"
TARGET_FPS: int = 0          # 0 = uncapped; everything scales with frame time
MAX_DT: float = 0.05         # clamp long frames (window drag, load hitch) so physics can't tunnel

# ---------------- Main menu (src/menu.py) ----------------
# Background frames, shown in turn; all the same size, with the title in the same place (the buttons go under it).
MENU_BACKGROUNDS: list[Path] = [MODELS_DIR / "Textures" / f"menu_{i}.png" for i in (1, 2, 3)]
MENU_FRAME_TIME: float = 0.3   # seconds each frame is shown
MENU_MUSIC: Path = MUSIC_DIR / "PrototypeMainTheme.mp3"   # loops while the menu is open

# ---------------- Camera / input ----------------
START_POSITION: pr.Vector3 = pr.Vector3(0.0, 2.8, -2.5)   # control room, lower half, facing the front
START_TARGET: pr.Vector3 = pr.Vector3(0.0, 2.8, 0.0)
CAMERA_FOVY: float = 60.0
PLAYER_SPEED: float = 3.6    # units / second
MOUSE_SENSITIVITY: float = 0.05
ZOOM_SPEED: float = 2.0      # mouse wheel, free camera only
DEBUG_REACH: float = 20.0    # with hitboxes on (F1), how far away the thing you look at gets its details shown

# ---------------- Drill ----------------
# Cars from the front backwards: (name, visible model, collision model). The first sits at DRILL_POS and each
# next one CAR_LENGTH further along -z (the control room's closed end faces +z).
DRILL_POS: pr.Vector3 = pr.Vector3(0, 1, 0)
CAR_LENGTH: float = 8.0
DRILL_CARS: list[tuple[str, Path, Path]] = [
    ("control_room", MODELS_DIR / "Control_Rooms" / "Control_Room.obj", MODELS_DIR / "Control_Rooms" / "Control_Room_Navmesh.obj"),
    ("rest_room", MODELS_DIR / "Rest_Rooms" / "Rest_Room.obj", MODELS_DIR / "Rest_Rooms" / "Rest_Room_Navmesh.obj"),
    ("oxygen_room", MODELS_DIR / "Oxygen_Rooms" / "Oxygen_Room.obj", MODELS_DIR / "Oxygen_Rooms" / "Oxygen_Room_Navmesh.obj"),
    ("storage_room", MODELS_DIR / "Storage_Rooms" / "Storage_Room.obj", MODELS_DIR / "Storage_Rooms" / "Storage_Room_Navmesh.obj"),
    ("engine_room", MODELS_DIR / "Engine_Rooms" / "Engine_Room.obj", MODELS_DIR / "Engine_Rooms" / "Engine_Room_Navmesh.obj"),
]

# ---------------- Models ----------------
LEVER_MODEL: Path = MODELS_DIR / "lever.obj"
LEVER_POS: pr.Vector3 = pr.Vector3(0, 2, 0)
VALVE_MODEL: Path = MODELS_DIR / "Valve.obj"
VALVE_POS: pr.Vector3 = pr.Vector3(0.6, 2, 0)
# Decorations modelled in place in a car (same origin as the car), drawn and lit, not solid: (car, file).
DECORATIONS: list[tuple[str, str]] = [
    ("control_room", "Control_Rooms/Posters.obj"),   # oxygen and temperature posters on the front wall
]
# Moving parts: rigged .glb files modelled in place in a car (same origin as the car), so each is placed at the
# position of the car it names (see DRILL_CARS). The entity's name is the file name in lower case (oxygen_level).
# Dials (src/dial.py): (car, file, low, high, sweep in degrees). The modelled needle pose shows `low`.
DIALS: list[tuple[str, str, float, float, float]] = [
    ("control_room", "Control_Rooms/Temperature_Pressure.glb", 0.0, 100.0, 360.0),   # console, left
    ("control_room", "Control_Rooms/Oxygen_Pressure.glb", 0.0, 100.0, 360.0),        # console, right
    ("control_room", "Control_Rooms/Power_Dial.glb", 0.0, 100.0, 360.0),             # flat gauge on the console
    ("oxygen_room", "Oxygen_Rooms/Oxygen_Dial.glb", 0.0, 100.0, 360.0),
    ("oxygen_room", "Oxygen_Rooms/Temperature_Dial.glb", 0.0, 100.0, 360.0),
]
# Sliding dials, a marker moving left / right along a straight scale (its Move animation, along the bone's -X):
# (car, file, low, high, distance it slides from low to high). Low and high are inside the red end blocks.
SLIDING_DIALS: list[tuple[str, str, float, float, float]] = [
    ("control_room", "Control_Rooms/Temperature_Level.glb", 0.0, 100.0, 0.637),   # console, left side panel
    ("control_room", "Control_Rooms/Oxygen_Level.glb", 0.0, 100.0, 0.637),        # console, right side panel
]
# Valves (src/interactable.py), grabbed and turned like VALVE_MODEL: (car, file).
VALVES: list[tuple[str, str]] = [
    ("oxygen_room", "Oxygen_Rooms/Oxygen_Blue_Valve.glb"),   # blue copy of Oxygen_Valve.glb, same place: one of them
    ("oxygen_room", "Oxygen_Rooms/Temperature_Valve.glb"),
    ("engine_room", "Engine_Rooms/Engine_Valve.glb"),        # back wall, by the door
]
# Levers / switches / breakers (src/interactable.py): (car, file, degrees they swing when pulled down).
SWITCHES: list[tuple[str, str, float]] = [
    # back wall, flip from up to down
    *[("control_room", f"Control_Rooms/Breaker_{i}.glb", 180.0) for i in range(1, 6)],
    ("control_room", "Control_Rooms/Power_Lever.glb", -90.0),   # console, twists a quarter turn
]
LEVER_FLIP_TIME: float = 0.25   # seconds a lever / switch takes to swing over
# Spinning parts (src/spinner.py): (car, file, degrees / s).
SPINNERS: list[tuple[str, str, float]] = [
    ("engine_room", "Engine_Rooms/Engine_Spin.glb", 216.0),   # the engine; 216 deg/s = its Spin360 animation's speed
]
# Which car's lamp each breaker switches (up = on). The light changes as the handle passes halfway.
BREAKER_LAMPS: dict[str, str] = {
    "breaker_1": "engine_room",
    "breaker_2": "storage_room",
    "breaker_3": "oxygen_room",
    "breaker_4": "rest_room",
    "breaker_5": "control_room",
}
DIAL_NEEDLE_SPEED: float = 4.0   # how fast needles follow their value (higher = snappier, ~1/s to settle)

# ---------------- Faults (src/faults.py) ----------------
# Every FAULT_INTERVAL seconds (a random time in that range) something has a FAULT_CHANCE to break.
FAULT_INTERVAL: tuple[float, float] = (5.0, 15.0)
FAULT_CHANCE: float = 0.25   # 0 = nothing ever breaks, 1 = something breaks every time

# ---------------- Lighting (src/lighting.py) ----------------
LIGHT_AMBIENT: float = 0.3   # brightness of a car with its lamp on, where the lamp doesn't reach (0 = black)
LIGHT_DARK: float = 0.08     # brightness of a car with its lamp off (breaker down): barely visible
LIGHT_BANDS: float = 5.0     # cel-shading steps per light (higher = smoother)
# Every car gets a ceiling lamp (Light.obj, which hangs down from its origin) with a light inside it.
LAMP_MODEL: Path = MODELS_DIR / "Light.obj"
LAMP_OFFSET: pr.Vector3 = pr.Vector3(0, 3.16, 0)   # where it hangs, relative to the car: under the ceiling beam
LAMP_LIGHT_DROP: float = 0.5                        # its light sits this far below that, inside the shade
LAMP_COLOR: pr.Color = pr.Color(230, 175, 48, 255)   # warm white
LAMP_INTENSITY: float = 1.0
LAMP_RANGE: float = 8.0
# Extra lights: (position, colour, intensity, range, blinks per second; 0 = steady). At most 8 lights in total,
# lamps included. Like the lamps, a light only lights the car it is in.
LIGHTS: list[tuple[pr.Vector3, pr.Color, float, float, float]] = [
    # (pr.Vector3(0, 4.0, -3), pr.RED, 1.0, 6.0, 1.0),   # e.g. a red alarm light in the control room
]

# ---------------- Vignette (src/vignette.py) ----------------
VIGNETTE_COLOR: pr.Color = pr.Color(0, 0, 0, 255)
VIGNETTE_STRENGTH: float = 0.85   # 0 = off, 1 = full colour in the corners
VIGNETTE_RADIUS: float = 0.3      # darkening starts this far from the centre (0.5 = middle of the screen edges)
VIGNETTE_SOFTNESS: float = 0.45   # and reaches full strength this much further out (the corners are at ~0.71)

# ---------------- Interactables ----------------
VALVE_TURN_SPEED: float = 0.1    # degrees per pixel of left / right mouse movement while holding a valve
VALVE_BREAK_SPIN: float = 90.0   # degrees / s a broken valve turns on its own (valve.spin)
VALVE_BREAK_TEST_AT: float | None = None   # test: seconds after start the valve breaks and spins open; None = never

# ---------------- Player cuboid ----------------
PLAYER_HALF: pr.Vector3 = pr.Vector3(0.4, 0.75, 0.4)
EYE_TO_CENTER: float = 1.0
STEP_UP: float = 0.6         # how high a ledge/sunken amount we can recover from

# ---------------- Gravity ----------------
GRAVITY: float = 25.0        # units / s^2
MAX_FALL_SPEED: float = 15.0  # kept below STEP_UP per frame so we can't tunnel through floors
WORLD_FLOOR_Y: float = 0.0   # fallback floor (the drawn plane) outside the collision model

# ---------------- Head bob (from raylib's first-person example) ----------------
BOB_SIDE: float = 0.01         # sideways sway
STEP_ROTATION: float = 0.0075  # roll while walking
WALK_FOV_DELTA: float = -5.0   # fov change while walking
