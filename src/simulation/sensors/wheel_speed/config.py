"""Sensor config dataclass. See docs/config.md for all field details."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

FaultInjectionFn = Callable[[float, float], float | None]


@dataclass
class WheelSpeedSensorConfig:
    # --- Encoder Geometry ---
    num_teeth: int = 48
    wheel_circumference_m: float = 1.98
    num_teeth_sweep_values: tuple[int, ...] = field(default_factory=lambda: (40, 44, 48, 50))

    # --- Noise Model ---
    low_freq_threshold_hz: float = 200.0
    low_freq_noise_pct: float = 0.01
    high_freq_noise_pct: float = 0.04

    # --- Quantization ---
    enable_quantization: bool = True

    # 0.4 μs → 2.5 MHz ECU counter;
    # See docs/config.md § Quantization
    ecu_timer_resolution_s: float = 4e-7

    # --- Fault Injection ---
    enable_fault_injection: bool = False
    fault_injection_fn: FaultInjectionFn | None = None

    # --- Reproducibility ---
    rng_seed: int | None = None
