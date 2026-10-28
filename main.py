"""Entry point. Run from anywhere: python main.py"""
from __future__ import annotations

import random
from pathlib import Path

import pyray as pr

from src import config
from src.alarm import Alarm
from src.audio import Audio
from src.call import Call
from src.controls import handle_hotkeys, handle_interaction, move_axes, move_camera
from src.computer import Computer, Status
from src.death import Death
from src.debug import DebugOptions, looked_at
from src.dial import Dial
from src.engine import Engine
from src.entity import Entity
from src import ui
from src.faults import FaultDirector
from src.fuel import CoalPile, Fuel, Hatch
from src.head_bob import HeadBob
from src.interactable import Button, Interactable, Lever, Valve
from src.life_support import LifeSupport, Regulator
from src.lighting import Lamp, Light, Lighting
from src.menu import MainMenu, MenuChoice
from src.pause import pause_menu
from src.pipes import Pipe, Pipes
from src.player import Player
from src.render import draw_hud, draw_scene
from src.screens import Screens
from src.spinner import Spinner
from src.stats import StatsScreen
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
    pr.set_exit_key(pr.KeyboardKey.KEY_NULL)   # Esc pauses the game (and quits the menu itself), not raylib
    audio = Audio(config.AMBIENCE_DIR)
    while True:   # menu (and its statistics), a game, and back to the menu when you die or leave
        audio.play_music(config.MENU_MUSIC)
        menu = MainMenu()
        choice = menu.run(audio)
        while choice == MenuChoice.STATS:
            choice = menu.run(audio) if StatsScreen().run(audio, menu.draw_background) else MenuChoice.QUIT
        menu.unload()
        if choice == MenuChoice.QUIT or not play(audio):
            break
    ui.unload()
    audio.unload()
    pr.close_window()


def play(audio: Audio) -> bool:
    """One game, from the spawn until you die or leave it from the pause menu (True: back to the menu) or close the
    window (False). Esc pauses it (pause.py)."""
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
    step_sound = audio.load_sound(config.STEP_SOUND)
    breath_sound = audio.load_sound(config.BREATH_SOUND)
    ringing_sound = audio.load_sound(config.EARS_RINGING_SOUND)
    repair_sound = audio.load_sound(config.PIPE_REPAIR_SOUND)
    take_sound = audio.load_sound(config.COAL_TAKE_SOUND)
    feed_sound = audio.load_sound(config.COAL_FEED_SOUND)

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
        Button("computer_lever", models / config.COMPUTER_LEVER, car_pos[config.COMPUTER_CAR],
               throw=config.COMPUTER_LEVER_THROW, bone_axis="x"),
    ]
    pile_car, pile_file, pile_solid = config.COAL_PILE
    coal_pile = CoalPile("coal_stockpile", models / pile_file, car_pos[pile_car], collision_path=models / pile_solid)
    hatch_car, hatch_file = config.HATCH
    hatch = Hatch("engine_hatch", models / hatch_file, car_pos[hatch_car], throw=config.HATCH_THROW,
                  flip_time=config.HATCH_OPEN_TIME)
    interactables += [coal_pile, hatch]
    coal = Entity("coal", models / config.COAL_MODEL, pr.Vector3(0.0, 0.0, 0.0))   # the piece you carry
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
    for entity in [*cars, *decorations, *interactables, *dials, *spinners, coal]:   # not the lamps: they are the light, drawn unlit
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
    fuel = Fuel(coal_pile, hatch, coal, audio, take_sound, feed_sound, named_dials.get(config.FUEL_DIAL))

    def regulator(name: str, parts: tuple[str, str, tuple[str, ...], tuple[str, ...]], coupling: float,
                  start: tuple[float, float, float], inverted: bool = False) -> Regulator:
        red, blue, pressure_dials, level_dials = parts
        return Regulator(name, valves[red], valves[blue], coupling, start,
                         [named_dials[d] for d in pressure_dials], [named_dials[d] for d in level_dials], inverted)

    life = LifeSupport(regulator("oxygen", config.OXYGEN_PARTS, config.OXYGEN_COUPLING, config.OXYGEN_START),
                       regulator("cooling", config.COOLING_PARTS, config.COOLING_COUPLING, config.COOLING_START,
                                 inverted=True))
    systems = {"oxygen": life.oxygen, "cooling": life.cooling}
    # the air you can hear: the oxygen from its tank, the cooling from every car's vent (volumes set every frame)
    airs = [(audio.add_source(config.AIR_FLOW_SOUND, valves[config.OXYGEN_PARTS[0]].center, 0.0,
                              *config.AIR_FLOW_RANGE, name="air_oxygen"), life.oxygen, config.AIR_FLOW_VOLUME)]
    airs += [(audio.add_source(config.AIR_VENT_SOUND, lamp.pos, 0.0, *config.AIR_VENT_RANGE, name=f"air_{car.name}"),
              life.cooling, config.AIR_VENT_VOLUME) for car, lamp in zip(cars, lamps)]
    pipe_parts = [Pipe(f"{Path(f).stem.lower()}_{car}", models / f, models / burst, car_pos[car], systems[system],
                       crack, car_zone(car_pos[car].z))
                  for car, system, f, burst, crack in config.PIPES]
    pipe_car = {pipe: car for pipe, (car, *_) in zip(pipe_parts, config.PIPES)}
    pipes = Pipes(pipe_parts, audio, repair_sound)
    entities += pipe_parts
    colliders += [pipe.collider for pipe in pipe_parts if pipe.collider is not None]
    for pipe in pipe_parts:
        lighting.add(pipe.whole_model)
        lighting.add(pipe.burst_model)
    fog = pr.Color(*(int(c * 255) for c in config.FOG_COLOR), 255)   # also behind everything
    alarm = Alarm(lamps, audio, alarm_sound)
    death = Death(audio, death_sound, ringing_sound)
    screens = Screens(car_pos["control_room"])
    call = Call(audio, audio.load_sound(config.INTRO_CALL))   # the phone call: the drill waits until it's over
    computer = Computer(switches["computer_lever"], car_pos[config.COMPUTER_CAR], audio, call)

    def die(cause: str, explode: bool = False) -> None:
        """Mission failed: the record only knows what the computer sent (no report: no depth, no cause)."""
        reported = computer.sent > 0
        death.start(cause if reported else None, computer.last_depth, survived, explode)

    def status() -> Status:
        """What the computer shows and sends: the drill's readings."""
        return Status(engine.depth, engine.speed, engine.state.value, fuel.level, life.oxygen.level,
                      life.cooling.level)

    pr.rl_set_line_width(2)

    back_to_menu = False
    paused = False
    survived = 0.0   # seconds played (not paused), for the run's report
    ears_ringing = False   # rang since the strain last climbed (re-armed once it is low again)
    view_camera = camera
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
                back_to_menu = True
                break
            continue

        # ---- paused: Esc (not while dying); the game stands still under the question (drawn below) ----
        if pr.is_key_pressed(pr.KeyboardKey.KEY_ESCAPE) and not death.active:
            paused = not paused
            pr.enable_cursor() if paused else pr.disable_cursor()
            call.pause() if paused else call.resume()

        if not paused:
            # during the call at the start nothing happens in the drill: its time stands still (`world`)
            call.update(dt)
            world = 0.0 if call.active else dt
            survived += world if not death.active else 0.0
            # ---- input ----
            camera_mode = handle_hotkeys(camera, camera_mode, debug)
            held = handle_interaction(camera, interactables, held)
            move_camera(camera, camera_mode, dt, look=held is None)

            # ---- world ----
            if not call.active:
                faults.update(dt)   # breakers flip, valves drift
            if debug.menu and pr.is_key_pressed(pr.KeyboardKey.KEY_F5):   # debug: break something now
                faults.cause_fault()
            if debug.menu and pr.is_key_pressed(pr.KeyboardKey.KEY_F4):   # debug: burst a pipe now
                whole = [pipe for pipe in pipe_parts if not pipe.burst]
                if whole:
                    pipes.burst(random.choice(whole))
            for thing in [*interactables, *dials]:
                thing.update(dt)
            fuel.update(world, camera, engine.speed, engine.depth)   # take coal, the hatch, feed it; the engine burns it
            engine.update(world, fuel.factor)   # after its valve, lever and fuel, before the spinner turns it
            # oxygen + cooling, after their valves (overclocking heats the drill); they set their dials for next frame
            life.update(world, engine.depth, fuel.heat)
            if life.cause:   # passed out
                die(life.cause)
            pipes.update(world, camera, pr.is_key_down(pr.KeyboardKey.KEY_E))   # bursts (by pressure), hold E to fix
            computer.update(dt, camera, status())   # skips the call, collects, then its lever sends the status
            for spinner in spinners:
                spinner.update(dt)
            for breaker, lamp in breaker_lamps:   # up = on; it switches as the handle passes halfway
                lamp.light.on = not breaker.thrown
            if engine.dead:   # stopped for good: every light goes out (the breakers can't help) and the drill blows
                out_of_fuel = fuel.level < config.FUEL_LOW
                die(config.DEATH_TEXT_FUEL if out_of_fuel else config.DEATH_TEXT_ENGINE, explode=True)
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
            # breathing hard while you are about to pass out: louder the closer you are
            breath = (life.strain - config.BREATH_FROM) / (1.0 - config.BREATH_FROM)
            quiet, loud = config.BREATH_VOLUME
            volume = quiet + (loud - quiet) * min(breath, 1.0) if breath > 0 else 0.0
            if volume > 0 and not audio.is_sound_playing(breath_sound):
                audio.play_sound(breath_sound, audio.sfx_volume * volume)
            elif audio.is_sound_playing(breath_sound):
                audio.set_sound_volume(breath_sound, volume)
            # and your ears ring (quietly) as it gets close, once each time
            if ears_ringing and life.strain < config.BREATH_FROM:
                ears_ringing = False
            elif not ears_ringing and life.strain > config.EARS_RINGING_FROM:
                ears_ringing = True
                audio.play_sound(ringing_sound, audio.sfx_volume * config.EARS_RINGING_VOLUME)
            # the air: louder and higher the harder its system pushes
            low, high = config.AIR_PITCH
            for name, system, loudness in airs:
                audio.sources[name].volume = loudness * system.pressure
                audio.sources[name].pitch = low + (high - low) * system.pressure

            # ---- player ----
            if camera_mode == pr.CameraMode.CAMERA_FIRST_PERSON:
                player.update(dt, colliders)
                forward, sideway = move_axes()
                bob.update(forward != 0 or sideway != 0, sideway, forward, dt)
                if bob.stepped and player.on_ground:   # a footstep, a little different each time
                    audio.play_sound(step_sound, audio.sfx_volume * config.STEP_VOLUME, pitch=random.uniform(0.9, 1.1))
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
        lighting.set_fog(view_camera.position)
        lighting.update(now)
        screens.update(0.0 if paused else dt, engine.depth, config.DRILL_SPEED * engine.speed, engine.speed,
                       not engine.dead)
        pr.begin_drawing()
        pr.clear_background(fog)
        inspected = looked_at(camera, entities) if debug.hitboxes else []   # their details go in the HUD
        steam_light = lambda pipe: 1.0 if car_lamp[pipe_car[pipe]].light.on else 0.2   # dim in a dark car
        draw_scene(view_camera, camera, player, entities, lighting.lights, debug, inspected,
                   (screens.draw, computer.draw, lambda: pipes.draw(view_camera, steam_light),
                    lambda: fuel.draw_held(view_camera)))   # last: over everything
        if not debug.no_vignette:
            vignette.draw()   # after the scene, before the HUD so the HUD stays readable
        draw_hud(camera, camera_mode, player, debug, inspected)
        pipes.draw_smoke(camera.position.z)   # over the HUD too: you are in it
        pipes.draw_hud()   # the repair ring, the blink
        death.draw()   # passing out: the screen goes dark
        choice = pause_menu() if paused else None
        pr.end_drawing()
        if choice == "leave":   # the run is not saved
            back_to_menu = True
            break
        if choice == "resume":
            paused = False
            pr.disable_cursor()
            call.resume()

    for entity in [*entities, coal]:
        entity.unload()
    lighting.unload()
    vignette.unload()
    screens.unload()
    pipes.unload()
    computer.unload()
    audio.clear()   # this game's sounds and music; the menu starts its own
    return back_to_menu


if __name__ == "__main__":
    main()
