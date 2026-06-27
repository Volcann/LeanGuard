# `WheelSpeedSensorConfig` — Field Reference

`WheelSpeedSensorConfig` controls all tunable parameters of the simulated Hall-effect wheel-speed sensor. The default values are chosen to match a Bosch-equipped KTM (e.g., KTM 1290 Super Duke / Adventure) or Ducati (e.g., Panigale / Multistrada) class motorcycle. If you change these parameters, make sure to update `wheel_speed.md` to keep the documentation consistent.

---

## § Encoder Geometry

### `num_teeth` · `int` · default `48`

The number of teeth (or slots) on the ABS tone ring of the motorcycle's wheel.

**Why we chose this value:** High-performance motorcycles from KTM, Ducati, and BMW natively integrate standard Bosch ABS (Motorcycle Stability Control) architectures, which utilize 48-slot (or 50-slot) tone rings (often referred to as phonic wheels). Although our physical noise reference datasheets (Bosch HA-M / HA-D 90 motorsport sensors) target different wheel configurations (like a 60-tooth target wheel), our simulation models the standard 48-slot geometry to match real-world street ABS installations while inheriting the auditable noise characteristics of the Bosch motorsport specifications.

(Note: Yamaha motorcycles use proprietary OEM speed sensors that are electrically incompatible with Bosch motorsport sensors as direct replacements, which is why we model the KTM/Ducati phonic wheel standard here.)

**Confidence Level:** Verified. Modern Bosch motorcycle ABS tone rings have 48 slots.

**Workaround:** We run a sensitivity sweep across the values in `num_teeth_sweep_values` to verify that the DEDR algorithm performs consistently even if the real tooth count differs slightly.

---

### `wheel_circumference_m` · `float` · default `1.98`

The outer circumference of the front wheel in meters, used to convert between speed and pulse frequency:

```
f = (v × N) / C   and   v = (f × C) / N
```

**Why we chose this value:** This is a standard nominal value for a 120/70-17 front tire under typical load and inflation pressure, which is standard for street/sport models like the KTM 1290 Super Duke R or Ducati Panigale V4.

**Sensitivity:** A 2% error in wheel circumference results in a 2% speed measurement error. This error is small compared to the random noise, so we don't expect it to affect the DEDR false-positive rate. No sweep is planned for this value.

---

### `num_teeth_sweep_values` · `tuple[int, ...]` · default `(40, 44, 48, 50)`

The range of tooth counts to check in our sensitivity sweep.

These values cover the physically likely range for Bosch-equipped motorcycles: 40 to 44 slots are typically found on smaller wheels or older setups, 48 is the standard for modern ABS/MSC systems, and 50 is a common alternative configuration. We test each option while holding other settings constant to ensure DEDR remains stable.

---

## § Noise Model

### `low_freq_threshold_hz` · `float` · default `200.0`

The frequency limit below which the low-speed noise settings are used.

**Why we chose this value:** Bosch datasheets specify that Hall-effect speed sensors achieve better accuracy at lower frequencies. Their published breakpoints target high-RPM engine crankshaft sensors, so we scaled the threshold down for a motorcycle wheel at road speeds. With the standard $N = 48$ tone ring spinning at 10 rev/s, the pulse frequency is $48 \times 10 = 480\text{ Hz}$, which corresponds to a wheel speed of $v = \frac{480 \times 1.98}{48} \approx 19.8\text{ m/s}$ (~71 km/h). The 200 Hz threshold therefore maps to $v = \frac{200 \times 1.98}{48} \approx 8.25\text{ m/s}$ (~30 km/h) — the low-speed boundary below which the tighter `low_freq_noise_pct` is applied.

---

### `low_freq_noise_pct` · `float` · default `0.01`

The Gaussian noise standard deviation as a fraction of the ideal frequency, used when `f_true ≤ low_freq_threshold_hz`.

**Why we chose this value:** Based on the Bosch HA-D 90 specification, which lists low-frequency accuracy as `< 1.0%`. We model this as a $1\sigma$ standard deviation.

---

### `high_freq_noise_pct` · `float` · default `0.04`

The Gaussian noise standard deviation as a fraction of the ideal frequency, used when `f_true > low_freq_threshold_hz`.

**Why we chose this value:** Based on the Bosch HA-M datasheet, which lists high-frequency accuracy as `< 4%`. Using this spec provides a conservative (worst-case) noise model for evaluating our safety logic.

---

## § Quantization

### `enable_quantization` · `bool` · default `True`

Toggles the ECU inter-pulse timing quantization. 

When enabled, the model simulates how a real Bosch ABS ECU processes speed: instead of aligning speed updates to the CARLA tick rate (which causes a blocky 1.62 m/s step pattern), it calculates the time between teeth, rounds it to the nearest ECU clock tick, and then converts it back to speed. This results in a realistic speed resolution of ~0.001 m/s at cruise speeds.

---

### `ecu_timer_resolution_s` · `float` · default `4e-7` (0.4 μs)

The clock step of the simulated ABS ECU, in seconds.

**Why we chose this value:** A 2.5 MHz clock (0.4 μs step) is typical for Bosch ABS 5.x and ABS 8 ECUs. The hardware captures this timer value on each tooth-edge interrupt to measure the time between pulses.

**Resolution Math:** The speed resolution from quantization is:

```
Δv ≈ v² × ecu_timer_resolution_s × N / C
```

At 13.7 m/s, this yields a resolution of 0.0018 m/s. This is about 900 times finer than the 30 Hz discrete simulator step.

**Limitation (Physics Frame Rate):** Because the simulator updates the vehicle's state at 30 Hz, the actual velocity is assumed to change linearly (constant acceleration) within each 33.3 ms step. Any high-frequency velocity changes occurring *inside* a single simulator frame cannot be captured by the sensor.

---

## § Fault Injection

### `enable_fault_injection` · `bool` · default `False`

Enables the scripted slip/lockup fault injection.

We model tire slip as a distinct fault rather than background noise because it represents a physical traction loss, not a sensor error. This lets us clearly mark fault windows during testing.

---

### `fault_injection_fn` · `Optional[FaultInjectionFn]` · default `None`

The custom function used to override the reported speed. 

It takes the true speed and the elapsed simulation time, and returns a modified speed float or `None` (which leaves the normal speed calculation unchanged). You can use `make_slip_fault` to simulate acceleration wheel spin (`slip_factor > 1.0`) or braking lockups (`slip_factor < 1.0`).

---

## § Reproducibility

### `rng_seed` · `Optional[int]` · default `None`

The seed for the random number generator used for Gaussian noise.

- `None` makes the noise random on every run.
- An integer seed produces the exact same noise sequence across runs, which is useful for debugging and repeatable tests.
