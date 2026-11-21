# Sicherheits- und Haftungshinweise

**Round Robin Hood ist ein privates Hobbyprojekt**, ursprünglich für den Eigenbedarf entwickelt. Bei Analyse, Entwicklung und Dokumentation wurde **künstliche Intelligenz** eingesetzt. Das Produkt hat keine zugesicherte Schadensfreiheit, keinen garantierten Wirtschaftlichkeitseffekt und ist **weder zertifiziertes Schutzgerät noch Not-Aus**. Diese Hinweise schließen gesetzlich zwingende Ansprüche nicht pauschal aus.

## Risiken

- Fehlerhafte Softwarelogik, Messwerte, HA-Integrationen, Netz- oder Schaltbefehle können elektrische Geräte **ungewollt weiterlaufen, einschalten, auf falscher Leistung regeln oder zu spät ausschalten** lassen.
- Heizlüfter/Heizgeräte können **überhitzen, Brände auslösen** oder Gegenstände in der Nähe beschädigen. Netzbetriebene Komponenten bergen elektrische Gefahren. Ein korrektes HA-Statussymbol garantiert keinen sicheren physischen Zustand.
- Schlechte Grenzwertwahl, verzögerte Abschaltung oder falsch eingestellte Leistungswerte können zu **ungeplantem Netzbezug, hohen Energiekosten und entgangener Einspeisevergütung** führen.
- HA-/RRH-Ausfall oder Strom-/Netzunterbrechung kann den Controller verhindern, sein Zielgerät tatsächlich zu erreichen; Software ersetzt keine **unabhängigen Temperaturbegrenzer, Thermostate, Sicherungen, FI/RCD, fachgerechte Installation und Beaufsichtigung**.

## Mindestvorkehrungen

1. Geeignete, korrekt abgesicherte Hardware verwenden und vom Fachpersonal dimensionieren lassen.
2. Heizgeräte sicher, standsicher, mit Abstand zu brennbaren Materialien und innerhalb der Herstellervorgaben betreiben; keinen unbeaufsichtigten Betrieb ohne unabhängigen Übertemperaturschutz.
3. Echte elektrische Leistungsaufnahme und Schaltreaktion unter sicheren Bedingungen prüfen. `number`-0 muss physisch AUS bedeuten; alle mehrstufigen Schaltwege inklusive AUS separat testen.
4. Netzsensor-Vorzeichen, Zeiteingang und Sensorausfall prüfen. Reserve und Verzögerungen konservativ einstellen.
5. Vor Updates **Alle AUS** und physischen Zustand prüfen, HA-Backup erstellen. Nach Updates zunächst im Demo-Betrieb abnehmen.
6. **Alle AUS** ist nur ein softwareseitiger Befehl. Für Notfälle eine von HA/RRH unabhängige Abschaltmöglichkeit sicherstellen.

## Warnhinweis erneut anzeigen

Der Dialog erscheint beim Öffnen, bis **„Verstanden, nicht wieder anzeigen“** ausdrücklich aktiviert und dauerhaft gespeichert ist. Der Haken ist **keine Erlaubnis**, Geräte unbeaufsichtigt zu betreiben. Der Dialog bleibt unter Einstellungen jederzeit abrufbar.

