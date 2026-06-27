"""Simulated Hall-effect wheel-speed sensor package."""

from simulation.sensors.wheel_speed.config import WheelSpeedSensorConfig
from simulation.sensors.wheel_speed.reading import WheelSpeedReading
from simulation.sensors.wheel_speed.sensor import WheelSpeedSensor, make_slip_fault

__all__ = [
    "WheelSpeedSensor",
    "make_slip_fault",
    "WheelSpeedSensorConfig",
    "WheelSpeedReading",
]
