# `WheelSpeedReading` — Field Reference

`WheelSpeedReading` is the **frozen snapshot** emitted by `WheelSpeedSensor` once
per CARLA tick. Every field is described below: what it represents physically, how it
is computed, and how (or whether) downstream code should consume it.

---

## `speed_mps` · `float`

**The v\_ego value that DEDR must consume.** Units: metres per second.

This is the final, pipeline-processed estimate of the ego vehicle's forward speed. It
has passed through all three corruption stages in sequence:

1. Gaussian noise was added to the ideal pulse frequency (see `WheelSpeedSensorConfig`
   § Gaussian noise bands).
2. The noisy frequency was converted back to a speed via `v = (f × C) / N`.
3. The speed was quantised to the nearest discrete step that a real encoder can resolve
   (see `WheelSpeedSensorConfig` § Quantization).
4. If a scripted fault was active on this tick, the value was overwritten by the
   fault-injection function (see `fault_active`).

**Never pass `true_speed_mps` to DEDR in place of this field.** Doing so bypasses the
entire sensor-simulation pipeline and makes the experiment scientifically invalid.

---

## `true_speed_mps` · `float`

**CARLA's unmodified ground-truth speed. For offline analysis and plots only.** Units:
metres per second.

Computed as the Euclidean magnitude of the actor's velocity vector returned by
`actor.get_velocity()`:

```
true_speed = sqrt(vx² + vy² + vz²)
```

This field exists so that post-run analysis scripts can compare the simulated sensor
reading against the true trajectory, measure the noise/quantisation error distribution,
and validate that the noise model is behaving as specified. It has **no role in the
real-time control or DEDR pipeline** — a real ECU does not have access to ground truth.

---

## `pulse_frequency_hz` · `float`

**The simulated encoder pulse frequency after Gaussian noise, before quantisation.**
Units: Hz.

Computed as:

```
f_ideal  = (true_speed × N) / C      # noiseless frequency
f_observed = f_ideal + gauss(0, σ)   # with banded noise applied
```

where `σ` is `f_ideal × noise_pct` for the applicable frequency band (see
`WheelSpeedSensorConfig.low_freq_noise_pct` / `high_freq_noise_pct`).

This intermediate value is stored primarily to support signal-chain diagnostics. It
lets an analysis script reconstruct *where* in the pipeline a large error arose (noise
stage vs. quantisation stage). It is **not** the same as the frequency that would
produce `speed_mps` after quantisation — they differ because quantisation snaps
the speed to a discrete grid after the frequency is converted back.

---

## `timestamp` · `float`

**CARLA simulation elapsed time at which this reading was captured.** Units: seconds.

Taken directly from `snapshot.timestamp.elapsed_seconds`, the monotonic clock
maintained by the CARLA server for the current episode. Its primary uses are:

- **Cross-sensor alignment** — correlating this reading with simultaneous IMU and radar
  snapshots taken on the same tick.
- **Fault-injection scheduling** — `make_slip_fault` uses this value to decide whether
  the fault window is currently active (`start_time_s ≤ elapsed_seconds < start_time_s
  + duration_s`).
- **Latency accounting** — comparing the reading's timestamp against the wall-clock time
  at which downstream code consumes it.

This is *not* wall-clock time and resets to zero at the start of each CARLA episode.
Do not compare timestamps across episodes.

---

## `fault_active` · `bool`

**True if and only if a scripted fault-injection function overwrote `speed_mps` on
this tick.**

When `True`, `speed_mps` reflects the fault function's return value rather than the
noise-and-quantisation pipeline output. `pulse_frequency_hz` is still the pre-fault,
noise-corrupted value — it is intentionally left unmodified so that analysis scripts
can reconstruct the fault magnitude as `speed_mps − (f_observed × C / N)`.

This flag is `False` in two situations:

1. `WheelSpeedSensorConfig.enable_fault_injection` is `False` (the normal operating
   mode).
2. The fault function returned `None` on this tick (the current time is outside the
   scripted fault window).

In test-report tables, `fault_active` is the authoritative label indicating which ticks
belong to the slip/lockup event vs. normal operation.
