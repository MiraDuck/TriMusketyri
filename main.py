"""Entry point. Run from anywhere: python main.py"""
from __future__ import annotations

import random
from pathlib import Path

import pyray as pr

from src import config
from src.audio import Audio
from src.controls import handle_hotkeys, handle_interaction, move_axes, move_camera
from src.debug import DebugOptions, looked_at
from src.dial import Dial
from src.entity import Entity
from src.faults import FaultDirector
from src.head_bob import HeadBob
from src.interactable import Interactable, Lever, Valve
from src.lighting import Lamp, Light, Lighting
from src.menu import MainMenu, MenuChoice
from src.player import Player
from src.render import draw_hud, draw_scene
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
    audio.play_music(config.MENU_MUSIC)
    menu = MainMenu()
    choice = menu.run(audio)
    menu.unload()
    if choice == MenuChoice.QUIT:
        audio.unload()
        pr.close_window()
        return
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

    cars = drill_cars()
    # each light only lights its own car (no shadows to stop it at the walls)
    lamps = [Lamp(f"lamp_{car.name}", pr.vector3_add(car.pos, config.LAMP_OFFSET), zone=car_zone(car.pos.z))
             for car in cars]
    car_lamp = {car.name: lamp for car, lamp in zip(cars, lamps)}
    # moving parts are modelled in place in their car, so they go at that car's position; named after the file
    car_pos = {car.name: car.pos for car in cars}
    models = config.MODELS_DIR
    valve = Valve("valve", config.VALVE_MODEL, config.VALVE_POS)
    interactables: list[Interactable] = [
        Lever("lever", config.LEVER_MODEL, config.LEVER_POS), valve,
        *[Valve(Path(f).stem.lower(), models / f, car_pos[car]) for car, f in config.VALVES],
        *[Lever(Path(f).stem.lower(), models / f, car_pos[car], throw=throw) for car, f, throw in config.SWITCHES],
    ]
    dials = [Dial(Path(f).stem.lower(), models / f, car_pos[car], low, high, sweep)
             for car, f, low, high, sweep in config.DIALS]
    dials += [Dial(Path(f).stem.lower(), models / f, car_pos[car], low, high, slide=distance)
              for car, f, low, high, distance in config.SLIDING_DIALS]
    decorations = [Entity(Path(f).stem.lower(), models / f, car_pos[car]) for car, f in config.DECORATIONS]
    spinners = [Spinner(Path(f).stem.lower(), models / f, car_pos[car], speed) for car, f, speed in config.SPINNERS]
    entities: list[Entity] = [*cars, *lamps, *decorations, *interactables, *dials, *spinners]
    colliders = [e.collider for e in entities if e.collider is not None]
    held: Interactable | None = None   # what the player is holding (a valve), None = mouse look is on
    switches = {i.name: i for i in interactables if isinstance(i, Lever)}
    breaker_lamps = [(switches[breaker], car_lamp[car]) for breaker, car in config.BREAKER_LAMPS.items()]

    lighting = Lighting([lamp.light for lamp in lamps] +
                        [Light(*light, zone=car_zone(light[0].z)) for light in config.LIGHTS])
    for entity in [*cars, *decorations, *interactables, *dials, *spinners]:   # not the lamps: they are the light, drawn unlit
        lighting.add(entity.model)

    vignette = Vignette()
    player = Player(camera)
    bob = HeadBob()
    debug = DebugOptions()
    faults = FaultDirector([breaker for breaker, _ in breaker_lamps])
    valve_break_at = config.VALVE_BREAK_TEST_AT
    dial_test_at = 0.0   # TEST (remove): next time the dials get new random values

    pr.rl_set_line_width(2)

    while not pr.window_should_close():
        dt: float = min(pr.get_frame_time(), config.MAX_DT)
        audio.update(camera)   # the real camera is the listener (sources get their volume / pan from it)

        # ---- input ----
        camera_mode = handle_hotkeys(camera, camera_mode, debug)
        held = handle_interaction(camera, interactables, held)
        move_camera(camera, camera_mode, dt, look=held is None)

        # ---- world ----
        faults.update(dt)   # every 5-15 s something may break (a breaker trips)
        if pr.is_key_pressed(pr.KeyboardKey.KEY_F3):   # debug: break something now
            faults.cause_fault()
        # Emergency example: set VALVE_BREAK_TEST_AT in config and the valve starts turning by itself then.
        # Real faults will do the same from the fault director: valve.spin = speed (0 = repaired).
        if valve_break_at is not None and pr.get_time() >= valve_break_at:
            valve.spin = config.VALVE_BREAK_SPIN   # degrees / s; positive opens, negative closes
            valve_break_at = None
        # TEST (remove): every 0.1 s each dial's value goes up or down by up to 3
        if pr.get_time() >= dial_test_at:
            for d in dials:
                d.value = min(max(d.value + random.uniform(-3.0, 3.0), d.low), d.high)
            dial_test_at = pr.get_time() + 0.1
        for thing in [*interactables, *dials, *spinners]:
            thing.update(dt)
        for breaker, lamp in breaker_lamps:   # up = on; it switches as the handle passes halfway
            lamp.light.on = not breaker.thrown

        # ---- player ----
        if camera_mode == pr.CameraMode.CAMERA_FIRST_PERSON:
            player.update(dt, colliders)
            forward, sideway = move_axes()
            bob.update(forward != 0 or sideway != 0, sideway, forward, dt)
            view_camera = bob.apply(camera)
        else:
            player.colliding = False
            view_camera = camera

        # ---- draw ----
        now = pr.get_time()
        for lamp in lamps:
            lamp.update(now)
        lighting.set_enabled(not debug.unlit)
        lighting.update(now)
        pr.begin_drawing()
        pr.clear_background(pr.RAYWHITE)
        inspected = looked_at(camera, entities) if debug.hitboxes else None   # its details go in the HUD
        draw_scene(view_camera, camera, player, entities, lighting.lights, debug, inspected)
        if not debug.no_vignette:
            vignette.draw()   # after the scene, before the HUD so the HUD stays readable
        draw_hud(camera, camera_mode, player, debug, inspected)
        pr.end_drawing()

    for entity in entities:
        entity.unload()
    lighting.unload()
    vignette.unload()
    audio.unload()
    pr.close_window()


if __name__ == "__main__":
    main()
