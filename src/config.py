"""All tunable constants in one place."""
from pathlib import Path

import pyray as pr

ROOT: Path = Path(__file__).resolve().parent.parent
MODELS_DIR: Path = ROOT / "Models"
MUSIC_DIR: Path = ROOT / "Music"
SFX_DIR: Path = ROOT / "SFX"

# ---------------- Audio ----------------
START_MUSIC: str = "ambience.wav"    # file in MUSIC_DIR played on launch ("" = none)
MUSIC_VOLUME: float = 1.0
SFX_VOLUME: float = 1.0

# ---------------- Window / timing ----------------
SCREEN_W: int = 1600
SCREEN_H: int = 900
WINDOW_TITLE: str = "raylib [core] example - 3d camera first person"
TARGET_FPS: int = 0          # 0 = uncapped; everything scales with frame time
MAX_DT: float = 0.05         # clamp long frames (window drag, load hitch) so physics can't tunnel

# ---------------- Camera / input ----------------
START_POSITION: pr.Vector3 = pr.Vector3(0.0, 2.5, 4.0)
START_TARGET: pr.Vector3 = pr.Vector3(0.0, 2.5, 0.0)
CAMERA_FOVY: float = 60.0
PLAYER_SPEED: float = 3.6    # units / second (was 0.06 per frame at 60 FPS)
MOUSE_SENSITIVITY: float = 0.05
ZOOM_SPEED: float = 2.0

# ---------------- Models ----------------
MODEL_POS: pr.Vector3 = pr.Vector3(0, 1, 0)
VISIBLE_MODEL: Path = MODELS_DIR / "test.obj"       # what you see
COLLISION_MODEL: Path = MODELS_DIR / "navmesh.obj"  # what you hit
LEVER_MODEL: Path = MODELS_DIR / "lever.obj"
LEVER_POS: pr.Vector3 = pr.Vector3(0, 2, 0)

# ---------------- Player cuboid ----------------
PLAYER_HALF: pr.Vector3 = pr.Vector3(0.4, 0.75, 0.4)
EYE_TO_CENTER: float = 1.0
STEP_UP: float = 0.6         # how high a ledge/sunken amount we can recover from

# ---------------- Gravity ----------------
GRAVITY: float = 25.0        # units / s^2
MAX_FALL_SPEED: float = 15.0  # kept below STEP_UP per frame so we can't tunnel through floors
WORLD_FLOOR_Y: float = 0.0   # fallback floor (the drawn plane) outside the collision model

# ---------------- Head bob (from bob_example.c) ----------------
BOB_SIDE: float = 0.01         # sideways sway
STEP_ROTATION: float = 0.0075  # roll while walking
WALK_FOV_DELTA: float = -5.0   # fov change while walking
