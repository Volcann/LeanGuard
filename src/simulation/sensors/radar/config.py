"""Sensor config dataclass. See docs/config.md for all field details."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RearRadarConfig:
    # --- AWR1642 FMCW Radar — docs/config.md § Hardware ---
    # Calibrated to TI AWR1642 77 GHz FMCW radar (SWRS203D).
    # 2TX / 4RX, IF bandwidth 5 MHz, automotive blind-spot detection.

    horizontal_fov_deg: float = 110.0
    """Antenna-defined horizontal field of view.
    
    The AWR1642 chip is antenna-agnostic; 110° reflects a typical BSD antenna
    configuration on TI evaluation hardware.  See docs/config.md § FOV.
    """

    vertical_fov_deg: float = 12.0
    """Vertical field of view. Typical for ground-clearance-aware BSD antennas."""

    range_m: float = 30.0
    """Maximum detection range in metres.

    Blind-spot relevant range is 3–10 m; 30 m provides forward headroom for
    approach-speed estimation.  Matches CARLA sensor attribute `range`.
    """

    points_per_second: int = 1500
    """Simulated point cloud density.

    Reflects the sparse real-world output of a 77 GHz FMCW radar constrained
    by the AWR1642's 5 MHz IF bandwidth.  See docs/config.md § Point Density.
    """

    # --- Mount point — docs/config.md § Mount Point ---
    mount_x_m: float = -1.0
    """Longitudinal offset from actor origin. Negative = rear of vehicle."""

    mount_y_m: float = 0.0
    """Lateral offset. 0.0 = centre-line (single-radar BSD architecture)."""

    mount_z_m: float = 0.5
    """Vertical offset from actor origin in metres."""

    mount_yaw_deg: float = 180.0
    """Sensor heading relative to actor forward vector.
    
    180° = facing rearward, matching CARLA's yaw convention.
    """

    # --- Buffer safety — docs/config.md § Buffer ---
    max_buffer_detections: int = 2000
    """Hard cap on in-flight detections awaiting tick() drain.

    Prevents unbounded memory growth if the consumer stalls.
    """
