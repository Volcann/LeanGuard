"""Simulated Bosch Motorsport MM5.10-class IMU sensor. See docs/design.md."""

from __future__ import annotations

import logging
import math
import random
import threading

import carla

from simulation.sensors.imu.config import ImuSensorConfig
from simulation.sensors.imu.low_pass_filter import LowPassFilter
from simulation.sensors.imu.reading import ImuReading

logger = logging.getLogger(__name__)


def _quantize(value: float, step: float) -> float:
    if step <= 0:
        return value
    return round(value / step) * step


class ImuSensor:

    def __init__(
        self,
        world: carla.World,
        parent_actor: carla.Actor,
        config: ImuSensorConfig | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._world = world
        self._parent_actor = parent_actor
        self._config = config or ImuSensorConfig()
        self._rng = random.Random(self._config.rng_seed)  # noqa: S311

        self._gyro_filters = [LowPassFilter(self._config.cutoff_frequency_hz) for _ in range(3)]
        self._accel_filters = [LowPassFilter(self._config.cutoff_frequency_hz) for _ in range(3)]
        self._last_timestamp: float | None = None

        self._reading = ImuReading(
            accelerometer_g=(0.0, 0.0, 0.0),
            gyroscope_dps=(0.0, 0.0, 0.0),
            compass=0.0,
            roll_deg_ground_truth=0.0,
        )

        bp_library = world.get_blueprint_library()
        imu_bp = bp_library.find("sensor.other.imu")
        imu_transform = carla.Transform(carla.Location(x=0.0, y=0.0, z=0.0))

        logger.info(
            "IMU sensor init (gyro range=±%.1f °/s, accel range=±%.1f g, cutoff=%.1f Hz)",
            self._config.gyro_measuring_range_dps,
            self._config.accel_measuring_range_g,
            self._config.cutoff_frequency_hz,
        )
        self._sensor: carla.Actor | None = world.spawn_actor(
            imu_bp,
            imu_transform,
            attach_to=parent_actor,
            attachment_type=carla.AttachmentType.Rigid,
        )
        if self._sensor is not None:
            self._sensor.listen(self._on_imu_measurement)

    def _apply_noise(self, value: float, std: float | None) -> float:
        if std is None or std <= 0:
            return value
        return value + self._rng.gauss(0.0, std)

    def _apply_range_fault(self, value: float, over_range_limit: float) -> tuple[float, bool]:
        if not self._config.enable_range_fault_flagging:
            return value, False
        if abs(value) > over_range_limit:
            return math.copysign(over_range_limit, value), True
        return value, False

    def _on_imu_measurement(self, measurement: carla.IMUMeasurement) -> None:
        # Ground-truth roll — see docs/design.md § 2 (Risk 1 caveat)
        try:
            roll_deg_ground_truth = float(self._parent_actor.get_transform().rotation.roll)
        except Exception as exc:
            logger.debug("Failed to retrieve parent actor transform for roll: %s", exc)
            roll_deg_ground_truth = 0.0

        timestamp = measurement.timestamp
        dt_s = 0.0 if self._last_timestamp is None else max(timestamp - self._last_timestamp, 0.0)
        self._last_timestamp = timestamp

        # Stage 1 — unit conversion; see docs/design.md § 4.1
        gyro_raw_dps = tuple(
            math.degrees(v)
            for v in (
                measurement.gyroscope.x,
                measurement.gyroscope.y,
                measurement.gyroscope.z,
            )
        )
        accel_raw_g = tuple(
            v / 9.81
            for v in (
                measurement.accelerometer.x,
                measurement.accelerometer.y,
                measurement.accelerometer.z,
            )
        )

        gyro_out: list[float] = []
        for val, filt in zip(gyro_raw_dps, self._gyro_filters, strict=False):
            # Stage 2 — noise; see docs/design.md § 4.2
            val = self._apply_noise(val, self._config.gyro_noise_std_dps)
            # Stage 3 — low-pass filter; see docs/design.md § 4.3
            if self._config.enable_lowpass_filter:
                val = filt.apply(val, dt_s)
            # Stage 4 — over-range fault; see docs/design.md § 4.4
            val, _ = self._apply_range_fault(val, self._config.gyro_over_range_limit_dps)
            # Stage 5 — quantization; see docs/design.md § 4.5
            if self._config.enable_quantization:
                val = _quantize(val, self._config.gyro_quantization_dps_per_digit)
            gyro_out.append(val)

        accel_out: list[float] = []
        for val, filt in zip(accel_raw_g, self._accel_filters, strict=False):
            # Stage 2 — noise; see docs/design.md § 4.2
            val = self._apply_noise(val, self._config.accel_noise_std_g)
            # Stage 3 — low-pass filter; see docs/design.md § 4.3
            if self._config.enable_lowpass_filter:
                val = filt.apply(val, dt_s)
            # Stage 4 — over-range fault; see docs/design.md § 4.4
            val, _ = self._apply_range_fault(val, self._config.accel_over_range_limit_g)
            # Stage 5 — quantization; see docs/design.md § 4.5
            if self._config.enable_quantization:
                val = _quantize(val, self._config.accel_quantization_g_per_digit)
            accel_out.append(val)

        with self._lock:
            self._reading = ImuReading(
                accelerometer_g=(accel_out[0], accel_out[1], accel_out[2]),
                gyroscope_dps=(gyro_out[0], gyro_out[1], gyro_out[2]),
                compass=float(measurement.compass),
                roll_deg_ground_truth=roll_deg_ground_truth,
            )

    @property
    def reading(self) -> ImuReading:
        with self._lock:
            return self._reading

    def destroy(self) -> None:
        with self._lock:
            if self._sensor is not None:
                try:
                    self._sensor.stop()
                except Exception as exc:
                    logger.debug("Failed to stop IMU sensor: %s", exc)
                try:
                    self._sensor.destroy()
                except Exception as exc:
                    logger.debug("Failed to destroy IMU sensor: %s", exc)
                self._sensor = None
        logger.info("IMU sensor destroyed.")
