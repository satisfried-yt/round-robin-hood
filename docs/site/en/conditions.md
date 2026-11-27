# Sensor conditions – thresholds and hysteresis

Conditions can be enabled per **profile** or per **consumer**. They block allocations when a numeric reading is missing or outside the selected threshold. A blocked profile prevents all member starts even if enough PV power is available.

| Field | Meaning |
|---|---|
| **Sensor entity** | Existing numeric HA `sensor.*` (e.g. a room thermometer); `unknown`/`unavailable` are invalid. |
| **Comparison** | `>`, `>=`, `<`, `<=`. |
| **Threshold** | Numeric bound in the sensor's own unit. |
| **Hysteresis** | Return offset to avoid rapid state flapping. |
| **ALL** | Every predicate must pass. |
| **ANY** | One predicate is sufficient. |
| **Enabled** | If disabled, this condition group does not filter allocation. |

**Example:** allow a room heater only if `sensor.room_temperature < 21`, with hysteresis `1` °C. A failed/missing sensor must not be treated as permission to start. This software rule is **not an independent over-temperature cutout**.

Dashboard and cards show `passed/total`, invalid sensors and threshold details. Changing sensor/operator/threshold clears stale hysteresis latches. Read [Safety](safety.md).


## Combining sensor and time conditions (0.9.5)

Numeric sensor rules and weekly schedules can be enabled separately. Sensor rules keep their ALL/ANY setting; the weekly schedule is always an additional AND requirement.

A consumer can start only when its profile is enabled, its profile schedule permits operation, its own schedule permits operation, and all applicable numeric sensor conditions allow it.

An invalid sensor still blocks the affected start. When a time window ends, RRH switches off its managed loads without waiting for minimum runtime. Software conditions do not replace independent safety devices.

Choose numeric entities using the Home Assistant searchable entity picker. Configure weekly windows in the separate profile and consumer editors.
