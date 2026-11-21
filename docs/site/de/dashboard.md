# Dashboard – alle Karten und Schalter

## Betrieb und Eingriff

| Anzeige/Aktion | Bedeutung |
|---|---|
| **Betrieb** | Aktueller Zustand (aktiv, pausiert, Fehler usw.) und Grund für Sperren. |
| **RRH EIN** | Startet die Automatik nur bei gültiger Konfiguration und frischer Netzmessung. Vorsicht: kann konfigurierte reale Geräte schalten. |
| **Alle AUS** | Fordert Abschaltung aller durch RRH verwalteten Geräte; Rückmeldungen prüfen. Kein zertifizierter Hardware-Not-Aus. |
| **Pause** | Stoppt Neuzuteilungen/Optimierung, schaltet **laufende Geräte nicht notwendigerweise aus**. |

## Leistungs- und Geldkarten

| Karte | Berechnung, Einheit und Grenze |
|---|---|
| **Netzeinspeisung** | Gemessener Netzfluss nach angewendetem Vorzeichen, W. Negative Werte bedeuten Netzbezug. Frische/Quelle beachten. |
| **Zusätzlich verfügbar** | Positive Einspeisung minus eingestellter Reserve, mindestens 0 W. Dies ist zusätzliche, noch nicht verbrauchte Leistung. |
| **Gesamtbudget** | Zusätzlich verfügbar plus bereits RRH-verwaltete bestätigte W. Rechenwert, kein Messgerät. |
| **Geschätzte verwaltete Leistung** | Summe laufender, bestätigter Verbraucher-Nennwerte in W. |
| **Netto-Vorteil jetzt** | Geschätzte kW der genutzten RRH-Leistung × (Strombezugspreis – Einspeisevergütung), **Geldeinheiten pro Stunde**. Live-Snapshot, nicht kumulativ. Fehlende Tarife ergeben „—“. |
| **Bisheriger Netto-Vorteil** | Aufgelaufener Schätzwert aus gültigen, bepreisten kWh minus entgangener Einspeisevergütung. Nicht notwendigerweise Ersparnis laut Rechnung. |
| **Von RRH genutzter Überschuss** | Zeitintegrierte, dem RRH zugerechnete PV-Energie in kWh. |
| **Überschuss-Nutzungsquote** | Augenblickliche RRH-Nutzleistung geteilt durch rekonstruierte positive Gesamteinspeise-/Nutzleistung in Prozent; bei unbrauchbaren Messungen „—“. |
| **PV-Leistung** | Optionaler vorhandener HA-PV-Leistungssensor in W; Anlagen-Nennleistung darunter in W. Ohne Sensor „—“. |

## Live-Effizienzkarte

Über die ganze Inhaltsbreite; wählbar als **Gauge, Linie, Balken, Fläche, Donut, gestapelt oder Sparkline**. Die Grafik visualisiert die berechnete momentane Nutzungsquote, nicht die absolute PV-Erzeugung. Ob eine Karte gezeigt wird, lässt sich unter **Einstellungen → Dashboard-Anzeigen & Sprache** einzeln ändern. Die Karten fließen responsive; das Diagramm bleibt über die gesamte Zeile.

## Aktuelle Vergabereihenfolge

Profile erscheinen nach ihrer Priorität; darunter zeigen Gerätkarten Ein-/Aus-Status, geplante Leistung, aktuelle Zuteilung, Bedingungen, Fairness und Sperrgründe. Grün markiert bestätigte RRH-gesteuerte Verbraucher; **inaktiv** bedeutet nicht zwingend einen Defekt. Profilbedingungen können auch bei vorhandenem Überschuss sämtliche Geräte eines Profils blockieren.

Siehe [Profile & Strategien](profiles.md) und [Energie & Kosten](energy.md).

## Bedienung und Funktionen

Das Dashboard verwendet den internationalen Slogan **Power your home. Not their profits.** / **Less to the grid. More for the little guy.**. Die Live-Anzeige des Netto-Vorteils ist eine geschätzte **Währungsmenge pro Stunde** mit zwei Nachkommastellen, nicht eine gemessene Einsparung. Ebenso zeigt die Karte des von RRH genutzten Überschusses zwei Nachkommastellen in kWh.

Unter dem bisherigen Netto-Vorteil liegt optional der Link **Gib einen Drink aus**. Ein Klick öffnet eine externe Spendenseite; es wird ohne Klick nichts nachgeladen. Unter **Einstellungen → Dashboard** kann der Link abgeschaltet werden.

**Regelkreis:** Ein 500-W-Verbraucher, der bei +500 W tatsächlicher Netzeinspeisung startet und den Export dadurch auf 0 W senkt, darf nicht allein deswegen ausgehen. Zusätzliche freie Leistung wird aus der **aktuellen** Einspeisung abzüglich Reserve ermittelt. Bereits aktive bestätigte Nennleistung dient nur der Schätzung des Gesamtpotenzials. Bei echtem Netzbezug greifen Defizitverzögerungen und Schutzbedingungen.

## Bedienung und Funktionen

Der optional sichtbare Link unter **Bisheriger Netto-Vorteil** heißt nun **„Gib einen Drink aus“**. Das Info-Symbol zeigt per Maus oder Berührung: **„Große Mengen Rum-Cola waren Treibstoff für dieses Projekt. Das kostet.“** Es werden ohne Klick auf den externen Link keine externen Inhalte eingebettet. Unter **Einstellungen → Dashboard** kannst du den Link weiterhin deaktivieren.

