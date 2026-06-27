# `ImuSensorConfig` — Field Reference

`ImuSensorConfig` controls all tunable parameters of the simulated Bosch Motorsport MM5.10-class Inertial Measurement Unit (IMU). If you change these parameters, make sure to update `design.md` to keep the documentation consistent.

---

## § Gyroscope

### `gyro_measuring_range_dps` · `float` · default `160.0`
The nominal measuring range in degrees per second ($^{\circ}/\text{s}$) for the yaw/roll rates.
* **Datasheet Citation:** Page 2, "Characteristic Application I", measuring range is listed as $\pm 160^{\circ}/\text{s}$. (Note: The front-page summary states $\pm 163^{\circ}/\text{s}$; we use the characteristic table value as the authoritative specification).

### `gyro_over_range_limit_dps` · `float` · default `1000.0`
The maximum physical limit in $^{\circ}/\text{s}$ beyond which the sensor output saturates or becomes undefined.
* **Datasheet Citation:** Page 2, "Characteristic Application I", over-range limit is listed as $\pm 1000^{\circ}/\text{s}$.

### `gyro_resolution_dps` · `float` · default `0.1`
The absolute physical resolution of the sensing element in $^{\circ}/\text{s}$.
* **Datasheet Citation:** Page 2, "Characteristic Application I", absolute physical resolution is listed as $0.1^{\circ}/\text{s}$.

### `gyro_quantization_dps_per_digit` · `float` · default `0.005`
The step size in $^{\circ}/\text{s}$ per digit for the digitized CAN message output.
* **Datasheet Citation:** Page 1, "CAN Parameters", Quantization Yaw/Roll Rate is listed as $0.005\text{ [}^{\circ}/\text{s/digit]}$.

### `gyro_noise_std_dps` · `Optional[float]` · default `None`
Standard deviation of Gaussian noise added to the gyroscope reading.
* **Note:** Left as `None` (unset) because the MM5.10 datasheet does not specify a noise-density or RMS noise floor. Do not arbitrarily populate this parameter without a citable specification.

---

## § Accelerometer

### `accel_measuring_range_g` · `float` · default `4.2`
The nominal measuring range in standard gravity units ($\text{g}$) for the X, Y, and Z axes.
* **Datasheet Citation:** Page 2, "Characteristic Application II", measuring range is listed as $\pm 4.2\text{ g}$.

### `accel_over_range_limit_g` · `float` · default `10.0`
The physical limit in $\text{g}$ beyond which the accelerometer saturates or becomes undefined.
* **Datasheet Citation:** Page 2, "Characteristic Application II", over-range limit is listed as $\pm 10\text{ g}$.

### `accel_resolution_g` · `float` · default `0.01`
The absolute physical resolution of the sensing element in $\text{g}$.
* **Datasheet Citation:** Page 2, "Characteristic Application II", absolute physical resolution is listed as $0.01\text{ g}$.

### `accel_quantization_g_per_digit` · `float` · default `0.0001274`
The step size in $\text{g}$ per digit for the digitized CAN message output.
* **Datasheet Citation:** Page 1, "CAN Parameters", Quantization Acc X/Y/Z-axis is listed as $0.0001274\text{ [g/digit]}$.

### `accel_noise_std_g` · `Optional[float]` · default `None`
Standard deviation of Gaussian noise added to the accelerometer reading.
* **Note:** Left as `None` (unset) because the MM5.10 datasheet does not specify a noise-density or RMS noise floor.

---

## § Low-Pass Filter

### `cutoff_frequency_hz` · `float` · default `30.0`
The $-3\text{ dB}$ cutoff frequency for the hardware low-pass filter.
* **Datasheet Citation:** Page 2, selectable options are $15\text{ Hz}$, $30\text{ Hz}$, or $60\text{ Hz}$.
* **Design Decision:** We default to $30\text{ Hz}$ to avoid excessive phase delay during fast transient leans while still attenuating simulator jitter.

### `enable_lowpass_filter` · `bool` · default `True`
Enables the first-order discrete IIR filter mimicking the sensor's bandwidth limit.

---

## § Pipeline Toggles

### `enable_quantization` · `bool` · default `True`
Toggles quantization of the final readings to the datasheet digit steps.

### `enable_range_fault_flagging` · `bool` · default `True`
Enables clamping the values to the over-range limits and flagging saturation.

---

## § Reproducibility

### `rng_seed` · `Optional[int]` · default `None`
The seed for the random number generator used for Gaussian noise (if noise parameters are set).
