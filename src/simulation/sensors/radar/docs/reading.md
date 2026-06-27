# `RadarDetection` — Field Reference

`RadarDetection` is the frozen dataclass returned by `RearRadar.tick()`.
Each instance represents one FMCW measurement point from a single radar frame.
This reference explains each field, its units, and how it is consumed by the
downstream LeanGuard pipeline (DEDR, LGEZ, SC08).

---

## `depth` · `float`

**Radial distance from the radar antenna phase-centre to the detected object.**
Units: metres (m).

* **Range:** `0.0` to `range_m` (default 30.0 m).
* **Physical basis:** Derived from the round-trip time of the FMCW chirp.
  On the AWR1642, range resolution is determined by the chirp bandwidth
  (SWRS203D Table 7-1).
* **Downstream use:** DEDR uses `depth` to gate detections by distance from
  the rear of the vehicle; LGEZ uses it as the primary geometric input for
  lean-exclusion calculations.

---

## `azimuth` · `float`

**Horizontal angle of the detection relative to the sensor boresight.**
Units: radians.

* **Sign convention:** Negative = left of sensor boresight, positive = right.
  Because the sensor is mounted facing rearward (`yaw=180°`), this maps
  directly to the vehicle's left/right frame.
* **Downstream use:** The `side` field is derived from `azimuth`'s sign (see
  `RadarSide`).  GRSA uses `azimuth` together with `depth` to compute the
  Cartesian lateral position of detected objects.

---

## `altitude` · `float`

**Vertical angle of the detection relative to the sensor boresight.**
Units: radians.

* **Downstream use:** LGEZ uses `altitude` to reject ground-return clutter
  (objects detected at steep negative altitude are road surface, not traffic).

---

## `velocity` · `float`

**Radial (Doppler) velocity of the detected object.**
Units: m/s.  Positive = moving away from the radar, negative = approaching.

* **Physical basis:** Derived from the Doppler frequency shift of the FMCW
  return signal.  On the AWR1642 this is enabled by the 2TX MIMO configuration
  (SWRS203D § 7.3).
* **Downstream use:** GRSA velocity-coherence check uses `velocity` to
  distinguish moving traffic from static infrastructure.  SC08 uses it to
  assess collision urgency.

---

## `side` · `RadarSide`

**Lateral side of the ego vehicle from which the detection originates.**

| Value | Azimuth sign | Vehicle side |
|---|---|---|
| `RadarSide.LEFT` | `azimuth < 0` | Left of motorcycle |
| `RadarSide.RIGHT` | `azimuth ≥ 0` | Right of motorcycle |

* **Derivation:** Assigned in `RearRadar._on_radar_measurement` from
  `azimuth` sign.  See `design.md § 3`.
* **Downstream use:** Every downstream component that performs per-side
  logic (DEDR left/right threat zones, LGEZ left/right exclusion polygons,
  SC08 alert channel selector) reads this field.  None of those components
  need to know whether the side came from hardware or software discrimination.

---

## `frame` · `int`

**CARLA simulation frame index at which this detection was recorded.**

* **Downstream use:** DEDR and LGEZ correlate radar detections with the
  vehicle state snapshot (speed, lean angle from IMU) from the same simulation
  frame to avoid temporal mismatches during high-dynamics manoeuvres.

---

## `is_static_guardrail` · `bool` · default `False`

**Classification flag set by the LGEZ lean-geometry exclusion filter.**

> [!CAUTION]
> This field is **written by the LGEZ filter, not by the sensor**.  The sensor
> always emits `False` here.  Any code that checks `is_static_guardrail`
> before LGEZ has processed the detection batch will always see `False`.
> Never read this field inside the sensor or the DEDR input stage.

* **Lifecycle:** `False` at emission → `True` if LGEZ classifies the point
  as a static guardrail/kerb return → passed downstream to SC08 which uses
  it to suppress false-positive BSD alerts during leaned cornering.
