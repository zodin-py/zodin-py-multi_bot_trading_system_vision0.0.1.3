---
name: news-analyzer
description: Analysiert News aus news-results.json, ergänzt fehlende Artikelbeschreibungen sequenziell über den Skill article-enricher und erstellt anschließend die Top-5-Coins mit dem höchsten positiven News-Score.
---

# News Analyzer

## 1. Aufgabe

Dieser Skill ist für die vollständige News-Analyse und das Ranking von Kryptowährungen verantwortlich.

Er arbeitet ausschließlich mit den lokal gespeicherten News-Daten und erstellt am Ende eine Liste der maximal fünf Coins, bei denen die vorhandenen Nachrichten auf eine kurzfristig positive Kursentwicklung hindeuten.

**Zielzeitraum:** nächste Stunden bis maximal 24 Stunden.

**Datenquelle:** ausschließlich `news-results.json` sowie die konfigurierte lokale Coin-Liste.

Es dürfen keine Kursdaten, Handelsvolumen, Indikatoren oder externen Marktdaten zur Bewertung verwendet werden.

Der verbindliche Pfad für `news-results.json` lautet `backend/News_card/news-results.json`, relativ zum Anwendungsstammverzeichnis (dem Projektverzeichnis, das `backend/News_card/news.py` enthält). Pfade dürfen nicht relativ zum Skill-Unterverzeichnis oder zum aktuellen Arbeitsverzeichnis aufgelöst werden.

## 2. Verbindliche Regeln

1. Alle Schritte müssen strikt von oben nach unten ausgeführt werden.
2. Nachrichten mit `coin_name: "General Market"` dürfen niemals analysiert oder bewertet werden.
3. Nur Nachrichten mit `importance` gleich `high` oder `very_high` werden zur Artikelanreicherung an Skill 2 übergeben.
4. Eine Nachricht darf nur dann an Skill 2 übergeben werden, wenn ihr Feld `description` fehlt, `null`, leer oder ausschließlich mit Leerzeichen gefüllt ist.
5. Skill 2 wird immer nur mit einem Artikel gleichzeitig aufgerufen.
6. Nach jedem Aufruf muss auf die Rückgabe von Skill 2 gewartet werden.
7. Erst nach Abschluss aller erforderlichen Aufrufe darf das Coin-Ranking beginnen.
8. Doppelte Nachrichten über dasselbe Ereignis dürfen nicht mehrfach als unabhängige Katalysatoren gezählt werden.
9. Es dürfen ausschließlich Coins mit einem positiven Gesamtscore in die Ergebnisliste aufgenommen werden.
10. Das Endergebnis enthält maximal fünf Coins. Es dürfen auch weniger als fünf sein.
11. Keine zusätzliche Marktanalyse, Marktprognose oder sonstige Ergebnisliste erstellen.

## 3. Dateien und Datenstruktur

### 3.1 Eingabedatei

Verbindlicher Pfad relativ zum Anwendungsstammverzeichnis:

`backend/News_card/news-results.json`

Die Datei enthält eine Liste von News-Objekten. Ein Objekt kann beispielsweise so aussehen:

```json
{
  "id": "69358173-8b08-5deb-acbb-37eda584c09c",
  "title": "Bitcoin tumbles to $76,000 as losses deepen",
  "coin_name": "Bitcoin",
  "sentiment": "negative",
  "importance": "high",
  "url": "https://news.google.com/rss/articles/...",
  "description": ""
}
```

Die vorhandenen Felder müssen erhalten bleiben. Die Feldreihenfolge darf sich ändern, sofern das JSON weiterhin korrekt ist.

### 3.2 Coin-Erkennung

Die betroffenen Coins müssen dynamisch anhand des vollständigen Inhalts der Nachrichten identifiziert werden.

Für jeden Artikel:

1. Alle erwähnten Kryptowährungen und Blockchain-Projekte identifizieren.
2. Prüfen, welche Coins direkt vom beschriebenen Ereignis betroffen sind.
3. Zusätzlich indirekt betroffene Coins identifizieren, sofern ein nachvollziehbarer Zusammenhang besteht.
4. Für jeden betroffenen Coin die konkrete Auswirkung auf seine kurzfristige Kursentwicklung bewerten.
5. Nur Coins berücksichtigen, für die ein nachvollziehbarer Zusammenhang zum Ereignis besteht.

Ein Coin muss nicht im Nachrichtentitel erwähnt werden. Entscheidend ist der vollständige Artikelinhalt.

Die identifizierten Coins werden anschließend anhand ihres Gesamtscores bewertet. Nur die fünf Coins mit dem höchsten positiven Score werden ausgegeben. Sind weniger als fünf Coins positiv bewertet, werden entsprechend weniger ausgegeben.

`General Market` wird vollständig ausgeschlossen.

### 3.3 Ausgabedatei

`today-coins.json`

Die Datei enthält ausschließlich das Ranking der positiven Coin-Kandidaten.

Beispiel:

```json
{
  "coins": [
    {
      "rank": 1,
      "coin_name": "Bitcoin",
      "symbol": "BTC",
      "score": 82.5,
      "reason": "Mehrere relevante positive Nachrichten mit kurzfristigem Kurspotenzial."
    }
  ]
}
```

Keine zusätzlichen Felder wie `market_analysis`, `market_sentiment`, `statistics`, `debug`, `diagnostics` oder allgemeine Marktprognosen hinzufügen.

## 4. Arbeitsablauf

### Schritt 1 – News-Datei laden

1. `news-results.json` lesen.
2. Prüfen, ob die Datei existiert und gültiges JSON enthält.
3. Sicherstellen, dass die oberste Ebene eine Liste von News-Objekten ist.
4. Jedes News-Objekt auf die erforderlichen Felder prüfen:
   - `id`
   - `title`
   - `coin_name`
   - `importance`
   - `sentiment`
   - `url`
   - `description`

Fehlende optionale Felder dürfen nicht erfunden werden.

Wenn die Datei nicht lesbar oder das JSON ungültig ist, den Vorgang abbrechen. Keine leere oder fehlerhafte Datei überschreiben.

### Schritt 2 – Nachrichten filtern

Jede Nachricht der Reihe nach prüfen.

**Sofort überspringen:**

- `coin_name` ist `General Market`.
- `coin_name` fehlt oder ist nicht eindeutig einem Coin zuzuordnen.
- `importance` ist weder `high` noch `very_high`.

Die Importance-Werte dürfen bei der Prüfung ohne Beachtung der Groß-/Kleinschreibung verglichen werden.

Beispielsweise gelten `HIGH` und `high` als gleichwertig.

### Schritt 3 – Beschreibung prüfen

Bei jeder verbleibenden Nachricht das Feld `description` prüfen.

Eine Beschreibung gilt als vorhanden, wenn sie ein nicht leeres Textfeld mit mindestens einem sinnvollen Zeichen enthält.

Folgende Werte gelten als fehlende Beschreibung:

```json
"description": null
```

```json
"description": ""
```

```json
"description": "   "
```

Auch ein vollständig fehlendes `description`-Feld gilt als fehlend.

**Wenn eine sinnvolle Beschreibung existiert:**

- Artikel nicht erneut abrufen.
- Skill 2 nicht aufrufen.
- Direkt mit der nächsten Nachricht fortfahren.

**Wenn keine Beschreibung existiert:**

- Prüfen, ob `id` und `url` vorhanden und gültig sind.
- Falls eines davon fehlt, den Artikel nicht an Skill 2 übergeben.
- Andernfalls Skill 2 gemäß Abschnitt 4.1 aufrufen.

### Schritt 4 – Skill 2 sequenziell aufrufen

Für jeden Artikel mit fehlender Beschreibung muss Skill 2 einzeln aufgerufen werden.

#### 4.1 Aufrufvertrag

Skill-Name:

`article-enricher`

Eingabe:

```json
{
  "id": "EXAKTE_NEWS_ID",
  "url": "EXAKTE_ARTIKEL_URL",
  "news_file": "backend/News_card/news-results.json"
}
```

`id` und `url` müssen direkt aus dem jeweiligen News-Objekt übernommen werden. `news_file` muss auf den verbindlichen Pfad relativ zum Anwendungsstammverzeichnis zeigen.

Keine IDs oder URLs selbst erzeugen oder verändern.

#### 4.2 Verbindliche Aufrufreihenfolge

Der Ablauf muss für jeden Artikel exakt so aussehen:

1. Artikel auswählen.
2. Fehlende Beschreibung feststellen.
3. Skill 2 mit genau einer `id` und einer `url` aufrufen.
4. Auf die vollständige Rückgabe von Skill 2 warten.
5. Rückgabestatus prüfen.
6. Erst danach den nächsten Artikel auswählen.

**VERBOTEN:**

- Mehrere Skill-2-Aufrufe gleichzeitig starten.
- Alle URLs gesammelt übergeben.
- Mit dem Ranking beginnen, während ein Aufruf noch läuft.
- Einen Artikel erneut abrufen, wenn seine Beschreibung inzwischen erfolgreich gespeichert wurde.

#### 4.3 Rückgabevertrag

Skill 2 muss einen Status zurückgeben:

```json
{
  "id": "EXAKTE_NEWS_ID",
  "status": "success",
  "description": "Zusammenfassung des Artikels."
}
```

Mögliche Statuswerte:

- `success`: Beschreibung wurde erfolgreich gespeichert.
- `partial`: Nur teilweise zugänglicher Artikelinhalt konnte zusammengefasst und gespeichert werden.
- `failed`: Beschreibung konnte nicht erstellt oder gespeichert werden.

Nach `success` oder `partial` darf Skill 1 mit dem nächsten Artikel fortfahren.

Nach `failed` darf Skill 1 ebenfalls mit dem nächsten Artikel fortfahren. Der fehlgeschlagene Artikel darf nicht endlos erneut aufgerufen werden.

### Schritt 5 – Aktualisierte News-Datei erneut laden

Nachdem alle erforderlichen Skill-2-Aufrufe abgeschlossen sind:

1. `news-results.json` erneut einlesen.
2. Die aktualisierten Beschreibungen verwenden.
3. Prüfen, ob die Datei weiterhin gültiges JSON enthält.
4. Die anschließende Bewertung ausschließlich auf Basis des tatsächlich vorhandenen Inhalts durchführen.

Die ursprünglichen Daten dürfen nicht durch einen veralteten Speicherstand überschrieben werden.

### Schritt 6 – Doppelte Nachrichten zusammenführen

Vor der Bewertung müssen Nachrichten auf doppelte oder nahezu identische Ereignisse geprüft werden.

Beispiele:

- Mehrere Artikel über dieselbe Bitcoin-ETF-Entscheidung.
- Mehrere Quellen über denselben Hack.
- Mehrere Meldungen über dieselbe Börsenankündigung.

Regeln:

- Dasselbe Ereignis darf nicht mehrfach als unabhängiger Katalysator zählen.
- Unterschiedliche Quellen dürfen die Glaubwürdigkeit eines Ereignisses erhöhen.
- Eine höhere Anzahl nahezu identischer Artikel darf den Score nicht künstlich vervielfachen.
- Unterschiedliche Ereignisse müssen getrennt bewertet werden.
- Bei Unsicherheit keine künstliche Zusammenführung vornehmen.

### Schritt 7 – Coins identifizieren

Für jedes relevante Ereignis feststellen:

1. Welcher Coin ist direkt betroffen?
2. Gibt es eindeutig belegbare indirekt betroffene Coins?
3. Ist der Zusammenhang kurzfristig relevant?
4. Ist der Zusammenhang positiv oder negativ?

Direkte Auswirkungen haben Vorrang.

Indirekte Auswirkungen dürfen nur berücksichtigt werden, wenn der Zusammenhang im Artikel nachvollziehbar belegt ist.

Beispielsweise darf eine Nachricht über eine Ethereum-basierte Anwendung nicht automatisch jedem Ethereum-Ökosystem-Coin positive Punkte geben.

`General Market` darf zu keinem Zeitpunkt als Coin oder Analyseobjekt verwendet werden.

### Schritt 8 – News bewerten

Die Bewertung erfolgt ausschließlich auf Basis der Nachrichteninhalte.

Jedes eigenständige Ereignis wird anhand folgender Kriterien bewertet:

| Kriterium | Wertebereich |
|---|---:|
| Erwartete kurzfristige Auswirkung | -3 bis +3 |
| Importance-Faktor | 0,25 bis 3,0 |
| Aktualität | 0 bis 1 |
| Quellenvertrauen | 0 bis 1 |
| Coin-Relevanz | 0 bis 1 |

#### 8.1 Importance-Faktor

| Importance | Faktor |
|---|---:|
| very_low | 0,25 |
| low | 0,50 |
| medium | 1,00 |
| high | 2,00 |
| very_high | 3,00 |

Fehlende oder unbekannte Importance-Werte erhalten den neutralen Faktor `1,0`.

#### 8.2 Erwartete kurzfristige Auswirkung

Der Inhalt der Nachricht ist entscheidend. Das vorhandene Feld `sentiment` darf als Hinweis verwendet werden, ersetzt aber nicht die inhaltliche Bewertung.

| Bewertung | Wert |
|---|---:|
| Sehr stark positiv | +3 |
| Positiv | +2 |
| Leicht positiv | +1 |
| Neutral / keine erkennbare Auswirkung | 0 |
| Leicht negativ | -1 |
| Negativ | -2 |
| Sehr stark negativ | -3 |

Beispiele:

- Neue wichtige Partnerschaft mit konkretem Nutzen: möglicherweise positiv.
- Bedeutendes Upgrade mit erfolgreicher Umsetzung: möglicherweise positiv.
- Hack, regulatorisches Verbot oder schwerwiegender Exploit: negativ.
- Unbestätigtes Gerücht: niedrigeres Quellenvertrauen.
- Reine Meinungsartikel ohne neues Ereignis: niedriger Katalysatorwert.

#### 8.3 Aktualität

Die Aktualität muss anhand des Veröffentlichungsdatums bewertet werden.

| Alter der Nachricht | Faktor |
|---|---:|
| Bis 1 Stunde | 1,00 |
| Über 1 bis 3 Stunden | 0,90 |
| Über 3 bis 6 Stunden | 0,75 |
| Über 6 bis 12 Stunden | 0,55 |
| Über 12 bis 24 Stunden | 0,30 |
| Älter als 24 Stunden | 0,10 |

Wenn kein verlässliches Veröffentlichungsdatum vorhanden ist, einen konservativen Faktor verwenden und keine Aktualität erfinden.

#### 8.4 Quellenvertrauen

Die Quelle anhand ihrer Identifizierbarkeit, journalistischen Qualität und Nachprüfbarkeit bewerten.

| Quellenqualität | Faktor |
|---|---:|
| Hoch | 1,00 |
| Mittel | 0,70 |
| Niedrig | 0,40 |
| Nicht verifizierbar | 0,20 |

Keine Quelle allein aufgrund eines bekannten Namens als fehlerfrei betrachten.

#### 8.5 Coin-Relevanz

| Beziehung zum Ereignis | Faktor |
|---|---:|
| Direkte Betroffenheit | 1,00 |
| Starker, belegbarer indirekter Zusammenhang | 0,60 |
| Schwacher Zusammenhang | 0,25 |
| Kein nachvollziehbarer Zusammenhang | 0 |

Bei keinem nachvollziehbaren Zusammenhang erhält der Coin keine Punkte aus diesem Ereignis.

#### 8.6 Berechnung pro Ereignis

```text
EventScore =
Impact
× ImportanceFactor
× FreshnessFactor
× SourceTrustFactor
× CoinRelevanceFactor
```

Positive Werte unterstützen den Coin, negative Werte belasten ihn.

Die Importance wird nur einmal multipliziert.

#### 8.7 Gesamtscore eines Coins

Alle eigenständigen Ereignisse eines Coins werden zusammengeführt:

```text
RawScore = Sum(EventScore)
```

Anschließend wird der Score auf einen begrenzten Bereich transformiert:

```text
FinalScore = 100 × tanh(RawScore / 10)
```

Der Score liegt damit zwischen -100 und +100.

Der Score ist ein relativer News-Score und keine mathematisch berechnete Wahrscheinlichkeit für einen Kursanstieg.

### Schritt 9 – Top 5 auswählen

1. Alle Coins mit einem positiven `FinalScore` sortieren.
2. Höchsten Score zuerst.
3. Negative und neutrale Coins vollständig ausschließen.
4. Maximal fünf Coins auswählen.
5. Wenn nur zwei Coins einen positiven Score besitzen, nur diese zwei ausgeben.
6. Keine Coins künstlich ergänzen, um fünf Einträge zu erreichen.

Bei identischen Scores gilt folgende Reihenfolge:

1. Mehr direkte positive Ereignisse.
2. Höhere durchschnittliche Quellenqualität.
3. Höhere Aktualität der positiven Nachrichten.

### Schritt 10 – Ergebnis speichern

Die Ergebnisse in `today-coins.json` speichern.

Format:

```json
{
  "coins": [
    {
      "rank": 1,
      "coin_name": "Bitcoin",
      "symbol": "BTC",
      "score": 82.5,
      "reason": "Kurzfristig positive Nachrichtenlage durch mehrere relevante und glaubwürdige Ereignisse."
    }
  ]
}
```

Regeln:

- Nur die Top-5-Ergebnisse speichern.
- Keine negativen oder neutralen Coins aufnehmen.
- Keine Marktanalyse hinzufügen.
- Keine zusätzlichen Statistiken oder Debug-Daten speichern.
- Wenn kein Coin positiv bewertet wurde, eine leere Liste speichern:

```json
{
  "coins": []
}
```

Die Datei muss gültiges JSON enthalten.

Die Datei darf erst nach vollständig abgeschlossener Analyse überschrieben werden. Verwende einen temporären Speicherstand und einen atomaren Austausch, damit bei einem Schreibfehler die bisherige Datei erhalten bleibt.

## 5. Fehlerbehandlung

| Fehler | Verhalten |
|---|---|
| `news-results.json` fehlt | Vorgang abbrechen |
| JSON ungültig | Vorgang abbrechen, Originaldatei erhalten |
| `id` fehlt | Artikel überspringen |
| `url` fehlt | Artikel überspringen |
| Beschreibung bereits vorhanden | Skill 2 nicht aufrufen |
| Skill 2 meldet `failed` | Nächsten Artikel bearbeiten |
| Skill 2 antwortet nicht | Aufruf als fehlgeschlagen behandeln |
| Skill 2 speichert Beschreibung nicht | Keine erfolgreiche Anreicherung annehmen |
| Coin-Liste fehlt | Nur identifizierbare News-Coins verwenden |
| Keine positiven Coins | `{"coins":[]}` speichern |
| Fehler beim Schreiben | Alte Ausgabedatei erhalten |

Ein einzelner fehlgeschlagener Artikel darf nicht die Verarbeitung aller übrigen Artikel verhindern.

## 6. Abschlussregel

Der Skill ist erst fertig, wenn:

1. Alle relevanten Nachrichten geprüft wurden.
2. Alle erforderlichen Skill-2-Aufrufe abgeschlossen oder fehlgeschlagen sind.
3. Die aktualisierte News-Datei erneut geladen wurde.
4. Die Coin-Bewertung abgeschlossen ist.
5. `today-coins.json` erfolgreich gespeichert wurde.

**Die einzige fachliche Ausgabe ist die Top-5-Coin-Liste.**