"""Sensor config dataclass. See docs/config.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WheelSpeedSensorConfig:
    # --- Encoder Geometry ---
    num_teeth: int = 48
    wheel_circumference_m: float = 1.98
    num_teeth_sweep_values: tuple[int, ...] = field(default_factory=lambda: (40, 44, 48, 50))

    low_freq_threshold_hz: float = 200.0
    low_freq_noise_pct: float = 0.01
    high_freq_noise_pct: float = 0.04

    enable_quantization: bool = True

    # 0.4 μs → 2.5 MHz ECU counter;
    # See docs/config.md § Quantization
    ecu_timer_resolution_s: float = 4e-7

    rng_seed: int | None = None
