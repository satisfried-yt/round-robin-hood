# Round Robin Hood - Handbuch

**Version 0.9.5.** [English](en/) | [Sicherheit](safety.md) | [Erste Schritte](setup.md)

RRH verteilt gemessenen PV-Überschuss auf geeignete Verbraucher nach konfigurierbaren Leistungswerten, Profilen und Strategien. Die eigentliche Regelgröße ist die **Netzleistung** (W oder kW), nicht ein kWh-Energiezähler. Bereits laufende Verbraucher sind im gemessenen Netzfluss berücksichtigt.

**Sicherheit:** Die Software kann echte Geräte schalten, aber keinen elektrischen oder thermischen Schutz ersetzen. Fehler können hohe Kosten, Überhitzung und Sachschäden verursachen. Vor dem Betrieb bitte die [Sicherheitshinweise](safety.md) lesen.

## Kapitel

- [Installation und Update](installation.md) - Sicherung und Rückweg.
- [Einrichtung](setup.md) - Sicherheitshinweis, Assistent, Demo, Überspringen.
- [Dashboard](dashboard.md) - Leistungswerte, Schaltaktionen und Diagramme.
- [Verbraucher](consumers.md) - Schalter und regelbare Geräte.
- [Profile und Strategien](profiles.md) - acht Verteilverfahren und Reihenfolge.
- [Bedingungen](conditions.md) - Sensorgrenzen und Hysterese.
- [Energie und Kosten](energy.md) - Tarife, PV-Leistung, geschätzte Bilanz.
- [Einstellungen](settings.md) - Betrieb, Reserve, Startverhalten, Demo, Reset.
- [Sensoren](sensors.md) - Einheiten, Werte und Datenqualität.
- [Startverhalten](startup.md) - Wiederaufnahme nach HA-Neustart.
- [Fehlerdiagnose](troubleshooting.md) - Störungen und Lösungen.
- [Sicherheit](safety.md), [FAQ](faq.md), [Glossar](glossary.md), [Über](about.md).

RRH hat keine eigene Strommesshardware und verändert nicht die Konfiguration des Home Assistant Energy Dashboards. Nennleistungen und Geldbeträge sind Schätzwerte, keine geeichten Messungen.


## Neu in Version 0.9.5

- Suche nach Home-Assistant-Entitäten in den Einstellungen, im Assistenten sowie in Verbraucher-, Sensor- und Energieformularen, auch auf Mobilgeräten.
- Wöchentliche Freigaben für Profile und einzelne Verbraucher mit Wochentagen, mehreren Zeitfenstern und Regeln über Mitternacht.
- Sensorbedingungen und beide Zeitpläne müssen erfüllt sein; endet die Freigabe, schaltet RRH selbst eingeschaltete Geräte auch vor Ablauf der Mindestlaufzeit aus.
- Bisherige Konfigurationen bleiben erhalten; die neuen Zeitpläne sind standardmäßig deaktiviert. Vor Updates immer das vollständige HA-Backup einschließlich .storage erstellen.
