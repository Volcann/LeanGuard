# `WheelSpeedReading` — Field Reference

`WheelSpeedReading` is the data structure returned by the `WheelSpeedSensor` at the end of each simulation frame. This reference explains what each field represents and how it is used in the pipeline.

---

## `speed_mps` · `float`

**The speed value ($v_{\text{ego}}$) that should be passed to DEDR.** Units: meters per second.

This is the final speed output from the sensor simulation, after applying all corruption stages:

1. **Jitter:** Gaussian noise is added to the ideal pulse frequency.
2. **Kinematic mapping:** The noisy frequency is converted to speed using `v = (f × C) / N`.
3. **Quantization:** The speed is rounded to match the resolution of a 2.5 MHz ECU clock.
4. **Fault Injection:** If active, the value is overridden by a scripted fault function.

To keep tests realistic, you must always pass this field to downstream algorithms rather than the ground-truth speed.

---

## `true_speed_mps` · `float`

**The exact ground-truth speed from the CARLA physics simulator.** Units: meters per second.

This is calculated as the Euclidean norm of the simulator's velocity vector:

$$v_{\text{true}} = \sqrt{v_x^2 + v_y^2 + v_z^2}$$

This field is used only for offline analysis and plotting to measure the sensor's error. It must not be used in the real-time DEDR pipeline, since a real ECU only sees the noisy sensor output.

---

## `pulse_frequency_hz` · `float`

**The simulated pulse frequency after noise is added, but before quantization.** Units: Hz.

It is computed as:

```
f_ideal = (v_true × N) / C
f_observed = f_ideal + Gaussian_noise(0, σ)
```

We keep this field to help debug the signal chain, making it easier to see if a large speed error was caused by the random noise stage or the quantization stage.

---

## `timestamp` · `float`

**The simulator time when this reading was captured.** Units: seconds.

This is pulled from the simulator's clock and is used to:
- Align wheel speed readings with IMU and radar data.
- Determine if a scripted fault window is currently active.
- Track processing latencies through the pipeline.

This value is relative and resets to zero at the start of each simulation run.

---

## `fault_active` · `bool`

**Indicates whether a scripted fault override was active during this frame.**

When this is `True`, `speed_mps` contains the overridden fault value instead of the normal speed calculation. The `pulse_frequency_hz` field is left unchanged so that analysis tools can calculate the exact fault deviation:

```
Δv = speed_mps - (pulse_frequency_hz × C / N)
```
