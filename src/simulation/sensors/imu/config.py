"""Sensor config dataclass. See docs/config.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImuSensorConfig:
    # --- Gyroscope — docs/config.md § Gyroscope ---
    gyro_measuring_range_dps: float = 160.0
    gyro_over_range_limit_dps: float = 1000.0
    gyro_resolution_dps: float = 0.1
    gyro_quantization_dps_per_digit: float = 0.005
    gyro_noise_std_dps: float | None = None

    # --- Accelerometer — docs/config.md § Accelerometer ---
    accel_measuring_range_g: float = 4.2
    accel_over_range_limit_g: float = 10.0
    accel_resolution_g: float = 0.01
    accel_quantization_g_per_digit: float = 0.0001274
    accel_noise_std_g: float | None = None

    # --- Low-pass filter — docs/config.md § Low-Pass Filter ---
    cutoff_frequency_hz: float = 30.0
    enable_lowpass_filter: bool = True

    # --- Pipeline toggles — docs/config.md § Pipeline Toggles ---
    enable_quantization: bool = True
    enable_range_fault_flagging: bool = True

    # --- Reproducibility — docs/config.md § Reproducibility ---
    rng_seed: int | None = None
