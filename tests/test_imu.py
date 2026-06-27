from __future__ import annotations

import math
from unittest.mock import MagicMock

from simulation.sensors.imu import LowPassFilter
from simulation.sensors.imu.config import ImuSensorConfig
from simulation.sensors.imu.sensor import ImuSensor, _quantize


def test_lowpass_filter_math() -> None:
    filt = LowPassFilter(cutoff_hz=30.0)

    val1 = filt.apply(10.0, dt_s=0.01)
    assert val1 == 10.0

    val2 = filt.apply(20.0, dt_s=0.01)

    rc = 1.0 / (2.0 * math.pi * 30.0)
    alpha = 0.01 / (rc + 0.01)
    expected = 10.0 + alpha * (20.0 - 10.0)

    assert math.isclose(val2, expected, rel_tol=1e-5)


def test_quantize_math() -> None:
    assert _quantize(0.002, 0.005) == 0.000
    assert _quantize(0.003, 0.005) == 0.005
    assert _quantize(-0.008, 0.005) == -0.010

    step = 0.0001274
    assert _quantize(0.0, step) == 0.0
    assert _quantize(0.00006, step) == 0.0
    assert math.isclose(_quantize(0.00007, step), step)


def test_sensor_init_and_pipeline() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_sensor_actor = MagicMock()

    mock_world.spawn_actor.return_value = mock_sensor_actor

    mock_transform = MagicMock()
    mock_transform.rotation.roll = 25.0
    mock_actor.get_transform.return_value = mock_transform

    config = ImuSensorConfig(
        gyro_noise_std_dps=None,
        accel_noise_std_g=None,
        enable_lowpass_filter=False,
        enable_quantization=True,
    )

    sensor = ImuSensor(mock_world, mock_actor, config)

    mock_measurement = MagicMock()
    mock_measurement.timestamp = 1.0

    mock_measurement.gyroscope.x = 0.5
    mock_measurement.gyroscope.y = 0.0
    mock_measurement.gyroscope.z = -0.5

    mock_measurement.accelerometer.x = 9.81
    mock_measurement.accelerometer.y = -9.81
    mock_measurement.accelerometer.z = 0.0

    mock_measurement.compass = 1.23

    sensor._on_imu_measurement(mock_measurement)

    reading = sensor.reading

    assert reading.roll_deg_ground_truth == 25.0
    assert reading.compass == 1.23

    assert math.isclose(reading.gyroscope_dps[0], 28.650)
    assert reading.gyroscope_dps[1] == 0.0
    assert math.isclose(reading.gyroscope_dps[2], -28.650)

    assert math.isclose(reading.accelerometer_g[0], 7849 * 0.0001274)
    assert math.isclose(reading.accelerometer_g[1], -7849 * 0.0001274)
    assert reading.accelerometer_g[2] == 0.0


def test_sensor_over_range_clamping() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_sensor_actor = MagicMock()
    mock_world.spawn_actor.return_value = mock_sensor_actor

    config = ImuSensorConfig(
        gyro_over_range_limit_dps=1000.0,
        accel_over_range_limit_g=10.0,
        enable_lowpass_filter=False,
        enable_quantization=False,
    )

    sensor = ImuSensor(mock_world, mock_actor, config)

    mock_measurement = MagicMock()
    mock_measurement.timestamp = 1.0
    mock_measurement.gyroscope.x = 20.0
    mock_measurement.gyroscope.y = 0.0
    mock_measurement.gyroscope.z = 0.0

    mock_measurement.accelerometer.x = 120.0
    mock_measurement.accelerometer.y = 0.0
    mock_measurement.accelerometer.z = 0.0

    mock_measurement.compass = 0.0

    sensor._on_imu_measurement(mock_measurement)

    reading = sensor.reading
    assert reading.gyroscope_dps[0] == 1000.0
    assert reading.accelerometer_g[0] == 10.0
