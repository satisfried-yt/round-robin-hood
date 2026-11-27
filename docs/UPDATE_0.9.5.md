# Round Robin Hood 0.9.4 → 0.9.5

## Scope and compatibility

Version 0.9.5 includes searchable Home Assistant entity pickers and optional weekly schedules on profiles and consumers. Existing settings and data (consumers, profile order, sensors, statistics, energy/cost history, restart policy) are retained. Both new schedule types are **disabled by default** on older configurations. Storage key `round_robin_hood.rebuild_2026.state` and storage/API schema versions remain unchanged.

**Important:** This update controls real devices. The installation procedure does not certify electrical safety. Time windows are software permissions, not physical safeguards.

## Before updating

1. Use RRH **All OFF** and physically verify **every** controlled actuator is off. Pause is not sufficient.
2. Make and verify a **full Home Assistant backup including `/config/.storage`**, ideally also stored outside the HA system. Ensure the restore procedure is known.
3. Confirm the currently installed `/config/custom_components/round_robin_hood/manifest.json` reports **0.9.4**. Do not run a 0.9.4-specific upgrade procedure on 0.9.3 or an arbitrary DEV build.
4. If RRH is set to automatic startup (`Always ON` or `Restore last`), choose **Always OFF** before stopping HA or updating if you do not want any consumer started after reboot.
5. Keep a copy of both the old code and the corresponding old `.storage` file; they must be restored **together** if you roll back. Stop Home Assistant Core before restoring a storage file.

## Preferred update through Marketplace / HACS

1. Add or locate `https://github.com/satisfried-yt/round-robin-hood` in HACS / Marketplace (custom repository if the public catalog listing is not yet approved).
2. Select the published stable **0.9.5** release, not the `develop` branch.
3. Apply the HACS update, restart Home Assistant Core and perform the acceptance checks below. Keep the pre-update backup.

## Manual update from the official release ZIP

Download `round-robin-hood-0.9.5.zip` and `round-robin-hood-0.9.5.sha256` from the official [GitHub release](https://github.com/satisfried-yt/round-robin-hood/releases/tag/v0.9.5). Copy both into `/config` and verify the SHA-256 checksum (the separate checksum is a corruption check, **not an independent authenticity guarantee**).

The following POSIX shell commands are intended for the Home Assistant terminal. They have deliberately strict preconditions and must **not** be re-run blindly after a partial failure.

```sh
(
set -eu
cd /config
sha256sum -c round-robin-hood-0.9.5.sha256

test -f /config/.storage/round_robin_hood.rebuild_2026.state
test -f /config/custom_components/round_robin_hood/manifest.json
grep -q '"version": "0.9.4"' /config/custom_components/round_robin_hood/manifest.json
test ! -e /config/rrh_backup_code_0.9.4
test ! -e /config/rrh_backup_storage_0.9.4.json
test ! -e /config/rrh_stage_0.9.5

unzip -tq round-robin-hood-0.9.5.zip
mkdir -p /config/rrh_stage_0.9.5
unzip -q round-robin-hood-0.9.5.zip 'custom_components/round_robin_hood/*' -d /config/rrh_stage_0.9.5
test -f /config/rrh_stage_0.9.5/custom_components/round_robin_hood/frontend/guides/de/index.html
test -f /config/rrh_stage_0.9.5/custom_components/round_robin_hood/frontend/guides/it/index.html
grep -q '"version": "0.9.5"' /config/rrh_stage_0.9.5/custom_components/round_robin_hood/manifest.json

cp -p /config/.storage/round_robin_hood.rebuild_2026.state /config/rrh_backup_storage_0.9.4.json
mv /config/custom_components/round_robin_hood /config/rrh_backup_code_0.9.4
mv /config/rrh_stage_0.9.5/custom_components/round_robin_hood /config/custom_components/round_robin_hood
)
```

**Stop at any failure.** If the final move fails, move `/config/rrh_backup_code_0.9.4` back to `/config/custom_components/round_robin_hood` before restarting; do not delete the backup. Do not copy the ZIP's entire repository into `custom_components`.

Restart **Home Assistant Core** from the UI when the new code directory is present.

## Acceptance checks

- About panel and integration manifest show **0.9.5**.
- All prior consumers, profiles, energy/financial statistics, sensor assignments, and startup policy are unchanged.
- Native searchable HA entity pickers can find existing entities without losing stored assignments on desktop and mobile.
- Under **Consumers** and **Profiles**, optional time windows support multiple intervals, weekdays, midnight-crossing spans and the configured HA timezone.
- With safe virtual/test loads, verify blocked starts outside a window and confirmed OFF at its end, including when minimum runtime is configured.
- Confirm the six-language offline handbook, language switch and in-guide search work. Check HA logs for errors.
- Use **All OFF**, visually confirm device states, and only then deliberately resume automation with independent physical protections.

## Rollback to 0.9.4

**Home Assistant Core must be stopped before replacing `.storage`.** The safest recovery is to restore the entire pre-upgrade HA backup, especially if Core cannot be stopped cleanly.

With Core stopped and both backups intact, restore the previous integration folder and matching RRH storage document:

```sh
test -d /config/rrh_backup_code_0.9.4
test -f /config/rrh_backup_storage_0.9.4.json
test ! -e /config/rrh_failed_code_0.9.5

mv /config/custom_components/round_robin_hood /config/rrh_failed_code_0.9.5
mv /config/rrh_backup_code_0.9.4 /config/custom_components/round_robin_hood
cp -p /config/rrh_backup_storage_0.9.4.json /config/.storage/round_robin_hood.rebuild_2026.state
```

Restart HA Core, check devices and the stored version, and enable RRH only after a safety review. A rollback loses RRH changes made after the backup. If any step fails or the backup is incomplete, restore the verified full HA backup instead.
