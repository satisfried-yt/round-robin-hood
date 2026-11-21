# Energie & Kosten – alle Felder und Kennzahlen

Die Seite bietet eine zusammenhängende Auswertung und die **einzige** Eingabestelle für Anlagen-Nennleistung und Tarife. Änderungen erst bei **pausiertem** RRH speichern; sie beeinflussen Schätzungen, nicht direkt die Schaltreserve. RRH schreibt **keine** Home-Assistant-Energiedashboard-Einstellungen.

## Konfiguration

| Feld | Bedeutung und Format |
|---|---|
| **Währung** | `EUR`, `CHF`, `USD`, `GBP`. Beträge werden nicht zum Wechselkurs umgerechnet. Vor Wechsel lokale Tarife prüfen; vorhandene wertbehaftete Historie sperrt Wechsel bis zum ausdrücklich zurückgesetzten Ledger. |
| **PV-Anlagengröße (W)** | Optionaler fester Nennwert (z. B. `4000` für 4 kW) oder HA-Zahlensensor. Intern werden bisherige `kWp`-Werte zu W ×1000 angezeigt; keine neue Leistungsmessung. |
| **Strompreis (je kWh)** | Fester Wert oder HA-Zahlensensor; beispielsweise `0,30` EUR/kWh. Dynamische Sensoren müssen eindeutige Einheiten liefern; einheitenlose Helfer werden nicht als Tarifquelle akzeptiert. |
| **Einspeisevergütung (je kWh)** | Gegenwert pro exportierter kWh, z. B. `0,08` EUR/kWh. Kann höher als Bezugspreis sein: Netto-Vorteil wird dann negativ. |
| **PV-Leistungssensor** | Optionaler `sensor.*` mit W oder kW für die aktuelle PV-Erzeugungsanzeige. |
| **PV-Energiezähler** | Optionaler kumulativer `sensor.*` mit Wh/kWh/MWh; liefert Zusatzinformationen, nicht den Budgetgeber. |
| **Netzeinspeisezähler** | Optionaler kumulativer `sensor.*` mit Wh/kWh/MWh. Nicht mit dem für Schaltungen notwendigen *Momentanwert* verwechseln. |

## Statistik-Karten

- **Von RRH genutzte Energie (kWh):** integrierte, dem RRH zugeordnete Überschussleistung; Geräteteilwerte werden nach bestätigten Nominal-W verteilt.
- **Potenzieller Überschuss (kWh)** und **verbleibende Einspeisung (kWh):** nur während gültiger aktiver Messungen rekonstruiert, keine historische Gesamterzeugung.
- **Brutto-Energiewert:** zugerechnete kWh × Bezugspreis.
- **Entgangene Vergütung:** zugerechnete kWh × Einspeisevergütung.
- **Netto-Vorteil:** Brutto minus entgangene Vergütung.
- **Bepreiste kWh:** Menge mit gültiger Tarifinformation; unbekannte Tarife erzeugen **keine** fiktiven Euro.
- **Laufzeit, Starts, Verbraucherstatistik, Tageswerte:** aus bestätigten RRH-Zuständen, mit getrenntem Fairness-Speicher. Tageswerte sind auf 45 Tage begrenzt; Gesamtsummen bleiben bis zum gezielten Reset erhalten.

## 24-Stunden-Live-Verlauf

Der Graph zeigt die **Überschuss-Nutzungsquote in Prozent** für die **letzten 24 Stunden** auf echter Zeitachse. Formel: `100 × RRH-gesteuerte W / (RRH-gesteuerte W + positiv gemessene Einspeise-W)` bei gültigen Daten. Y-Achse 0/50/100 %, X-Achse Stunden vor Jetzt. Typisch ein Wert alle 30 s, maximal 2890 gespeicherte Verlaufseinträge. Messausfälle, Pause, veraltete oder ungültige Ablesungen führen zu **Lücken** statt erfundenen Verläufen. Die Historie wird in RRH gespeichert und übersteht HA-Neustarts; vor der Installation liegende Werte werden nicht nachgetragen. Das ist **kein Energie- oder Geldzähler**.

## Währung korrekt wechseln

Ein bestehender Geldledger mit bepreisten kWh kann nicht einfach nachträglich von EUR in USD/CHF/GBP umetikettiert werden. Nach Export und bewusstem Reset der **Gesamtstatistik** darf die gewünschte Währung mit den **passenden, neu bestätigten lokalen Tarifen** konfiguriert werden. Einheiten dynamischer Tarifsensoren und `ct/kWh` bzw. `EUR/MWh` müssen zur Auswahl passen. Die faire Verteilung bleibt vom Statistik-Reset unabhängig.

[Detailliertes Dashboard](dashboard.md) · [Einstellungen](settings.md)

## Bedienung und Funktionen

PV-Nennleistung, Strombezugspreis, Einspeisevergütung, Währung und optionale HA-Sensoren stehen jetzt **oben**, vor der Statistik. Die Eingaben stehen auf breiten Bildschirmen in drei, auf schmalen in ein oder zwei Spalten. Der Abschnitt ist standardmäßig geöffnet. Vorhandene Wertquellen werden beim Update unverändert übernommen.

## Bedienung und Funktionen

Sensoren werden nach zur Währung passender Einheit gefiltert; ungültige Live-Werte werden nicht bepreist. Mehr dazu: [HA-Sensoren](sensors.md).
