"""First-order discrete IIR low-pass filter implementation. See docs/design.md § 3."""

from __future__ import annotations

import math


class LowPassFilter:

    def __init__(self, cutoff_hz: float) -> None:
        self._cutoff_hz = cutoff_hz
        self._state: float | None = None

    def apply(self, value: float, dt_s: float) -> float:
        if self._cutoff_hz <= 0 or dt_s <= 0:
            return value
        rc = 1.0 / (2.0 * math.pi * self._cutoff_hz)
        alpha = dt_s / (rc + dt_s)
        if self._state is None:
            self._state = value
        self._state = self._state + alpha * (value - self._state)
        return self._state
