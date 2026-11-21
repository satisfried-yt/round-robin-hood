# Einstellungen – alle Schalter und Eingaben

**Wichtig:** Einstellungen verändern den realen Controller. Bei laufendem Betrieb zunächst **Pause** oder **Alle AUS**, ausstehende Schaltbestätigungen abwarten. Pause ist kein physisches Ausschalten.

## Netzquelle

| Feld | Erklärung / Standard |
|---|---|
| **Netzleistung aus Home Assistant** | Vorhandener `sensor.*` mit *momentanem* W/kW-Netzfluss. Pflicht für Einschaltungen. |
| **Vorzeichen** | `Positiv = Einspeisung` (Standard) bzw. `Negativ = Einspeisung`; falsches Vorzeichen verfälscht das gesamte Leistungsbudget. |
| **Datenqualität anzeigen** | Blendbaren Abschnitt mit Alter und Fehlerstatus der Netzquelle sichtbar halten. Standard eingeschaltet. |

## Leistung & Schaltverhalten

| Feld | Erklärung / Standard |
|---|---|
| **Leistungsreserve** | W, Standard **100**, Bereich 0–100.000. Abzug von positiver Einspeisung, reduziert Flattern/Netzbezug. |
| **Globale Unterlastverzögerung aktiv** | Standard an; bei Unterschreitung zeitlich verzögert abschalten. **Alle AUS** bleibt davon unberührt. |
| **Globale Unterlastverzögerung** | Sekunden, Standard **30**, Bereich 0–600. Kurzzeitiger Netzbezug möglich. |
| **Timer-Überspringen bestätigen** | Nachfrage bei manuellem Beenden von Mindestlaufzeit/Kühlpause. Standard an. |
| **Profil-Deaktivierung bestätigen** | Nachfrage vor Profil-Deaktivierung. Standard an. |
| **Restüberschussverbraucher** | Optional genau ein mehrstufiges/stufenloses Gerät für die *letzte* überschüssige Leistung, stets nachrangig gegenüber normalen Profilen. |

## Datenqualität

| Feld | Erklärung / Standard |
|---|---|
| **Maximales Meldungsalter** | Sekunden, Standard **60**, Bereich 5–3600. Ein alter/unbestimmter HA-Netzwert ist **keine gültige neue Messung**; keine neuen Starts. Gleiche Zahlen mit **neuem** HA-Zeitstempel gelten als neue Meldung. |

## Dashboard-Anzeigen & Sprache

| Feld | Erklärung |
|---|---|
| **Live-Diagramm** | Gauge, Linie, Balken, Fläche, Donut, gestapelt, Sparkline. Nur Darstellung, keine Änderung der Steuerung. |
| **Sprache** | `auto` übernimmt HA-Locale, ansonsten DE, EN, FR, ES, PT oder IT. Spezial-/Alttexte können bei FR/ES/PT/IT noch deutsch/englisch sein. |
| **Karten ein-/ausblenden** | Netzfluss, Budget, managed W, Live-Effizienz, Netto-Rate, Netto-Summe, RRH-kWh, Quote, Profile, PV-Leistung. Das volle Diagramm rückt sich automatisch ein. |

## Werkzeuge

| Aktion | Wirkung |
|---|---|
| **Demo-Modus** | Wechsel zu komplett getrennter, nur im Speicher existierender Simulation; realer Controller muss vorher vollständig AUS sein. Testverbraucher, PV-Schieberegler und simulierte Statistiken beeinflussen reale Geräte/Daten nicht. |
| **Einrichtungsassistent erneut starten** | Übernimmt bestehende Werte als Entwurf, ändert erst nach bewusster Bestätigung; siehe [Setup](setup.md). |
| **Sicherheitshinweis anzeigen** | Warnung jederzeit erneut anzeigen, optional „nicht mehr anzeigen“ zurücksetzen; siehe [Sicherheit](safety.md). |
| **Gesamtstatistik zurücksetzen** (unter Energie & Kosten) | Bestätigtes Löschen des Statistikledgers; Fair-Runtime/Energie-Gutschriften bleiben erhalten. Geldhistorie **nicht** nachträglich umbenennen. |

**Verschoben:** Währung, PV-Nennleistung, Tarife und optionale Energiesensoren werden ausschließlich unter [Energie & Kosten](energy.md) bearbeitet.

## Bedienung und Funktionen

- **Spendenhinweis im Dashboard anzeigen:** Aktiviert oder versteckt den Link „Gib einen Drink aus“. Standard für bisherige Installationen: ein. Die Statistiken bleiben unverändert.
- **RRH vollständig zurücksetzen:** Im Bereich Einstellungen **Alle RRH-Daten löschen** anklicken und `RESET ROUND ROBIN HOOD` exakt eingeben. RRH sendet **Alle AUS** und erwartet eine bestätigte AUS-Rückmeldung jedes konfigurierten Aktors. Erst danach werden alle RRH-Konfigurationen, Verbraucher, Profile, Zeit-/Fairness-Werte, Statistiken, Setup- und Hinweisbestätigungen gelöscht. **Kein Undo** in RRH. Vorher vollständiges HA-Backup samt `.storage` erstellen. Bei unbestätigten Aktoren oder Speicherfehlern wird nicht normal fortgefahren; HA-Protokoll und Geräte kontrollieren. Externe HA-Entitäten, Recorder-Historie und andere Integrationen bleiben unverändert.
- Nach erfolgreichem Reset erscheint erst der Sicherheitshinweis und dann die Auswahl des Einstiegswegs. Die Automatik startet **nicht** von selbst.

## Bedienung und Funktionen

**Immer AUS** (Standard), **Immer EIN** oder **letzten Zustand wiederherstellen**. Details, Sicherheitsprüfungen und Verhalten bei Neustarts: [Startverhalten](startup.md).

## Bedienung und Funktionen

Die Einstellungskarten haben **innerhalb derselben Rasterzeile die gleiche Höhe**, auch wenn einzelne Beschreibungen länger sind. Der optionale Spendenlink heißt jetzt **„Gib einen Drink aus“**; über das kleine Info-Symbol erscheint auch auf Touch-Geräten der Hinweis: „Große Mengen Rum-Cola waren Treibstoff für dieses Projekt. Das kostet.“ Der Link bleibt deaktivierbar. Neue Nutzer können nach dem Sicherheitshinweis Assistent, isolierte Demo oder eine leere Einrichtung wählen.

