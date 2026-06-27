"""Sensor output snapshot. See docs/reading.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WheelSpeedReading:
    speed_mps: float
    true_speed_mps: float
    pulse_frequency_hz: float
    timestamp: float
    fault_active: bool
