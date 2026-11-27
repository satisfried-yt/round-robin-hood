# Installation, Update und Rückweg

## Neue Installation

1. Vollständiges Home-Assistant-Backup inklusive `.storage` erstellen.
2. Den Ordner `custom_components/round_robin_hood` aus dem Paket nach `/config/custom_components/round_robin_hood` kopieren. Keine fremden Unterordner überschreiben.
3. Home Assistant Core neu starten, unter **Einstellungen > Geräte & Dienste** Round Robin Hood hinzufügen und die Integration in der Seitenleiste öffnen.
4. Sicherheitshinweis lesen und Einrichtungsassistent, isolierte Demo oder manuelle Einrichtung wählen. RRH schaltet bei der Einrichtung nicht eigenständig Verbraucher ein.

## Bestehende Installation aktualisieren

1. **Alle AUS** ausführen und den tatsächlichen Ausschaltzustand jedes Aktors prüfen. Pause reicht nicht.
2. Vollständiges Home-Assistant-Backup inklusive `.storage` anlegen und Wiederherstellungsmöglichkeit prüfen.
3. Den versionsgeprüften Updatebefehl aus `docs/UPDATE_0.9.5.md` verwenden. Dieser Weg ist für ein vorhandenes **v0.9.4** vorgesehen.
4. Danach HA Core neu starten und vorhandene Verbraucher, Profile, Sensoren, Statistiken, das Startverhalten sowie **Alle AUS** prüfen.

## Zurücksetzen und Wiederherstellen

Zum Rückweg müssen **Code und zugehöriger RRH-Datenstand zusammen** wiederhergestellt werden. Die `.storage`-Datei nicht während des laufenden HA-Core-Betriebs ersetzen. Nach dem Backup geänderte RRH-Daten gehen beim Rückweg verloren. Alternativ vollständiges HA-Backup einspielen.

Ein RRH-Werksreset löscht RRH-Daten, nicht Home-Assistant-Geräte oder den HA-Recorder-Verlauf. Backup vorher erstellen.


## Update von 0.9.4 auf 0.9.5

- Mit RRH „Alle AUS“ ausführen und jeden Aktor tatsächlich kontrollieren. „Pause“ ist keine Abschaltung.
- Ein vollständiges Home-Assistant-Backup einschließlich /config/.storage erstellen und den Rückweg prüfen. Falls automatischer Start konfiguriert ist, für das Update „Immer AUS“ wählen.
- v0.9.5 über HACS/Marketplace oder die offizielle GitHub-Release-Datei installieren. Bei manueller Installation nur custom_components/round_robin_hood ersetzen; vollständige Schritte und Rückweg stehen in docs/UPDATE_0.9.5.md.
- Home Assistant Core neu starten; vorhandene Profile, Geräte, Bedingungen und Statistiken kontrollieren, die neue Entitätssuche und Zeitpläne testen.
- Die neuen Wochenpläne sind standardmäßig AUS. Beim Rückweg Code und den zusammengehörigen .storage-Stand bei gestopptem HA wiederherstellen.
