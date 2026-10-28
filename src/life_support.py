"""Life support: the oxygen and the cooling, both kept by valves in the oxygen room. Let either level drift out of
LIFE_SAFE for too long and you pass out (Death).

    life = LifeSupport(oxygen, cooling)    # two Regulators, see main.py
    life.update(dt, depth)                 # every frame, after the valves (the deeper, the hotter)
    life.cause                             # None, or the death text once you passed out
    life.strain                            # 0..1: how close to passing out (for the eyes-closing effect, later)

Each system is a Regulator with a red valve (PRESSURE: how hard it pushes, 0..1 = closed..open) and a blue valve
(the IDEAL LEVEL it pushes towards). Every second the level moves `coupling * pressure * (ideal - level)` towards
the ideal, plus its drift: the oxygen falls as you breathe it (OXYGEN_USE), the temperature rises as the drill heats
up (HEAT + HEAT_PER_METRE * depth, at most HEAT_MAX; the engine will add to it later). So the level settles where
the push and the drift balance: `ideal - drift / (coupling * pressure)` away from the ideal; too little pressure and
it can't keep up, and the deeper you go, the more pressure (or the colder the ideal) the cooling needs, up to
HEAT_MAX (1800 m), which full cooling can always hold. The cooling is coupled 3x as
strongly (COOLING_COUPLING), so it reacts faster and is easy to overdo: too cold is as deadly as too hot.

The pressure itself follows its valve with a lag (LIFE_PRESSURE_RATE). The dials show the pressure and the level,
0..100 (the level sliders' red ends are outside the safe levels).
"""
from __future__ import annotations

from .config import (
    COOLING_COUPLING, DEATH_TEXT_COLD, DEATH_TEXT_HOT, DEATH_TEXT_OXYGEN_HIGH, DEATH_TEXT_OXYGEN_LOW, HEAT,
    HEAT_MAX, HEAT_PER_METRE, LIFE_PASS_OUT_TIME, LIFE_PRESSURE_RATE, LIFE_SAFE, LIFE_VALVE_TURNS, OXYGEN_COUPLING, OXYGEN_USE,
)
from .dial import Dial
from .interactable import Valve


class Regulator:
    """One system: `pressure` follows the red valve, `level` is pushed towards the blue valve's ideal."""

    def __init__(self, name: str, pressure_valve: Valve, ideal_valve: Valve, coupling: float,
                 start: tuple[float, float, float], pressure_dials: list[Dial], level_dials: list[Dial],
                 inverted: bool = False) -> None:
        self.name: str = name
        self.pressure_valve: Valve = pressure_valve
        self.ideal_valve: Valve = ideal_valve
        self.coupling: float = coupling
        self.inverted: bool = inverted   # opening the blue valve lowers the ideal (cooling: more open = colder)
        self.pressure_dials: list[Dial] = pressure_dials
        self.level_dials: list[Dial] = level_dials
        red, blue, self.level = start
        for valve, opening in ((pressure_valve, red), (ideal_valve, blue)):
            valve.max_angle = 360.0 * LIFE_VALVE_TURNS
            valve.set_angle(valve.max_angle * opening)
            valve.debug_extra = self.debug_lines
        self.pressure: float = red
        self.strain: float = 0.0   # 0..1, 1 = passed out

    @staticmethod
    def _opening(valve: Valve) -> float:
        return valve.angle / valve.max_angle

    @property
    def ideal(self) -> float:
        opening = self._opening(self.ideal_valve)
        return 1.0 - opening if self.inverted else opening

    @property
    def out_of_range(self) -> str | None:
        """"low" / "high" while the level is outside LIFE_SAFE."""
        low, high = LIFE_SAFE
        return "low" if self.level < low else "high" if self.level > high else None

    def update(self, dt: float, drift: float) -> None:
        self.pressure += (self._opening(self.pressure_valve) - self.pressure) * min(LIFE_PRESSURE_RATE * dt, 1.0)
        push = self.coupling * self.pressure * (self.ideal - self.level)
        self.level = min(max(self.level + (push + drift) * dt, 0.0), 1.0)
        if self.out_of_range:
            self.strain = min(self.strain + dt / LIFE_PASS_OUT_TIME, 1.0)
        else:
            self.strain = max(self.strain - dt / (2 * LIFE_PASS_OUT_TIME), 0.0)
        for dials, value in ((self.pressure_dials, self.pressure), (self.level_dials, self.level)):
            for dial in dials:
                dial.value = dial.low + (dial.high - dial.low) * value

    def debug_lines(self) -> list[str]:
        danger = f", {self.out_of_range.upper()}" if self.out_of_range else ""
        return [f"{self.name}: pressure {self.pressure:.0%}, ideal {self.ideal:.0%}, level {self.level:.0%}{danger}, "
                f"passing out {self.strain:.0%}"]


class LifeSupport:
    def __init__(self, oxygen: Regulator, cooling: Regulator) -> None:
        self.oxygen: Regulator = oxygen
        self.cooling: Regulator = cooling

    @staticmethod
    def heat(depth: float) -> float:
        """How fast the drill heats up at `depth` metres (temperature level / s); at most HEAT_MAX, so the game can
        go on forever."""
        return min(HEAT + HEAT_PER_METRE * depth, HEAT_MAX)

    def update(self, dt: float, depth: float) -> None:
        self.oxygen.update(dt, -OXYGEN_USE)
        self.cooling.update(dt, self.heat(depth))

    @property
    def strain(self) -> float:
        return max(self.oxygen.strain, self.cooling.strain)

    @property
    def cause(self) -> str | None:
        """The death text once you passed out, else None."""
        for system, low, high in ((self.oxygen, DEATH_TEXT_OXYGEN_LOW, DEATH_TEXT_OXYGEN_HIGH),
                                  (self.cooling, DEATH_TEXT_COLD, DEATH_TEXT_HOT)):
            if system.strain >= 1.0:
                return low if system.level < LIFE_SAFE[0] else high
        return None
