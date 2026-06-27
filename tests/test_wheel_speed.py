from __future__ import annotations

import math
from unittest.mock import MagicMock

from simulation.sensors.wheel_speed.config import WheelSpeedSensorConfig
from simulation.sensors.wheel_speed.sensor import WheelSpeedSensor


def test_wheel_speed_no_noise_calculation() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_world.on_tick.return_value = 123

    mock_velocity = MagicMock()
    mock_velocity.x = 1.0
    mock_velocity.y = 0.0
    mock_velocity.z = 0.0
    mock_actor.get_velocity.return_value = mock_velocity

    config = WheelSpeedSensorConfig(
        num_teeth=48,
        wheel_circumference_m=1.98,
        low_freq_noise_pct=0.0,
        high_freq_noise_pct=0.0,
        enable_quantization=False,
    )

    sensor = WheelSpeedSensor(mock_world, mock_actor, config)

    mock_snapshot = MagicMock()
    mock_snapshot.timestamp.elapsed_seconds = 10.5

    sensor._on_world_tick(mock_snapshot)

    reading = sensor.reading
    assert math.isclose(reading.speed_mps, 1.0, rel_tol=1e-5)
    assert math.isclose(reading.true_speed_mps, 1.0, rel_tol=1e-5)
    assert reading.timestamp == 10.5

    expected_freq = (1.0 * 48) / 1.98
    assert math.isclose(reading.pulse_frequency_hz, expected_freq, rel_tol=1e-5)


def test_wheel_speed_quantization() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_world.on_tick.return_value = 123

    mock_velocity = MagicMock()
    mock_velocity.x = 13.7
    mock_velocity.y = 0.0
    mock_velocity.z = 0.0
    mock_actor.get_velocity.return_value = mock_velocity

    config = WheelSpeedSensorConfig(
        num_teeth=48,
        wheel_circumference_m=1.98,
        low_freq_noise_pct=0.0,
        high_freq_noise_pct=0.0,
        enable_quantization=True,
        ecu_timer_resolution_s=4e-7,
    )

    sensor = WheelSpeedSensor(mock_world, mock_actor, config)

    mock_snapshot = MagicMock()
    mock_snapshot.timestamp.elapsed_seconds = 1.0

    sensor._on_world_tick(mock_snapshot)

    expected_quantized_time = round((0.04125 / 13.7) / 4e-7) * 4e-7
    expected_speed = 0.04125 / expected_quantized_time

    reading = sensor.reading
    assert math.isclose(reading.speed_mps, expected_speed, rel_tol=1e-5)
    assert math.isclose(reading.true_speed_mps, 13.7, rel_tol=1e-5)


def test_wheel_speed_noise_scaling() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_world.on_tick.return_value = 123

    config = WheelSpeedSensorConfig(
        num_teeth=48,
        wheel_circumference_m=1.98,
        low_freq_threshold_hz=200.0,
        low_freq_noise_pct=0.01,
        high_freq_noise_pct=0.04,
        enable_quantization=False,
        rng_seed=42,
    )

    sensor = WheelSpeedSensor(mock_world, mock_actor, config)
    mock_snapshot = MagicMock()
    mock_snapshot.timestamp.elapsed_seconds = 1.0

    mock_velocity_low = MagicMock()
    mock_velocity_low.x = 5.0
    mock_velocity_low.y = 0.0
    mock_velocity_low.z = 0.0
    mock_actor.get_velocity.return_value = mock_velocity_low

    sensor._on_world_tick(mock_snapshot)
    reading_low = sensor.reading
    assert abs(reading_low.speed_mps - 5.0) < 5.0 * 0.05

    mock_velocity_high = MagicMock()
    mock_velocity_high.x = 20.0
    mock_velocity_high.y = 0.0
    mock_velocity_high.z = 0.0
    mock_actor.get_velocity.return_value = mock_velocity_high

    sensor._on_world_tick(mock_snapshot)
    reading_high = sensor.reading
    assert abs(reading_high.speed_mps - 20.0) < 20.0 * 0.20
