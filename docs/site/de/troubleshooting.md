# Fehlerdiagnose und Wiederherstellung

## RRH startet nach einem Neustart nicht

1. Prüfe **Einstellungen → Startverhalten**. „Immer AUS“ ist der sichere Standard.
2. Prüfe **Netzleistung** (W/kW, Vorzeichen, Meldungsalter und `restored`-Status).
3. Prüfe alle Verbraucherzustände (`on`/`off`). Nicht verfügbare Aktoren blockieren die automatische Wiederaufnahme.
4. Lies **Home Assistant → Einstellungen → System → Protokolle** und die RRH-Statusmeldung.
5. Vor einer erneuten Aktivierung ungeklärte Aktorzustände sicher prüfen; bei offenen „Alle AUS“-Fehlern dessen Rückmeldungen klären.

## Strompreis wird nicht angeboten

Der ausgewählte Sensor muss zum aktuellen Währungscode passen und einen gültigen Zahlenwert mit Einheiten wie `EUR/kWh` oder `ct/kWh` liefern. HA-Entitäten mit `°C`, `W`, `kWh` oder ohne passende Einheit sind keine Tarifsensoren. Siehe [Sensoren](sensors.md).

## Keine Verbraucher werden eingeschaltet

Prüfe Netz-Einspeisung, Reserve, aktive Profile, Sensorbedingungen, Mindestlaufzeiten, Wiedereinschaltsperren, Leistungsbedarf, externe Änderungen und bestätigte Aktorzustände. Mit **Pause** bleibt die Last physisch an; **Alle AUS** sendet Ausschaltbefehle, deren Erfolg bestätigt werden muss.

## Nach einem fehlgeschlagenen Update

Beende aktive Schaltvorgänge, erstelle bei Bedarf ein vollständiges HA-Backup und folge der zum ZIP gehörenden `docs/UPDATE_*.md`. **Nicht** mehrere fehlgeschlagene Installationsbefehle blind wiederholen. RRH-eigene Daten liegen separat unter `.storage/round_robin_hood.rebuild_2026.state`.


## Fehlersuche: Zeitsteuerung und Entitätssuche (0.9.5)

Keine Schaltung trotz PV-Überschuss: Status von Profil und Verbraucher öffnen. Beide Zeitpläne und die Sensorbedingungen müssen freigeben. Zusätzlich Netzmessung, Reserve, Mindestleistung und Wiedereinschaltsperre prüfen.

Falsche Uhrzeit oder unerwarteter Folgetag: Unter Home Assistant die konfigurierte Zeitzone kontrollieren. Bei Zeitfenstern über Mitternacht ist der ausgewählte Wochentag der Starttag. Bei Sommer-/Winterzeitumstellung können lokale Uhrzeiten übersprungen oder doppelt vorkommen.

Entität fehlt in der Suche: HA-Entität und passende Domäne/Einheit prüfen. Bereits gespeicherte oder momentan nicht verfügbare Entitäten bleiben nach Möglichkeit erhalten. Falls die neue Ansicht nicht erscheint, Browsercache aktualisieren und HA nach dem Update neu starten.

Nach fehlgeschlagener Abschaltbestätigung den realen Gerätzustand kontrollieren und HA-Protokolle prüfen. RRH ist keine elektrische Notabschaltung; nicht unkontrolliert neu starten.
