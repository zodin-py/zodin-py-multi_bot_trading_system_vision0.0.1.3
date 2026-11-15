# KI-Trading-Agent mit spezialisierten Subagenten

**Status:** Entwurf – Phase 1 (Datei- und Spezifikationsstruktur)  
**Sprache:** Deutsch  
**Bereich:** `multi_bot_trading_system_vision0.0.1.3/backend/agents/` und bestehender RAG-/Chat-Stack

## Ziel

Der Nutzer soll im bestehenden LLM-Copilot Fragen zum Projekt und zu den verfügbaren Trading-Daten stellen können. Ein Hauptagent soll später je nach Frage passende spezialisierte Subagenten aufrufen, deren Ergebnisse zusammenführen und eine nachvollziehbare Einschätzung abgeben, ob ein Trade sinnvoll erscheint.

Die Agenten sollen in separaten Markdown-Dateien beschrieben werden. Ihre konkreten Regeln, Strategien, Schwellenwerte und Entscheidungslogik werden erst in späteren Phasen ergänzt.

## Ist-Zustand und Abgrenzung

- Das Frontend besitzt bereits einen LLM-Copilot und sendet Chat-Anfragen an `/api/rag/chat`.
- Im Backend existiert bereits ein RAG-Dienst mit Anthropic-API-Aufruf und Zugriff auf konfigurierte JSON-Wissensquellen.
- Die Oberfläche antwortet laut Nutzer aktuell nicht zuverlässig. Die Ursache ist mit dieser Phase nicht diagnostiziert oder behoben.
- Diese Phase erstellt nur die Agenten-Dateistruktur und die Spezifikation. Keine Laufzeitintegration, API-Änderung, Provider-Migration oder Trading-Logik.
- Die vorhandene Integration ist vor einer späteren Implementierung zu prüfen und möglichst weiterzuverwenden.

## Geplante Agentenstruktur

| Datei | Aufgabe |
|---|---|
| `multi_bot_trading_system_vision0.0.1.3/backend/agents/orchestrator.md` | Hauptagent: Frage einordnen, relevante Subagenten auswählen, Ergebnisse zusammenführen und Rückfragen bzw. Grenzen kenntlich machen |
| `multi_bot_trading_system_vision0.0.1.3/backend/agents/news_analyst.md` | Nachrichten und Ereignisse aus verfügbaren, zeitlich nachvollziehbaren Quellen untersuchen |
| `multi_bot_trading_system_vision0.0.1.3/backend/agents/technical_analyst.md` | Kurs-, Candle- und Indikatordaten auswerten |
| `multi_bot_trading_system_vision0.0.1.3/backend/agents/strategy_analyst.md` | Eine Frage anhand später festgelegter Strategien und vorhandener Strategiedaten beurteilen |
| `multi_bot_trading_system_vision0.0.1.3/backend/agents/risk_analyst.md` | Risiken und fehlende Risikoinformationen anhand später festgelegter Vorgaben prüfen |

Die Markdown-Dateien sind in Phase 1 Rollen-Skelette, keine aktiv ausführbaren Agenten. Jede Datei bekommt einheitliche Metadaten und Abschnitte für Zweck, Eingaben, erlaubte Ressourcen/Werkzeuge, Ausgabeformat, Grenzen und spätere Regeln. Noch nicht definierte Regeln bleiben ausdrücklich als Platzhalter stehen.

## Zielarchitektur für spätere Phasen

1. Das Frontend sendet Frage und Gesprächsverlauf an das Backend.
2. Das Backend prüft Eingaben und stellt den Modellzugriff ausschließlich serverseitig bereit.
3. Ein Ressourcen-/Tool-Layer liefert nur für die Frage benötigte, freigegebene Daten.
4. Der Hauptagent entscheidet, ob eine direkte Antwort ausreicht oder welche Subagenten benötigt werden.
5. Subagenten erhalten nur die für ihre Aufgabe benötigten Daten und liefern Ergebnisse in einem gemeinsamen strukturierten Format zurück.
6. Der Hauptagent fasst Belege, Unsicherheiten und gegebenenfalls widersprüchliche Ergebnisse zusammen.
7. Die API liefert eine verständliche Antwort mit Status und Quellen-/Zeitangaben an das Frontend.

Die konkreten Bibliotheken, Agenten-Orchestrierung und Modellwahl sind vor der Implementierung anhand des bestehenden Backends zu entscheiden. Bestehende Anthropic-/RAG-Funktionen sollen nicht parallel oder doppelt aufgebaut werden.

## Ressourcen und Zugriff

„Alle Ressourcen sehen“ bedeutet Zugriff auf alle vom Backend ausdrücklich freigegebenen und für den Agenten registrierten Anwendungsdaten – nicht uneingeschränkten Zugriff auf Dateisystem, Umgebungsvariablen oder Geheimnisse.

Als mögliche Datenquellen sind vor einer Implementierung die tatsächlich vorhandenen Schnittstellen und Daten zu prüfen, insbesondere:

- RAG-Wissensquellen und deren Quellenmetadaten
- Preis-, Candle- und Indikatordaten
- Nachrichten und deren Veröffentlichungszeitpunkt/Quelle
- Strategien und Analyseergebnisse
- Wallet- und Trade-Daten, sofern verfügbar und für den Nutzer freigegeben

Der Modellanbieter erhält niemals API-Schlüssel oder andere Zugangsdaten. Datenzugriff ist minimal, explizit, nachvollziehbar und zunächst lesend. Fehlende, veraltete oder nicht erreichbare Quellen müssen als solche ausgewiesen werden.

## Sicherheits- und Produktgrenzen

- Die Agenten dürfen in allen geplanten Phasen zunächst nur analysieren und Empfehlungen formulieren.
- Keine Order-Erstellung, -Änderung oder -Stornierung; keine Ausführung von Trades.
- Keine erfundenen Marktwerte, Nachrichten, Quellen oder Indikatorwerte.
- Jede datenbasierte Aussage soll, soweit möglich, Quelle und Datenzeitpunkt nennen.
- Unzureichende oder widersprüchliche Daten führen zu einer Rückfrage oder einer klar gekennzeichneten unsicheren Einschätzung, nicht zu einer vorgetäuschten Gewissheit.
- Konkrete Handelsregeln, Risikolimits und Entscheidungsgrenzen müssen vom Nutzer festgelegt und getestet werden, bevor der Agent Trade-Empfehlungen bewerten darf.
- Modellfehler, fehlende Konfiguration, Timeouts und Backendfehler müssen sichtbar an die Oberfläche gelangen; keine leere oder scheinbar erfolgreiche Antwort.

## Antwort- und Agentenvertrag (spätere Laufzeitintegration)

Jeder Agent soll später ein strukturiertes Ergebnis liefern:

```json
{
  "agent_id": "technical_analyst",
  "status": "ok",
  "summary": "Kurze Einschätzung",
  "findings": [],
  "sources": [],
  "data_as_of": null,
  "uncertainties": []
}
```

Der Hauptagent soll eine Nutzerantwort mit mindestens folgenden Informationen erzeugen:

- verständliche Antwort auf die Frage
- verwendete Agenten (falls Subagenten aufgerufen wurden)
- Quellen und Datenzeitpunkte
- Unsicherheiten oder fehlende Daten
- bei einer später freigegebenen Trade-Einschätzung: Entscheidungskategorie und nachvollziehbare Begründung

Das endgültige Schema ist vor der Laufzeitimplementierung mit den vorhandenen API-Modellen abzugleichen.

## Phasen und Nicht-Ziele

### Phase 1 – jetzt

- Spezifikation und Datei-/Rollenstruktur erstellen.
- Agentenregeln und Handelsstrategien ausdrücklich offenlassen.
- Keine Änderung am Chat-Verhalten oder an Backend-/Frontend-Code.

### Phase 2 – Chat-Verbindung zuverlässig machen

- Den nicht antwortenden Chat reproduzierbar diagnostizieren.
- Frontend-Anfrage, Backend-Route, Konfiguration, API-Key-Verfügbarkeit, Providerantwort, Timeouts und Fehlerdarstellung prüfen.
- Einen aussagekräftigen End-to-End-Test für eine echte oder kontrolliert gemockte Antwort ergänzen.

### Phase 3 – lesende Ressourcen anbinden

- Freigegebenen Ressourcen-/Tool-Katalog definieren und Datenquellen mit Zugriffstests anbinden.
- Aktualität, Herkunft und Berechtigungen jeder Quelle transportieren.
- Modellantworten und Fehler in einem stabilen API-Vertrag abbilden.

### Phase 4 – Agenten ausbauen

- Nutzerregeln und Aufgaben je Agent ergänzen.
- Agentenaufruf und -auswahl implementieren.
- Strukturierte Ergebnisse, Quellenprüfung und Zusammenführung testen.
- Erst danach Trade-Einschätzungen aktivieren; keine Ausführung von Trades.

Nicht-Ziele der aktuellen Phase sind Änderungen an Angular, Anbindung zusätzlicher Anbieter, automatische Orderausführung, Festlegung von Trading-Regeln und die Behebung des aktuellen Chat-Fehlers.

## Abnahmekriterien für Phase 1

- Eine zentrale Agenten-Übersicht beschreibt Dateikonvention und Status der Definitionen.
- Hauptagent und News-, Technik-, Strategie- und Risiko-Subagent haben jeweils eine eigene Markdown-Datei.
- Jede Datei ist als Entwurf/Platzhalter erkennbar und enthält keine erfundenen Strategieparameter oder ausführbaren Handelsregeln.
- Die Spezifikation trennt Phase 1 klar von Chat-Diagnose, Laufzeitintegration und späteren Trade-Einschätzungen.
- Es wurden keine Programmdateien verändert.
