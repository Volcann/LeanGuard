from __future__ import annotations

from unittest.mock import MagicMock, patch

import carla
import pytest

from simulation.sensors.radar.config import RearRadarConfig
from simulation.sensors.radar.reading import RadarSide
from simulation.sensors.radar.sensor import RearRadar


def test_radar_init_and_spawn() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_sensor_actor = MagicMock()
    mock_blueprint = MagicMock()

    mock_world.get_blueprint_library().find.return_value = mock_blueprint
    mock_world.spawn_actor.return_value = mock_sensor_actor

    config = RearRadarConfig(
        horizontal_fov_deg=90.0,
        vertical_fov_deg=10.0,
        range_m=25.0,
        points_per_second=1000,
        mount_x_m=-1.5,
        mount_y_m=0.1,
        mount_z_m=0.6,
        mount_yaw_deg=180.0,
    )

    radar = RearRadar(mock_world, mock_actor, config)

    mock_blueprint.set_attribute.assert_any_call("horizontal_fov", "90.0")
    mock_blueprint.set_attribute.assert_any_call("vertical_fov", "10.0")
    mock_blueprint.set_attribute.assert_any_call("range", "25.0")
    mock_blueprint.set_attribute.assert_any_call("points_per_second", "1000")

    mock_world.spawn_actor.assert_called_once()
    spawn_args = mock_world.spawn_actor.call_args[0]
    assert spawn_args[0] == mock_blueprint

    transform = spawn_args[1]
    assert transform.location.x == pytest.approx(-1.5)
    assert transform.location.y == pytest.approx(0.1)
    assert transform.location.z == pytest.approx(0.6)
    assert transform.rotation.yaw == pytest.approx(180.0)
    assert transform.rotation.pitch == pytest.approx(0.0)
    assert transform.rotation.roll == pytest.approx(0.0)

    assert radar._sensor == mock_sensor_actor
    mock_sensor_actor.listen.assert_called_once_with(radar._on_radar_measurement)


def test_radar_callback_parsing() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_sensor_actor = MagicMock()

    mock_world.spawn_actor.return_value = mock_sensor_actor

    radar = RearRadar(mock_world, mock_actor)

    mock_measurement = MagicMock(spec=carla.RadarMeasurement)
    mock_measurement.frame = 42

    mock_point_left = MagicMock()
    mock_point_left.depth = 5.0
    mock_point_left.azimuth = -0.2
    mock_point_left.altitude = 0.05
    mock_point_left.velocity = -2.5

    mock_point_right = MagicMock()
    mock_point_right.depth = 12.0
    mock_point_right.azimuth = 0.3
    mock_point_right.altitude = -0.01
    mock_point_right.velocity = 1.0

    mock_measurement.__iter__.return_value = [mock_point_left, mock_point_right]

    radar._on_radar_measurement(mock_measurement)

    detections = radar.tick()
    assert len(detections) == 2

    assert detections[0].depth == 5.0
    assert detections[0].azimuth == -0.2
    assert detections[0].altitude == 0.05
    assert detections[0].velocity == -2.5
    assert detections[0].side == RadarSide.LEFT
    assert detections[0].frame == 42
    assert not detections[0].is_static_guardrail

    assert detections[1].depth == 12.0
    assert detections[1].azimuth == 0.3
    assert detections[1].altitude == -0.01
    assert detections[1].velocity == 1.0
    assert detections[1].side == RadarSide.RIGHT
    assert detections[1].frame == 42


def test_radar_buffer_overflow() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_sensor_actor = MagicMock()
    mock_world.spawn_actor.return_value = mock_sensor_actor

    config = RearRadarConfig(max_buffer_detections=3)
    radar = RearRadar(mock_world, mock_actor, config)

    mock_meas_1 = MagicMock()
    mock_meas_1.frame = 100
    p1 = MagicMock()
    p1.depth = 1.0
    p1.azimuth = -0.1
    p1.altitude = 0.0
    p1.velocity = 0.0

    p2 = MagicMock()
    p2.depth = 2.0
    p2.azimuth = 0.1
    p2.altitude = 0.0
    p2.velocity = 0.0

    p3 = MagicMock()
    p3.depth = 3.0
    p3.azimuth = 0.2
    p3.altitude = 0.0
    p3.velocity = 0.0

    mock_meas_1.__iter__.return_value = [p1, p2, p3]
    radar._on_radar_measurement(mock_meas_1)

    assert len(radar._detections) == 3

    mock_meas_2 = MagicMock()
    mock_meas_2.frame = 101
    p4 = MagicMock()
    p4.depth = 4.0
    p4.azimuth = 0.0
    p4.altitude = 0.0
    p4.velocity = 0.0
    mock_meas_2.__iter__.return_value = [p4]

    with patch("simulation.sensors.radar.sensor.logger.warning") as mock_warning:
        radar._on_radar_measurement(mock_meas_2)
        mock_warning.assert_called_once()

    detections = radar.tick()
    assert len(detections) == 3
    assert [d.depth for d in detections] == [1.0, 2.0, 3.0]


def test_radar_destroy() -> None:
    mock_world = MagicMock()
    mock_actor = MagicMock()
    mock_sensor_actor = MagicMock()
    mock_world.spawn_actor.return_value = mock_sensor_actor

    radar = RearRadar(mock_world, mock_actor)
    assert radar._sensor is not None

    radar.destroy()
    mock_sensor_actor.stop.assert_called_once()
    mock_sensor_actor.destroy.assert_called_once()
    assert radar._sensor is None

    radar.destroy()
    assert mock_sensor_actor.stop.call_count == 1
    assert mock_sensor_actor.destroy.call_count == 1
