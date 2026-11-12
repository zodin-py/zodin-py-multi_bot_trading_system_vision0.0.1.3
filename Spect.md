# Spezifikation: JSON-gesteuerte Coin-Analyse

## 1. Ziel und Geltungsbereich

Das bestehende Multi-Bot-Trading-Dashboard soll um einen ausdrücklich gestarteten Analyseablauf erweitert werden. Eine externe JSON-Datei legt fest, welche Analyseschritte in welcher Reihenfolge ausgeführt werden. Der Benutzer kann die Anweisungen in der Datei bearbeiten, ohne den Programmcode zu ändern.

Die Analyse verwendet den im Dashboard gewählten Coin und Timeframe sowie die im Analysebereich ausgewählten Strategien. Sie liefert eine nachvollziehbare Einschätzung, führt aber **keine Trades aus und verändert keine Orders**.

## 2. Bestehende Architektur und verbindliche Integrationspunkte

Die Implementierung muss sich in die vorhandene Anwendung integrieren:

- Backend und HTTP-Endpunkte: Flask in `multi_bot_trading_system_vision0.0.1.3/backend/api_only.py`.
- Frontend: Angular in `multi_bot_trading_system_vision0.0.1.3/frontend/angular`.
- Coin- und Timeframe-Auswahl sowie Kerzenchart: vorhandene Coin-Selection-Komponente.
- Technische Indikatoren: `IndicatorService` in `backend/services/indicators_service.py`. Der Dienst liefert RSI, MACD, MACD-Signal, Histogramm und EMA aus Marktdaten.
- Nachrichten: vorhandener News-Service unter `backend/News_card/`. Er sammelt und liefert Meldungen, erstellt derzeit aber keine verlässliche Sentimentbewertung.
- Unterstützte Timeframes: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`, entsprechend der Backend-Konfiguration.

Im aktuellen Programm gibt es noch keinen Analyseendpunkt, keine Strategie-Dropdown-Liste und keine implementierten Strategie-Bots. Diese Funktionalität ist Teil dieser Erweiterung. Vorhandene Auswahl- und Datenabrufkomponenten sollen weiterverwendet werden; vorhandene Indikator- und News-Funktionen dürfen nicht dupliziert werden.

## 3. Regeldatei und Datenformat

Die Regeln liegen in `multi_bot_trading_system_vision0.0.1.3/backend/regeln.json` und werden ausschließlich serverseitig gelesen. Der Pfad wird relativ zur Backend-Datei aufgelöst und hängt nicht vom aktuellen Arbeitsverzeichnis ab.

Beispiel:

```json
{
  "version": 1,
  "analysis_rules": [
    {
      "step": 1,
      "action": "indicators",
      "title": "Technische Indikatoren",
      "instructions": "Bewerte RSI, MACD und EMA im gewählten Timeframe. Nenne fehlende Werte ausdrücklich."
    },
    {
      "step": 2,
      "action": "news",
      "title": "Nachrichten",
      "instructions": "Fasse passende aktuelle Meldungen neutral zusammen. Leite keine Stimmung ab, wenn die Daten dafür nicht ausreichen."
    },
    {
      "step": 3,
      "action": "strategies",
      "title": "Ausgewählte Strategien",
      "instructions": "Berücksichtige ausschließlich die Strategien, die für diesen Analyseauftrag ausgewählt wurden."
    },
    {
      "step": 4,
      "action": "summary",
      "title": "Gesamtbewertung",
      "instructions": "Fasse die vorherigen Ergebnisse zusammen und nenne Unsicherheiten und fehlende Daten."
    }
  ]
}
```

Jeder Schritt hat:

- `step`: positive, eindeutige Ganzzahl; dient der Validierung und Anzeige.
- `action`: unterstützte technische Aktion, beispielsweise `indicators`, `news`, `strategies` oder `summary`.
- `title`: nicht leer; verständlicher Name des Schritts.
- `instructions`: nicht leer; editierbarer Text mit zusätzlichen Bewertungs- und Ausgabehinweisen.

Die tatsächliche Reihenfolge ergibt sich aus der Reihenfolge im JSON-Array. `step`-Werte müssen in dieser Reihenfolge aufsteigend und eindeutig sein. Unbekannte Aktionen werden als Konfigurationsfehler behandelt.

Freitext wird zusammen mit dem Ergebnis protokolliert und im Dashboard angezeigt. Die Berechnungen richten sich nach der fest implementierten Aktion; der Freitext ändert die Berechnungslogik nicht und ist kein ausführbarer Programmcode. Die Anwendung darf keine beliebigen Aktionen allein aus Freitext ableiten. Falls später ein KI-Modell Anweisungen interpretieren soll, muss es separat konfiguriert und gegen nicht vertrauenswürdige Anweisungen abgesichert werden.

## 4. Ablauf eines Analyseauftrags

1. Der Benutzer wählt Coin, Timeframe und mindestens eine Strategie in der Analyseoberfläche aus.
2. Der Benutzer startet die Analyse ausdrücklich über eine Aktion im Dashboard.
3. Das Frontend sendet Coin-Symbol, Timeframe und ausgewählte Strategie-IDs an den Analyseendpunkt.
4. Das Backend lädt und validiert `regeln.json` für genau diesen Auftrag neu. Es darf keine beim Programmstart zwischengespeicherte Regelversion verwenden.
5. Das Backend führt die Schritte in der JSON-Array-Reihenfolge aus. Ein Schritt erhält Zugriff auf die Auftragseingaben und die Ergebnisse vorheriger Schritte.
6. Jeder Schritt liefert einen strukturierten Status und ein Ergebnis. Fehlende Daten werden als fehlend ausgewiesen und nicht durch erfundene Werte ersetzt.
7. Die Gesamtbewertung fasst die verfügbaren Ergebnisse zusammen. Sie darf keine nicht ausgeführten Schritte oder nicht belegten Fakten behaupten.
8. Das Backend liefert Ergebnis und Ablaufprotokoll an das Frontend zurück.

Die automatische Dashboard-Aktualisierung (einschließlich der periodischen Preis-/Indikatorabfragen) startet **keine** neue Analyse. Eine neue Analyse erfolgt nur durch eine ausdrückliche Benutzeraktion.

## 5. Strategien und Auswahl im Dashboard

Die Strategieauswahl wird als neue Dropdown- bzw. Mehrfachauswahl-Komponente in das vorhandene Angular-Dashboard integriert. Sie ist die einzige Quelle der aktuell ausgewählten Strategien; es darf keine zweite, unabhängige Strategieauswahl in der JSON-Datei geben.

Für den ersten Umfang werden folgende Strategie-IDs vorgesehen:

- `sr` — Support und Resistance
- `smc` — Smart Money Concepts
- `harmonic` — Harmonische Muster
- `trend` — Trendanalyse

Da diese Strategie-Bots aktuell nicht vorhanden sind, müssen sie als Backend-Analysen neu bereitgestellt werden. Jede Strategie liefert ein strukturiertes Ergebnis mit mindestens Strategie-ID, Status, Signal (`BUY`, `SELL`, `HOLD` oder `INCONCLUSIVE`), Begründung und verwendeten Daten. Nicht verfügbare oder nicht ausführbare Strategien werden als fehlgeschlagen bzw. nicht verfügbar ausgewiesen.

Die erste Version verwendet klar ausgewiesene Heuristiken: S/R sucht bestätigte Swing-Pivots in bis zu 200 Kerzen und bewertet einen Abstand von höchstens 1 % zum nächsten Level; SMC erkennt Fair-Value-Gaps in bis zu 60 Kerzen und signalisiert nur, wenn der letzte Schlusskurs in einer erkannten Zone liegt; Harmonic prüft die letzten fünf alternierenden Swing-Punkte gegen Fibonacci-Verhältnisse für Gartley, Bat, Butterfly und Crab; Trend vergleicht EMA 9 und EMA 21 sowie die EMA-21-Richtung über fünf Kerzen. Zu wenige oder ungeeignete Daten ergeben `INCONCLUSIVE`. Diese Regeln sind deterministische Ausgangs-Heuristiken, keine Aussage über Profitabilität.

Beim Start eines Analyseauftrags wird die aktuelle Auswahl einmalig übernommen und mit diesem Auftrag gespeichert. Der `strategies`-Schritt führt ausschließlich diese Auswahl aus. Die JSON-Datei darf Strategie-IDs nicht selbstständig aktivieren, deaktivieren oder duplizieren.

Sind keine Strategien ausgewählt und enthält die Regeldatei einen `strategies`-Schritt, wird der Auftrag verständlich abgelehnt oder der Schritt gemäß einem ausdrücklich festgelegten Validierungsverhalten als nicht ausführbar protokolliert. Eine leere Auswahl darf nicht stillschweigend durch „alle Strategien“ ersetzt werden.

Die Indikatoraktion verwendet RSI-Grenzen von 30/70 und vergleicht MACD mit der Signallinie, soweit Werte vorhanden sind. Die News-Aktion zeigt passende Meldungen an, behauptet aber keine automatische Sentimentbewertung. Die Gesamtbewertung zählt die ausführbaren `BUY`-, `SELL`- und `HOLD`-Signale aus Indikator- und Strategieaktionen; bei Gleichstand oder fehlenden Richtungssignalen lautet das Gesamtsignal `HOLD` bzw. `INCONCLUSIVE`.

## 6. API-Vertrag

Es wird ein neuer Endpunkt `POST /api/analyze` in der bestehenden Flask-Anwendung ergänzt.

Beispielanfrage:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "strategies": ["sr", "trend"]
}
```

Die Antwort enthält mindestens:

- normalisiertes Symbol und Timeframe,
- die beim Auftrag verwendeten Strategie-IDs,
- Regelversion sowie SHA-256-Prüfsumme der geladenen Regeldatei,
- Startzeitpunkt und Gesamtstatus,
- die geordneten Einzelschritte mit `step`, `action`, Status, Ergebnis und gegebenenfalls Fehlermeldung,
- die Gesamtbewertung.

Ungültige Eingaben und eine ungültige Regeldatei werden mit einer passenden HTTP-Fehlerantwort und einer verständlichen Fehlermeldung zurückgegeben. Bestehende API-Endpunkte und Antwortformate bleiben unverändert.

## 7. Validierung und Fehlerverhalten

Vor Beginn der Analyse wird die vollständige Regeldatei geprüft:

- Datei fehlt oder ist nicht lesbar.
- JSON enthält einen Syntaxfehler.
- `analysis_rules` fehlt, ist leer oder hat einen falschen Typ.
- Ein Schritt fehlt, hat ungültige oder doppelte `step`-Werte.
- `action`, `title` oder `instructions` fehlen, sind leer oder haben einen falschen Typ.
- `action` wird nicht unterstützt.
- Die Reihenfolge der Schritte ist nicht aufsteigend.

Bei einem Validierungsfehler startet keine Teilauswertung. Das Backend überschreibt oder repariert die Regeldatei nicht automatisch. Die Meldung benennt den betroffenen Schritt bzw. das betroffene Feld, soweit verfügbar.

Scheitert dagegen ein einzelner Datenabruf oder Analyseschritt während eines gültigen Auftrags, wird der Fehler im Ablaufprotokoll festgehalten. Nachfolgende Schritte dürfen nur ausgeführt werden, wenn ihre benötigten Eingaben vorhanden sind. Abhängige Schritte werden andernfalls als nicht ausführbar markiert; Ergebnisse werden nicht erfunden.

## 8. Protokollierung

Jeder Analyseauftrag muss nachvollziehbar sein. Das Protokoll umfasst:

- Zeitpunkt und Symbol/Timeframe,
- die verwendete Regelversion und Regeldatei-Prüfsumme,
- die ausgewählten Strategien,
- Reihenfolge, Status und Ergebnis jedes Schritts,
- Fehlermeldungen und Angaben zu fehlenden Daten,
- Gesamtstatus und Gesamtbewertung.

Das Protokoll darf keine API-Schlüssel oder andere Zugangsdaten enthalten. Analysedaten werden nur in dem Umfang gespeichert, der zur Nachvollziehbarkeit erforderlich ist. Die konkrete Persistenz muss mit der bestehenden Projektstruktur umgesetzt und darf nicht in der veränderbaren Regeldatei abgelegt werden.

## 9. Sicherheits- und Trading-Grenzen

- Die Analyse darf keine Order eröffnen, ändern oder schließen.
- Der Endpunkt akzeptiert nur unterstützte Coins, Timeframes, Aktionen und Strategie-IDs.
- Regeldatei-Inhalte werden als Daten behandelt; sie dürfen keine Dateien, Shell-Befehle oder beliebigen Python-Funktionen ausführen.
- Ein Analyseergebnis ist keine Garantie für ein zukünftiges Marktergebnis und darf nicht als ausgeführter Trade dargestellt werden.
- Die vorhandenen Wallet-, Trade-History- und Marktdaten-Endpunkte bleiben von dieser Funktion getrennt.

## 10. Akzeptanzkriterien

1. Ein Benutzer kann eine Analyse im Dashboard ausdrücklich starten.
2. Coin, Timeframe und Strategieauswahl des Auftrags werden an das Backend übergeben und in der Antwort ausgewiesen.
3. Das Backend liest die aktuelle Regeldatei für jeden ausdrücklichen Analyseauftrag erneut ein; Änderungen sind beim nächsten Auftrag ohne Neustart wirksam.
4. Eine gültige Regeldatei wird deterministisch und strikt in Array-Reihenfolge ausgeführt.
5. Die vorhandene `IndicatorService`- und News-Funktionalität wird wiederverwendet, nicht parallel neu implementiert.
6. Eine einzelne Strategieauswahl ist die Quelle der Strategie-IDs; die Regeldatei verwaltet keine zweite Auswahl.
7. Die vier vorgesehenen Strategien sind auswählbar und liefern strukturierte Ergebnisse oder einen klar protokollierten Fehlerstatus.
8. Fehlende Daten, ungültige Regeln und fehlgeschlagene Schritte werden verständlich gemeldet; es werden keine Ergebnisse erfunden.
9. Die Analyse erzeugt oder verändert keine Trades.
10. Das Protokoll enthält Regelprüfsumme, gewählte Strategien sowie Status und Ergebnis aller Schritte.
11. Fehlerhafte Regeldateien werden nicht automatisch überschrieben.
12. Bestehende Dashboard-Aktualisierung, API-Endpunkte, Coin-/Timeframe-Auswahl und Trading-Abläufe bleiben funktionsfähig.
