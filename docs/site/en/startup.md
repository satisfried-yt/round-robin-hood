# Restart behavior

Choose **RRH → Settings → Behavior on Home Assistant restart**.

| Option | Behavior |
|---|---|
| **Always OFF** (default) | RRH does not resume its automatic controller after reboot. This is **not** a physical OFF command to devices that were already on. |
| **Always ON** | RRH attempts to start only after its safety checks have succeeded. |
| **Restore last state** | Previously running → attempt to start; paused → remain paused; OFF → remain stopped. |

## Features and usage

**Always ON** and **Restore last = ON** now work for **manually configured** installations even when the optional setup wizard was not completed. RRH stays paused while the automatic start is pending. It starts only after all configured HA actuators return a known `on`/`off` state and a **new valid grid-power report** arrives after HA restart. Late-appearing entities no longer cancel the startup intent permanently. Unresolved switching or a bad grid source still blocks automation. Device ON states are never blindly restored.

## Safety gate before any automatic dispatch

1. Valid grid source, configured consumers and an enabled profile (wizard completion is optional).
2. No pending or unresolved prior switching commands.
3. All configured actuator states observed as `on`/`off`; never blindly adopt an externally controlled load.
4. A **new** valid grid report must arrive after restart; a cached reading cannot dispatch a command.
5. Unavailable data keeps the controller paused with a diagnostic reason. Unresolved prior commands require manual action.

Restart policy does not blindly restore physical switch states. Pause stops RRH decisions but does not turn running appliances off. For heaters or unattended electrical loads, prefer **Always OFF** and use independent safety hardware. RRH is not a certified emergency stop.
