"""Sensor output snapshot. See docs/reading.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImuReading:
    accelerometer_g: tuple[float, float, float]
    gyroscope_dps: tuple[float, float, float]
    compass: float
    roll_deg_ground_truth: float
