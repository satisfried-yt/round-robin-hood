# Installation, Update und Rückweg

## Neue Installation

1. Vollständiges Home-Assistant-Backup inklusive `.storage` erstellen.
2. Den Ordner `custom_components/round_robin_hood` aus dem Paket nach `/config/custom_components/round_robin_hood` kopieren. Keine fremden Unterordner überschreiben.
3. Home Assistant Core neu starten, unter **Einstellungen > Geräte & Dienste** Round Robin Hood hinzufügen und die Integration in der Seitenleiste öffnen.
4. Sicherheitshinweis lesen und Einrichtungsassistent, isolierte Demo oder manuelle Einrichtung wählen. RRH schaltet bei der Einrichtung nicht eigenständig Verbraucher ein.

## Bestehende Installation aktualisieren

1. **Alle AUS** ausführen und den tatsächlichen Ausschaltzustand jedes Aktors prüfen. Pause reicht nicht.
2. Vollständiges Home-Assistant-Backup inklusive `.storage` anlegen und Wiederherstellungsmöglichkeit prüfen.
3. Den versionsgeprüften Updatebefehl aus `docs/UPDATE_0.9.3.md` verwenden. Dieser Weg ist für ein vorhandenes **v0.9.2** vorgesehen.
4. Danach HA Core neu starten und vorhandene Verbraucher, Profile, Sensoren, Statistiken, das Startverhalten sowie **Alle AUS** prüfen.

## Zurücksetzen und Wiederherstellen

Zum Rückweg müssen **Code und zugehöriger RRH-Datenstand zusammen** wiederhergestellt werden. Die `.storage`-Datei nicht während des laufenden HA-Core-Betriebs ersetzen. Nach dem Backup geänderte RRH-Daten gehen beim Rückweg verloren. Alternativ vollständiges HA-Backup einspielen.

Ein RRH-Werksreset löscht RRH-Daten, nicht Home-Assistant-Geräte oder den HA-Recorder-Verlauf. Backup vorher erstellen.
