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

# ---------------- Window / timing ----------------
SCREEN_W: int = 1600
SCREEN_H: int = 900
WINDOW_TITLE: str = "TriMusketyri"
TARGET_FPS: int = 0          # 0 = uncapped; everything scales with frame time
MAX_DT: float = 0.05         # clamp long frames (window drag, load hitch) so physics can't tunnel

# ---------------- Camera / input ----------------
START_POSITION: pr.Vector3 = pr.Vector3(0.0, 2.8, -2.5)   # control room, lower half, facing the front
START_TARGET: pr.Vector3 = pr.Vector3(0.0, 2.8, 0.0)
CAMERA_FOVY: float = 60.0
PLAYER_SPEED: float = 3.6    # units / second
MOUSE_SENSITIVITY: float = 0.05
ZOOM_SPEED: float = 2.0      # mouse wheel, free camera only

# ---------------- Drill ----------------
# Cars from the front backwards: (name, visible model, collision model). The first sits at DRILL_POS and each
# next one CAR_LENGTH further along -z (the control room's closed end faces +z).
DRILL_POS: pr.Vector3 = pr.Vector3(0, 1, 0)
CAR_LENGTH: float = 8.0
ROOM_MODEL: Path = MODELS_DIR / "Room.obj"
ROOM_COLLISION: Path = MODELS_DIR / "Room_Navmesh.obj"
DRILL_CARS: list[tuple[str, Path, Path]] = [
    ("control_room", MODELS_DIR / "Control_Room.obj", MODELS_DIR / "Control_Room_Navmesh.obj"),
    ("room_1", ROOM_MODEL, ROOM_COLLISION),
    ("oxygen_room", MODELS_DIR / "Oxygen_Room.obj", MODELS_DIR / "Oxygen_Room_Navmesh.obj"),
    ("room_2", ROOM_MODEL, ROOM_COLLISION),
    ("room_3", ROOM_MODEL, ROOM_COLLISION),
]

# ---------------- Models ----------------
LEVER_MODEL: Path = MODELS_DIR / "lever.obj"
LEVER_POS: pr.Vector3 = pr.Vector3(0, 2, 0)
VALVE_MODEL: Path = MODELS_DIR / "Valve.obj"
VALVE_POS: pr.Vector3 = pr.Vector3(0.6, 2, 0)

# ---------------- Lighting (src/lighting.py) ----------------
LIGHT_AMBIENT: float = 0.3   # brightness where no light reaches (0 = black)
LIGHT_BANDS: float = 5.0     # cel-shading steps per light (higher = smoother)
LIT_ENTITIES: set[str] = {"control_room", "lever", "valve"}   # drawn with the lighting shader; the rest is unlit
# (position, colour, intensity, range, blinks per second; 0 = steady). At most 8. Lights shine through walls,
# so keep the range inside the car.
LIGHTS: list[tuple[pr.Vector3, pr.Color, float, float, float]] = [
    (pr.Vector3(0, 4.25, 0), pr.Color(255, 225, 190, 255), 1.0, 8.0, 0.0),   # control room ceiling lamp
    # (pr.Vector3(0, 4.25, -3), pr.RED, 1.0, 6.0, 1.0),                      # e.g. a red alarm light
]

# ---------------- Interactables ----------------
VALVE_TURN_SPEED: float = 0.5    # degrees per pixel of left / right mouse movement while holding a valve
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
