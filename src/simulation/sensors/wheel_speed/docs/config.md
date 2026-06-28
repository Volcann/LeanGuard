# `WheelSpeedSensorConfig` — Field Reference

## 1. Overview

`WheelSpeedSensorConfig` defines all tunable parameters of the simulated Hall-effect wheel-speed sensor described in `design.md`. The default values are chosen to match a Bosch-equipped KTM (e.g., KTM 1290 Super Duke / Adventure) or Ducati (e.g., Panigale / Multistrada) class motorcycle. Any change to these parameters must be accompanied by a corresponding update to `design.md`, so that the configuration and its supporting justification remain consistent with one another.

## 2. Encoder Geometry Parameters

### `num_teeth` · `int` · default `48`

**Definition.** The number of teeth (or slots) on the ABS tone ring of the motorcycle's wheel.

**Rationale.** High-performance motorcycles from KTM, Ducati, and BMW natively integrate standard Bosch ABS (Motorcycle Stability Control) architectures, which utilize 48-slot (or 50-slot) tone rings, commonly referred to as phonic wheels. Although the physical noise reference datasheets (Bosch HA-M / HA-D 90 motorsport sensors) target a different wheel configuration (a 60-tooth target wheel), the simulation models the standard 48-slot geometry in order to match real-world street ABS installations, while still inheriting the auditable noise characteristics published in the Bosch motorsport specifications.

> [!NOTE]
> Yamaha motorcycles use proprietary OEM speed sensors that are electrically incompatible with Bosch motorsport sensors as direct replacements. This incompatibility is the reason the KTM/Ducati phonic-wheel standard is modeled here rather than a Yamaha-specific configuration.

**Confidence level.** Verified. Modern Bosch motorcycle ABS tone rings have 48 slots.

**Workaround.** A sensitivity sweep is run across the values in `num_teeth_sweep_values` to verify that the DEDR algorithm performs consistently even if the real tooth count differs slightly from the assumed default.

---

### `wheel_circumference_m` · `float` · default `1.98`

**Definition.** The outer circumference of the front wheel, in meters, used to convert between speed and pulse frequency:

```
f = (v × N) / C   and   v = (f × C) / N
```

**Rationale.** This is a standard nominal value for a 120/70-17 front tire under typical load and inflation pressure — standard for street/sport models such as the KTM 1290 Super Duke R or Ducati Panigale V4.

**Sensitivity.** A 2% error in wheel circumference results in a 2% speed-measurement error. This error is small compared to the random noise component, so it is not expected to affect the DEDR false-positive rate. No sensitivity sweep is planned for this value.

---

### `num_teeth_sweep_values` · `tuple[int, ...]` · default `(40, 44, 48, 50)`

**Definition.** The range of tooth counts evaluated in the sensitivity sweep referenced under `num_teeth`.

**Rationale.** These values cover the physically plausible range for Bosch-equipped motorcycles: 40 and 44 slots are typically found on smaller wheels or older setups, 48 is the standard for modern ABS/MSC systems, and 50 is a common alternative configuration. Each option is tested while holding all other settings constant, to confirm that DEDR remains stable across this range.

## 3. Noise Model Parameters

### `low_freq_threshold_hz` · `float` · default `200.0`

**Definition.** The pulse-frequency boundary below which the low-speed noise setting (`low_freq_noise_pct`) is applied; above this boundary, `high_freq_noise_pct` is applied instead.

**Rationale.** Bosch datasheets specify that Hall-effect speed sensors achieve better accuracy at lower frequencies. Because the published breakpoints in those datasheets target high-RPM engine crankshaft sensors, the threshold was scaled down for a motorcycle wheel operating at road speeds. With the standard $N = 48$ tone ring spinning at 10 rev/s, the pulse frequency is $48 \times 10 = 480\text{ Hz}$, corresponding to a wheel speed of $v = \frac{480 \times 1.98}{48} \approx 19.8\text{ m/s}$ (≈ 71 km/h). The 200 Hz threshold therefore maps to $v = \frac{200 \times 1.98}{48} \approx 8.25\text{ m/s}$ (≈ 30 km/h) — the low-speed boundary below which the tighter `low_freq_noise_pct` is applied.

---

### `low_freq_noise_pct` · `float` · default `0.01`

**Definition.** The Gaussian noise standard deviation, expressed as a fraction of the ideal frequency, applied when `f_true ≤ low_freq_threshold_hz`.

**Rationale.** Based on the Bosch HA-D 90 specification, which lists low-frequency accuracy as `< 1.0%`. This bound is modeled as a $1\sigma$ standard deviation.

---

### `high_freq_noise_pct` · `float` · default `0.04`

**Definition.** The Gaussian noise standard deviation, expressed as a fraction of the ideal frequency, applied when `f_true > low_freq_threshold_hz`.

**Rationale.** Based on the Bosch HA-M datasheet, which lists high-frequency accuracy as `< 4%`. Using this specification provides a conservative (worst-case) noise model for evaluating the safety logic.

## 4. Bandwidth Limitation Parameters

### `max_operating_frequency_hz` · `float` · default `4200.0`

**Definition.** The maximum operating frequency of the physical Bosch HA-M sensor, in Hz. If the computed ideal pulse frequency exceeds this value, the sensor output is immediately zeroed (`speed_mps = 0.0`, `pulse_frequency_hz = 0.0`).

**Primary source.** Official Bosch HA-M datasheet [1]:

> *"Max. frequency: ≤ 4.2 kHz"*
> *"Accuracy repeatability of the falling edge of tooth: < 4% (≤ 4.2 kHz)"*

The datasheet specifies **no behavior beyond this limit**. The `< 4%` accuracy guarantee ends exactly at 4.2 kHz; nothing further is stated or characterized.

**Why hard dropout and not soft attenuation.** An exponential soft-clipping model was investigated during development:

$$f_{\text{attenuated}} = f_{\text{max}} \cdot e^{-\alpha (f - f_{\text{max}})}$$

A value of $\alpha = 0.00032$ was initially derived by assuming the sensor retains 15% amplitude at 10,000 Hz (where the error was assumed to double to < 8%). After re-reading both primary sources, neither document contains any data point beyond 4,200 Hz — no 10 kHz endpoint, no secondary error bound, no amplitude curve. The $\alpha$ value was therefore unverifiable, and the model was dropped entirely.

The **hard cutoff is the only academically defensible implementation** given the available primary sources.

**Practical impact.** For the default setup ($N = 48$, $C = 1.98\text{ m}$), this ceiling maps to $v \approx 173.25\text{ m/s}$ (≈ 624 km/h) — physically unreachable by any production motorcycle. This field is a correctness safety rail, not a normal operating constraint. See `design.md §6` ("Frequency Ceiling and Saturation Behavior," §6.3–6.4) for the full justification and the speed-threshold table.

## 5. Quantization Parameters

### `enable_quantization` · `bool` · default `True`

**Definition.** Toggles the ECU inter-pulse timing quantization.

**Behavior.** When enabled, the model simulates how a real Bosch ABS ECU processes speed: instead of aligning speed updates to the CARLA tick rate — which causes a blocky 1.62 m/s step pattern — it calculates the time between teeth, rounds it to the nearest ECU clock tick, and converts the rounded value back to speed. This yields a realistic speed resolution of approximately 0.001 m/s at cruise speeds.

---

### `ecu_timer_resolution_s` · `float` · default `4e-7` (0.4 μs)

**Definition.** The clock step of the simulated ABS ECU, in seconds.

**Rationale.** A 2.5 MHz clock (0.4 μs step) is typical for Bosch ABS 5.x and ABS 8 ECUs. The hardware captures this timer value on each tooth-edge interrupt to measure the time between pulses.

**Resolution math.** The speed resolution arising from quantization is:

```
Δv ≈ v² × ecu_timer_resolution_s × N / C
```

At 13.7 m/s, this yields a resolution of 0.0018 m/s — approximately 900 times finer than the 30 Hz discrete simulator step.

**Limitation (physics frame rate).** Because the simulator updates the vehicle's state at 30 Hz, the actual velocity is assumed to change linearly (constant acceleration) within each 33.3 ms step. Any high-frequency velocity change occurring *inside* a single simulator frame cannot be captured by the sensor.

## 6. Reproducibility Parameters

### `rng_seed` · `Optional[int]` · default `None`

**Definition.** The seed for the random number generator used to produce the Gaussian noise.

**Behavior.**
- `None` makes the noise random on every run.
- An integer seed produces the exact same noise sequence across runs, which is useful for debugging and repeatable tests.
