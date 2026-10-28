"""Faults: things breaking on their own while you play.

    faults = FaultDirector(breakers)
    faults.update(dt)    # every frame

Every FAULT_INTERVAL seconds (a random time in that range) it rolls FAULT_CHANCE; on a hit one of the faults that
can happen right now happens (picked at random). To add a fault, add a method that makes it happen and returns
True (False if it can't happen now, e.g. every breaker is already down), and list it in `self._faults`.

Faults so far:
  - A breaker trips: it flips down by itself, so its car's lamp goes out. Flip it back up to fix it.
"""
from __future__ import annotations

import random
from typing import Callable

from .config import FAULT_CHANCE, FAULT_INTERVAL
from .interactable import Lever


class FaultDirector:
    def __init__(self, breakers: list[Lever]) -> None:
        self.breakers: list[Lever] = breakers
        self.until_next: float = random.uniform(*FAULT_INTERVAL)   # seconds until the next roll
        self._faults: list[Callable[[], bool]] = [self._trip_breaker]

    def update(self, dt: float) -> None:
        self.until_next -= dt
        if self.until_next > 0:
            return
        self.until_next = random.uniform(*FAULT_INTERVAL)
        if random.random() < FAULT_CHANCE:
            self.cause_fault()

    def cause_fault(self) -> bool:
        """Make one random fault happen now (tries the others if it can't). False if none could."""
        for fault in random.sample(self._faults, len(self._faults)):
            if fault():
                return True
        return False

    def _trip_breaker(self) -> bool:
        up = [breaker for breaker in self.breakers if not breaker.down]
        if not up:
            return False
        breaker = random.choice(up)
        breaker.down = True   # swings down like a click would; the main loop turns its lamp off
        print(f"FAULT: {breaker.name} tripped")
        return True
