# Round Robin Hood 0.9.3 -> 0.9.4

## Scope

This patch avoids blocking file I/O during Home Assistant startup, statistics sampling and statistics/factory resets by resolving the configured timezone once asynchronously. Allocation behavior, storage schema and WebSocket API remain unchanged. Existing consumers, profiles, energy/cost history and setup flags are preserved.

## Before replacing the integration

1. Use **All OFF** in RRH and physically verify that every controlled load is off. Pause is not sufficient.
2. Make and verify a full **Home Assistant backup including `/config/.storage`**. Save a copy outside the installation directory.
3. Use this command only when the installed integration manifest reports **0.9.3** and `/config/.storage/round_robin_hood.rebuild_2026.state` exists.
4. Keep the 0.9.3 code and corresponding RRH storage backup until the 0.9.4 installation and HA start have been accepted.
5. If automatic start is enabled, loads may be switched on after HA restart once RRH receives a new valid grid reading and verifies device states. Set the policy to Always OFF before upgrading if this is not wanted.

## Installation

Copy `round-robin-hood-0.9.4.zip` unchanged to `/config/custom_components/round-robin-hood-0.9.4.zip`. Then run this command in the Home Assistant terminal exactly once:

```sh
cd /config/custom_components && \
test -f round-robin-hood-0.9.4.zip && \
test -d round_robin_hood && \
test -f /config/.storage/round_robin_hood.rebuild_2026.state && \
grep -q '"version": "0.9.3"' round_robin_hood/manifest.json && \
test ! -e /config/rrh_code_backup_0.9.3 && \
test ! -e /config/rrh_storage_backup_0.9.3.json && \
test ! -e /config/rrh_stage_0.9.4 && \
unzip -tq round-robin-hood-0.9.4.zip && \
unzip -q round-robin-hood-0.9.4.zip 'custom_components/round_robin_hood/*' -d /config/rrh_stage_0.9.4 && \
test -f /config/rrh_stage_0.9.4/custom_components/round_robin_hood/brand/icon.png && \
test -f /config/rrh_stage_0.9.4/custom_components/round_robin_hood/frontend/guides/fr/index.html && \
test -f /config/rrh_stage_0.9.4/custom_components/round_robin_hood/translations/it.json && \
grep -q '"version": "0.9.4"' /config/rrh_stage_0.9.4/custom_components/round_robin_hood/manifest.json && \
cp -p /config/.storage/round_robin_hood.rebuild_2026.state /config/rrh_storage_backup_0.9.3.json && \
mv round_robin_hood /config/rrh_code_backup_0.9.3 && \
( mv /config/rrh_stage_0.9.4/custom_components/round_robin_hood round_robin_hood || \
  { mv /config/rrh_code_backup_0.9.3 round_robin_hood; false; } ) && \
cat round_robin_hood/manifest.json
```

If the command stops early, examine its output before taking another step; do not repeat it blindly. After successful installation restart **Home Assistant Core** through the user interface.

## Acceptance checks

- RRH loads and displays version **0.9.4**, without old development badges.
- Existing consumers, profiles, sensors, statistics and restart policy remain unchanged.
- Local calendar day accounting remains correct for the configured timezone, with no ZoneInfo blocking warnings.
- **Anleitung / How-to** offers all six languages and working in-article search; verify language switching.
- In a safe simulated environment, verify Pause, All OFF, startup policy and positive/negative grid readings.
- Confirm the dashboard and sensor/unit filter operate as previously; no real electrical load was exercised in the package test.

## Rollback to 0.9.3 (Home Assistant Core stopped)

**Stop HA Core before replacing its `.storage` file**. If that is not possible, restore your verified full HA backup instead. Rollback loses RRH data saved after the pre-upgrade backup.

```sh
cd /config/custom_components && \
test -d round_robin_hood && \
test -d /config/rrh_code_backup_0.9.3 && \
test -f /config/rrh_storage_backup_0.9.3.json && \
test ! -e /config/rrh_failed_code_0.9.4 && \
grep -q '"version": "0.9.3"' /config/rrh_code_backup_0.9.3/manifest.json && \
mv round_robin_hood /config/rrh_failed_code_0.9.4 && \
mv /config/rrh_code_backup_0.9.3 round_robin_hood && \
cp -p /config/rrh_storage_backup_0.9.3.json /config/.storage/round_robin_hood.rebuild_2026.state && \
cat round_robin_hood/manifest.json
```

After restoration start HA Core and verify every device state before enabling RRH again. Do not delete backup directories until the restored installation is confirmed.
