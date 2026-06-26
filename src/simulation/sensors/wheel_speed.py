"""Simulated Hall-effect wheel-speed sensor. See sensors/wheel_speed.md."""

from __future__ import annotations

import logging
import math
import random
import threading

import carla

from simulation.config.wheel_speed_config import FaultInjectionFn, WheelSpeedSensorConfig
from simulation.config.wheel_speed_reading import WheelSpeedReading

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

        self._rng = random.Random(self._config.rng_seed)
        self._reading = WheelSpeedReading(
            speed_mps=0.0,
            true_speed_mps=0.0,
            pulse_frequency_hz=0.0,
            timestamp=0.0,
            fault_active=False,
        )

        logger.info(
            "Wheel-speed sensor init (N=%d, C=%.3f m, quantize=%s, fault=%s)",
            self._config.num_teeth,
            self._config.wheel_circumference_m,
            self._config.enable_quantization,
            self._config.enable_fault_injection,
        )
        self._callback_id: int | None = self._world.on_tick(self._on_world_tick)

    def _on_world_tick(self, snapshot: carla.WorldSnapshot) -> None:
        # 5-stage pipeline — see wheel_speed.md § 1
        try:
            velocity = self._parent_actor.get_velocity()
        except RuntimeError as e:
            logger.debug("Actor unavailable: %s", e)
            return

        true_speed_mps = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
        tooth_count = self._config.num_teeth
        circumference_m = self._config.wheel_circumference_m

        ideal_pulse_freq_hz = (
            (true_speed_mps * tooth_count) / circumference_m
            if circumference_m > 0
            else 0.0
        )

        # Banded noise — see config/wheel_speed_config.md § Noise Model
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

        estimated_speed_mps = (
            (noisy_pulse_freq_hz * circumference_m) / tooth_count
            if tooth_count > 0
            else 0.0
        )

        # Quantisation — see config/wheel_speed_config.md § Quantization
        if self._config.enable_quantization and tooth_count > 0 and circumference_m > 0:
            tick_duration_s = snapshot.timestamp.delta_seconds or (1.0 / 20.0)
            speed_resolution_step = (circumference_m / tooth_count) / tick_duration_s if tick_duration_s > 0 else 0.0
            if speed_resolution_step > 0:
                estimated_speed_mps = round(estimated_speed_mps / speed_resolution_step) * speed_resolution_step

        fault_active = False
        if self._config.enable_fault_injection and self._config.fault_injection_fn:
            injected_speed = self._config.fault_injection_fn(
                true_speed_mps, snapshot.timestamp.elapsed_seconds
            )
            if injected_speed is not None:
                estimated_speed_mps = injected_speed
                fault_active = True

        estimated_speed_mps = max(estimated_speed_mps, 0.0)

        with self._lock:
            self._reading = WheelSpeedReading(
                speed_mps=estimated_speed_mps,
                true_speed_mps=true_speed_mps,
                pulse_frequency_hz=noisy_pulse_freq_hz,
                timestamp=snapshot.timestamp.elapsed_seconds,
                fault_active=fault_active,
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


def make_slip_fault(
    start_time_s: float,
    duration_s: float,
    slip_factor: float,
) -> FaultInjectionFn:
    # See config/wheel_speed_config.md § Fault Injection
    def _fault(true_speed_mps: float, elapsed_seconds: float) -> float | None:
        if start_time_s <= elapsed_seconds < start_time_s + duration_s:
            return max(true_speed_mps * slip_factor, 0.0)
        return None

    return _fault
