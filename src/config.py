"""All tunable constants in one place."""
from pathlib import Path

from pyray import Vector3

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "Models"
MUSIC_DIR = ROOT / "Music"
SFX_DIR = ROOT / "SFX"

# ---------------- Audio ----------------
START_MUSIC = "ambience.wav"    # file in MUSIC_DIR played on launch ("" = none)
MUSIC_VOLUME = 1.0
SFX_VOLUME = 1.0

# ---------------- Window / timing ----------------
SCREEN_W = 1600
SCREEN_H = 900
WINDOW_TITLE = "raylib [core] example - 3d camera first person"
TARGET_FPS = 0          # 0 = uncapped; everything scales with frame time
MAX_DT = 0.05           # clamp long frames (window drag, load hitch) so physics can't tunnel

# ---------------- Camera / input ----------------
START_POSITION = Vector3(0.0, 2.5, 4.0)
START_TARGET = Vector3(0.0, 2.5, 0.0)
CAMERA_FOVY = 60.0
PLAYER_SPEED = 3.6      # units / second (was 0.06 per frame at 60 FPS)
MOUSE_SENSITIVITY = 0.05
ZOOM_SPEED = 2.0

# ---------------- Models ----------------
MODEL_POS = Vector3(0, 1, 0)
VISIBLE_MODEL = MODELS_DIR / "test.obj"     # what you see
COLLISION_MODEL = MODELS_DIR / "navmesh.obj"  # what you hit

# ---------------- Player cuboid ----------------
PLAYER_HALF = Vector3(0.4, 0.75, 0.4)
EYE_TO_CENTER = 1.0
STEP_UP = 0.6           # how high a ledge/sunken amount we can recover from

# ---------------- Gravity ----------------
GRAVITY = 25.0          # units / s^2
MAX_FALL_SPEED = 15.0   # kept below STEP_UP per frame so we can't tunnel through floors
WORLD_FLOOR_Y = 0.0     # fallback floor (the drawn plane) outside the collision model

# ---------------- Head bob (from bob_example.c) ----------------
BOB_SIDE = 0.01         # sideways sway
STEP_ROTATION = 0.0075  # roll while walking
WALK_FOV_DELTA = -5.0   # fov change while walking
