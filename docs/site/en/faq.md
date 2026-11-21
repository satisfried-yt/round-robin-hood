# FAQ and troubleshooting

**Why will no load start even though PV is generating?** RRH uses the *net grid-power sensor*, not overall PV generation. Check export sign, freshness, reserve, state, conditions, nominal watts, cooldown and active profile.

**Pause versus All OFF?** Pause suspends allocations and may leave loads on; All OFF requests OFF for RRH-managed loads. Independent physical disconnection is required for actual emergencies.

**Why is money shown as a dash?** Import/feed-in tariff unavailable or invalid. RRH does not retroactively invent prices for previously unpriced kWh.

**Why is the 24h chart empty or discontinuous?** Invalid readings, Pause, HA downtime/restart, stale values or less than 24 hours of collected history. The graph only shows observations RRH actually made.

**Why is currency switching rejected?** Existing priced money history is protected from silent re-labelling. See [Energy & costs](energy.md) for export, reset and correct local tariff entry.

**Why doesn't the setup wizard auto-run after an upgrade?** Existing configurations are preserved. Only a truly empty install shows the automatic wizard; rerun it manually from Settings.

**Can I type an icon name?** The free-text icon field was removed. Choose an icon from the clickable gallery instead; custom PNG/WebP images up to 48 KB are also supported.

**Can I pick any HA control?** No. Only supported `switch`, `select`, `climate` and `number` actions are whitelisted. New bindings require explicit authorization.

**Why is a device off although surplus is available?** Review profile assignment, conditions, reading freshness, strategy order, power margin, cooldown and fairness advantage. Cards explain common blocking reasons.

**Can I use existing HA Energy Dashboard sources?** Yes, select suitable existing sensor entities; RRH neither configures the Energy Dashboard nor imports historical energy data.

**Why are some words in German?** `auto` follows HA language. The KB is complete in DE/EN for this version; some legacy specialized UI messages may still fall back to DE/EN for FR/ES/PT/IT.

**How do I report a bug?** Note version, page/action, sanitized HA logs, safe test setup, expected and actual results. If an actuator behaves dangerously, physically isolate it before troubleshooting.
