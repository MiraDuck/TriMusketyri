"""Faults: things breaking on their own while you play.

    faults = FaultDirector(breakers, valves, flicker)   # flicker: starts the lights' flicker (flicker.py)
    faults.update(dt)    # every frame

Each kind of fault has its own schedule: every `interval` seconds (a random time in that range) it rolls `chance`
and on a hit it happens. To add one: a method that makes it happen and returns True (False if it can't happen
now), plus a `_Schedule` for it in `self._schedules`.

Faults so far:
  - Lights (every LIGHT_FAULT_INTERVAL, always): a random breaker flips by itself, so its car's lamp goes out, or
    comes back on if it was off. Flip it back to fix it. With BREAKER_GROUP_CHANCE it takes its neighbours along:
    BREAKER_GROUP_SIZE breakers side by side all flip, or all go off, or all come on, at the same time.
  - Drift (every FAULT_INTERVAL, FAULT_CHANCE): a random valve that isn't drifting yet creeps a little open or
    shut by itself (VALVE_DRIFT_AMOUNT of its range at VALVE_DRIFT_RATE, then it stops), pushing its system
    (oxygen, cooling, the engine's power) off a bit. Go and turn it back (holding it for VALVE_FIX_TIME stops it
    sooner).
  - Flicker (every FLICKER_INTERVAL, FLICKER_CHANCE): the lights in the cars next to you stutter for a moment.
    Nothing to fix.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from .config import (
    BREAKER_GROUP_CHANCE, BREAKER_GROUP_SIZE, FAULT_CHANCE, FAULT_INTERVAL, FLICKER_CHANCE, FLICKER_INTERVAL,
    LIGHT_FAULT_INTERVAL, VALVE_DRIFT_AMOUNT, VALVE_DRIFT_RATE,
)
from .interactable import Lever, Valve


@dataclass
class _Schedule:
    fault: Callable[[], bool]
    interval: tuple[float, float]
    chance: float
    until_next: float = field(init=False)

    def __post_init__(self) -> None:
        self.until_next = random.uniform(*self.interval)


class FaultDirector:
    def __init__(self, breakers: list[Lever], valves: list[Valve], flicker: Callable[[], bool]) -> None:
        self.breakers: list[Lever] = breakers   # in the order they sit on the wall
        self.valves: list[Valve] = valves
        self._schedules: list[_Schedule] = [
            _Schedule(self._flip_breakers, LIGHT_FAULT_INTERVAL, 1.0),
            _Schedule(self._drift_valve, FAULT_INTERVAL, FAULT_CHANCE),
            _Schedule(flicker, FLICKER_INTERVAL, FLICKER_CHANCE),
        ]

    def update(self, dt: float) -> None:
        for schedule in self._schedules:
            schedule.until_next -= dt
            if schedule.until_next <= 0:
                schedule.until_next = random.uniform(*schedule.interval)
                if random.random() < schedule.chance:
                    schedule.fault()

    def cause_fault(self) -> bool:
        """Make one random fault happen now (tries the others if it can't). False if none could. (F3)"""
        for schedule in random.sample(self._schedules, len(self._schedules)):
            if schedule.fault():
                return True
        return False

    def _flip_breakers(self) -> bool:
        """One breaker flips, or with BREAKER_GROUP_CHANCE a few side by side: each to its other side, or all off,
        or all on. Always changes something: if they all are where they would go, they flip instead."""
        if not self.breakers:
            return False
        grouped = random.random() < BREAKER_GROUP_CHANCE
        size = min(random.randint(*BREAKER_GROUP_SIZE) if grouped else 1, len(self.breakers))
        first = random.randrange(len(self.breakers) - size + 1)
        group = self.breakers[first:first + size]
        down = random.choice((None, False, True))   # flip, all on, all off
        if all(breaker.down == down for breaker in group):
            down = None
        for breaker in group:
            breaker.down = not breaker.down if down is None else down
            print(f"FAULT: {breaker.name} flipped {'down' if breaker.down else 'up'}")
        return True

    def _drift_valve(self) -> bool:
        steady = [valve for valve in self.valves if not valve.drift]
        if not steady:
            return False
        valve = random.choice(steady)
        direction = random.choice((-1.0, 1.0))
        full = valve.max_angle or 360.0
        valve.start_drift(direction * VALVE_DRIFT_RATE * full, VALVE_DRIFT_AMOUNT * full)
        print(f"FAULT: {valve.name} drifting {'open' if direction > 0 else 'shut'}")
        return True
