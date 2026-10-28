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
    # drill in front of the control room: loud there, then a steady 10 % through the whole drill
    ("DrillDoingWhateverDrillsDoButWithTheSoundOfEngine.wav", pr.Vector3(0, 3, 8), 1.0, 6.0, 14.0, 0.1),
    # the motor, in the engine room (z -36..-28): gone by the middle of the storage room; its volume and pitch
    # follow how fast it turns (src/engine.py)
    ("engine.wav", pr.Vector3(-1, 2, -33), 1.0, 3.0, 10.0, 0.0),
]
# Short sounds (files in SFX/) played from where a part is when it moves; heard fully within SFX_NEAR, gone by
# SFX_FAR (a breaker flipping in the control room is still loud in the next car, nearly gone two cars away).
SWITCH_SOUND: str = "lever-push-pull.wav"                       # breakers and other switches
SWITCH_SOUNDS: dict[str, str] = {"power_button": "button-press.wav"}   # switches with their own sound
VALVE_SOUND: str = "valve-turn.wav"                             # repeats while a valve turns
SFX_NEAR: float = 3.0
SFX_FAR: float = 14.0

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
# Decorations modelled in place in a car (same origin as the car), drawn and lit: (car, file, solid). `solid` is
# its collision model (the player is stopped by it), or None to walk through it.
DECORATIONS: list[tuple[str, str, str | None]] = [
    ("control_room", "Control_Rooms/Posters.obj", None),   # oxygen and temperature posters on the front wall
    ("oxygen_room", "Oxygen_Rooms/Posters_Oxygen_Room.obj", None),   # labels on the tanks, valves and dials
    ("engine_room", "Engine_Rooms/Engine_Room_Posters.obj", None),   # "výkon motoru" on the back wall
]
# Items modelled at their own origin, placed at the car's position + offset; drawn and lit, not solid:
# (car, file, offset).
ITEMS: list[tuple[str, str, pr.Vector3]] = [
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
# Valves (src/interactable.py), grabbed and turned by moving the mouse left / right: (car, file).
VALVES: list[tuple[str, str]] = [
    ("oxygen_room", "Oxygen_Rooms/Oxygen_Valve.glb"),
    ("oxygen_room", "Oxygen_Rooms/Oxygen_Blue_Valve.glb"),   # TODO: exported at the same spot as Oxygen_Valve
    ("oxygen_room", "Oxygen_Rooms/Temperature_Valve.glb"),
    ("oxygen_room", "Oxygen_Rooms/Temperature_Blue_Valve.glb"),   # on the pipe by the front door
    ("engine_room", "Engine_Rooms/Engine_Valve.glb"),        # back wall, by the door
]
# Levers / switches / breakers (src/interactable.py): (car, file, degrees they swing when pulled down).
SWITCHES: list[tuple[str, str, float]] = [
    # back wall, flip from up to down
    *[("control_room", f"Control_Rooms/Breaker_{i}.glb", 180.0) for i in range(1, 6)],
]
# Press buttons (Button in src/interactable.py): a click swings them there and back. (car, file, name, degrees).
BUTTONS: list[tuple[str, str, str, float]] = [
    ("control_room", "Control_Rooms/Power_Lever.glb", "power_button", -90.0),   # console, twists a quarter turn
]
LEVER_FLIP_TIME: float = 0.25   # seconds a lever / switch takes to swing over (a button: each way)
# Spinning parts (src/spinner.py): (car, file, degrees / s).
SPINNERS: list[tuple[str, str, float]] = [
    ("engine_room", "Engine_Rooms/Engine_Spin.glb", 0.0),   # the motor: src/engine.py sets its speed
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

# ---------------- Engine (src/engine.py) ----------------
# The engine valve sets the motor's power: 0..ENGINE_VALVE_TURNS turns = 0..100 %. The power button restarts it.
ENGINE_VALVE: str = "engine_valve"
ENGINE_BUTTON: str = "power_button"
ENGINE_SPINNER: str = "engine_spin"
ENGINE_DIAL: str = "power_dial"          # shows how fast it turns
# Needle angles (clockwise from its modelled pose, straight up) at the edges of the red sector on the power dial's
# face: 0 % sits at the first, ENGINE_MIN_POWER (30 %) at the second, so the needle is in the red while it dies.
ENGINE_DIAL_RED: tuple[float, float] = (145.0, 215.0)
ENGINE_SOUND: str = "engine"             # the SOUND_SOURCES entry (file name without extension)
ENGINE_VALVE_TURNS: float = 2.0
ENGINE_START_POWER: float = 0.6
ENGINE_MIN_POWER: float = 0.3            # once its speed drops below this it dies and the alarm goes
ENGINE_RESTART_POWER: float = 0.4        # the power button restarts it and turns the valve at least this open
ENGINE_RESTART_VALVE_SPIN: float = 180.0 # degrees / s the valve turns itself up to that after a restart
ENGINE_SPIN_UP: float = 0.05             # how fast its speed follows the valve up (fraction of full speed / s)
ENGINE_SPIN_DOWN: float = 0.04           # and down (100 % -> 30 % in ~18 s: time to turn it back up)
ENGINE_COAST_RATE: float = 0.015         # how fast it slows down once it died (30 % -> stopped in 20 s)
ENGINE_MAX_SPIN: float = 360.0           # degrees / s the engine model turns at full speed
ENGINE_SOUND_VOLUME: float = 1.0         # at full speed
ENGINE_SOUND_PITCH: tuple[float, float] = (0.5, 1.1)   # at standstill, at full speed

# ---------------- Alarm (src/alarm.py) ----------------
# While the motor is down every lamp that is on flashes red, and each flash beeps from the nearest lit lamp.
ALARM_COLOR: pr.Color = pr.Color(255, 30, 20, 255)
ALARM_FILL_COLOR: tuple[float, float, float] = (1.0, 0.15, 0.1)   # tints the lit cars red (white = normal)
ALARM_BLINK: float = 1.5            # flashes per second
ALARM_SOUND: str = "error-warning.wav"
ALARM_NEAR: float = 3.0             # the beep is full volume this close to the lamp,
ALARM_FAR: float = 12.0             # and gone this far (from a dark car the next lit one is quiet)

# ---------------- Faults (src/faults.py) ----------------
# Each kind of fault: every <interval> seconds (a random time in that range) it has a <chance> to happen.
LIGHT_FAULT_INTERVAL: tuple[float, float] = (60.0, 120.0)   # a random breaker flips (always)
FAULT_INTERVAL: tuple[float, float] = (5.0, 15.0)           # for the faults still to come (valves)
FAULT_CHANCE: float = 0.25

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
