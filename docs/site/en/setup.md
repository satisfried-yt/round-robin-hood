# First-run setup and safety dialog

## Before the wizard

On each fresh browser opening, RRH shows the safety notice until **“Understood, do not show again”** has been checked and saved. Clicking **“Understood · continue”** without checking only dismisses it for that view. Open it any time via **Settings → Show safety notice**. The preference belongs to the persistent real configuration, not the temporary demo. It does not constitute an electrical safety certification.

## Features and usage

After acknowledging the existing safety notice, choose **Start setup wizard**, **Try Demo mode** or **Skip setup**. Demo uses a separate, temporary sandbox with six virtual consumers and **never** sends real HA switch commands. Skipping leaves RRH **OFF** and stores no grid source, consumer or profile. You can configure RRH manually or rerun the wizard from Settings. Factory reset returns to the safety notice and the same choices. “Do not show again” affects only the safety notice.

## Seven steps

1. **Introduction:** Read the concept; setup will not start physical devices.
2. **Grid source:** Select a `sensor.*` reporting instantaneous grid power (W/kW) and choose whether export is **positive** or **negative**. Do not select a cumulative kWh sensor. Stale readings prevent switching.
3. **Consumers:** Add one or several existing `switch.*` entities, human-readable names and declared **W**. Every entity must be unique. Configure staged/variable devices later in the advanced [consumer editor](consumers.md).
4. **Strategy:** Choose one of [eight strategies](profiles.md) and read its explanation. Initial setup creates a default profile; reruns may alter the first profile's strategy.
5. **Energy & costs:** Enter currency, optional PV nameplate watts, import tariff and feed-in tariff **per kWh**. Existing dynamic sources stay configured when their respective inputs are left blank.
6. **Controls:** Set reserve watts, global deficit delay seconds, delay enable flag, and maximum sensor age.
7. **Summary:** Review and save. Adding a real HA switch requires a separate **explicit authorization** confirming independent safety protection.

RRH stays **paused** after saving; no new device is automatically turned on. Only start after safe-switch validation and a fresh correctly signed grid sensor.

## Restarting setup

Open **Settings → Restart setup wizard**. Existing configurations require confirmation and Cancel never changes data. Existing consumers, other profiles, fairness counters and statistics are preserved. Be aware that rerunning can change the first profile's chosen strategy.

## Locale and initial defaults

RRH first follows Home Assistant's language (`auto`; DE/EN for onboarding). Later select a manual UI language under [Settings](settings.md). Initial reserve is **100 W**, global delay **30 s**, maximum reading age **60 s**; adjust these to the actual installation.


## Selecting entities in 0.9.5

Setup now uses searchable Home Assistant entity selectors. Type part of the displayed name or entity ID and select the match; allowed domains depend on the field.

Search also works on phones. If the native picker has not registered, a compatible search/selection control remains available. You can add weekly windows later under Consumers and Profiles.

Automatic control still requires deliberate activation, valid measurements and safety checks. Sensor conditions, schedules and independent protections remain separate.
