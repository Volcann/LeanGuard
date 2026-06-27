# `RearRadarConfig` — Field Reference

`RearRadarConfig` controls all tunable parameters of the simulated TI AWR1642-class
rear radar.  If you change these parameters, update `design.md` to keep the
documentation consistent.

---

## § Hardware — FMCW Radar Attributes

### `horizontal_fov_deg` · `float` · default `110.0`

Horizontal field of view of the radar antenna in degrees.

* **Datasheet Note (SWRS203D):** The AWR1642 chip is antenna-agnostic; the FOV
  is determined by the antenna array design, not the chip itself.
* **Design Decision:** 110° reflects a typical BSD antenna configuration on TI
  AWR1642 evaluation hardware (EVM).  The valid range for BSD EVMs is
  approximately 60–120°.  This value is defensible; add the following sentence
  in any written methodology:

  > *"The horizontal FOV of 110° reflects a typical antenna configuration for
  > automotive blind-spot radar based on the AWR1642 evaluation hardware; the
  > chip itself is antenna-agnostic."*

---

### `vertical_fov_deg` · `float` · default `12.0`

Vertical field of view in degrees.

* **Design Decision:** 12° is sufficient to cover the height range of relevant
  targets (passenger cars, motorcycles, trucks) at BSD distances (3–10 m) while
  avoiding unnecessary ground clutter at longer ranges.

---

### `range_m` · `float` · default `30.0`

Maximum detection range in metres (maps to CARLA attribute `range`).

* **Design Decision:** The practical BSD alert zone is 3–10 m.  30 m provides
  headroom for approach-velocity estimation and allows the KIATS classifier to
  build a velocity track before the object enters the warning zone.
* **AWR1642 Capability:** The chip supports ranges well beyond 30 m; the limit
  here is set by the simulation requirement, not hardware.

---

### `points_per_second` · `int` · default `1500`

Simulated point cloud density per second (maps to CARLA attribute
`points_per_second`).

* **Datasheet Citation (SWRS203D, Table 7-1):** IF bandwidth is 5 MHz.  Real
  77 GHz automotive BSD radars output a sparse point cloud (typically hundreds
  to low-thousands of points per second) as a consequence of this constraint.
* **Calibration:** 1500 pps is consistent with real-world sparse 77 GHz
  automotive radar output.  Inflating this value (e.g., to 10 000+) would make
  the simulation unrealistically dense and degrade generalisability.

---

## § Mount Point

The sensor is mounted at the **rear centre-line** of the ego vehicle.
All offsets are relative to the vehicle's origin in CARLA's coordinate system
(X = forward, Y = right, Z = up).

### `mount_x_m` · `float` · default `-1.0`

Longitudinal offset in metres.  Negative = towards the rear of the vehicle.

### `mount_y_m` · `float` · default `0.0`

Lateral offset in metres.  `0.0` = centre-line.

> [!IMPORTANT]
> Keeping `mount_y_m = 0.0` is the defining characteristic of the
> single-centre-radar architecture.  Changing this value to a non-zero offset
> would require revisiting the azimuth-sign side discrimination logic in
> `sensor.py` — see `design.md § 3`.

### `mount_z_m` · `float` · default `0.5`

Vertical offset in metres above the vehicle origin.  0.5 m places the sensor
at approximately tail-light height on a standard motorcycle.

### `mount_yaw_deg` · `float` · default `180.0`

Sensor heading relative to the vehicle's forward vector in degrees.
180° = facing rearward, which is the required orientation for BSD.

---

## § Buffer

### `max_buffer_detections` · `int` · default `2000`

Hard cap on the number of detections that can accumulate in the internal
buffer between `tick()` calls.

* **Rationale:** At 1500 pps and a 30 Hz simulation tick rate, approximately
  50 points arrive per frame.  A cap of 2000 allows ~40 frames of backlog
  before triggering the overflow guard — well beyond any realistic stall
  scenario while still bounding worst-case memory usage.
* **Overflow behaviour:** When the cap is reached, the entire incoming frame
  is dropped (not partial points), preserving temporal coherence of individual
  measurement frames.
