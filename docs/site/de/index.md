# Round Robin Hood - Handbuch

**Version 0.9.3.** [English](en/) | [Sicherheit](safety.md) | [Erste Schritte](setup.md)

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
