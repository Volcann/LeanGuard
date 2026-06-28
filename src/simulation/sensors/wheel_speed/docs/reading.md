# `WheelSpeedReading` — Field Reference

## 1. Overview

`WheelSpeedReading` is the data structure returned by the `WheelSpeedSensor` at the end of each simulation frame. This reference specifies what each field represents and how it is intended to be used within the pipeline.

## 2. Field Reference

### 2.1 Primary Sensor Output

#### `speed_mps` · `float`

**Definition.** The speed value ($v_{\text{ego}}$) that should be passed to DEDR. Units: meters per second.

This is the final speed output from the sensor simulation, produced after three corruption stages are applied, in order:

1. **Jitter.** Gaussian noise is added to the ideal pulse frequency.
2. **Kinematic mapping.** The noisy frequency is converted to speed using $v = \frac{f \times C}{N}$.
3. **Quantization.** The speed is rounded to match the resolution of a 2.5 MHz ECU clock.

> [!IMPORTANT]
> To keep tests realistic, downstream algorithms must always receive this field — never the ground-truth speed.

### 2.2 Ground-Truth Reference (Offline Use Only)

#### `true_speed_mps` · `float`

**Definition.** The exact ground-truth speed from the CARLA physics simulator. Units: meters per second.

This value is computed as the Euclidean norm of the simulator's velocity vector:

$$v_{\text{true}} = \sqrt{v_x^2 + v_y^2 + v_z^2}$$

> [!IMPORTANT]
> This field is used only for offline analysis and plotting, to measure the sensor's error. It must not be used in the real-time DEDR pipeline, since a real ECU only ever sees the noisy sensor output.

### 2.3 Intermediate Diagnostic Signal

#### `pulse_frequency_hz` · `float`

**Definition.** The simulated pulse frequency after noise has been added, but before quantization. Units: Hz.

It is computed as:

```
f_ideal = (v_true × N) / C
f_observed = f_ideal + Gaussian_noise(0, σ)
```

This field is retained to support debugging of the signal chain, making it possible to determine whether a large speed error originates from the random-noise stage or the quantization stage.

### 2.4 Temporal Reference

#### `timestamp` · `float`

**Definition.** The simulator time at which this reading was captured. Units: seconds.

This value is drawn from the simulator's clock and is used to:
- Align wheel-speed readings with IMU and radar data.
- Track processing latencies through the pipeline.

This value is relative and resets to zero at the start of each simulation run.
