"""Sensor config dataclass. See docs/config.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RearRadarConfig:
    # --- Hardware — docs/config.md § Hardware ---
    horizontal_fov_deg: float = 110.0
    vertical_fov_deg: float = 12.0
    range_m: float = 30.0
    points_per_second: int = 1500

    # --- Mount Point — docs/config.md § Mount Point ---
    mount_x_m: float = -1.0
    mount_y_m: float = 0.0
    mount_z_m: float = 0.5
    mount_yaw_deg: float = 180.0

    # --- Buffer — docs/config.md § Buffer ---
    max_buffer_detections: int = 2000
