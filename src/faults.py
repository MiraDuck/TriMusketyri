"""Faults: things breaking on their own while you play.

    faults = FaultDirector(breakers)
    faults.update(dt)    # every frame

Each kind of fault has its own schedule: every `interval` seconds (a random time in that range) it rolls `chance`
and on a hit it happens. To add one: a method that makes it happen and returns True (False if it can't happen
now), plus a `_Schedule` for it in `self._schedules`. Valve faults will use FAULT_INTERVAL / FAULT_CHANCE.

Faults so far:
  - Lights (every LIGHT_FAULT_INTERVAL, always): a random breaker flips by itself, so its car's lamp goes out, or
    comes back on if it was off. Flip it back to fix it.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from .config import LIGHT_FAULT_INTERVAL
from .interactable import Lever


@dataclass
class _Schedule:
    fault: Callable[[], bool]
    interval: tuple[float, float]   # seconds between rolls, random in this range
    chance: float                   # of happening on each roll (1 = every time)
    until_next: float = field(init=False)

    def __post_init__(self) -> None:
        self.until_next = random.uniform(*self.interval)


class FaultDirector:
    def __init__(self, breakers: list[Lever]) -> None:
        self.breakers: list[Lever] = breakers
        self._schedules: list[_Schedule] = [
            _Schedule(self._flip_breaker, LIGHT_FAULT_INTERVAL, 1.0),
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

    def _flip_breaker(self) -> bool:
        if not self.breakers:
            return False
        breaker = random.choice(self.breakers)
        breaker.down = not breaker.down   # swings like a click would; the main loop switches its lamp
        print(f"FAULT: {breaker.name} flipped {'down' if breaker.down else 'up'}")
        return True
