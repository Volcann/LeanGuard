"""Simulated Hall-effect wheel-speed sensor. See docs/design.md."""

from __future__ import annotations

import logging
import math
import random
import threading

import carla

from simulation.sensors.wheel_speed.config import (
    WheelSpeedSensorConfig,
)
from simulation.sensors.wheel_speed.reading import WheelSpeedReading

logger = logging.getLogger(__name__)


class WheelSpeedSensor:

    def __init__(
        self,
        world: carla.World,
        parent_actor: carla.Actor,
        config: WheelSpeedSensorConfig | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._world = world
        self._parent_actor = parent_actor
        self._config = config or WheelSpeedSensorConfig()

        self._rng = random.Random(self._config.rng_seed)  # noqa: S311
        self._reading = WheelSpeedReading(
            speed_mps=0.0,
            true_speed_mps=0.0,
            pulse_frequency_hz=0.0,
            timestamp=0.0,
        )

        logger.info(
            "Wheel-speed sensor init (N=%d, C=%.3f m, quantize=%s)",
            self._config.num_teeth,
            self._config.wheel_circumference_m,
            self._config.enable_quantization,
        )
        self._callback_id: int | None = self._world.on_tick(self._on_world_tick)

    def _on_world_tick(self, snapshot: carla.WorldSnapshot) -> None:
        # 5-stage pipeline — see docs/design.md § 1
        try:
            velocity = self._parent_actor.get_velocity()
        except RuntimeError as e:
            logger.debug("Actor unavailable: %s", e)
            return

        true_speed_mps = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
        tooth_count = self._config.num_teeth
        circumference_m = self._config.wheel_circumference_m
        distance_per_tooth_m = circumference_m / tooth_count if tooth_count > 0 else 0.0

        # Stage 1 — ideal pulse frequency; see docs/design.md § 1
        ideal_pulse_freq_hz = (
            true_speed_mps / distance_per_tooth_m
            if distance_per_tooth_m > 0
            else 0.0
        )

        # Banded noise — see docs/config.md § Noise Model
        noise_fraction = (
            self._config.low_freq_noise_pct
            if ideal_pulse_freq_hz <= self._config.low_freq_threshold_hz
            else self._config.high_freq_noise_pct
        )
        noise_std_hz = max(ideal_pulse_freq_hz * noise_fraction, 0.0)
        noisy_pulse_freq_hz = (
            ideal_pulse_freq_hz + self._rng.gauss(0.0, noise_std_hz)
            if noise_std_hz > 0
            else ideal_pulse_freq_hz
        )
        noisy_pulse_freq_hz = max(noisy_pulse_freq_hz, 0.0)

        # Stage 3 — convert noisy frequency back to speed
        noisy_speed_mps = noisy_pulse_freq_hz * distance_per_tooth_m

        # Stage 4 — ECU inter-pulse timing quantization
        # see docs/config.md § Quantization
        estimated_speed_mps = noisy_speed_mps
        if (
            self._config.enable_quantization
            and noisy_speed_mps > 0
            and distance_per_tooth_m > 0
        ):
            ideal_inter_pulse_s = distance_per_tooth_m / noisy_speed_mps
            timer_res = self._config.ecu_timer_resolution_s
            if timer_res > 0:
                quantized_inter_pulse_s = (
                    round(ideal_inter_pulse_s / timer_res) * timer_res
                )
                if quantized_inter_pulse_s > 0:
                    estimated_speed_mps = (
                        distance_per_tooth_m / quantized_inter_pulse_s
                    )

        estimated_speed_mps = max(estimated_speed_mps, 0.0)

        with self._lock:
            self._reading = WheelSpeedReading(
                speed_mps=estimated_speed_mps,
                true_speed_mps=true_speed_mps,
                pulse_frequency_hz=noisy_pulse_freq_hz,
                timestamp=snapshot.timestamp.elapsed_seconds,
            )

    @property
    def reading(self) -> WheelSpeedReading:
        with self._lock:
            return self._reading

    def destroy(self) -> None:
        with self._lock:
            if self._callback_id is not None:
                try:
                    self._world.remove_on_tick(self._callback_id)
                except Exception as e:
                    logger.debug("Failed to remove on_tick callback: %s", e)
                self._callback_id = None
        logger.info("Wheel-speed sensor destroyed.")
