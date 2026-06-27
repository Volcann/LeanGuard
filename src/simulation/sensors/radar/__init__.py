"""Simulated TI AWR1642-class rear radar sensor package. See docs/design.md."""

from simulation.sensors.radar.config import RearRadarConfig
from simulation.sensors.radar.reading import RadarDetection, RadarSide
from simulation.sensors.radar.sensor import RearRadar

__all__ = [
    "RadarDetection",
    "RadarSide",
    "RearRadar",
    "RearRadarConfig",
]
