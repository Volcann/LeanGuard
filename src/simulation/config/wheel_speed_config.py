"""Sensor config dataclass. See config/wheel_speed_config.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Callable

FaultInjectionFn = Callable[[float, float], float | None]


@dataclass
class WheelSpeedSensorConfig:
    num_teeth: int = 37
    wheel_circumference_m: float = 1.98
    num_teeth_sweep_values: tuple[int, ...] = field(default_factory=lambda: (36, 37, 38, 40))

    low_freq_threshold_hz: float = 200.0
    low_freq_noise_pct: float = 0.01
    high_freq_noise_pct: float = 0.04

    enable_quantization: bool = True

    enable_fault_injection: bool = False
    fault_injection_fn: FaultInjectionFn | None = None

    rng_seed: int | None = None
