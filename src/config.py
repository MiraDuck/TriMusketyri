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
SWITCH_SOUNDS: dict[str, str] = {   # switches with their own sound
    "power_button": "button-press.wav",
    "engine_hatch": "furnace-Animnation.wav",   # the furnace hatch swinging open / shut (src/fuel.py)
}
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
    ("rest_room", "Rest_Rooms/Miras_Duck.obj", None),
    ("rest_room", "Rest_Rooms/Computer.obj", None),   # its screen and lever: src/computer.py
    ("rest_room", "Rest_Rooms/Paper_Stack.obj", None),   # a poem and a sudoku book on the table
    ("rest_room", "Rest_Rooms/Radio.obj", None),
]
# Items modelled at their own origin, placed at the car's position + offset; drawn and lit, not solid:
# (car, file, offset).
ITEMS: list[tuple[str, str, pr.Vector3]] = [
]
# Moving parts: rigged .glb files modelled in place in a car (same origin as the car), so each is placed at the
# position of the car it names (see DRILL_CARS). The entity's name is the file name in lower case (oxygen_level).
# Dials (src/dial.py): (car, file, low, high, sweep in degrees, start: degrees clockwise from the modelled pose,
# straight up, where `low` is). The control room's faces have a red sector at the bottom (145..215 deg).
DIALS: list[tuple[str, str, float, float, float, float]] = [
    # console, left / right: cooling / oxygen pressure, round from the red sector's left edge to its right one
    ("control_room", "Control_Rooms/Temperature_Pressure.glb", 0.0, 100.0, 290.0, 215.0),
    ("control_room", "Control_Rooms/Oxygen_Pressure.glb", 0.0, 100.0, 290.0, 215.0),
    ("control_room", "Control_Rooms/Power_Dial.glb", 0.0, 100.0, 360.0, 0.0),   # the engine sets its own (engine.py)
    # on the tanks, plain faces: oxygen level / temperature, from lower left round to lower right
    ("oxygen_room", "Oxygen_Rooms/Oxygen_Dial.glb", 0.0, 100.0, 270.0, 225.0),
    ("oxygen_room", "Oxygen_Rooms/Temperature_Dial.glb", 0.0, 100.0, 270.0, 225.0),
]
# Sliding dials, a marker moving left / right along a straight scale (its Move animation, along the bone's -X):
# (car, file, low, high, distance it slides from low to high). Low and high are inside the red end blocks.
SLIDING_DIALS: list[tuple[str, str, float, float, float]] = [
    ("control_room", "Control_Rooms/Temperature_Level.glb", 0.0, 100.0, 0.637),   # console, left side panel
    ("control_room", "Control_Rooms/Oxygen_Level.glb", 0.0, 100.0, 0.637),        # console, right side panel
    # console, the vertical bar between the drill screen and the depth panel: modelled at the top, slides down
    ("control_room", "Control_Rooms/Fuel_Level.glb", 0.0, 100.0, 0.637),           # the fuel (src/fuel.py)
]
# Valves (src/interactable.py), grabbed and turned by moving the mouse left / right: (car, file).
VALVES: list[tuple[str, str]] = [
    ("oxygen_room", "Oxygen_Rooms/Oxygen_Valve.glb"),
    ("oxygen_room", "Oxygen_Rooms/Oxygen_Blue_Valve.glb"),
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
# face: 0 % sits at the first, ENGINE_MIN_POWER (30 %) at the second, so the needle is in the red while it dies;
# 30..100 % takes the rest of the face, all the way round to the first edge again.
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
DRILL_SPEED: float = 2.0                 # metres / s the drill digs down at full engine speed (depth)
ENGINE_SOUND_VOLUME: float = 1.0         # at full speed
ENGINE_SOUND_PITCH: tuple[float, float] = (0.5, 1.1)   # at standstill, at full speed

# ---------------- Fuel (src/fuel.py) ----------------
# Coal: click the stockpile in the storage room to take a piece, carry it to the engine room, click the furnace hatch
# to open it and click it again to throw the coal in. The engine burns it as it turns; the bar on the console (between
# the drill screen and the depth panel: Fuel_Level, in SLIDING_DIALS) shows how much is left.
COAL_PILE: tuple[str, str, str] = ("storage_room", "Storage_Rooms/Coal_Stockpile.obj",
                                   "Storage_Rooms/Coal_Stockpile_Navmesh.obj")   # (car, model, solid), in place
COAL_MODEL: str = "Storage_Rooms/Coal.obj"   # the piece you carry (modelled at its own origin)
COAL_HELD_OFFSET: tuple[float, float, float] = (0.24, -0.19, 0.55)   # in your hand: right, up, forward of the eye
COAL_HELD_SCALE: float = 0.35
COAL_TAKE_SOUND: str = "shoveling-coal.wav"      # from the pile when you take a piece
COAL_FEED_SOUND: str = "pebles-hitting-metal.mp3"   # from the hatch when it goes in
HATCH: tuple[str, str] = ("engine_room", "Engine_Rooms/Engine_Hatch.glb")   # the furnace door, rigged, in place
HATCH_THROW: float = 100.0      # degrees it swings open about its bone (outwards, into the room)
HATCH_OPEN_TIME: float = 0.6    # seconds it takes, each way (its sound: SWITCH_SOUNDS)
FUEL_DIAL: str = "fuel_level"   # the fuel bar on the console
FUEL_START: float = 0.6         # 0..1
FUEL_PER_COAL: float = 0.1      # one piece of coal
FUEL_BURN: float = 0.003        # fuel / s at full engine speed (times its speed): a piece every ~33 s,
FUEL_BURN_PER_METRE: float = 0.000003   # + this per metre of depth (1000 m doubles it),
FUEL_BURN_MAX: float = 0.006    # but never more
FUEL_LOW: float = 0.3           # below this the engine loses power, down to none at 0 (it dies on the way)
FUEL_OVERCLOCK: float = 0.9     # above this it overclocks: more power, up to
FUEL_OVERCLOCK_BOOST: float = 1.3   # x this at full (130 % speed: digs and burns faster)
FUEL_OVERCLOCK_HEAT: float = 0.03   # and heats the drill: temperature / s at full, on top of the depth's heat

# ---------------- Console screens (src/screens.py) ----------------
# Drawn as quads just in front of the control room console's panels, in car coordinates (the car's position is
# added): (top left, top right, bottom right, bottom left) as you see them standing at the console.
# The display left of the vertical depth gauge (the green grid): the drill turning, drill_1..4 cycled.
DRILL_SCREEN_CORNERS: tuple[pr.Vector3, ...] = (
    pr.Vector3(0.765, 2.19, 3.784), pr.Vector3(-0.1, 2.19, 3.784),
    pr.Vector3(-0.1, 1.712, 3.784), pr.Vector3(0.765, 1.712, 3.784))
DRILL_SCREEN_FRAMES: list[Path] = [MODELS_DIR / "Textures" / f"drill_{i}.png" for i in (1, 2, 3, 4)]
DRILL_SCREEN_FPS: float = 4.0          # frames / s at full engine speed (stands still when it stops)
# The black panel right of the gauge: the depth.
DEPTH_PANEL_CORNERS: tuple[pr.Vector3, ...] = (
    pr.Vector3(-0.328, 2.269, 3.683), pr.Vector3(-0.712, 2.269, 3.683),
    pr.Vector3(-0.712, 1.648, 3.683), pr.Vector3(-0.328, 1.648, 3.683))
DEPTH_PANEL_SIZE: tuple[int, int] = (248, 400)   # its texture, pixels (the panel's proportions)
SCREEN_GREEN: pr.Color = pr.Color(70, 190, 70, 255)   # the screens' green
SCREEN_BLACK: pr.Color = pr.Color(28, 28, 30, 255)

# ---------------- Pipes (src/pipes.py) ----------------
# The oxygen and cooling pipes can burst: the more pressure their system has, the likelier. A burst pipe shoots
# steam (particles), fills its car with smoke (over your eyes) and loses part of its system's pressure (turn the red valve up to make up
# for it, and back down once it's fixed). Fix it: look at it, hold E until the ring is full, blink.
# Both pipes run through every car, against its front wall left of the door (modelled in place, like the parts),
# except the control room: there they would stand in the console, through its screens.
PIPE_CARS: list[str] = ["rest_room", "oxygen_room", "storage_room", "engine_room"]
# (car, system: "oxygen" / "cooling", model, burst model, where the steam comes out in car coordinates)
PIPES: list[tuple[str, str, str, str, pr.Vector3]] = [
    pipe
    for car in PIPE_CARS
    for pipe in (
        (car, "oxygen", "Pipes/Pipe_Oxygen.obj", "Pipes/Pipe_Oxygen_Broken.obj", pr.Vector3(-0.27, 1.52, 3.66)),
        (car, "cooling", "Pipes/Pipe_Temperature.obj", "Pipes/Pipe_Temperature_Broken.obj",
         pr.Vector3(0.19, 1.52, 3.66)),
    )
]
PIPE_CHECK_INTERVAL: tuple[float, float] = (8.0, 16.0)   # seconds between a pipe's burst rolls
PIPE_BURST_CHANCE: float = 0.05    # per pipe and roll at full pressure; * pressure^2 (half pressure: 1/4 of it)
PIPE_LEAK: float = 0.5             # share of its system's pressure a burst pipe loses (two: 75 %, ...)
PIPE_REPAIR_TIME: float = 3.0      # seconds holding E
PIPE_REPAIR_REACH: float = 2.5     # how close you have to be
PIPE_LEAK_SOUND: str = "pipe-leak.wav"         # loops at the crack while it is burst
PIPE_REPAIR_SOUND: str = "repair-generic.wav"  # when it is fixed
BLINK_TIME: tuple[float, float, float] = (0.12, 0.15, 0.3)   # eyes closing, closed (it gets fixed), opening
# Steam: particles shot out of the crack, mostly straight into the room (-z, away from the wall)
STEAM_RATE: float = 200.0          # particles / s
STEAM_LIFE: float = 1.4            # seconds each one lives
STEAM_SPEED: tuple[float, float] = (2.0, 4.0)   # units / s it shoots out at
STEAM_SPREAD: float = 0.7          # sideways / up-down speed, of the forward speed
STEAM_SIZE: tuple[float, float] = (0.15, 0.9)   # size when it comes out, when it fades
STEAM_COLOR: pr.Color = pr.Color(110, 110, 115, 255)   # dark smoke

# ---------------- Fog (lit.fs) ----------------
FOG_COLOR: tuple[float, float, float] = (0.05, 0.05, 0.06)   # a little everywhere: far things fade into the dark
FOG_DENSITY: float = 0.05          # 1 - exp(-density * distance): ~33 % at 8 m (the next car)
# Smoke: while you are in a car with a burst pipe, it covers the whole screen, HUD included (pipes.draw_smoke)
SMOKE_COLOR: pr.Color = pr.Color(28, 28, 30, 255)
SMOKE_MAX: float = 0.75            # how much it covers once the car has filled up (0..1)
SMOKE_RISE: float = 0.3            # how fast the car fills (of the max / s: full in ~3 s)
SMOKE_CLEAR: float = 0.05          # how fast it clears once fixed (of the max / s: 20 s)

# ---------------- Player sounds ----------------
STEP_SOUND: str = "walk.wav"       # one footstep, played on every step of the head bob (on the ground)
STEP_VOLUME: float = 0.5
BREATH_SOUND: str = "breath.wav"   # repeats, louder and louder, while you are about to pass out
BREATH_FROM: float = 0.3           # starts at this much strain (0..1, life support), full volume at 1
BREATH_VOLUME: tuple[float, float] = (4.0, 12.0)   # when it starts, at full strain (the file is very quiet: its
                                                    # loudest is ~5 % of full scale, so > 1 amplifies it)

# ---------------- Computer (src/computer.py) ----------------
# The rest room's computer collects the drill's status ("Sbírání dat...", data_1) for COMPUTER_COOLDOWN, then shows
# "Data připravena" (data_2): pull its lever to send the status (depth, engine, oxygen, temperature) and it starts
# collecting again.
COMPUTER_CAR: str = "rest_room"
COMPUTER_LEVER: str = "Rest_Rooms/Computer_Lever.glb"   # sticks out of a slot on its side
COMPUTER_LEVER_THROW: float = 60.0     # degrees it swings down (about its bone's X axis), then back
# A quad just in front of its screen (car coordinates): top left, top right, bottom right, bottom left as you see it
COMPUTER_SCREEN_CORNERS: tuple[pr.Vector3, ...] = (
    pr.Vector3(-0.144, 1.704, -3.025), pr.Vector3(0.358, 1.704, -3.025),
    pr.Vector3(0.358, 1.357, -3.025), pr.Vector3(-0.144, 1.357, -3.025))
COMPUTER_SCREENS: tuple[Path, Path] = (MODELS_DIR / "Textures" / "data_1.png",   # collecting
                                       MODELS_DIR / "Textures" / "data_2.png")   # ready to send
COMPUTER_SCREEN_WIDTH: int = 1024      # the pictures are 3508 px wide: scaled down when loaded
COMPUTER_COOLDOWN: float = 60.0        # seconds it collects before the data is ready again
# When it sends, it beeps the depth in Morse code: a sine tone made in code (computer.morse_wave), not a recording
COMPUTER_MORSE_TONE: float = 700.0     # Hz
COMPUTER_MORSE_UNIT: float = 0.07      # seconds per dot (a dash is 3); ~17 words per minute
COMPUTER_MORSE_VOLUME: float = 0.5     # of full scale
COMPUTER_MORSE_RATE: int = 44100       # samples / s

# ---------------- Alarm (src/alarm.py) ----------------
# While the motor is down every lamp that is on flashes red, and each flash beeps from the nearest lit lamp.
ALARM_COLOR: pr.Color = pr.Color(255, 30, 20, 255)
ALARM_FILL_COLOR: tuple[float, float, float] = (1.0, 0.15, 0.1)   # tints the lit cars red (white = normal)
ALARM_BLINK: float = 1.5            # flashes per second
ALARM_SOUND: str = "error-warning.wav"
ALARM_NEAR: float = 3.0             # the beep is full volume this close to the lamp,
ALARM_FAR: float = 12.0             # and gone this far (from a dark car the next lit one is quiet)

# ---------------- Death (src/death.py) ----------------
# When the motor stops for good every light goes out, the failure sound plays and the drill explodes: you die.
DEATH_SOUND: str = "engine-faliure-explosion.wav"   # (sic, the file's name) rumbles, then the bang
DEATH_EXPLOSION_AT: float = 5.2     # seconds into the sound where the bang is
DEATH_SHAKE: float = 0.04           # how far (units) the view shakes just before the bang (grows from 0)
DEATH_FLASH_COLOR: pr.Color = pr.Color(255, 190, 120, 255)
DEATH_FLASH_TIME: float = 1.5       # the flash fades to black over this
DEATH_TEXT_AT: float = 2.0          # seconds after the bang the run's report fades in (you can type your name)
DEATH_CONTINUE_AT: float = 4.0      # seconds after the bang Enter saves it / Esc skips it, back to the menu
PASS_OUT_FADE: float = 3.0          # passing out: seconds the screen takes to go black (no explosion)
DEATH_TITLE: str = "MISSION FAILED"
# What failed: the run's report (records.py) and the statistics show it.
DEATH_TEXT_ENGINE: str = "Výbuch motoru"
DEATH_TEXT_FUEL: str = "Došlo palivo"
DEATH_TEXT_OXYGEN_LOW: str = "Nedostatek kyslíku"
DEATH_TEXT_OXYGEN_HIGH: str = "Přebytek kyslíku"
DEATH_TEXT_HOT: str = "Přehřátí"
DEATH_TEXT_COLD: str = "Podchlazení"
DEATH_NAME_LENGTH: int = 20         # letters you can type for the report's name
DEATH_UNNAMED: str = "Neznámý"      # saved with no name typed

# ---------------- Records, statistics (src/records.py, src/stats.py) ----------------
RUNS_FILE: Path = ROOT / "runs.json"   # every saved run's report (not in git)

# ---------------- Pause (src/pause.py) ----------------
PAUSE_QUESTION: str = "Opravdu chcete odejít?\nProgress není uložen."
PAUSE_LEAVE: str = "Odejít"            # back to the main menu
PAUSE_RESUME: str = "Zpět do hry"

# ---------------- UI text (src/ui.py) ----------------
# raylib's own font has no Czech letters: the menus and screens use the first of these fonts that exists (put a
# .ttf in Fonts/ to ship one with the game); with none, the letters lose their accents.
UI_FONTS: list[Path] = [ROOT / "Fonts" / "ui.ttf", ROOT / "Fonts" / "death.ttf",
                        Path("C:/Windows/Fonts/consola.ttf"), Path("C:/Windows/Fonts/arial.ttf")]

# ---------------- Life support (src/life_support.py) ----------------
# Oxygen and cooling, each kept by two valves in the oxygen room: the red one sets the PRESSURE (how hard the system
# pushes), the blue one the IDEAL LEVEL (where it pushes the level to). The level moves towards the ideal at
# coupling * pressure per second, while something pulls it away: you breathe the oxygen, the depth heats the drill.
# Turned all the way the valves are 0 / 100 %. Keep both levels inside LIFE_SAFE or you pass out.
LIFE_VALVE_TURNS: float = 1.0          # turns from closed to fully open
LIFE_PRESSURE_RATE: float = 0.5        # how fast the pressure follows its valve (of the gap per s)
LIFE_SAFE: tuple[float, float] = (0.25, 0.75)   # levels (0..1) you can live in; the sliders' red ends are outside
LIFE_PASS_OUT_TIME: float = 20.0       # seconds outside the safe levels until you pass out (recovers at half that rate)
# (red valve, blue valve, the dials that show the pressure, the dials that show the level)
OXYGEN_PARTS: tuple[str, str, tuple[str, ...], tuple[str, ...]] = (
    "oxygen_valve", "oxygen_blue_valve", ("oxygen_pressure",), ("oxygen_level", "oxygen_dial"))
COOLING_PARTS: tuple[str, str, tuple[str, ...], tuple[str, ...]] = (
    "temperature_valve", "temperature_blue_valve", ("temperature_pressure",), ("temperature_level", "temperature_dial"))
OXYGEN_COUPLING: float = 0.1           # the oxygen follows its ideal level slowly,
COOLING_COUPLING: float = 0.3          # the temperature 3x as strongly (easy to overcool)
OXYGEN_USE: float = 0.01               # oxygen level you breathe away per s (with no pressure: 0.5 -> 0.25 in 25 s)
HEAT: float = 0.01                     # temperature level the drill heats up by per s at the surface,
HEAT_PER_METRE: float = 0.00005        # + this per metre of depth (500 m doubles it: cool harder the deeper you go)
HEAT_MAX: float = 0.1                  # but never more (reached at 1800 m), so the cooling can always keep up
# Start: (red valve, blue valve, level). Oxygen: the ideal is the blue valve's opening. Cooling: opening the blue valve
# more cools more (ideal temperature = 1 - its opening). Both start balanced around the middle.
OXYGEN_START: tuple[float, float, float] = (0.5, 0.7, 0.5)
COOLING_START: tuple[float, float, float] = (0.5, 0.55, 0.5)

# ---------------- Faults (src/faults.py) ----------------
# Each kind of fault: every <interval> seconds (a random time in that range) it has a <chance> to happen.
LIGHT_FAULT_INTERVAL: tuple[float, float] = (60.0, 120.0)   # a random breaker flips (always)
FAULT_INTERVAL: tuple[float, float] = (5.0, 15.0)           # a random valve starts drifting,
FAULT_CHANCE: float = 0.4                                   # with this chance (so about every 25 s)
VALVE_DRIFT_RATE: float = 0.02   # how fast a drifting valve creeps: of its whole range per s (2 % / s), either way
VALVE_DRIFT_AMOUNT: float = 0.15  # how far it creeps before it stops by itself: of its range (15 %, in ~7 s)

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
VALVE_FIX_TIME: float = 1.5      # seconds you hold a drifting valve to stabilize it (stops its drift)

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
