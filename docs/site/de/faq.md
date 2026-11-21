# FAQ und Fehlerbehebung

**Warum schaltet kein Gerät, obwohl PV-Leistung vorhanden ist?** RRH verwendet den *Netzleistungssensor*, nicht die PV-Erzeugungsleistung. Prüfe `Netzeinspeisung`, Vorzeichen, maximal erlaubtes Alter, Reserve, Status, Profil- und Verbraucherbedingungen, Mindest-Watt, Sperrzeiten und aktive Profile.

**Was ist der Unterschied zwischen „Pause“ und „Alle AUS“?** Pause hält die automatische Vergabe an und kann Geräte weiterlaufen lassen. Alle AUS fordert Abschaltung aller von RRH verwalteten Verbraucher. Nur eine unabhängige Trenneinrichtung ist eine physische Sicherheitsmaßnahme.

**Warum steht beim Geld ein Strich?** Bezugs- oder Einspeisetarif fehlt/ist ungültig. Nachträgliche Preise erzeugen keine erfundene Bewertung früherer unbepreister kWh.

**Warum ist der 24h-Graph leer oder lückenhaft?** Keine gültigen aktiven Messungen, Pause, HA-Neustart, alte/unbekannte Werte, noch keine 24h Betriebszeit. Der Graph beginnt erst mit eigener Erfassung.

**Warum meldet der Währungswechsel einen Fehler?** Bereits bepreiste Geldhistorie wird bewusst vor einer falschen Umetikettierung geschützt. [Energie & Kosten](energy.md) beschreibt Export, Reset und Neueingabe lokaler Tarife.

**Warum startet der Assistent nicht automatisch nach einem Upgrade?** Bestandskonfigurationen werden als eingerichtet behandelt. Der Assistent startet automatisch nur bei einem wirklich leeren System; du kannst ihn unter Einstellungen manuell öffnen.

**Kann ich Icon-Namen eingeben?** Das freie Texteingabefeld wurde entfernt. Wähle das Symbol direkt in der anklickbaren Icon-Galerie; eigene PNG-/WebP-Bilder bis 48 KB sind ebenfalls möglich.

**Darf ich die HA-Entität frei wählen?** Nein, nur unterstützte `switch`-, `select`-, `climate`- und `number`-Pfade und deren freigegebene Aktionen. Neuzuordnungen erfordern eine ausdrückliche Bestätigung.

**Warum bleibt ein Gerät trotz genügend Strom aus?** Prüfe Profilzuordnung, Bedingungen, Sensorqualität, dynamische Reihenfolge, Mindestleistung, Startabstand, Sperre und Fairness-Vorsprung. Fehlertext und Wartehinweis stehen in der jeweiligen Karte.

**Kann ich Daten aus dem HA Energy Dashboard übernehmen?** Du kannst passende vorhandene Sensor-Entitäten auswählen; RRH konfiguriert das HA-Energiedashboard nicht und synchronisiert auch keine rückwirkenden Daten.

**Warum wird mir eine andere Sprache angezeigt?** `auto` orientiert sich an HA. Die vollständige neue KB existiert auf DE/EN, ältere Spezialtexte der Oberfläche können in FR/ES/PT/IT noch teilweise deutsch/englisch sein.

**Wie melde ich Fehler?** Version, betreffende Seite/Aktion, relevante HA-Logs (ohne persönliche Daten), ungefährlichen Testaufbau, erwartetes und beobachtetes Verhalten dokumentieren. Bei unsicherem Aktor zuerst unabhängige Abschaltung veranlassen.
