# Profile, Prioritäten und Strategien

Profile gruppieren Verbraucher. Ein Verbraucher kann nur einem Profil angehören (außer gesondert definiertem Restüberschussgerät). Profile haben eine priorisierte Reihenfolge; höhere Prioritäten können unter bestimmten Schutzbedingungen laufende Niedrigprioritätszuweisungen verdrängen.

## Acht Strategien

| Strategie | Verhalten | Geeignet für |
|---|---|---|
| **Klassischer Round Robin** | Verbraucher kommen zyklisch nacheinander zum Zug; optional **Strikt** oder **Überspringen**, wenn die Leistung nicht reicht. | Faire Reihenfolge ohne besondere Messstrategie. |
| **Faire Laufzeitverteilung** | Geringste bestätigte RRH-Laufzeit erhält Vorrang; Mindestvorsprung und Rotationsintervall verhindern hektische Wechsel. | Ausgeglichene Betriebsstunden. |
| **Faire Energieverteilung** | Geringste geschätzte zugeteilte Wh (W × Laufzeit) erhält Vorrang; eigene Mindestdifferenz. | Verschiedene Geräte-Nennleistungen. |
| **Feste Priorität** | Erstes berechtigtes Gerät bevorzugt, streng oder unter Überspringen unpassender Geräte. | Planbare Prioritätsordnung. |
| **Maximale Effizienz** | Sucht Kombinationen mit besserer Watt-Nutzung des verfügbaren Überschusses; begrenzt auf 24 Verbraucher pro Profil. | Möglichst vollständige Nutzung bei passender Gerätekombination. |
| **Leistung aufsteigend** | Kleinste Leistungsaufnahme zuerst; streng oder überspringend. | Kleine Geräte bevorzugen. |
| **Leistung absteigend** | Größte Leistungsaufnahme zuerst; streng oder überspringend. | Große Geräte bevorzugen. |
| **Stabiler Betrieb** | Bevorzugt Laufkontinuität, vermeidet unnötiges Wechseln. | Geräte mit störendem Schaltverhalten. |

## Profilfelder und Standardparameter

| Feld | Erklärung / Standard |
|---|---|
| **Profilname / aktiv** | Anzeigename; deaktiviert nimmt nicht an der Vergabe teil. |
| **Priorität ↑/↓** | Reihenfolge der Profile; unabhängig von der Verbraucherreihenfolge. |
| **Verbraucher zuordnen** | Einmalige Mitgliedschaft, separat bei mehreren Profilen. |
| **Strategie** | Wählt Algorithmus; zugehörige Unteroptionen stehen in einem eigenen eingerahmten Bereich. |
| **Dashboard-Reihenfolge** | Feste oder dynamische Reihenfolge für unterstützte Strategien. |
| **Strikt / Überspringen** | Im Strikt-Modus blockiert ein nicht passendes Gerät die weiteren Zuteilungen; Überspringen erlaubt anderen geeigneten Mitgliedern die Chance. Nicht bei jeder Strategie verfügbar. |
| **Faire Vergleichsperiode** | Gesamt oder feste 24 h, 7 d, 14 d, 30 d; kein gleitendes Zeitfenster. Periode beginnt beim ersten aktiven Betrieb, läuft kalendarisch auch bei Pause weiter. |
| **Fair-Rotation** | Mindestzeit zwischen freiwilligen Fairnesswechseln, Standard **900 s**, 60–86400 s. |
| **Mindestvorsprung Laufzeit** | Mindestunterschied der Fair-Runtime-Gutschrift, Standard **60 s**. |
| **Mindestvorsprung Energie** | Mindestunterschied der Fair-Energy-Gutschrift, Standard **10 Wh**. |
| **Mindestverbesserung** | Für Maximum Efficiency: minimale zusätzliche nutzbare Leistung, Standard **200 W**. |
| **Optimierungsintervall** | Mindestabstand zwischen Optimierungen, Standard **60 s**, 10–3600 s. |
| **Start-Sicherheitsabstand** | Zusätzliche Leistungsreserve vor neuen Starts in Maximum Efficiency, Standard **50 W**. |
| **Sensorbedingungen** | Profilfreigabe nach UND/ODER, Grenzwerten und Hysterese. |
| **Fairnesszähler zurücksetzen** | Setzt nur ausgewählten fairen Vergleichswert zurück, nicht die Geldstatistik oder andere Zähler. |

**Wichtig:** Fair-Runtime-/Fair-Energy-Zähler messen nur bestätigte RRH-Zuteilung während der jeweiligen Strategie, nicht alle Gerätestunden. Mindestlaufzeit, Abkühlzeiten, Sensorqualität und **Alle AUS** gelten strategiübergreifend. Siehe [Sensorbedingungen](conditions.md).

## Teilnehmer des Profils

Die Mitgliedsauswahl und Grundreihenfolge sind im Profil-Editor jetzt in einem gemeinsam beschrifteten Abschnitt **Teilnehmer des Profils** gruppiert. Das beeinflusst nur die Darstellung, nicht die Priorität oder Strategie.


## Wochenzeitpläne für Profile (ab 0.9.5)

Unter Profile → Bearbeiten lässt sich pro Profil ein eigener Wochenplan aktivieren. Für jeden Zeitraum kannst du mehrere Wochentage sowie Beginn und Ende auswählen; mehrere Zeitfenster pro Tag sind möglich.

Ein Profilzeitplan ist unabhängig vom Verbraucherzeitplan. Startfreigabe besteht nur, wenn Profil aktiv, Profilzeitplan, Verbraucherzeitplan und vorhandene Sensorbedingungen erfüllt sind. Die Verteilstrategie bestimmt dann, welcher berechtigte Verbraucher startet.

Endet der Profilzeitraum, fordert RRH für seine laufenden Profilverbraucher eine bestätigte Abschaltung an. Sind mehrere betroffen, kann der vorhandene Gruppen-AUS-Befehl genutzt werden. Extern eingeschaltete Geräte werden durch die Zeitsteuerung nicht übernommen.

Zeitfenster über Mitternacht gehören zum Startwochentag. RRH nutzt die unter Home Assistant eingestellte Zeitzone einschließlich Zeitumstellungen. Das Panel zeigt Freigabe und nächstes Zeitfenster.
