# Safety and liability information

**Round Robin Hood is a private hobby project**, initially built for its developer's personal use, with **AI assistance** in development and documentation. No damage-free operation or guaranteed savings are promised. It is **not a certified safety controller or physical emergency stop**. Mandatory statutory rights are not categorically waived by this notice.

## Main risks

- Bugs, incorrect measurements, integrations, network delays or device services can cause loads to **run unexpectedly, stay on, start at the wrong level or shut down late**.
- Heaters may **overheat or start fires** if installed near combustible material or operated without independent protection. Mains equipment also poses electric-shock risk. HA feedback does not prove actual physical safety.
- Poor threshold selection, strict runtime settings, or inaccurate ratings can cause **unplanned grid imports, electricity bills and lost feed-in compensation**.
- An HA/RRH/network/power failure can prevent a software OFF command from reaching the actual device. Software never replaces **independent thermal cutouts, thermostats, breakers, residual-current protection, compliant installation or supervision**.

## Required precautions

1. Use appropriately rated and protected equipment, with competent electrical installation.
2. Position heating appliances securely, away from flammables, in accordance with manufacturer instructions; never rely on software alone for unattended operation.
3. Verify true power draw and actual OFF responses in a safe test setup. A `number` value of `0` must actually switch off; test every staged-level and OFF route.
4. Check grid-meter sign, update timestamps and missing-sensor behavior. Use conservative reserve and delays.
5. Before updates use **All OFF**, inspect real actuators and back up HA. Test updates in demo/isolated demo first.
6. **All OFF** is a software command only. Maintain an independent physical disconnect for emergencies.

## Notice recurrence

The notice reappears on opening until **“Understood, do not show again”** is deliberately checked and stored. The checkbox is **not authorization** for unattended devices. The dialog can be reopened under Settings at any time.

