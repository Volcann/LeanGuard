# `WheelSpeedSensorConfig` — Field Reference

`WheelSpeedSensorConfig` controls every tunable aspect of the simulated Hall-effect
wheel-speed sensor. Defaults are chosen to match the best available physical evidence
for a Yamaha YZF-R1 / YZF-R6 class sportbike. Before changing any value, read the
relevant section below and update both this file and `wheel_speed.md` if the rationale
changes.

---

## § Encoder Geometry

### `num_teeth` · `int` · default `37`

Number of teeth on the ABS tone ring fitted to the modelled motorcycle's front wheel.

**Evidence basis:** Two independently corroborating aftermarket ABS tone ring listings
(eBay seller *yanleb*, and Ten Kate Racing Products — a Yamaha WorldSSP parts supplier)
both reference OEM interchange part number `1SD-2517G-00-00` / `1SD2517G0000` and
describe fitment to the Yamaha YZF-R1 (2015+) and YZF-R6 (2017+) front wheel. Physical
photographs in the first listing show a ring with 37 teeth (see listing evidence below).

![Custom Tone Rings (37 and 38 teeth)](../sensors/assets/custom_tone_rings_37_38_teeth.png)
![eBay Listing details](../sensors/assets/ebay_item_description.png)

**Confidence level:** Best-available public evidence, *not* a Yamaha factory
specification. Yamaha does not publish tone-ring tooth counts. The seller whose photos
show 37 teeth has a feedback history dominated by unrelated electronics parts, which is
a mild provenance concern. A companion ring in the same listing shows 38 teeth,
suggesting possible front/rear or model-year variation.

**Mitigation:** Do not commit to this single value alone. Run the sensitivity sweep
defined in `num_teeth_sweep_values` and report DEDR performance stability across the
range. This converts an unverifiable assumption into a tested robustness claim.

---

### `wheel_circumference_m` · `float` · default `1.98`

Front wheel outer circumference in metres. Used in both directions of the speed ↔
frequency conversion: `f = (v × N) / C` and `v = (f × C) / N`.

**Evidence basis:** Representative value for a 120/70-17 front tyre — the standard
fitment on most Yamaha R-series sportbikes — derived from published tyre geometry.
Rolling circumference varies slightly with inflation pressure and load; 1.98 m is
a commonly cited nominal value for this size.

**Sensitivity:** A 2% error in `C` produces an equivalent 2% error in the computed
speed. This is small relative to the Gaussian noise terms and is not expected to
materially affect DEDR's false-positive rate. No sweep is planned for this parameter.

---

### `num_teeth_sweep_values` · `tuple[int, ...]` · default `(36, 37, 38, 40)`

Tooth-count values to iterate over in the sensitivity sweep. See `wheel_speed.md`
§ 5 (Open Items) for the full rationale.

These values bracket the physically plausible range: 36 and 38 appear in the same
aftermarket listing as the primary assumption of 37; 40 represents a round-number upper
bound sometimes cited for sportbike front wheels. The sweep is run by substituting each
value for `num_teeth` while holding all other parameters fixed, then comparing DEDR's
false-positive rate across the four configurations.

---

## § Noise Model

### `low_freq_threshold_hz` · `float` · default `200.0`

Pulse-frequency boundary (Hz) below which the tighter noise band applies.

**Rationale:** Bosch Hall-effect speed sensor datasheets (HA-D 90, HA-M) report accuracy
as a function of pulse frequency, with tighter accuracy at lower frequencies. The Bosch
breakpoints are in the kHz range (automotive crank/cam applications), which are
rescaled here to the much lower frequencies produced by a motorcycle wheel at riding
speed (≈ 37 teeth × 10 rev/s = 370 Hz at ~70 km/h). 200 Hz corresponds to roughly
32 km/h — a representative low-speed threshold. This rescaling is an engineering
adaptation; the Bosch datasheets are cited only for the *shape* of the
frequency-dependent accuracy curve, not for the literal breakpoint values.

---

### `low_freq_noise_pct` · `float` · default `0.01`

Gaussian noise standard deviation expressed as a fraction of the true pulse frequency,
applied when `f_true ≤ low_freq_threshold_hz`.

**Source:** Derived from the Bosch HA-D 90 datasheet's `< 1.0%` accuracy figure for the
lower frequency band. Stated as a standard deviation (1σ), not a peak error bound, which
is consistent with modelling the noise as Gaussian. Values above 200 Hz use
`high_freq_noise_pct` instead.

---

### `high_freq_noise_pct` · `float` · default `0.04`

Gaussian noise standard deviation as a fraction of the true pulse frequency, applied
when `f_true > low_freq_threshold_hz`.

**Source:** Derived from the Bosch HA-M datasheet's `< 4%` accuracy figure for the
higher frequency band. The HA-M is a slightly lower-spec sensor than the HA-D 90;
using its figure for the high-frequency band produces a conservative (pessimistic)
noise model, which is the safer direction for a safety system evaluation.

---

## § Quantization

### `enable_quantization` · `bool` · default `True`

Master switch for the ECU inter-pulse timing quantization stage. Set to `False` only
in ablation experiments designed to isolate the quantization contribution to DEDR error.

When `True`, the sensor models speed resolution the way a real Bosch ABS ECU does:
rather than snapping speed to a grid defined by the CARLA tick interval, it computes
the ideal time between successive tooth edges at the noisy speed, quantizes *that
interval* to the nearest multiple of `ecu_timer_resolution_s`, then back-converts to
speed. This removes the 1.62 m/s artifact that results from using the 30 Hz tick period
directly and produces a resolution of ~0.001 m/s at cruise speed — consistent with
real hardware.

---

### `ecu_timer_resolution_s` · `float` · default `4e-7` (0.4 μs)

The timer tick period of the simulated ABS ECU, in seconds.

**Physical basis:** A 2.5 MHz free-running counter (period = 0.4 μs) is representative
of the Bosch ABS 5.x / ABS 8 ECU generation. The ECU latches this counter on each
tooth-edge interrupt and computes the inter-pulse interval as the difference between
consecutive latch values. This is the standard ABS wheel-speed measurement architecture
described in Bosch Automotive Handbook (9th ed.) and is independent of the vehicle CAN
bus rate or any simulation tick rate.

**Effect on speed resolution:** Speed resolution from timer quantization alone is:

```
Δv ≈ (C / N) × (ecu_timer_resolution_s / inter_pulse_time²)
   = v² × ecu_timer_resolution_s × N / C
```

At 13.7 m/s (N=37, C=1.98 m, inter_pulse ≈ 3.9 ms):

```
Δv ≈ (1.98/37) × (4e-7 / (3.9e-3)²)  ≈  0.0014 m/s
```

This is ~1,160× finer than the previous tick-rate model (1.62 m/s at 30 Hz), and is
consistent with the sub-0.1 m/s resolution reported in published ABS ECU evaluations.

**Honest limitation:** The improvement applies at steady speed. Between CARLA ticks the
vehicle speed is assumed constant; intra-tick acceleration events are invisible
regardless of `ecu_timer_resolution_s`. At 30 Hz this limits effective acceleration
observability to changes occurring over ≥ 33 ms — a real ECU has no such constraint
because it operates asynchronously from the vehicle CAN bus.

---

## § Fault Injection

### `enable_fault_injection` · `bool` · default `False`

Master switch for the scripted slip/lockup fault mechanism. Must be `True` *and*
`fault_injection_fn` must be non-`None` for any fault to take effect.

Slip/lockup is modelled as a separate, deterministic fault event rather than as part of
the continuous Gaussian noise because it is physically distinct: it is a transient
decoupling of wheel speed from ground speed caused by tyre saturation, not background
sensor noise. Folding it into the noise term would misrepresent its character and make
it impossible to clearly label fault vs. non-fault ticks in the test output.

---

### `fault_injection_fn` · `Optional[FaultInjectionFn]` · default `None`

Callable with signature `(true_speed_mps: float, elapsed_seconds: float) ->
Optional[float]`. When active (non-`None` and `enable_fault_injection=True`):

- Return a `float` to override the sensor's reported speed on this tick.
- Return `None` to leave the normal noise/quantisation pipeline output unchanged.

Use `make_slip_fault(start_time_s, duration_s, slip_factor)` from `wheel_speed.py` to
build a standard slip or lockup event. The `slip_factor` parameter encodes the fault
type: values `> 1.0` simulate rear-wheel spin under hard acceleration (wheel faster
than ground), values `< 1.0` simulate wheel lockup under hard braking (wheel slower
than ground).

---

## § Reproducibility

### `rng_seed` · `Optional[int]` · default `None`

Seed for the `random.Random` instance that generates Gaussian noise samples.

- `None` → nondeterministic; each run produces a different noise sequence.
- Any integer → fully reproducible; the same seed and the same CARLA episode will
  produce byte-identical noise across runs.

Set a fixed seed when running the 10-trials-per-scenario repeatability requirement
described in the test plan. Leave as `None` for exploratory or sensitivity-sweep runs
where stochastic variation is informative.
