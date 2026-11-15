# Agenten-Definitionen

Diese Markdown-Dateien bilden die geplante Rollenstruktur des KI-Trading-Agenten ab. Sie sind derzeit **nur Entwürfe** und werden von der Anwendung noch nicht geladen oder ausgeführt.

## Rollen

| Datei | Rolle |
|---|---|
| [orchestrator.md](./orchestrator.md) | Hauptagent und spätere Koordination |
| [news_analyst.md](./news_analyst.md) | Nachrichtenanalyse |
| [technical_analyst.md](./technical_analyst.md) | Markt- und Indikatoranalyse |
| [strategy_analyst.md](./strategy_analyst.md) | Strategiebeurteilung |
| [risk_analyst.md](./risk_analyst.md) | Risikoprüfung |

## Konvention

- Eine Datei beschreibt genau eine Rolle.
- `id` ist stabil und maschinenfreundlich; der Dateiname soll dazu passen.
- Zweck, Eingaben, freigegebene Ressourcen, Ausgabeformat, Grenzen und Regeln werden getrennt dokumentiert.
- Nicht festgelegte Regeln bleiben als `Noch festzulegen` markiert. Platzhalter sind keine Laufzeitanweisungen.
- Neue Agenten dürfen keine Order-Ausführung erhalten. Empfehlungen bleiben bis auf Weiteres unverbindlich.
- Diese Definitionen enthalten keine Zugangsdaten. Ressourcen werden später über explizite Backend-Schnittstellen bereitgestellt.

Vor einer Laufzeitintegration ist ein Loader-/Schemaformat festzulegen. Bis dahin sind die Dateien reine Dokumentation.
