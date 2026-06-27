"""Sensor output snapshot and side enum. See docs/reading.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RadarSide(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class RadarDetection:
    depth: float
    azimuth: float
    altitude: float
    velocity: float
    side: RadarSide
    frame: int
    is_static_guardrail: bool = False
