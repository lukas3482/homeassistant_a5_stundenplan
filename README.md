# FHV A5-Stundenplan Home Assistant

Diese Home Assistant Integration ermöglicht es, den Stundenplan der FHV (Fachhochschule Vorarlberg) aus dem A5-System abzurufen und als Kalender in Home Assistant darzustellen.

## 📌 Funktionen

- **Automatische Authentifizierung** mit dem A5-System der FHV
- **Darstellung der Stundenplan-Daten** als Kalender in Home Assistant

## 🔧 Installation

1. Lade den Ordner `custom_components/homeassistant_a5_stundenplan/` mit allen Dateien in das `custom_components/`-Verzeichnis deines Home Assistant Setups hoch.
2. Füge die folgende Konfiguration in deine `configuration.yaml` ein:

   ```yaml
   homeassistant_a5_stundenplan:
     username: "dein_benutzername"
     password: "dein_passwort"
   ```

3. Starte Home Assistant neu.

## ⚙️ Konfigurationsoptionen

| Option             | Beschreibung                                        | Erforderlich | Standardwert |
|-------------------|------------------------------------------------|-------------|-------------|
| `username`       | Dein FHV A5-Benutzername                     | ✅ Ja        | -           |
| `password`       | Dein FHV A5-Passwort                         | ✅ Ja        | -           |

## 🔄 Aktualisierung des Stundenplans

Der Stundenplan wird mit einem Intervall von **1 Stunde** aktualisiert 

## 📅 Nutzung

Nach der Installation wird in Home Assistant ein neuer Kalender mit dem Namen **FHV A5 Stundenplan** verfügbar sein. Alle Vorlesungen und Prüfungen werden als Ereignisse eingetragen.