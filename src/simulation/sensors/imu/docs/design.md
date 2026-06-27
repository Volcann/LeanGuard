# IMU Sensor Simulation — Design Justification

## Why This Document Exists

Our motorcycle validation filters and EKF (Extended Kalman Filter) need realistic inertial readings (accelerometer and gyroscope data). While the CARLA simulator can provide perfect, noise-free ground-truth physics values, real sensor hardware is limited by physical constraints, finite resolution, low-pass filters, and quantization.

This document details the design of the simulated Inertial Measurement Unit (IMU) based on the **Bosch Motorsport MM5.10 Acceleration Sensor**, ensuring our simulation results are physically representative and academically defensible.

---

## 1. The Bosch Motorsport MM5.10 as a Public Proxy

Production street-bike IMUs are proprietary and their detailed performance specifications are usually kept confidential by manufacturers. To make our simulation academically reproducible, we use the public technical specifications of the Bosch Motorsport MM5.10 sensor as a mathematically sound proxy.

Key characteristics used to model the sensor:
* **2-axis rotation rate** (Yaw rate and Roll rate up to $\pm 160^{\circ}/\text{s}$)
* **3-axis accelerometer** (X, Y, and Z acceleration up to $\pm 4.2\text{ g}$)
* **Selectable Low-Pass Filter** (Defaulting to $30\text{ Hz}$ cutoff, with options for $15\text{ Hz}$ and $60\text{ Hz}$)
* **CAN message format and quantization** (LSB Intel, 16-bit unsigned with a $0\text{x8000}$ offset)

---

## 2. Risk 1 Caveat: Ground-Truth Roll Angle

A critical bug/limitation in naive simulation IMUs is the direct usage of the vehicle's ground-truth roll/lean angle.

> [!WARNING]
> In the real world, a standard IMU cannot sense the motorcycle's lean angle directly. This is because gravity and centrifugal force cancel out in the lateral axis during a coordinated turn, meaning the lateral accelerometer reads approximately $0\text{ g}$ rather than showing the lean angle.
>
> Using `self._parent_actor.get_transform().rotation.roll` inside decision-making code (like the EKF or DEDR) is a "cheat" that must be strictly avoided. We keep the field `roll_deg_ground_truth` in `ImuReading` exclusively for offline validation and error analysis, never feeding it into any decision-making logic.

---

## 3. Low-Pass Filter Discrete Implementation

The Bosch MM5.10 datasheet offers three selectable $-3\text{ dB}$ cutoff frequencies: $15\text{ Hz}$, $30\text{ Hz}$, or $60\text{ Hz}$.
We implement this via a discrete-time first-order Infinite Impulse Response (IIR) filter.

The continuous-time time constant $\tau$ (RC) for a given cutoff frequency $f_c$ is:
$$\tau = \frac{1}{2 \pi f_c}$$

Using the Euler backward method, the smoothing factor $\alpha$ for sample interval $dt$ is:
$$\alpha = \frac{dt}{\tau + dt}$$

The filter update equation is:
$$x_{\text{filtered}}[k] = x_{\text{filtered}}[k-1] + \alpha \cdot (x_{\text{raw}}[k] - x_{\text{filtered}}[k-1])$$

We choose a default cutoff frequency of $30\text{ Hz}$ as a balance between noise attenuation and phase delay.

---

## 4. 5-Stage Signal Corruption Pipeline

To transform the perfect CARLA physics values into realistic sensor outputs, we apply a 5-stage pipeline for each coordinate axis:

### § 4.1. Unit Conversion
CARLA outputs angular velocity in $\text{rad/s}$ and acceleration in $\text{m/s}^2$. The Bosch MM5.10 operates in degrees per second ($^{\circ}/\text{s}$) and standard gravity ($\text{g}$):
* $\omega_{\text{dps}} = \omega_{\text{rad/s}} \times \frac{180}{\pi}$
* $a_{\text{g}} = \frac{a_{\text{m/s}^2}}{9.81}$

### § 4.2. Noise Model
The MM5.10 datasheet does not publish a specific RMS noise-density or jitter figure. Therefore, the parameters `gyro_noise_std_dps` and `accel_noise_std_g` are left empty by default.
* If a verified noise value is supplied, zero-mean Gaussian white noise is added at this stage.
* If left as `None`, only quantization and bandwidth limitations are modeled, preventing the use of unverified parameters.

### § 4.3. Low-Pass Filter
The discrete first-order IIR filter described in § 3 is applied to attenuate high-frequency noise and simulate the hardware analog/digital filter chain.

### § 4.4. Over-Range Fault Flagging
If the physical value exceeds the datasheet's over-range limit ($\pm 1000^{\circ}/\text{s}$ for gyroscope or $\pm 10\text{ g}$ for accelerometer), the signal clamps to the limit and can be configured to flag a fault status.

### § 4.5. Quantization
To match the CAN output of the physical sensor, we round the values to the datasheet's quantization step sizes:
* **Gyroscope (Roll/Yaw rate):** $0.005^{\circ}/\text{s}$ per digit.
* **Accelerometer (X, Y, Z):** $0.0001274\text{ g}$ per digit.

---

## 5. References

* **[1]** Bosch Engineering GmbH (2015). *Acceleration Sensor MM5.10 Datasheet* (Doc. 9818827275 | en, V2, 05 Nov 2015). Abstatt, Germany: Bosch Motorsport. Available: [Bosch Motorsport MM5.10 Acceleration Sensor Datasheet](https://www.bosch-motorsport.com/content/downloads/Raceparts/Resources/pdf/Acceleration_Sensor_MM5.10_Datasheet_51_en_9818827275pdf.pdf)
