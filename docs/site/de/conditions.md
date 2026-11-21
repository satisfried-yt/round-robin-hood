# Sensorbedingungen – Grenzwerte, Logik, Hysterese

Bedingungen können **pro Profil** oder **pro Verbraucher** eingeschaltet werden. Sie verhindern Zuteilungen, wenn ein echter Messwert fehlt oder einen Grenzwert nicht erfüllt. Ein gesperrtes Profil gibt **keines** seiner Geräte frei, auch wenn genügend PV-Überschuss vorliegt.

| Feld | Erklärung |
|---|---|
| **Sensorentität** | Vorhandener numerischer HA-`sensor.*` (z. B. Temperatur). `unknown` / `unavailable` sind ungültig. |
| **Vergleichsoperator** | `>`, `>=`, `<`, `<=` gemäß Zielzustand. |
| **Grenzwert** | Numerische Schwelle in derselben Einheit wie der Sensor. |
| **Hysterese** | Rücksetzabstand zum Grenzwert, verhindert Flattern bei knappem Überschreiten. |
| **UND (alle)** | Sämtliche Bedingungen müssen erfüllt sein. |
| **ODER (eine)** | Mindestens eine Bedingung muss erfüllt sein. |
| **Aktivieren** | Ohne Aktivierung ist diese Bedingungsgruppe nicht als Filter wirksam. |

**Beispiel:** Heizgerät darf nur starten, wenn `sensor.raumtemperatur < 21` mit Hysterese `1` °C. Wenn derselbe Sensor nicht zuverlässig liefert, darf das Gerät nicht neu gestartet werden. Eine solche Softwarebedingung ist **kein unabhängiger Temperaturbegrenzer**.

In Dashboard und Verbraucherübersicht zeigen Detailinformationen Erfüllung `x/y`, ungültige Sensoren und Schwellenwertprüfung. Änderungen an Regel/Operator/Sensor setzen die gespeicherte Hysterese-Logik sicher zurück. [Sicherheitshinweise](safety.md).
