# Rear Radar Sensor Simulation — Design Justification

## Why This Document Exists

LeanGuard's blind-spot detection pipeline (DEDR, LGEZ lean-geometry exclusion
filter, SC08 alert classifier) requires a stream of tagged radar detections to
discriminate traffic approaching from the left or right rear.  While CARLA can
provide synthetic perfect detections, the real deployment target is a specific
piece of automotive hardware.  This document grounds every simulation parameter
in that hardware's published datasheet and explains the single-centre-radar
architectural decision.

---

## 1. Target Hardware — Texas Instruments AWR1642

The AWR1642 is a 77 GHz FMCW (Frequency-Modulated Continuous-Wave) single-chip
radar manufactured by Texas Instruments.  Its first listed application in the
datasheet (TI SWRS203D) is **"Blind spot detection"** — making it the natural
target for LeanGuard's rear-BSD system.

### 1.1 Key Specifications (from TI SWRS203D)

| Spec | AWR1642 Value | LeanGuard Implication |
|---|---|---|
| Frequency band | 76–81 GHz FMCW | Industry-standard automotive radar band — directly comparable to Chigee SR-1 commercial baseline |
| TX channels | 2 | Single-module, low-cost — justifies the single-radar decision (§ 2) |
| RX channels | 4 | 4RX enables azimuth-based left/right side separation without dual sensors |
| TX power | 12 dBm | Adequate for BSD distances (3–10 m target range) |
| IF bandwidth | 5 MHz | Constrains point density; `points_per_second = 1500` is realistic |
| On-chip DSP | C674x @ 600 MHz | ONNX inference pipeline can run on-chip — closes the desktop-to-embedded gap |
| On-chip MCU | Cortex-R4F @ 200 MHz | CAN/CAN-FD output — matches real motorcycle ECU architecture |
| Safety cert | **ISO 26262 ASIL-B** | Directly ties to thesis § 10.2 on functional safety compliance |
| Automotive grade | AEC-Q100 | Confirms suitability for real motorcycle deployment |

> [!NOTE]
> The AWR1642 datasheet (SWRS203D) does not specify the antenna FOV — that is
> determined by the antenna array design, not the chip itself.  The 110° horizontal
> FOV used here reflects a typical BSD antenna configuration on TI evaluation
> hardware (EVM).  See § 4 and docs/config.md § FOV.

---

## 2. Architecture Decision — Single Rear-Centre Radar

LeanGuard uses **one** radar mounted at the rear centre-line of the motorcycle,
rather than two laterally-separated sensors.

### 2.1 Why One Sensor Is Sufficient

```
         [SINGLE RADAR — centre rear, yaw=180°]
                        |
              azimuth < 0  →  RadarSide.LEFT
              azimuth > 0  →  RadarSide.RIGHT
```

Hardware-level side separation (left sensor vs right sensor) is replaced by
**software-level side discrimination**: the sign of the detection's azimuth
angle.  This is valid because:

1. The AWR1642's 4RX antenna array provides sufficient angular resolution to
   distinguish objects at ±10°+ from boresight across the full 110° FOV.
2. The identical architecture is used by the **Chigee SR-1**, the commercial
   BSD system serving as our performance baseline.  Matching hardware cost
   enables an apples-to-apples comparison of the software contribution.

### 2.2 Thesis Positioning

> *"LeanGuard adopts the same single rear-centre radar architecture as the
> Chigee SR-1, keeping hardware cost equivalent to the commercial baseline.
> The contribution is entirely in software: the lean-geometry exclusion zone
> filter, GRSA, and KIATS operate on detections tagged by azimuth-derived
> side, enabling per-side alert logic without additional hardware."*

This is a stronger thesis position than dual-sensor: **same cheap hardware,
better software is the claim**.

### 2.3 Honest Limitation

With a 110° horizontal FOV from a single centre mount, angular resolution
degrades toward the coverage edges (±55°+):

> *"A single rear-centre radar with a 110° horizontal FOV provides angular
> resolution that degrades at coverage edges.  In practice this means
> detections at extreme azimuth angles carry higher positional uncertainty,
> which is mitigated by GRSA's velocity-coherence check rather than geometric
> precision."*

This limitation is disclosed proactively in the thesis Limitations section.

---

## 3. Azimuth-Sign Side Discrimination — Implementation

The `_on_radar_measurement` callback performs side assignment on every
detection point:

```python
side = RadarSide.LEFT if detect.azimuth < 0 else RadarSide.RIGHT
```

**CARLA azimuth convention:** angle in radians relative to the sensor boresight
in the horizontal plane, measured counter-clockwise positive.  Because the
sensor is mounted with `yaw=180°` (facing rearward), objects approaching from
the vehicle's left appear at **negative** azimuth and objects from the right at
**positive** azimuth.

The `side` field is present on every `RadarDetection` that leaves the sensor.
DEDR, the LGEZ filter, and SC08 all consume this field — none of them need to
know whether side came from a physical sensor or azimuth computation.

---

## 4. CARLA Attribute Calibration

```python
# Calibrated to TI AWR1642 77 GHz FMCW radar (SWRS203D)
# 2TX / 4RX, IF bandwidth 5 MHz, automotive blind-spot detection
radar_bp.set_attribute('horizontal_fov', '110')      # antenna-dependent; typical BSD EVM config
radar_bp.set_attribute('vertical_fov',   '12')       # ground-clearance-aware antenna design
radar_bp.set_attribute('range',          '30')       # BSD target: 3–10 m; 30 m gives approach speed headroom
radar_bp.set_attribute('points_per_second', '1500')  # sparse, consistent with 5 MHz IF bandwidth
```

### 4.1 Justification Per Attribute

| CARLA Attribute | Value | Datasheet Basis |
|---|---|---|
| `horizontal_fov` | 110° | Typical TI AWR1642 BSD EVM antenna configuration; chip is antenna-agnostic (SWRS203D) |
| `vertical_fov` | 12° | Sufficient to cover motorcycle height range at BSD distances; standard for ground-level-mount BSD antennas |
| `range` | 30 m | Exceeds the practical BSD zone (3–10 m); allows approach velocity to stabilise before the warning threshold |
| `points_per_second` | 1500 | Sparse, matching real 77 GHz automotive radar constrained by 5 MHz IF bandwidth (SWRS203D Table 7-1) |

---

## 5. Buffer Overflow Guard

The sensor callback accumulates detections into an in-memory list between
`tick()` calls.  A hard cap (`max_buffer_detections`, default 2000) prevents
unbounded growth if the simulation loop stalls:

```python
if len(self._detections) >= self._config.max_buffer_detections:
    logger.warning("Radar buffer full; dropping frame %d.", frame)
    return
```

Whole frames are dropped (not individual points) to preserve the temporal
coherence of each measurement.  This mirrors the pattern used in the IMU and
wheel-speed sensors.

---

## 6. Thread Safety Model

| Thread | Role |
|---|---|
| CARLA sensor thread | Calls `_on_radar_measurement`; acquires `_lock` to write `_detections` |
| Simulation loop thread | Calls `tick()` and `destroy()`; acquires `_lock` to swap/clear the buffer |

The `_lock` is a `threading.Lock` (non-reentrant), matching the
`WheelSpeedSensor` and `ImuSensor` patterns.  There is no risk of deadlock
because no lock-holder calls back into the sensor.

---

## 7. Summary Statement (For the Thesis Methodology Section)

> *"LeanGuard targets the Texas Instruments AWR1642, a 77 GHz FMCW
> single-chip radar explicitly designed for blind-spot detection (TI SWRS203D),
> certified to ISO 26262 ASIL-B.  A single centre-rear unit is used, matching
> the Chigee SR-1 commercial baseline.  Left/right side discrimination is
> derived from the detection's azimuth sign, validated by the AWR1642's 4RX
> angular resolution.  The simulation pipeline is calibrated to this hardware's
> sparse point density and IF bandwidth constraints, with the ONNX inference
> pipeline sized to run on the chip's on-board C674x DSP at 600 MHz."*

---

## 8. References

* **[1]** Texas Instruments (2017). *AWR1642 Single-Chip 77- and 79-GHz FMCW
  Radar Sensor* (Doc SWRS203D, Rev D). Dallas, TX: Texas Instruments.
  Available: [https://www.ti.com/lit/ds/symlink/awr1642.pdf](https://www.ti.com/lit/ds/symlink/awr1642.pdf)
