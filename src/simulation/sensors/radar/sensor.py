"""Simulated TI AWR1642-class rear-centre radar sensor. See docs/design.md."""

from __future__ import annotations

import logging
import threading

import carla

from simulation.sensors.radar.config import RearRadarConfig
from simulation.sensors.radar.reading import RadarDetection, RadarSide

logger = logging.getLogger(__name__)


class RearRadar:
    """Wraps a single CARLA radar sensor mounted at the rear-centre of the ego vehicle.

    Models a Texas Instruments AWR1642 77 GHz FMCW single-chip radar
    (datasheet: TI SWRS203D), the primary target hardware for LeanGuard's
    blind-spot detection system.

    Architecture — single centre-rear radar:
    ::

               [REAR RADAR — centre mount]
                          |
                azimuth < 0  →  RadarSide.LEFT
                azimuth > 0  →  RadarSide.RIGHT

    Left/right discrimination is derived from the sign of the FMCW azimuth
    angle rather than from which physical sensor fired.  This matches the
    Chigee SR-1 commercial baseline and is valid because the AWR1642's 4RX
    array provides sufficient angular resolution for side separation.

    See docs/design.md for the full hardware justification and pipeline
    description.

    Thread safety:
        ``_on_radar_measurement`` runs on CARLA's internal sensor thread.
        ``tick()`` and ``destroy()`` are called from the simulation loop thread.
        All shared state is protected by ``_lock``.
    """

    def __init__(
        self,
        world: carla.World,
        parent_actor: carla.Actor,
        config: RearRadarConfig | None = None,
    ) -> None:
        """Spawn and attach the centre-rear radar to *parent_actor*.

        Args:
            world: Active CARLA World instance.
            parent_actor: Ego vehicle actor to attach the sensor to.
            config: Optional config override; defaults to ``RearRadarConfig()``.
        """
        self._lock = threading.Lock()
        self._detections: list[RadarDetection] = []
        self._config = config or RearRadarConfig()
        self._sensor: carla.Actor | None = None

        # ------------------------------------------------------------------ #
        # Blueprint — calibrated to TI AWR1642 (SWRS203D)                   #
        # ------------------------------------------------------------------ #
        bp_library = world.get_blueprint_library()
        radar_bp = bp_library.find("sensor.other.radar")

        # AWR1642: IF bandwidth 5 MHz → sparse point cloud; see docs/design.md § 2
        radar_bp.set_attribute("horizontal_fov", str(self._config.horizontal_fov_deg))
        radar_bp.set_attribute("vertical_fov",   str(self._config.vertical_fov_deg))
        radar_bp.set_attribute("range",           str(self._config.range_m))
        radar_bp.set_attribute("points_per_second", str(self._config.points_per_second))

        # ------------------------------------------------------------------ #
        # Mount — centre rear; see docs/config.md § Mount Point              #
        # ------------------------------------------------------------------ #
        loc = carla.Location(
            x=self._config.mount_x_m,
            y=self._config.mount_y_m,
            z=self._config.mount_z_m,
        )
        rot = carla.Rotation(pitch=0.0, yaw=self._config.mount_yaw_deg, roll=0.0)

        logger.info(
            "Rear radar init (AWR1642-class, hFOV=%.0f°, range=%.0f m, pps=%d)",
            self._config.horizontal_fov_deg,
            self._config.range_m,
            self._config.points_per_second,
        )
        self._sensor = world.spawn_actor(
            radar_bp,
            carla.Transform(loc, rot),
            attach_to=parent_actor,
            attachment_type=carla.AttachmentType.Rigid,
        )
        if self._sensor is None:
            logger.error("Rear radar spawn returned None — sensor is inactive.")
            return

        self._sensor.listen(self._on_radar_measurement)

    # ---------------------------------------------------------------------- #
    # Internal callback (runs on CARLA sensor thread)                        #
    # ---------------------------------------------------------------------- #

    def _on_radar_measurement(self, measurement: carla.RadarMeasurement) -> None:
        """Parse a raw CARLA RadarMeasurement into :class:`RadarDetection` objects.

        Implements the azimuth-sign left/right discrimination described in
        docs/design.md § 3.  Detections accumulate in ``_detections`` until
        drained by :meth:`tick`.

        Buffer overflow guard: if the consumer has not called ``tick()`` and
        the buffer is full, the entire frame is dropped with a warning rather
        than silently growing memory without bound.
        """
        frame = measurement.frame
        with self._lock:
            if len(self._detections) >= self._config.max_buffer_detections:
                logger.warning(
                    "Radar buffer full (%d detections); dropping frame %d.",
                    self._config.max_buffer_detections,
                    frame,
                )
                return

            for detect in measurement:
                # Azimuth-sign side discrimination — see docs/design.md § 3
                side = RadarSide.LEFT if detect.azimuth < 0 else RadarSide.RIGHT

                self._detections.append(
                    RadarDetection(
                        depth=float(detect.depth),
                        azimuth=float(detect.azimuth),
                        altitude=float(detect.altitude),
                        velocity=float(detect.velocity),
                        side=side,
                        frame=frame,
                        is_static_guardrail=False,
                    )
                )

    # ---------------------------------------------------------------------- #
    # Public API                                                              #
    # ---------------------------------------------------------------------- #

    def tick(self) -> list[RadarDetection]:
        """Return all detections accumulated since the last call and clear the buffer.

        Implements the clear-on-read pattern used by the sibling
        ``WheelSpeedSensor`` and ``ImuSensor`` classes.

        Returns:
            Snapshot of all :class:`RadarDetection` objects since the previous
            ``tick()``.  May be empty if no measurement frames arrived yet.
        """
        with self._lock:
            detections = self._detections
            self._detections = []
            return detections

    def destroy(self) -> None:
        """Stop the CARLA sensor and release all resources.

        Safe to call multiple times; subsequent calls are no-ops.
        Mirrors the ``destroy()`` contract of ``ImuSensor``.
        """
        with self._lock:
            if self._sensor is not None:
                try:
                    self._sensor.stop()
                except Exception as exc:
                    logger.debug("Failed to stop rear radar: %s", exc)
                try:
                    self._sensor.destroy()
                except Exception as exc:
                    logger.debug("Failed to destroy rear radar: %s", exc)
                self._sensor = None
        logger.info("Rear radar sensor destroyed.")
