"""Entry point. Run from anywhere: python main.py"""
from __future__ import annotations

from pathlib import Path

import pyray as pr

from src import config
from src.alarm import Alarm
from src.audio import Audio
from src.controls import handle_hotkeys, handle_interaction, move_axes, move_camera
from src.death import Death
from src.debug import DebugOptions, looked_at
from src.dial import Dial
from src.engine import Engine
from src.entity import Entity
from src.faults import FaultDirector
from src.head_bob import HeadBob
from src.interactable import Button, Interactable, Lever, Valve
from src.life_support import LifeSupport, Regulator
from src.lighting import Lamp, Light, Lighting
from src.menu import MainMenu, MenuChoice
from src.player import Player
from src.render import draw_hud, draw_scene
from src.screens import Screens
from src.spinner import Spinner
from src.vignette import Vignette


def car_zone(z: float) -> tuple[float, float]:
    """The z range of the car that z is in (cars are CAR_LENGTH long, centred on their position)."""
    d, half = config.DRILL_POS, config.CAR_LENGTH / 2
    i = round((d.z - z) / config.CAR_LENGTH)
    return d.z - i * config.CAR_LENGTH - half, d.z - i * config.CAR_LENGTH + half


def drill_cars() -> list[Entity]:
    """The cars from config.DRILL_CARS, the first at DRILL_POS and each next one CAR_LENGTH further along -z."""
    d = config.DRILL_POS
    return [
        Entity(name, model, pr.Vector3(d.x, d.y, d.z - i * config.CAR_LENGTH), collision_path=collision)
        for i, (name, model, collision) in enumerate(config.DRILL_CARS)
    ]


def main() -> None:
    pr.set_trace_log_level(pr.TraceLogLevel.LOG_WARNING)
    pr.init_window(config.SCREEN_W, config.SCREEN_H, config.WINDOW_TITLE)
    pr.set_target_fps(config.TARGET_FPS)
    audio = Audio(config.AMBIENCE_DIR)
    while True:   # menu, a game, and back to the menu when you die
        audio.play_music(config.MENU_MUSIC)
        menu = MainMenu()
        choice = menu.run(audio)
        menu.unload()
        if choice == MenuChoice.QUIT or not play(audio):
            break
    audio.unload()
    pr.close_window()


def play(audio: Audio) -> bool:
    """One game, from the spawn until you die (True: back to the menu) or close the window (False)."""
    pr.disable_cursor()

    # `camera` is the player's real position (input and physics move it); what we draw from is a copy of it
    # with head bob added (view_camera below), so the bob can never affect collision.
    camera = pr.Camera3D(
        config.START_POSITION,
        config.START_TARGET,
        pr.Vector3(0.0, 1.0, 0.0),
        config.CAMERA_FOVY,
        pr.CameraProjection.CAMERA_PERSPECTIVE,
    )
    camera_mode: int = pr.CameraMode.CAMERA_FIRST_PERSON

    audio.stop_music()   # the menu theme
    if config.START_MUSIC:
        audio.play_music(config.START_MUSIC)
    for filename, pos, volume, near, far, floor in config.SOUND_SOURCES:
        audio.add_source(filename, pos, volume, near, far, floor)
    switch_sound = audio.load_sound(config.SWITCH_SOUND)
    switch_sounds = {name: audio.load_sound(f) for name, f in config.SWITCH_SOUNDS.items()}
    valve_sound = audio.load_sound(config.VALVE_SOUND)
    alarm_sound = audio.load_sound(config.ALARM_SOUND)
    death_sound = audio.load_sound(config.DEATH_SOUND)

    cars = drill_cars()
    # each light only lights its own car (no shadows to stop it at the walls)
    lamps = [Lamp(f"lamp_{car.name}", pr.vector3_add(car.pos, config.LAMP_OFFSET), zone=car_zone(car.pos.z))
             for car in cars]
    car_lamp = {car.name: lamp for car, lamp in zip(cars, lamps)}
    # moving parts are modelled in place in their car, so they go at that car's position; named after the file
    car_pos = {car.name: car.pos for car in cars}
    models = config.MODELS_DIR
    interactables: list[Interactable] = [
        *[Valve(Path(f).stem.lower(), models / f, car_pos[car]) for car, f in config.VALVES],
        *[Lever(Path(f).stem.lower(), models / f, car_pos[car], throw=throw) for car, f, throw in config.SWITCHES],
        *[Button(name, models / f, car_pos[car], throw=throw) for car, f, name, throw in config.BUTTONS],
    ]
    dials = [Dial(Path(f).stem.lower(), models / f, car_pos[car], low, high, sweep, start=start)
             for car, f, low, high, sweep, start in config.DIALS]
    dials += [Dial(Path(f).stem.lower(), models / f, car_pos[car], low, high, slide=distance)
              for car, f, low, high, distance in config.SLIDING_DIALS]
    decorations = [Entity(Path(f).stem.lower(), models / f, car_pos[car],
                          collision_path=models / solid if solid else None)
                   for car, f, solid in config.DECORATIONS]
    decorations += [Entity(Path(f).stem.lower(), models / f, pr.vector3_add(car_pos[car], offset))
                    for car, f, offset in config.ITEMS]
    spinners = [Spinner(Path(f).stem.lower(), models / f, car_pos[car], speed) for car, f, speed in config.SPINNERS]
    entities: list[Entity] = [*cars, *lamps, *decorations, *interactables, *dials, *spinners]
    colliders = [e.collider for e in entities if e.collider is not None]
    held: Interactable | None = None   # what the player is holding (a valve), None = mouse look is on
    switches = {i.name: i for i in interactables if isinstance(i, Lever)}
    valves = {i.name: i for i in interactables if isinstance(i, Valve)}
    breaker_lamps = [(switches[breaker], car_lamp[car]) for breaker, car in config.BREAKER_LAMPS.items()]

    lighting = Lighting([lamp.light for lamp in lamps] +
                        [Light(*light, zone=car_zone(light[0].z)) for light in config.LIGHTS])
    for entity in [*cars, *decorations, *interactables, *dials, *spinners]:   # not the lamps: they are the light, drawn unlit
        lighting.add(entity.model)

    vignette = Vignette()
    player = Player(camera)
    bob = HeadBob()
    debug = DebugOptions()
    faults = FaultDirector([breaker for breaker, _ in breaker_lamps], list(valves.values()))
    engine = Engine(
        next(s for s in spinners if s.name == config.ENGINE_SPINNER), valves[config.ENGINE_VALVE],
        switches[config.ENGINE_BUTTON], next((d for d in dials if d.name == config.ENGINE_DIAL), None),
        audio.sources.get(config.ENGINE_SOUND),
    )
    named_dials = {d.name: d for d in dials}

    def regulator(name: str, parts: tuple[str, str, tuple[str, ...], tuple[str, ...]], coupling: float,
                  start: tuple[float, float, float], inverted: bool = False) -> Regulator:
        red, blue, pressure_dials, level_dials = parts
        return Regulator(name, valves[red], valves[blue], coupling, start,
                         [named_dials[d] for d in pressure_dials], [named_dials[d] for d in level_dials], inverted)

    life = LifeSupport(regulator("oxygen", config.OXYGEN_PARTS, config.OXYGEN_COUPLING, config.OXYGEN_START),
                       regulator("cooling", config.COOLING_PARTS, config.COOLING_COUPLING, config.COOLING_START,
                                 inverted=True))
    alarm = Alarm(lamps, audio, alarm_sound)
    death = Death(audio, death_sound)
    screens = Screens(car_pos["control_room"])

    pr.rl_set_line_width(2)

    died = False
    while not pr.window_should_close():
        dt: float = min(pr.get_frame_time(), config.MAX_DT)
        audio.update(camera)   # the real camera is the listener (sources get their volume / pan from it)

        # ---- dead: once the screen is black (exploded / passed out) only the death screen is left ----
        death.update(dt)
        if death.over:
            pr.begin_drawing()
            death.draw()
            pr.end_drawing()
            if death.finished:
                died = True
                break
            continue

        # ---- input ----
        camera_mode = handle_hotkeys(camera, camera_mode, debug)
        held = handle_interaction(camera, interactables, held)
        move_camera(camera, camera_mode, dt, look=held is None)

        # ---- world ----
        faults.update(dt)   # breakers flip, valves drift
        if pr.is_key_pressed(pr.KeyboardKey.KEY_F3):   # debug: break something now
            faults.cause_fault()
        for thing in [*interactables, *dials]:
            thing.update(dt)
        engine.update(dt)   # after its valve and lever, before the spinner turns it
        life.update(dt, engine.depth)   # oxygen + cooling, after their valves; they set their dials for next frame
        if life.cause:   # passed out
            death.start(life.cause, engine.depth)
        for spinner in spinners:
            spinner.update(dt)
        for breaker, lamp in breaker_lamps:   # up = on; it switches as the handle passes halfway
            lamp.light.on = not breaker.thrown
        if engine.dead:   # stopped for good: every light goes out (the breakers can't help) and the drill blows
            death.start(config.DEATH_TEXT_ENGINE, engine.depth, explode=True)
            for light in lighting.lights:
                light.on = False
        alarm.active = engine.failing   # red flashing lamps + beeps until the motor runs again (none once dark)
        alarm.update(pr.get_time(), camera)

        # ---- sounds of the parts, from where they are ----
        for switch in switches.values():
            if switch.flipped:   # clicked or flipped by a fault
                audio.play_sound_at(switch_sounds.get(switch.name, switch_sound), switch.center, camera,
                                    config.SFX_NEAR, config.SFX_FAR)
        for valve in valves.values():
            if valve.turning and not audio.is_sound_playing(valve_sound):
                audio.play_sound_at(valve_sound, valve.center, camera, config.SFX_NEAR, config.SFX_FAR)

        # ---- player ----
        if camera_mode == pr.CameraMode.CAMERA_FIRST_PERSON:
            player.update(dt, colliders)
            forward, sideway = move_axes()
            bob.update(forward != 0 or sideway != 0, sideway, forward, dt)
            view_camera = bob.apply(camera)
        else:
            player.colliding = False
            view_camera = camera
        view_camera = death.shake(view_camera)   # harder and harder until the drill blows

        # ---- draw ----
        now = pr.get_time()
        for lamp in lamps:
            lamp.update(now)
        lighting.set_enabled(not debug.unlit)
        lighting.update(now)
        screens.update(dt, engine.depth, config.DRILL_SPEED * engine.speed, engine.speed, not engine.dead)
        pr.begin_drawing()
        pr.clear_background(pr.RAYWHITE)
        inspected = looked_at(camera, entities) if debug.hitboxes else []   # their details go in the HUD
        draw_scene(view_camera, camera, player, entities, lighting.lights, debug, inspected, screens)
        if not debug.no_vignette:
            vignette.draw()   # after the scene, before the HUD so the HUD stays readable
        draw_hud(camera, camera_mode, player, debug, inspected)
        death.draw()   # passing out: the screen goes dark
        pr.end_drawing()

    for entity in entities:
        entity.unload()
    lighting.unload()
    vignette.unload()
    screens.unload()
    death.unload()
    audio.clear()   # this game's sounds and music; the menu starts its own
    return died


if __name__ == "__main__":
    main()
