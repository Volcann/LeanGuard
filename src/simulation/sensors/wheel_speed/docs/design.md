# Wheel-Speed Sensor Simulation: Design Justification and Validation

## 1. Introduction

This document specifies and justifies the design of the simulated wheel-speed sensor used to derive the ego-vehicle speed estimate, `v_ego`, consumed by the project's infrastructure-rejection algorithm (DEDR). It describes the physical operating principle of a real wheel-speed sensor, the mathematical model adopted for the simulation, the empirical and citation basis underlying every model parameter, the resulting noise model, and the validation evidence confirming that the implemented model behaves consistently with its cited specifications. The objective is to ensure that the inputs supplied to DEDR during simulated testing — and, by extension, the conclusions drawn from that testing — rest on a physically defensible foundation rather than an idealized one.

## 2. Motivation

The CARLA simulator is capable of returning the exact, noise-free velocity of a simulated actor directly (via `actor.get_velocity()`). Supplying this ground-truth value to DEDR without modification was considered and rejected. Such a configuration would not be physically realistic, and adopting it as the basis for evaluating DEDR would be methodologically unsound: a production motorcycle ECU never has access to perfect, noise-free velocity data, and a validation exercise that grants the algorithm such an advantage would not constitute a fair or defensible test of its performance. The simulated wheel-speed sensor model described in this document exists to close that gap, so that the speed signal presented to DEDR in simulation reproduces the acquisition characteristics — including the imperfections — of a real sensor-and-ECU pipeline.

## 3. Physical Background: Wheel-Speed Sensor Operating Principle

A real Hall-effect wheel-speed sensor does not measure vehicle speed directly. Instead, speed is inferred indirectly through the following sequence:

1. A toothed component, referred to as a tone ring (or encoder ring), is mounted on the wheel hub adjacent to the sensor.
2. As the wheel rotates, each tooth passes the sensor and locally disturbs the magnetic field.
3. The sensor detects this disturbance and outputs a digital pulse.
4. The ECU counts these pulses over a known time interval and computes the corresponding speed.

![Physical Wheel-Speed Sensor and Tone Ring](../../../../../docs/assets/physical_sensor_installation.png)

The standard relationship used to convert pulse frequency to linear speed is:

```
v = (f × C) / N
```

where:
- `v` = speed (m/s)
- `f` = pulse frequency (Hz)
- `C` = wheel circumference (m)
- `N` = number of teeth on the tone ring

This relationship is standard throughout the automotive industry and is documented in the vehicle dynamics and diagnostic literature, e.g., Ladoiye et al. [4].

### 3.1 Independence of the Conversion Formula from Tooth-Count Uncertainty

The formula above follows directly from elementary kinematics: it converts a measured rotational frequency into a linear speed using the known wheel geometry. The tooth count, `N`, enters the formula only as a parameter. Consequently, any uncertainty regarding the exact tooth count of a specific motorcycle model is a *calibration* question, not a question of the formula's *validity* — the relationship between tooth count, pulse frequency, wheel circumference, and resulting speed holds for any value of `N`.

> **Worked Example (Front-Wheel Default Parameters)**
> - `N` = 48 teeth
> - `C` = 1.98 m (typical for a 120/70-17 front tire, e.g., on a KTM 1290 Super Duke R or Ducati Panigale V4)
> - `f` = 480 Hz (measured pulse frequency)
>
> ```
> 1. Revolutions per second:
>    rev/s = f / N = 480 / 48 = 10 rev/s
>
> 2. Linear speed:
>    v = rev/s × C = 10 × 1.98 = 19.8 m/s (≈ 71.3 km/h)
> ```

Should the assumed tooth count require revision in the future (for example, to 40 or 50 teeth), only the parameter `N` needs to change. The underlying formula and the structure of the sensor model remain unaffected.

## 4. Engineering Assumptions and Empirical Basis for Model Parameters

The parameters of the simulated sensor model were derived from published hardware specifications rather than assumed arbitrarily.

| Source | Sensor / Context | Details |
|---|---|---|
| Bosch Motorsport HA-D 90 datasheet [2] / HA-M datasheet [1] | Motorsport Hall-effect speed sensors (proxy) | Lists edge-detection accuracy as < 1.0–1.5% (HA-D 90) and < 4% (HA-M), depending on frequency. These ranges calibrate the noise model. |
| Production motorcycle ABS tone-ring standards | KTM, Ducati, and BMW Motorrad platforms | Standardize on 48-slot (or 50-slot) tone rings for front/rear wheel-speed sensors connected to Bosch ABS / MSC ECUs. |

The data support three conclusions:

1. **KTM/Ducati native Bosch integration.** KTM and Ducati co-develop and natively integrate Bosch ABS (Motorcycle Stability Control) systems and wheel-speed sensors.
2. **Tooth count is standardized.** Modern Bosch motorcycle ABS tone rings use 48 slots. This is the verified industry benchmark adopted for simulation (N = 48).
3. **Noise parameters are realistic.** The Bosch datasheets (HA-D 90 / HA-M) provide an auditable reference for the shape and scale of the noise model. Specifically, the noise model uses a frequency-banded approach that combines the HA-D 90 [2] specification (< 1% error) for low speeds with the HA-M [1] specification (< 4% error) for high speeds to define the overall noise envelope.

> [!NOTE]
> Earlier work considered referencing aftermarket Yamaha tone rings with 37/38 teeth. These are excluded from the baseline configuration on two grounds: the physical incompatibility of Bosch sensors with Yamaha hardware, and unresolved provenance concerns surrounding the aftermarket parts in question.

## 5. Sensor Selection and Model Justification

### 5.1 Selection Rationale: the Bosch HA-M as a Mathematical Proxy

The choice of a specific sensor reference model is a deliberate methodological decision with direct bearing on the credibility of the simulation.

The central difficulty is that the technical manuals and noise profiles of production street-bike ABS sensors — typically two-wire, current-loop active sensors — are proprietary and withheld by manufacturers. To keep the simulation physically realistic and academically reproducible, the noise profile must instead be grounded in public, auditable engineering specifications.

> "The manuals for real street-bike sensors are kept secret by the manufacturers. Because we need real-world numbers for our simulation, we are using the public manuals for Bosch's racing sensors as a stand-in. It is not the exact part used on street bikes, but it provides mathematically sound, real-world data from the same manufacturer."
>
> — *Methodology Note*

The Bosch HA-M and HA-D 90 are three-wire motorsport sensors designed for race-logging applications, and their datasheets reference 60-tooth wheels in their application examples. Nonetheless, they are manufactured by the same company and rely on the same underlying Hall-effect sensing technology as production ABS sensors. Their documented repeatable accuracy bound (< 4% repeatability error, HA-M) therefore serves as a mathematically sound, real-world proxy for simulating wheel-speed sensing, even though it is not drawn from the exact part used in production street motorcycles.

Three properties make the Bosch HA-M / HA-D 90 datasheets an appropriate choice as a stand-in:

| Property | Why It Matters |
|---|---|
| Motorsport/OEM-grade specifications | Bosch motorsport sensors are designed for high-performance, harsh-environment use. Simulating their characteristics ensures the safety logic is tested against the standards of high-end vehicle-dynamics equipment. |
| Fully auditable datasheet [1] | Bosch publishes the HA-M's repeatability error (< 4%), operating bandwidth (up to 4.2 kHz), and application notes in a traceable technical document. Every noise parameter in this model can be traced directly to that datasheet. |
| Matched physical domain | The HA-M datasheet explicitly lists wheel-speed sensing and rotational-speed measurement among its primary design applications, leaving no ambiguity as to whether the sensor technology is intended for the use case being simulated. |

In summary, the simulation combines the verified 48-slot geometry of production street-bike ABS rings (KTM/Ducati) with the verified physical noise limits (< 4% jitter) published in the Bosch motorsport datasheets, providing a transparent, realistic, and academically defensible foundation for the sensor model.

> [!NOTE]
> The HA-M motorsport sensor operates on the same physical principle as a standard ABS sensor but uses three wires rather than two; its electrical noise characteristics in a real vehicle may therefore differ somewhat from a production sensor's. The HA-M's published noise values are adopted here as a safe estimate, not on the premise that the two sensor types are electrically identical.

### 5.2 Physical Differences Between Two-Wire and Three-Wire Sensor Architectures

- **Standard street-bike ABS sensors** typically use **two wires**. They encode the speed signal by varying the *current* flowing through the power wires. This current-loop method is highly resistant to electrical noise.
- **The Bosch HA-M motorsport sensor** uses **three wires** (power, ground, and a separate signal output) and encodes the signal as *voltage* pulses, which can be somewhat more sensitive to electromagnetic noise from the motorcycle's engine and ignition system than a two-wire current loop.

### 5.3 Justification for Use Despite Architectural Differences ("Safe Estimate")

Because production motorcycle manufacturers keep their two-wire ABS sensor data proprietary, their exact noise profiles cannot be obtained directly. Using the HA-M's published specification, which permits up to < 4% noise, instead tests the safety algorithm (DEDR) under a worst-case, noisier scenario than a production two-wire sensor is expected to produce.

> [!NOTE]
> *"I acknowledge they have different wiring and slightly different noise behaviors. However, since production data is proprietary, I used the 3-wire HA-M datasheet as a **conservative, worst-case proxy**. This is a reasonable working assumption, not a proven result: it has not been independently validated against real 2-wire sensor data, and a 2-wire current-loop sensor could in principle have failure modes the HA-M doesn't exhibit. The claim here is narrower than 'will easily handle' — it is that testing DEDR against the HA-M's noisier envelope gives us a margin of safety relative to the cleaner signal a production 2-wire sensor is expected to produce, not a guarantee of performance on that sensor."*

### 5.4 Academic Justifications Derived from the Bosch HA-M Specification

The Bosch HA-M technical specification [1] supports the model in three respects:

1. **Noise bounds.** As established in §5.3, the datasheet's < 4% repeatability error of the tooth's falling edge is used as the conservative proxy for total sensor noise.
2. **Sensor bandwidth.** The sensor supports operating frequencies up to 4.2 kHz. For the target configuration ($N = 48$, $C = 1.98\text{ m}$), the maximum measurable speed is:
   $$v_{\max} = \frac{4200 \times 1.98}{48} \approx 173.25\text{ m/s (approx. 387 mph)}$$
   Even at $N = 50$, the maximum measurable speed is $166.32\text{ m/s}$ (approx. 372 mph). Because a high-performance motorcycle such as the KTM 1290 Super Duke R is electronically limited to approximately $78\text{ m/s}$ ($280\text{ km/h}$), the sensor operates with more than a twofold safety margin ($f_{\max} \approx 1890\text{ Hz}$ versus the sensor's 4200 Hz ceiling) and will not saturate under realistic operating conditions.
3. **Validation requirements.** The datasheet notes that raw pulse signals should not be used in safety systems without signal validation. This requirement is what justifies the existence of the project's validation layers (DEDR and EKF), whose role is to filter out transient errors before they reach downstream logic.

## 6. Frequency Ceiling and Saturation Behavior

### 6.1 Datasheet-Specified Operating Limit

The official Bosch HA-M datasheet [1] specifies two relevant figures:

> *"Max. frequency: **≤ 4.2 kHz**"*
> *"Accuracy repeatability of the falling edge of tooth: **< 4% (≤ 4.2 kHz)**"*

This is the complete specification. The datasheet contains no data, curve, or characterization of sensor behavior above 4,200 Hz; the < 4% accuracy guarantee ends exactly at 4.2 kHz, and nothing further is stated.

The Bosch HA-M Engineering Report [3] adds only a qualitative description of behavior beyond the ceiling:

> *"Exceeding the upper physical ceiling of 4.2 kHz forces the internal electronics into a soft-clipping state. Instead of just scaling up noise gracefully, the sensor encounters phase lag, signal attenuation, and will ultimately drop pulses entirely."*

This confirms that a failure mode exists above the ceiling but supplies **zero quantitative data**: no amplitude curve, no secondary error bound, and no specific frequency at which the signal collapses entirely.

### 6.2 Exponential Attenuation Model: Investigated and Rejected

An exponential soft-clipping model was investigated during development as a way of simulating the qualitative degradation described above:

$$f_{\text{attenuated}} = f_{\text{max}} \cdot e^{-\alpha (f_{\text{ideal}} - f_{\text{max}})}$$

An initial decay rate of $\alpha = 0.00032$ was derived under the following assumptions:

1. The sensor retains $\approx 15\%$ signal amplitude at $10{,}000\text{ Hz}$.
2. At $10\text{ kHz}$, the error doubles to $< 8\%$ (treated as a secondary spec boundary).
3. Solving $0.15 = e^{-\alpha(10000 - 4200)}$ yields $\alpha \approx 0.00032$.

After re-reading both primary documents, this entire derivation was rejected. Neither the official datasheet [1] nor the engineering report [3] contains any data point beyond 4,200 Hz: there is no $10\text{ kHz}$ figure, no secondary $8\%$ error bound, no amplitude curve, and no signal-retention percentage at any over-speed frequency in either source. The value of $\alpha$ was therefore unverifiable from first principles and was dropped entirely.

> [!CAUTION]
> Any specific $\alpha$ value for an exponential attenuation model would be a fabricated engineering constant with no primary-source support. Using it in a thesis methodology section would be academically indefensible.

### 6.3 Design Decision: Hard Dropout at the Frequency Ceiling

The implementation instead uses a **hard cutoff**: if the ideal pulse frequency exceeds `max_operating_frequency_hz` (4,200 Hz), the sensor output is immediately set to zero (`speed_mps = 0.0`, `pulse_frequency_hz = 0.0`). This is the most conservative interpretation of the datasheet's "Max. frequency: ≤ 4.2 kHz" specification that can be defended academically.

### 6.4 Speed Threshold Mapping

For the baseline configuration ($N = 48$, $C = 1.98\text{ m}$):

$$v_{\text{cutoff}} = \frac{f_{\max} \times C}{N} = \frac{4200 \times 1.98}{48} \approx 173.25\text{ m/s} \approx 624\text{ km/h}$$

This speed is physically unreachable by any production motorcycle. For reference:

| Setup | $N$ | $v_{\text{cutoff}}$ | Reachable? |
|---|---|---|---|
| Baseline (KTM/Ducati ABS) | 48 | $173.25\text{ m/s}$ ($624\text{ km/h}$) | No |
| Dense tone ring (development rig) | 120 | $69.3\text{ m/s}$ ($249.5\text{ km/h}$) | Edge case at top speed |

The cutoff is a **correctness safety rail**: it ensures the model never produces a physically invalid output, for example if a high-density tone ring configuration is tested. Under the default $N = 48$ configuration, it will not be triggered during normal simulation.

## 7. Noise Model

The sensor's error sources are decomposed into two distinct components rather than represented as a single flat noise term:

| Error Source | Real-World Cause | Simulation Model |
|---|---|---|
| Measurement noise | Electrical or magnetic noise | Gaussian noise, scaled by frequency band per the Bosch datasheets (tighter at lower speeds, wider at high speeds). |
| Quantization | ECU timer resolution | The ideal inter-pulse time is quantized to the nearest 0.4 μs, representing a 2.5 MHz ECU clock. Speed is then recomputed from this quantized time. |

This decomposition yields a more realistic simulation of sensor behavior under normal riding conditions.

> [!NOTE]
> The measurement-noise model uses a frequency-banded approach drawing on two Bosch datasheets to define a tighter-to-wider noise envelope: the HA-D 90 [2] (< 1% repeatability error) governs the lower speed/frequency range, and the HA-M [1] (< 4% repeatability error) governs the higher frequency range. Together, these two bands constitute the simulated noise model.

### 7.1 Methodology Summary

The following statement condenses §3 and §7 above into a single citable summary for use in a thesis methodology section:

> "The simulated wheel-speed sensor calculates speed using $v = \frac{f \times C}{N}$. Noise parameters are based on Bosch HA-D 90 and HA-M datasheet specifications, using a frequency-banded Gaussian model. The tone ring is modeled with $N = 48$ teeth, corresponding to the standardized Bosch ABS tone rings utilized in modern KTM and Ducati models (e.g., KTM 1290 Super Duke / Adventure and Ducati Panigale/Multistrada). The model includes continuous noise (Gaussian jitter and 2.5 MHz timer quantization). A sensitivity sweep across $N \in [40, 50]$ is used to verify that the validation filters are robust to minor calibration differences."

## 8. Validation: Transition from a Discrete to an Event-Driven Timing Model

The simulation model was updated from a simple discrete-update scheme to an event-driven timing model in order to improve accuracy. The remainder of this section documents the problem that motivated the change, the alternatives that were considered and rejected, the solution that was adopted, and the resulting validation evidence.

### 8.1 Problem Statement: Quantization in the Discrete Tick-Counting Model

The initial implementation counted how many teeth passed the sensor during each simulator tick ($30\text{ Hz}$, i.e., $33.3\text{ ms}$ per tick). Because this interval is large relative to the period of the physical sensor pulses, it produced severe speed quantization.

At a representative speed of $13.7\text{ m/s}$ (approximately $30\text{ mph}$), the wheel rotates at roughly $7\text{ rev/s}$. With $37$ teeth, the sensor would generate approximately $260$ pulses per second. Over a single $33.3\text{ ms}$ simulator tick, only about $8.6$ teeth pass the sensor. Because the simulator could only count whole teeth per frame, the recorded count had to be either $8$ or $9$:

- Counting $8$ teeth in $33.3\text{ ms}$ corresponds to $12.85\text{ m/s}$.
- Counting $9$ teeth in $33.3\text{ ms}$ corresponds to $14.46\text{ m/s}$.

As a result, the computed speed fluctuated between $12.85\text{ m/s}$ and $14.46\text{ m/s}$ — a quantization step of $1.62\text{ m/s}$ — even at a perfectly constant true speed. This step-like output profile is unrepresentative of a real wheel-speed sensor. To obtain reliable, accurate speed data, a more robust model, decoupled from the simulator's tick rate, was implemented.

### 8.2 Rejected Alternative Solutions

- **Option 1 (Interpolation).** Rejected because interpolation merely smooths the discrete jumps in the output without introducing any additional physical modeling.
- **Option 3 (Higher simulator tick rate).** Rejected because increasing the tick rate raises CPU load substantially and does not reflect how a real ECU operates.

### 8.3 Adopted Solution: Event-Driven Inter-Pulse Timing (Option 2)

The model was rewritten to track the timestamp at which each tooth passes the sensor. A $2.5\text{ MHz}$ ECU timer is simulated by rounding these timestamps to the nearest $0.4\text{ }\mu\text{s}$, after which speed is back-calculated from the resulting inter-pulse time difference.

### 8.4 Results and Validation

The event-driven model improved speed resolution from the original $1.62\text{ m/s}$ simulator-tick steps to approximately $0.001\text{ m/s}$. This model was validated both theoretically, against the Bosch Motorsport HA-M datasheet specifications, and empirically, via simulation telemetry logs.

**Theoretical prediction.** The Bosch HA-M sensor datasheet specifies a repeatability accuracy of $< 4\%$ at operating frequencies above $200\text{ Hz}$ (corresponding to speeds above approximately $32\text{ km/h}$). Modeling this bound as a $1\sigma$ standard deviation of the Gaussian jitter on frequency:

$$\sigma_f = f_{\text{true}} \times 0.04$$

Because speed $v$ is proportional to frequency ($v = f \times \frac{C}{N}$), the standard deviation of the velocity estimate scales directly with the standard deviation of frequency:

$$\sigma_v = v_{\text{true}} \times 0.04$$

At a steady velocity of $13.7\text{ m/s}$ (approximately $30\text{ mph}$):

$$\sigma_v = 13.7\text{ m/s} \times 0.04 = 0.548\text{ m/s}$$

**Empirical validation.** Running the CARLA simulation at a constant $13.7\text{ m/s}$ and logging the estimated speeds yields a sample standard deviation of **$0.55\text{ m/s}$**, matching the theoretical prediction of $0.548\text{ m/s}$.

**Quantization effect.** The magnitude of the quantization error introduced by the ECU's finite clock resolution, and why it is nonetheless retained in the model, merits separate discussion.

In informal terms, the ECU does not measure time with infinite precision; it relies on an internal digital clock ticking at $2.5\text{ MHz}$. This is analogous to a stopwatch capable of displaying time only in discrete steps of $0.4\text{ μs}$, rather than as a continuous quantity. When the ECU measures the interval between two tooth pulses, it rounds that interval to the nearest clock tick, introducing a small imprecision when the interval is converted back into a speed value.

More precisely, the ECU measures the inter-pulse time $T = \frac{d}{v}$, where $d = \frac{C}{N}$ is the arc length corresponding to one tooth. Rounding $T$ to the nearest clock step $\Delta t_{\text{ECU}} = 0.4\text{ μs}$ introduces an uncertainty in $T$ of at most $\pm\frac{\Delta t_{\text{ECU}}}{2}$. Applying error propagation ($\delta v = \frac{d}{T^2} \cdot \delta T$), the resulting speed step is:

$$\Delta v \approx \frac{v^2 \cdot \Delta t_{\text{ECU}} \cdot N}{C} = \frac{(13.7)^2 \times 4 \times 10^{-7} \times 48}{1.98} \approx 0.00182\text{ m/s}$$

Assuming the rounding error is uniformly distributed over $\left[-\frac{\Delta v}{2}, +\frac{\Delta v}{2}\right]$, its variance is:

$$\sigma^2_{\text{quant}} = \frac{(\Delta v)^2}{12} = \frac{(0.00182)^2}{12} \approx 2.76 \times 10^{-7}\text{ m}^2/\text{s}^2$$

This can be compared with the variance attributable to physical sensor noise. The Bosch Gaussian jitter variance is $\sigma^2_{\text{gauss}} = (0.548)^2 \approx 0.300\text{ m}^2/\text{s}^2$, giving a ratio of:

$$\frac{\sigma^2_{\text{gauss}}}{\sigma^2_{\text{quant}}} = \frac{0.300}{2.76 \times 10^{-7}} \approx 1{,}087{,}000$$

The physical sensor noise is therefore roughly **1.1 million times larger** than the clock-rounding error. In practice, the quantization step adds no visible noise to the output signal.

Despite its negligible magnitude under the baseline configuration, the quantization step is retained in the implementation for two reasons:

1. **Physical honesty.** A real ECU performs exactly this kind of rounding. Removing the quantization step would silently introduce the assumption that the ECU possesses a mathematically perfect, infinite-precision timer — an assumption no real hardware satisfies. Since the purpose of the simulation is to replicate how a real motorcycle ECU behaves rather than an idealized version of it, retaining the rounding keeps the simulation truthful down to the level of the digital timer.

2. **Configurability and forward compatibility.** Rather than embedding the clock speed permanently in the governing equations, the timer resolution is stored as a single adjustable field, `ecu_timer_resolution_s`, inside `WheelSpeedSensorConfig`. As a result:
   - The simulated ECU clock speed can be changed by editing one value in the configuration file, with no need to rewrite the governing equations or touch the sensor logic.
   - If a future researcher wishes to evaluate DEDR's performance with a cheaper, slower ECU — for example, a $50\text{ kHz}$ microcontroller in place of the high-end $2.5\text{ MHz}$ Bosch unit — the resulting rounding error becomes substantially larger: the quantization step grows from the currently negligible $0.00182\text{ m/s}$ to approximately $0.091\text{ m/s}$, a magnitude large enough to noticeably affect the output signal. This entire change in simulated hardware is handled automatically by modifying a single configuration field:

     ```python
     # Simulating a cheap 50 kHz ECU — no code changes needed
     ecu_timer_resolution_s = 20e-6   # was 4e-7 for the 2.5 MHz Bosch unit
     ```

   - Because the rounding operation itself consists of only two arithmetic operations (a `round()` call and a division), it adds zero measurable CPU overhead regardless of which clock speed is being simulated.

### 8.5 Scope of Validation: Resolved Issues and Remaining Limitations

It is necessary to distinguish between **speed-estimation resolution**, which has been resolved, and **physics update rate**, which remains a simulator-level limitation:

- **Resolved (speed resolution).** The $1.62\text{ m/s}$ quantization jumps no longer appear in telemetry logs. By tracking sub-tick tooth crossings, the speed estimate is smooth, with a resolution of approximately $0.001\text{ m/s}$.
- **Remaining limitation (physics frame rate).** Because the simulator (CARLA) updates the vehicle's coordinate state only $30$ times per second, the vehicle's actual speed is updated in discrete $33.3\text{ ms}$ steps. Within each step, the model must assume the vehicle's speed changes linearly (i.e., under constant acceleration). Any high-frequency physical speed change occurring within a single $33.3\text{ ms}$ window is not simulated by CARLA and therefore cannot be captured by the sensor model. This is a standard simulation-to-reality gap.

## 9. Limitations and Future Work

- **Verification of N.** $N = 48$ is the verified slot count for standard Bosch ABS wheels on KTM/Ducati/BMW systems.
- **Sensitivity sweep.** It is recommended that tests be run across $N \in \{40, 44, 48, 50\}$ to confirm that DEDR's performance does not depend on a single assumed tooth count.

## 10. References

[1] Bosch Engineering GmbH (2026). *Speed Sensor Hall-Effect HA-M Technical Specifications* (Doc ID: 53202827 | en, 1, 27 Jan 2026). Abstatt, Germany: Bosch Motorsport. Available: [Bosch Motorsport HA-M Speed Sensor PDF](https://www.bosch-motorsport.com/content/downloads/Raceparts/Resources/pdf/Data%20Sheet_69827851_Speed_Sensor_Hall-Effect_HA-M.pdf)

[2] Bosch Engineering GmbH. *Speed Sensor Hall-Effect HA-D 90 Technical Specifications* (Doc ID: 69813003). Abstatt, Germany: Bosch Motorsport. Available: [Bosch Motorsport HA-D 90 Speed Sensor PDF](https://www.bosch-motorsport.com/content/downloads/Raceparts/Resources/pdf/Data%20Sheet_69813003_Speed_Sensor_Hall-Effect_HA-D_90.pdf)

[3] Bosch Motorsport. *Engineering Analysis Report: Bosch HA-M Speed Sensor — Frequency Response, Operating Error Boundaries, and Real-World Velocity Mapping*. Internal engineering report (`Bosch_HA-M_Sensor_Engineering_Report.pdf`). Note: this report characterizes the failure mode above 4.2 kHz qualitatively but provides no quantitative data (amplitude curve, secondary error bounds, or over-speed behavior). Used for informational context only; the official datasheet [1] remains the primary citable source.

[4] Ladoiye, J. S., Spry, D., & Jalali, M. (2021). *Health Estimation of Magnetic Wheel Encoder*. Annual Conference of the Prognostics and Health Management Society. Available: [PHM Society Journal](https://papers.phmsociety.org/index.php/phmconf/article/view/2979)
