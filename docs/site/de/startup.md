# Startverhalten nach Home-Assistant-Neustart

Unter **RRH → Einstellungen → Startverhalten bei HA-Neustart** wählst du, wie die Automatik nach einem Neustart reagieren soll.

| Einstellung | Verhalten |
|---|---|
| **Immer AUS** (Standard) | RRH nimmt nach dem Neustart die Automatik **nicht** wieder auf. Das ist kein elektrischer Ausschaltbefehl für schon eingeschaltete Geräte. |
| **Immer EIN** | RRH versucht die Automatik wieder zu aktivieren, sofern Einrichtung und Sicherheitsprüfungen dies zulassen. |
| **Letzten Zustand wiederherstellen** | Gespeichertes RRH EIN → Startversuch; Pause → bleibt pausiert; AUS → bleibt gestoppt. |

## Bedienung und Funktionen

Bei **Immer EIN** und **Letzten Zustand = EIN** funktioniert der Wiederanlauf jetzt auch nach einer **manuellen Einrichtung**, ohne dass der Assistent abgeschlossen worden sein muss. RRH zeigt zunächst einen **ausstehenden Autostart** an und wartet, bis sämtliche konfigurierten Geräte einen bekannten `on`/`off`-Zustand besitzen und **nach** dem Neustart eine neue, gültige Netzmessung eintrifft. Bis dahin bleibt die Regelung pausiert und es wird **kein** gespeicherter Einschaltbefehl ausgeführt. Ein verspätet verfügbarer Schalter verwirft die Startabsicht nicht mehr dauerhaft. Bleibt ein Sensor oder Aktor ungültig, bleibt die Regelung gesperrt und zeigt den Grund. **Immer AUS** bleibt Standard und hat kein automatisches Schalten zur Folge.

## Was die Startoption **nicht** macht

Sie schaltet nicht blind Geräte wieder ein und garantiert kein Abschalten während eines Stromausfalls. Pause unterbricht die RRH-Steuerung, nicht die Stromversorgung. Ein HA-Switch kann seinen Zustand unabhängig von RRH behalten oder wiederherstellen.

## Sicherheitsprüfungen beim automatischen Start

1. Gültige Konfiguration mit Netzleistungssensor, Verbraucher und Profil. Der Assistent muss bei manueller Einrichtung nicht abgeschlossen sein.
2. Keine unbestätigten Schaltaufträge oder offenen „Alle AUS“-Fehler.
3. Zustände aller RRH-Verbraucher sind als `on`/`off` bekannt. Fremde Verbraucher werden nicht übernommen.
4. Eine **neue** Netzleistungsmeldung nach dem Neustart muss eintreffen und gültig sein. Ein zwischengespeicherter HA-Wert alleine darf keine Schaltung auslösen.
5. Bei Fehlern ist **manuelles Eingreifen erforderlich**; RRH führt keine unkontrollierte Start-/Schaltwiederholung aus.

## Praxistipp

Bei Heiztechnik und Geräten, die unbeaufsichtigt laufen könnten, **Immer AUS** bevorzugen und unabhängige Temperaturbegrenzer sowie elektrische Schutzmaßnahmen einsetzen. Eine RRH-Aktion ist **kein zertifizierter Not-Aus**.
