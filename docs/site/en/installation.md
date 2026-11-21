# Installation, upgrades and rollback

## Fresh installation

1. Create a restorable full Home Assistant backup including `.storage`.
2. Copy `custom_components/round_robin_hood` from the package to `/config/custom_components/round_robin_hood`. Do not overwrite unrelated integrations.
3. Restart Home Assistant Core, add Round Robin Hood under **Settings > Devices & Services**, then open its sidebar panel.
4. Read the safety notice and choose the setup wizard, isolated demo or manual setup. Setup does not automatically activate loads.

## Upgrade an existing installation

1. Use **All OFF** and physically verify that every configured actuator is off. Pause is not an electrical disconnect.
2. Create a full Home Assistant backup including `.storage` and verify it can be restored.
3. Follow the version-guarded upgrade in `docs/UPDATE_0.9.3.md`. This command is intended for **v0.9.2** installations.
4. Restart HA Core and verify existing consumers, profiles, sensors, statistics, startup behavior and **All OFF**.

## Rollback and recovery

Restore the **code and matching RRH data together**. Never replace `.storage` while HA Core is running. RRH changes since the backup will be lost. Alternatively restore the verified full Home Assistant backup.

RRH factory reset removes RRH data, not Home Assistant devices or recorder history. Back up first.
