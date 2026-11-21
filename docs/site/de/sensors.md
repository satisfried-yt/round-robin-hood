# HA-Sensoren korrekt auswählen

RRH unterscheidet **Steuerdaten** von **Statistikdaten**. Die Netzleistung ist die einzige Quelle für das aktuelle Schaltbudget. Tarifsensoren beeinflussen ausschließlich die Wirtschaftlichkeitsrechnung.

## Welche Entität gehört wohin?

| Feld | Einheit | Beispiel | Verwendung |
|---|---|---|---|
| Netzleistung | W oder kW | `sensor.netzleistung` | Echtzeit-Steuerung, Einspeisung/Bezug |
| PV-Anlagengröße | W, Wp, kW, kWp | `sensor.pv_nennleistung` | Nur zur Einordnung der Anlagenleistung, **keine** Messung der aktuellen Produktion |
| PV-Leistung | W oder kW | `sensor.pv_aktuell` | Anzeige der momentanen Erzeugung |
| PV-Energiezähler | Wh, kWh oder MWh | `sensor.pv_gesamtenergie` | Zusatzstatistik |
| Strompreis | EUR/kWh, €/kWh, ct/kWh, EUR/MWh | `sensor.strompreis` | Aktueller Bewertungstarif |
| Einspeisevergütung | Wie Strompreis | `sensor.einspeisepreis` | Entgangene Vergütung je selbst genutzter kWh |

Für CHF, USD und GBP gelten die zur gewählten Währung passenden Einheiten. **`0.32` ohne Einheit** ist nicht eindeutig und wird für neu ausgewählte Tarifsensoren nicht angeboten. Lege bei Bedarf einen HA-Template-Sensor mit korrekter `unit_of_measurement` an. Ein Temperatur- oder Zeitstempelsensor darf niemals als Preisquelle verwendet werden.

## Was passiert bei `unknown`, `unavailable` oder `nan`?

**Netzleistungsmesser:** Die Automatik darf ohne gültigen und frischen Netzleistungswert keine neuen Schaltvorgänge durchführen. In der bestehenden Steuerung führt ein ungültiger Wert im aktiven Betrieb zur Fehlerpause. Laufende elektrische Verbraucher werden dadurch **nicht automatisch elektrisch getrennt**.

**Tarif- und PV-Sensoren:** Ungültige Werte werden in der Berechnung ausgelassen. Die bisherige Euro-Statistik bleibt unverändert; fehlende Preise werden nicht ausgedacht. Die Steuerung selbst läuft aufgrund eines ausgefallenen Tarifsensors unverändert weiter.

## Einheiten und Umrechnung

- `ct/kWh` wird durch 100 in EUR/kWh umgerechnet.
- `EUR/MWh` wird durch 1.000 in EUR/kWh umgerechnet.
- `kW` wird mit 1.000 in W umgerechnet.
- `Wh` wird durch 1.000 in kWh umgerechnet.

**Wichtig:** Die Netzleistung am Anschlusspunkt wird bereits von eingeschalteten Verbrauchern beeinflusst. RRH zieht deren Leistung nicht ein zweites Mal von der aktuellen Einspeisung ab. Siehe [Dashboard](dashboard.md).

## Fehlersuche

Wenn eine Entität nicht in der Auswahl erscheint, prüfe in Home Assistant unter *Entwicklerwerkzeuge → Zustände* die `unit_of_measurement`, `state` und die Sensorverfügbarkeit. Prüfe auch die konfigurierte Währung. Bereits gespeicherte, inkompatible Sensoren werden mit Warnhinweis angezeigt, statt stillschweigend ersetzt zu werden.
