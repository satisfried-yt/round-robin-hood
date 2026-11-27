# Verbraucher – Geräte und Schutzregeln

## Kachelübersicht

Das responsive Raster zeigt auf breiten Ansichten **drei feste, gleich breite Spalten**. Bei vier oder fünf Geräten bleiben nicht belegte Plätze in der letzten Zeile leer; bei schmalem Panel erscheinen zwei oder eine Spalte. Eine Karte enthält Namen, Icon, bestätigten Zustand, Nenn-/Soll-W, Teilnahme, zugeordnetes Profil, Warnungen und bei Fairness-Strategien die anrechenbare Zeit/Energie.

| Aktion | Wirkung |
|---|---|
| **Teilnehmen / Teilnahme beenden** | Aktiviert/deaktiviert den Verbraucher für die Vergabe. Ein gerade eingeschaltetes Gerät kann bis zur geregelten Abschaltung weiterlaufen. |
| **↑ / ↓** | Ändert die globale Reihenfolge (bei leistungssortierten Strategien keine frei erzwungene Reihenfolge). |
| **Bearbeiten** | Öffnet Geräte-, Zeit- und Bedingungsparameter. |
| **Entfernen** | Entfernt nur RRH-Zuordnung, **nicht** die HA-Entität. Aktive/fremd eingeschaltete Geräte dürfen nicht sicherheitswidrig gelöscht werden. |

## Grundfelder im Editor

| Feld | Bedeutung / Standard |
|---|---|
| **Name** | Frei wählbar, 1–80 Zeichen. |
| **Typ** | **Ein/Aus**, **mehrstufig**, **stufenlos**; bestimmt erlaubte HA-Serviceaufrufe. |
| **HA-Steuerentität** | Reale HA-Entität. Nicht wiederverwenden. Vor einer neuen/ersetzten Steuerentität ist eine zusätzliche **ausdrückliche Freigabe** erforderlich. |
| **Nenn- oder Mindestleistung (W)** | Positive Zahl, ≤100.000; Planungswert, keine gemessene Aufnahme. Bei Stufen-/Wattreglern Mindeststartwert. |
| **Teilnahme** | Ob das Gerät in der automatischen Zuteilung erlaubt ist; unabhängig von HA-Gerätezustand. |
| **Icon** | Anklickbare MDI-Galerie mit Symbolvorschau oder eigenes PNG/WebP bis 48 KB. Nur Darstellung, keine Schaltwirkung. |

## Gerätearten und zusätzliche Felder

**Ein/Aus (`switch.*`):** ein festes Nennwatt, `switch.turn_on`/`switch.turn_off`, mit Statuskontrolle.

**Mehrstufig (`switch.*`, `select.*`, `climate.*`):** Stufensteuerungsentität und Zeilen `Watt=Option` (z. B. `500=1` und `1000=2`), bei `select.*` eine echte **AUS-Option**. Die erste Stufe ist die minimale Startleistung. Ein HA-Lüftermodus ist kein Beweis für die tatsächliche Wattaufnahme. Der OFF-Pfad hängt von der Geräteart ab.

**Stufenlos (`number.*`):** minimale und **maximale** Leistung, **Regelauflösung (W)**, **Regelhysterese/Mindeständerung (W)** sowie **Mindest-Regelintervall (s)**. Die Entität muss `0` als tatsächlich sicheren OFF-Wert unterstützen und den Sollwert zurückmelden. Kein allgemein freier Service-Aufruf.

## Zeitverhalten

| Feld | Wirkung |
|---|---|
| **Eigene Abschaltverzögerung** | Überschreibt globale Verzögerung für dieses Gerät. 0–600 s. |
| **Mindestlaufzeit** | Stunden/Minuten/Sekunden nach Einschalten; freiwillige Wechsel werden zunächst blockiert. |
| **Mindestlaufzeit bei Leistungsdefizit erzwingen** | Vorsicht: Kann kurzfristigen **Netzbezug/Kosten** verursachen. Externe Schutzschaltungen werden dadurch nicht ersetzt. |
| **Wiedereinschaltsperre** | Stunden/Minuten/Sekunden nach Abschalten, verhindert schnelles Wiedereinschalten. |
| **Sperrmodus** | Gesperrtes Gerät überspringen oder auf es warten. |
| **Timer beenden** | Kann Schutzabstände verkürzen; je nach Einstellung separate Nachfrage. |

## Bedingungen

Individuell freischalten und über `UND` / `ODER` kombinieren, siehe [Sensorbedingungen](conditions.md). Ausschließlich echte HA-Sensorwerte, nicht geschätzte Wunschwerte verwenden. Bei fehlender Rückmeldung oder externer Betätigung darf RRH nicht annehmen, dass ein Gerät sicher geschaltet wurde.

**Sicherheit:** Die früher redundante Checkbox im Formular wurde entfernt. Das bedeutet **keine** pauschale Freigabe: Neue Bindungen verlangen eine gesonderte Bestätigung; Backend-Domänen und Rückmeldungen bleiben geprüft. Unabhängiger Temperaturbegrenzer und elektrische Absicherung sind bei Heizlasten obligatorisch.

## Bedienung und Funktionen

Im Verbrauchereditor gibt es keinen technischen MDI-Dropdown mehr. Wähle ein Symbol direkt in der anklickbaren Icon-Galerie (mit Vorschau); das ausgewählte Symbol wird umrandet. Bereits konfigurierte Symbole werden beim Update nicht überschrieben. Eigene PNG- und WebP-Symbole bleiben möglich.


## Neu in 0.9.5: Entitätssuche und Verbraucherzeitplan

Öffne Verbraucher → Bearbeiten. HA-Steuerentität und ggf. Stufensteuerung sind jetzt über die durchsuchbare Home-Assistant-Auswahl zugänglich. Gib einen Teil des Namens oder der Entitäts-ID ein; bestehende Zuordnungen bleiben erhalten.

Aktiviere „Zeitsteuerung für diesen Verbraucher“ nur bei Bedarf. Wähle mit „Zeitfenster hinzufügen“ einen oder mehrere Zeiträume; pro Zeile kannst du Mo–So markieren sowie Beginn und Ende (HH:MM) wählen. Ohne aktivierten Plan gibt es keine zusätzliche zeitliche Sperre.

Ein Intervall Montag 22:00–Dienstag 02:00 wird unter Montag angelegt. Das Ende ist exklusiv (02:00 ist bereits gesperrt). Mehrere Zeitfenster werden als ODER betrachtet, Sensor- und Profilbedingungen gelten zusätzlich mit UND.

Läuft ein von RRH verwalteter Verbraucher beim Ende seines Zeitfensters, schaltet RRH ihn ab – auch bei strikter Mindestlaufzeit. Das ersetzt keinen unabhängigen Temperatur- oder elektrischen Schutz. Der Status zeigt die nächste erlaubte Öffnung in der HA-Zeitzone.
