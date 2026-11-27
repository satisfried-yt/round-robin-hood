# Round Robin Hood 0.9.5

**Release scope:** searchable Home Assistant entity selection and weekly time restrictions for profiles and consumers. This is the DEV-tested successor to the public 0.9.4 maintenance release. Existing 0.9.4 installation and configuration remain supported.

## What's new

### Searchable Home Assistant entity pickers

- Native searchable Home Assistant entity selection in the first-run wizard, settings, consumer control/stage selection, energy/statistics and numeric sensor conditions.
- Search by entity name/ID instead of scrolling long lists, with suitable domain/unit filtering and a usable fallback when Home Assistant's native picker has not registered.
- Existing entity assignments are retained when editing. Desktop and smartphone UX were accepted in a dedicated HA DEV environment.

### Independent weekly schedules

- Optional **per-profile** and **per-consumer** weekly time windows, disabled on existing settings unless explicitly enabled.
- Pick one or more weekdays for each window; add multiple windows per day, including overnight spans (the selected weekday is the START day). Start inclusive, end exclusive.
- Home Assistant's timezone applies, including daylight saving transitions.
- Eligibility is **profile enabled AND profile schedule AND consumer schedule AND applicable numeric sensor conditions**. Within each enabled schedule, any matching window permits its own schedule.
- Ending an active window stops **RRH-owned running loads**, including during strict minimum runtime; multiple managed loads within a blocked profile can use the confirmed group OFF path. External loads are not adopted.
- Block reasons and next available opening appear in the panel.

### Compatibility, safety and testing

- No destructive migration, config reset, new storage key or WebSocket API version; existing consumers, profiles and history remain intact.
- Automation remains subject to actual HA feedback. Time/sensor restrictions are software limits, **not electrical or thermal safety devices**.
- Includes Python schedule/DST/validation and preflight-race tests, frontend checks, six-language offline handbook checks, and HACS/Hassfest release gating.
- Tested in an isolated HA DEV installation before release. Production hardware is not covered by automated tests.

**Not included:** multi-target smartphone/speaker notifications, first-daily-start/error/low-capture notification events, and the future device-independent multistage setup wizard. These remain roadmap items rather than released features.

## Installation, update and rollback

Search for **Round Robin Hood** in Home Assistant Marketplace or HACS; until an official catalog entry is approved, add `https://github.com/satisfried-yt/round-robin-hood` as a custom integration repository.

For a manual upgrade from 0.9.4, use [Update and rollback: 0.9.4 → 0.9.5](UPDATE_0.9.5.md). Before any update use RRH **All OFF**, physically verify controlled loads and create a restorable HA backup including `.storage`. Restart Home Assistant Core after replacing the integration. Check the stored configuration and start policy before re-enabling real devices.

## Zusammenfassung (Deutsch)

- Durchsuchbare native Home-Assistant-Entitätsauswahl im Assistenten und in den wichtigen Konfigurationsfeldern, auch mobil.
- Neue optionale Wochenzeitpläne für Profile und Verbraucher: frei wählbare Wochentage, mehrere Zeitfenster, Zeiten über Mitternacht und HA-Zeitzone.
- Start nur bei erfüllten Profil-, Verbraucher-, Sensor- **und** Zeitbedingungen. RRH schaltet eigene laufende Verbraucher nach Ablauf der Freigabe auch bei Mindestlaufzeit aus.
- Bestehende Konfiguration bleibt erhalten, Zeitpläne sind zunächst deaktiviert. Neue Benachrichtigungen gehören **nicht** zu v0.9.5.

## Résumé (Français)

- Recherche native des entités Home Assistant dans les formulaires, y compris sur mobile.
- Plannings hebdomadaires facultatifs par profil et appareil, avec plusieurs plages, passage à minuit et fuseau horaire HA.
- Démarrage soumis aux conditions des capteurs et aux deux plannings. RRH arrête les appareils actifs qu'il gère en fin de plage.
- Configuration conservée ; plannings désactivés par défaut. Notifications non incluses.

## Resumen (Español)

- Búsqueda nativa de entidades Home Assistant en formularios, también en móviles.
- Horarios semanales opcionales para perfiles y consumidores, con varias franjas, medianoche y zona horaria HA.
- El inicio requiere cumplir las condiciones y ambos horarios; RRH apaga las cargas que controla al terminar la franja.
- Se conserva la configuración; horarios desactivados por defecto. Las notificaciones no están incluidas.

## Resumo (Português)

- Pesquisa nativa de entidades Home Assistant nos formulários, também em telemóveis.
- Horários semanais opcionais por perfil e consumidor, com vários períodos, meia-noite e fuso horário HA.
- Arranque sujeito às condições dos sensores e a ambos os horários; RRH desliga os dispositivos que gere quando o período termina.
- Configuração preservada; horários desativados por defeito. Notificações não incluídas.

## Riepilogo (Italiano)

- Ricerca nativa delle entità Home Assistant nei moduli, anche da smartphone.
- Programmazioni settimanali facoltative per profili e dispositivi, con più fasce, mezzanotte e fuso orario HA.
- Avvio solo con sensori ed entrambe le programmazioni validi; RRH spegne i dispositivi gestiti alla fine della fascia.
- Configurazione conservata; orari disattivati inizialmente. Notifiche non incluse.

## Verification

Public archive: `round-robin-hood-0.9.5.zip` plus `.sha256` (with internal `SHA256SUMS`). See [archive verification](../VERIFY_RELEASE.md). The GitHub release workflow runs the complete checks before publishing and refuses to overwrite an existing tag.
