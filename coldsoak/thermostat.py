"""Hysteresis heater controller with an independent cell-temperature safety cutoff.

Control chases the PAD sensor (fast, the thing that can overheat).
Safety guards the CELL sensor (slow, the thing that matters).
"""
from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    OFF = "off"
    HEATING = "heating"
    TRIPPED = "tripped"     # latched until a human resets it


@dataclass
class Thermostat:
    on_below_c: float = 10.0
    off_above_c: float = 18.0
    pad_max_c: float = 45.0
    cell_max_c: float = 40.0
    sensor_timeout_s: float = 5.0
    state: State = State.OFF
    trip_reason: str = ""
    _last_ok: float = field(default=0.0, repr=False)

    def update(self, now: float, pad_c: float | None, cell_c: float | None) -> bool:
        """Return True if the heater MOSFET should be on."""
        if self.state is State.TRIPPED:
            return False
        if pad_c is None or cell_c is None:
            if now - self._last_ok > self.sensor_timeout_s:
                return self._trip("sensor timeout")
            return self.state is State.HEATING
        self._last_ok = now
        # DS18B20 reports 85.0 C on power-on reset and -127 on a read fault
        if pad_c in (85.0, -127.0) or cell_c in (85.0, -127.0):
            return self._trip(f"sensor fault value pad={pad_c} cell={cell_c}")
        if cell_c >= self.cell_max_c:
            return self._trip(f"cell over-temp {cell_c:.1f} C")
        if pad_c >= self.pad_max_c:
            return self._trip(f"pad over-temp {pad_c:.1f} C")
        if self.state is State.OFF and pad_c < self.on_below_c:
            self.state = State.HEATING
        elif self.state is State.HEATING and pad_c > self.off_above_c:
            self.state = State.OFF
        return self.state is State.HEATING

    def _trip(self, reason):
        self.state, self.trip_reason = State.TRIPPED, reason
        return False

    def reset(self):
        self.state, self.trip_reason = State.OFF, ""
