"""Engine: the drill's motor. The engine valve sets its power, the power button restarts it.

    engine = Engine(spinner, engine_valve, power_button, power_dial, audio.sources["engine"])
    engine.update(dt)    # every frame, after the valve and the button have updated

- Power = how far the engine valve is open: 0..ENGINE_VALVE_TURNS turns = 0..100 % (the valve stops there).
- `speed` (0..1) is how fast the motor really turns. It follows the power slowly (ENGINE_SPIN_UP / _DOWN: a heavy
  flywheel), so turning the valve down doesn't kill it straight away. The engine model spins at
  ENGINE_MAX_SPIN * speed, the engine sound's volume and pitch follow it, and the power dial on the console shows it
  (its red sector is 0..30 %, the rest of the face 30..100 %: ENGINE_DIAL_RED).
- The drill digs DRILL_SPEED * speed metres / s: `depth`.
- It runs at ENGINE_MIN_POWER (30 %) .. 100 %. When its speed drops below that it DIES and coasts down
  (ENGINE_COAST_RATE; `failing`: the main loop sounds the alarm). Press the power button in the control room while
  it still spins to restart it: that also turns the valve up to at least ENGINE_RESTART_POWER (40 %), so it
  doesn't die again straight away, and it STARTS: it speeds back up and is RUNNING again once past 30 %.
  Once it has stopped it is DEAD: the lights die and the drill explodes (death.py).
"""
from __future__ import annotations

from enum import Enum

from .audio import SoundSource
from .config import (
    DRILL_SPEED, ENGINE_COAST_RATE, ENGINE_DIAL_RED, ENGINE_MAX_SPIN, ENGINE_MIN_POWER, ENGINE_RESTART_POWER,
    ENGINE_RESTART_VALVE_SPIN, ENGINE_SOUND_PITCH, ENGINE_SOUND_VOLUME, ENGINE_SPIN_DOWN, ENGINE_SPIN_UP,
    ENGINE_START_POWER, ENGINE_VALVE_TURNS,
)
from .dial import Dial
from .interactable import Lever, Valve
from .spinner import Spinner


class EngineState(Enum):
    RUNNING = "running"
    DYING = "dying"         # its speed dropped below the minimum: coasting down, restart it with the power button
    STARTING = "starting"   # restarted: speeding back up to the minimum
    DEAD = "dead"           # stopped: the drill explodes


class Engine:
    def __init__(self, spinner: Spinner, valve: Valve, button: Lever, dial: Dial | None = None,
                 sound: SoundSource | None = None) -> None:
        self.spinner: Spinner = spinner
        self.valve: Valve = valve
        self.button: Lever = button
        self.dial: Dial | None = dial
        self.sound: SoundSource | None = sound
        valve.max_angle = 360.0 * ENGINE_VALVE_TURNS
        valve.set_angle(valve.max_angle * ENGINE_START_POWER)
        if dial is not None:   # a full turn from the red sector's first edge: see _dial_value
            dial.start = ENGINE_DIAL_RED[0]
            dial.sweep = 360.0
        self.state: EngineState = EngineState.RUNNING
        self.speed: float = ENGINE_START_POWER
        self.depth: float = 0.0   # metres dug so far
        self._valve_target: float | None = None   # the angle a restart is turning the valve up to
        for part in (spinner, valve, button):   # its state shows in the debug panel when you look at them
            part.debug_extra = self.debug_lines

    @property
    def power(self) -> float:
        """0..1: how far the engine valve is open."""
        return self.valve.angle / self.valve.max_angle

    @property
    def failing(self) -> bool:
        """Dying or dead: the alarm goes while this is True."""
        return self.state in (EngineState.DYING, EngineState.DEAD)

    @property
    def dead(self) -> bool:
        """Stopped for good: the drill blows up (death.py)."""
        return self.state == EngineState.DEAD

    def _set_state(self, state: EngineState, message: str) -> None:
        self.state = state
        print(f"ENGINE: {message}")

    def _turn_valve_up(self) -> None:
        """After a restart: turn the valve by itself (valve.spin) until it is ENGINE_RESTART_POWER open."""
        target = self.valve.max_angle * ENGINE_RESTART_POWER
        if self.valve.angle < target:
            self._valve_target = target
            self.valve.spin = ENGINE_RESTART_VALVE_SPIN

    def update(self, dt: float) -> None:
        if self._valve_target is not None and self.valve.angle >= self._valve_target:
            self.valve.spin = 0.0
            self._valve_target = None

        if self.state == EngineState.RUNNING and self.speed < ENGINE_MIN_POWER:
            self._set_state(EngineState.DYING, f"died at {self.power:.0%} power; press the power button while it "
                                               f"still spins")
        elif self.state == EngineState.DYING:
            if self.button.flipped:
                self._turn_valve_up()
                self._set_state(EngineState.STARTING, f"restarting at {self.speed:.0%} speed")
            elif self.speed <= 0:
                self._set_state(EngineState.DEAD, "stopped")
        elif self.state == EngineState.STARTING:
            if self.speed >= ENGINE_MIN_POWER:
                self._set_state(EngineState.RUNNING, f"running again at {self.power:.0%} power")
            elif self._valve_target is None and self.power < ENGINE_MIN_POWER:
                self._set_state(EngineState.DYING, f"valve turned down to {self.power:.0%} while restarting")

        # how fast it really turns: slowly towards the power while it runs, coasting down once it died
        if self.state in (EngineState.RUNNING, EngineState.STARTING):
            if self.power > self.speed:
                self.speed = min(self.speed + ENGINE_SPIN_UP * dt, self.power)
            else:
                self.speed = max(self.speed - ENGINE_SPIN_DOWN * dt, self.power)
        else:
            self.speed = max(self.speed - ENGINE_COAST_RATE * dt, 0.0)

        self.depth += DRILL_SPEED * self.speed * dt   # it digs as fast as it turns (more fuel to go faster: later)
        self.spinner.speed = ENGINE_MAX_SPIN * self.speed
        if self.dial is not None:
            self.dial.value = self.dial.low + (self.dial.high - self.dial.low) * self._dial_fraction()
        if self.sound is not None:
            self.sound.volume = ENGINE_SOUND_VOLUME * self.speed
            low, high = ENGINE_SOUND_PITCH
            self.sound.pitch = low + (high - low) * self.speed

    def _dial_fraction(self) -> float:
        """How far round the power dial's face (0..1 of a turn from the red sector's first edge) the speed is:
        0..ENGINE_MIN_POWER fills the red sector, the rest of the speed the rest of the face."""
        red_from, red_to = ENGINE_DIAL_RED
        red = (red_to - red_from) / 360.0
        if self.speed < ENGINE_MIN_POWER:
            return red * self.speed / ENGINE_MIN_POWER
        return red + (1.0 - red) * (self.speed - ENGINE_MIN_POWER) / (1.0 - ENGINE_MIN_POWER)

    def debug_lines(self) -> list[str]:
        return [f"engine: {self.state.value}, power {self.power:.0%}, speed {self.speed:.0%}, depth {self.depth:.0f} m"]
