# Ersteinrichtung und Sicherheitsdialog

## Vor dem Assistenten

Bei jeder neuen Browseröffnung zeigt RRH den Sicherheitshinweis, solange **„Verstanden, nicht wieder anzeigen“** nicht aktiviert und gespeichert wurde. Ein Klick auf **„Verstanden · weiter“** ohne Haken gilt nur für diese Ansicht. Über **Einstellungen → Sicherheitshinweis anzeigen** ist er jederzeit erneut abrufbar. Die Einstellung wird im realen RRH-Speicher abgelegt, nicht im flüchtigen Demo-Speicher. Der Dialog ersetzt keine elektrische Sicherheitsprüfung.

## Bedienung und Funktionen

Nach **„Verstanden · weiter“** wählst du zwischen **Einrichtungsassistent starten**, **Demo-Modus ausprobieren** und **Einrichtung überspringen**. Der Demo-Modus erstellt ausschließlich eine isolierte Simulation mit sechs virtuellen Verbrauchern und schaltet keine echten HA-Geräte. Beim Überspringen ist RRH **AUS**; keine Netzquelle, Verbraucher oder Profile werden angelegt. Du kannst später alles manuell einrichten oder den Assistenten unter Einstellungen starten. Der Werksreset führt erneut zum Sicherheitshinweis und dieser Startauswahl. Die Option „Verstanden, nicht wieder anzeigen“ bezieht sich nur auf den Sicherheitshinweis.

## Die sieben Schritte

1. **Einleitung:** Konzept lesen; der Vorgang schaltet nichts ein.
2. **Netzquelle:** `sensor.*` mit momentaner Netzleistung (W/kW) wählen; Vorzeichen festlegen (**positiv = Einspeisung** oder **negativ = Einspeisung**). Nicht den kWh-Zähler auswählen. Eine veraltete Messung sperrt Starts.
3. **Verbraucher:** ein oder mehrere vorhandene `switch.*`-Entitäten samt Name und nomineller Leistung in **W** hinzufügen. Eindeutige Zuordnung ist Pflicht. Für mehrstufige oder stufenlose Geräte danach den ausführlichen [Verbrauchereditor](consumers.md) verwenden.
4. **Strategie:** eine der [acht Strategien](profiles.md) auswählen und Hilfetext lesen. Der Assistent erstellt das Standardprofil oder ändert bei bewusster Wiederholung dessen Strategie.
5. **Energie & Kosten:** Währung, optionale PV-Nennleistung in W sowie Strombezugspreis und Vergütung **je kWh** angeben. Bestehende dynamische Sensorquellen bleiben erhalten, wenn entsprechende Felder leer bleiben.
6. **Betrieb:** Leistungsreserve in W, globale Abschaltverzögerung in Sekunden, deren Aktivierung und maximales Sensormeldungsalter einstellen.
7. **Zusammenfassung:** Angaben überprüfen und speichern. Vor der Freigabe neuer HA-Schalter folgt eine **ausdrückliche Sicherheitsbestätigung**.

Danach ist die Konfiguration gespeichert, RRH bleibt **pausiert**. Kein neu konfiguriertes Gerät wird automatisch eingeschaltet. Aktiviere RRH erst nach erfolgreichem Test mit sicheren Schaltern und gültigem Netzsensor.

## Erneut starten

Unter **Einstellungen → Einrichtungsassistent erneut starten** lässt sich der Wizard öffnen. Er fragt bei bestehenden Einstellungen ausdrücklich nach; Abbrechen verändert nichts. Vorhandene Verbraucher, andere Profile, Fairnesszähler und Statistiken bleiben erhalten. Falls ein Profil bereits besteht, ändert der Assistent dessen Strategie – dies in der Zusammenfassung beachten. Der Assistent überschreibt nicht heimlich bestehende Geräte.

## Sprache und Standardwerte

Die Oberfläche orientiert sich zunächst an der Home-Assistant-Sprache (`auto`, DE/EN bevorzugt). Die [Einstellungen](settings.md) erlauben spätere manuelle Sprachwahl. Reserve ist standardmäßig **100 W**, globale Verzögerung **30 s**, maximales Datenalter **60 s**; vor Verwendung an die reale Anlage anpassen.
