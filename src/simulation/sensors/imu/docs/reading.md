# `ImuReading` — Field Reference

`ImuReading` is the data structure returned by the `ImuSensor` at the end of each simulation frame. This reference explains what each field represents, its units, and how it is used in the downstream LeanGuard pipeline.

---

## `accelerometer_g` · `tuple[float, float, float]`

**The measured linear acceleration vector along the vehicle's body axes.** Units: standard gravity ($\text{g}$).
* **Index 0 (X):** Longitudinal acceleration (positive forward).
* **Index 1 (Y):** Lateral acceleration (positive left).
* **Index 2 (Z):** Vertical acceleration (positive up).

**Processing:**
This vector is converted from CARLA's raw $\text{m/s}^2$ output, low-pass filtered, clamped to the over-range limit ($\pm 10\text{ g}$), and quantized to $0.0001274\text{ g}$ steps.

---

## `gyroscope_dps` · `tuple[float, float, float]`

**The measured angular velocity (rotation rates) around the vehicle's body axes.** Units: degrees per second ($^{\circ}/\text{s}$).
* **Index 0 (X):** Roll rate.
* **Index 1 (Y):** Pitch rate.
* **Index 2 (Z):** Yaw rate.

**Processing:**
This vector is converted from CARLA's raw radians per second ($\text{rad/s}$), low-pass filtered, clamped to the over-range limit ($\pm 1000^{\circ}/\text{s}$), and quantized to $0.005^{\circ}/\text{s}$ steps.

---

## `compass` · `float`

**The simulated compass reading representing heading.** Units: radians.
* **Range:** $[0, 2\pi]$ (yaw angle relative to North).

---

## `roll_deg_ground_truth` · `float`

**The perfect ground-truth roll (lean) angle directly from the physics engine.** Units: degrees.

> [!CAUTION]
> This field exists **exclusively for offline analysis, plotting, and error auditing**.
>
> Because a physical IMU cannot directly measure lean angle (due to gravity and centrifugal forces balancing out during coordinated turns), using this field in any safety-critical estimation or controller logic violates physical realism and represents a simulation cheat. It must **never** be passed to the EKF or DEDR pipelines.
