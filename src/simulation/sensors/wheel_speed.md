# Wheel-Speed Sensor Simulation — Design Justification

## Why This Document Exists

DEDR (our infrastructure-rejection algorithm) depends on knowing the motorcycle's own
forward velocity, `v_ego`. CARLA can hand us a perfect velocity vector for free
(`actor.get_velocity()`), but using that directly would be scientifically dishonest —
no real motorcycle ECU has access to perfect, noise-free speed. This document explains
**what real wheel-speed sensors actually look like**, and how that maps onto the
simulated sensor model used in this project, so the design choice is defensible rather
than assumed.

---

## 1. How a Real Wheel-Speed Sensor Works

A Hall-effect wheel-speed sensor does not measure speed directly. It sits next to a
toothed ring (the "tone ring" or "encoder ring") mounted on the wheel hub. As each
tooth passes, it disturbs the local magnetic field; the sensor's internal Hall element
detects that disturbance and an integrated signal-conditioning circuit turns it into a
clean digital pulse. The sensor itself never calculates anything — it is a pulse
generator. The ECU (or, in our case, the simulation pipeline standing in for one) is
what counts pulses over time and converts that into a speed value.

The standard relationship, consistent across automotive literature and independently
confirmed by a peer-reviewed wheel-speed-sensor retrofit study on a two-wheeled vehicle
(a 50cc scooter), is:

```
v = (f × C) / N
```

where `f` is pulse frequency (Hz), `C` is wheel circumference (m), and `N` is the
number of teeth on the encoder ring. This is the same formula our simulation uses, and
it is not an invented shortcut — it is how the underlying hardware works.

### Why This Formula Is Solid Regardless of the Tooth-Count Debate

It's worth being explicit about something that's easy to lose track of after a long
back-and-forth about tooth counts: **the formula itself is not in question.** It is a
direct consequence of basic kinematics — count pulses per revolution, measure pulse
frequency, multiply by how far one revolution travels — and it is confirmed
independently in both automotive industry sources and a peer-reviewed paper (Section 2).
`N` is an *input parameter* to a sound formula, not a weak link in the formula's logic.
Uncertainty about which value of `N` matches a specific motorcycle is a **calibration
question**, not a **validity question** — the relationship between teeth, frequency,
circumference, and speed holds no matter what the real tooth count turns out to be.

**Worked example**, using the project's primary assumption (`N = 37`, Section 2) and a
representative front-wheel circumference for a sportbike-class motorcycle
(`C ≈ 1.98 m`, e.g. a 120/70-17 front tire):

```
Given:
    N = 37 teeth
    C = 1.98 m
    f = 370 Hz   (measured/simulated pulse frequency)

Step 1 — Revolutions per second:
    rev/s = f / N = 370 / 37 = 10 rev/s

Step 2 — Linear speed:
    v = rev/s × C = 10 × 1.98 = 19.8 m/s

    19.8 m/s × 3.6 = 71.3 km/h
```

This is the exact calculation the simulated sensor performs every frame: convert a
pulse frequency into a speed using the wheel's known geometry. **If a different tooth
count is later confirmed or adopted (36, 38, 40 — see Section 5's sensitivity sweep),
only `N` in this calculation changes.** The method, the formula, and its physical
justification stay exactly the same.

---

## 2. What Real Sensors Actually Achieve (Cited, Not Assumed)

Rather than picking an accuracy figure out of thin air, the following numbers come from
published sources:

| Source | Sensor / Context | What It Actually Tells Us |
|---|---|---|
| Bosch Motorsport HA-D 90 / HA-M datasheets | **Automotive** Hall-effect speed sensors (car/motorsport crank & wheel applications) | Accuracy/repeatability of the pulse falling edge: **< 1.0–1.5% (HA-D 90)**, **< 4% (HA-M)**, both frequency-dependent. Cited only for the general *accuracy behavior of this sensor category* (Hall-effect, toothed-encoder speed sensing) — not for tooth count or any motorcycle-specific geometry. |
| Aftermarket "custom ABS tone ring" listing (eBay, seller *yanleb*), fitting Yamaha FZ-10 / MT-09 / MT-10 / YZF-R1 / YZF-R6, interchange part number `1SD-2517G-00-00` | **Motorcycle**, physical reproduction part | Photographed physical rings show **37 teeth** and **38 teeth** (two separate rings, likely front/rear or model-year variants). |
| Independent corroborating listing (Ten Kate Racing Products, a Yamaha WorldSSP racing parts supplier), part number `1SD2517G0000` | **Motorcycle**, "ABS sensor rotor YZF-R1 15> & front wheel YZF-R6 17>" | Same interchange part number as above, confirming **fitment** to R1 (2015+) and R6 (2017+) front wheel from a second, independent seller. |

What this evidence does and does not establish:

1. **Fitment is well corroborated.** Two independent sellers reference the same OEM
   interchange part number for the same bikes (R1 2015+, R6 2017+ front wheel). This is
   the strongest fitment evidence available — it is not a single unverified listing.
2. **Tooth count is the sellers' claim about a physical object, not a Yamaha factory
   specification.** Neither source is a Yamaha datasheet or service manual; both are
   aftermarket reproductions of the OEM ring. Yamaha does not publish tooth count for
   any tone ring, so "37/38 teeth" should be understood as **the best available public
   evidence**, not a confirmed OEM number. The selling seller (eBay) also has a
   feedback history dominated by unrelated electronics parts (TV power boards), which
   is a mild provenance concern worth disclosing rather than hiding.
3. **The Bosch automotive accuracy figures remain useful for the noise-magnitude
   discussion** (Section 3 below), but, as before, must never be used to justify a
   tooth count — that was the original mistake in an earlier draft of this document,
   corrected here.

---

## 3. What This Means for Our Noise Model

Given the above, a single flat Gaussian noise term is not the full picture of how a
real sensor errs. The error budget for a real Hall-effect wheel-speed sensor has at
least three distinct components:

| Error Source | Real-World Cause | How We Model It |
|---|---|---|
| Random measurement noise | Electrical/thermal noise in the sensor circuit | Gaussian noise, scaled by frequency band per the Bosch datasheet bands above (tighter at low speed, looser at high speed) |
| Quantization | The encoder is discrete — speed is only resolvable between tooth edges | Speed value snapped to the nearest step implied by `N = 37` teeth (primary assumption, see Section 2) and the wheel's circumference |
| Slip / lockup events | Hard acceleration or braking can decouple wheel speed from true ground speed | A scripted fault-injection event in selected test scenarios (e.g. during deceleration), not modeled as continuous background noise |

This is the honest answer to your question:

### Are we adding Gaussian noise?

**Yes — but not as the whole model, and not as a single fixed value.** Gaussian noise
is the correct way to represent the *random* component of sensor error, and it is now
backed by a real source (the Bosch accuracy-vs-frequency figures above) instead of an
assumed constant. But Gaussian noise alone does not represent quantization or
slip/lockup behavior, both of which are real, documented failure modes of this exact
sensor type. The simulation should therefore apply Gaussian noise *and* quantization as
standing, continuous effects, with slip/lockup modeled separately as a deliberate,
scripted test event — not folded into the everyday noise term, since slip is a
transient fault, not background randomness.

### Do we actually know how Bosch sensors behave?

Yes, to the extent that matters for this project — but it's worth being precise about
what "knowing" means here. We do not have a Yamaha factory specification for the exact
tone ring fitted to the R1/R6/MT-09 (that information is not published by the
manufacturer). What we do have is:

- Bosch's own published accuracy specifications for their Hall-effect speed sensor
  product line, which describe how *this category* of sensor behaves and errs.
- Two independently corroborating aftermarket part listings (Section 2) that confirm
  both fitment to our target bikes and a physical, countable tooth number on the
  reproduction part.

That is a legitimate, citable basis for the *shape* and *order of magnitude* of our
noise model, and a reasonable best-available basis for tooth count. It is not a basis
for claiming we've reproduced "Yamaha's exact factory sensor," and the thesis should
not imply otherwise.

---

## 4. Summary Statement (For the Thesis Methodology Section)

> "The simulated wheel-speed sensor models `v_ego` as `v = (f × C) / N`, the standard
> relationship by which real Hall-effect wheel-speed sensors operate. Noise parameters
> are derived from published Bosch Hall-effect speed sensor datasheets, which report
> accuracy as a function of pulse frequency rather than a single fixed value. The
> encoder tooth count (`N = 37`) is adopted from a physical aftermarket ABS tone ring
> reproduction part documented as fitting the Yamaha YZF-R1 (2015+) and YZF-R6 (2017+)
> front wheel, corroborated by an independent secondary listing referencing the same
> OEM interchange part number; manufacturer-published tooth counts for these tone
> rings could not be located, so this value is adopted as the best available public
> evidence rather than a confirmed factory specification. The model includes both
> continuous error sources (Gaussian noise scaled by frequency band, and quantization
> from the discrete encoder) and a separately scripted slip/lockup fault-injection
> event used in dedicated test scenarios, since slip is a transient failure mode
> rather than background noise. Given the uncertainty around the exact tooth count, a
> sensitivity sweep across plausible values (36–40 teeth) is also reported to confirm
> that DEDR's performance is not narrowly dependent on this single assumed value."

---

## 5. Open Items Still Worth Resolving

- The Bosch figures above are for **automotive (Bosch Motorsport) Hall-effect sensors**,
  not a motorcycle-specific Bosch product. They are cited only for general sensor-category
  accuracy behavior, never for tooth count or motorcycle-specific geometry. A
  motorcycle-specific Bosch datasheet, if one can be located, would be a stronger citation
  and should replace this if found.
- `N = 37` is justified by a physical aftermarket part listing (Section 2), corroborated
  by an independent secondary listing referencing the same OEM interchange part number.
  This is the strongest evidence currently available for these specific bikes, but it is
  still **not a Yamaha factory specification** — both sources are third-party
  reproductions, not manufacturer datasheets. This should remain explicitly labeled as a
  best-available-evidence assumption in the thesis, not a confirmed fact.
- A companion ring in the same listing showed 38 teeth, suggesting front/rear or
  model-year variation. The thesis should state explicitly which wheel (front) and which
  model years the `N = 37` assumption is intended to represent.
- **Recommended mitigation**: rather than committing to a single tooth count, run the
  DEDR sensitivity sweep across `N ∈ {36, 37, 38, 40}` and report whether false-positive
  rate is stable across this range. This converts an unverifiable single-number
  assumption into a tested robustness claim, which is more defensible than picking one
  value and hoping it is correct.
- To be unambiguous about scope: none of the above casts doubt on the underlying
  `v = (f × C) / N` formula (Section 1), which is independently established physics.
  This is solely a calibration question — which value of `N` correctly describes these
  specific motorcycles — and is treated here as exactly that, not as a flaw in the
  sensor model's design.
  