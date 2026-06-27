"""Sensor output snapshot and side enum. See docs/reading.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RadarSide(Enum):
    """Lateral side of the ego vehicle from which a detection originates.

    Derived from the sign of the detection's azimuth angle — negative azimuth
    maps to the left side, positive to the right.  This matches the convention
    used by the DEDR, LGEZ filter, and SC08 pipeline stages downstream.

    See docs/design.md § 3 for the azimuth-sign mapping rationale.
    """

    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class RadarDetection:
    """A single point returned by the AWR1642-class FMCW radar per measurement frame.

    All fields are in sensor-frame coordinates (rear-facing, CARLA convention).
    See docs/reading.md for unit details and downstream usage guidance.
    """

    depth: float
    """Radial distance from the radar origin to the detected object. Units: metres (m).

    Range on AWR1642: limited by CARLA's `range` attribute (default 30 m).
    """

    azimuth: float
    """Horizontal angle of the detection relative to the sensor's boresight. Units: radians.

    Negative = left of boresight, positive = right.
    This sign convention directly determines `side`.
    """

    altitude: float
    """Vertical angle of the detection relative to the sensor's boresight. Units: radians."""

    velocity: float
    """Radial velocity of the detected object (positive = moving away). Units: m/s.

    Corresponds to Doppler velocity measured by the FMCW waveform.
    On the AWR1642 this is derived from the IF bandwidth of 5 MHz.
    """

    side: RadarSide
    """Left/right discrimination derived from azimuth sign. See docs/design.md § 3."""

    frame: int
    """CARLA simulation frame index at which this detection was recorded.

    Used by DEDR and LGEZ to correlate detections with the vehicle state snapshot
    from the same simulation tick.
    """

    is_static_guardrail: bool = False
    """True once the LGEZ lean-geometry exclusion filter classifies this point as
    a static roadside barrier (guardrail/kerb).  Set by the filter, not the sensor.
    """
