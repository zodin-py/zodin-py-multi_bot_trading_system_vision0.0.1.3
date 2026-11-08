# Feature Specification: Left Chart Toolbar – MultiTradingBot

## 1. Ziel

Implementiere eine vertikale Werkzeugleiste auf der linken Seite des bestehenden Charts im MultiTradingBot.

Die Toolbar soll sich optisch und funktional an der bereitgestellten Referenz (TradingView Drawing Toolbar) orientieren.

**WICHTIG:**
- Der bestehende Chart ist bereits vollständig implementiert und funktionsfähig.
- Die Chart-Engine darf nicht ersetzt oder neu implementiert werden.
- Bestehende Chart-Funktionen, Indikatoren, Datenfeeds, Zoom, Scrolling und Interaktionen müssen erhalten bleiben.
- Es soll ausschließlich die linke Toolbar ergänzt und mit dem bestehenden Chart verbunden werden.

## 2. Position und Design

Die Toolbar wird direkt links innerhalb des Chart-Bereichs positioniert.

### Layout
- Vertikale Anordnung.
- Feste Breite: ca. 48–52 px.
- Höhe: 100 % des verfügbaren Chart-Bereichs.
- Dunkler Hintergrund passend zum bestehenden Dark Theme.
- Dezente rechte Trennlinie zum Chart.
- Icons mittig ausgerichtet.
- Einheitliche Abstände zwischen den Icons.
- Toolbar bleibt beim Scrollen und Zoomen des Charts an ihrer Position.
- Responsive Verhalten für unterschiedliche Bildschirmgrößen.

### Design-Stil
- Minimalistisches TradingView-inspiriertes Design.
- Kleine, dezente Icons.
- Keine großen Beschriftungen.
- Aktives Werkzeug bekommt einen deutlich sichtbaren Hintergrund.
- Hover-Effekt für jedes Icon.
- Tooltips beim Darüberfahren mit der Maus.
- Dezente Trennlinien zwischen zusammengehörigen Werkzeuggruppen.

## 3. Aufbau der Toolbar

Die Reihenfolge soll sich an der Referenz orientieren.

### Gruppe 1 – Auswahl

1. **Cursor / Select Tool**
   - Standardmäßig aktiviert.
   - Auswahl und Verschieben vorhandener Zeichnungen.
   - Auswahl von Chart-Objekten.

2. **Favorites**
   - Häufig verwendete Werkzeuge als Favoriten verwalten.
   - Favoriten-Menü öffnen.
   - Werkzeuge können hinzugefügt und entfernt werden.

### Gruppe 2 – Drawing Tools

3. **Trend Line**
   - Zeichnen von diagonalen Trendlinien.
   - Start- und Endpunkt durch Mausklick festlegen.

4. **Horizontal Line / Levels**
   - Horizontale Linien auf bestimmten Preisniveaus zeichnen.
   - Unterstützung für Support- und Resistance-Level.

5. **Fibonacci Tools**
   - Fibonacci-Retracement zeichnen.
   - Automatische Berechnung der Fibonacci-Level.
   - Darstellung der Level direkt im Chart.

6. **Geometric / Pattern Tools**
   - Zeichnen geometrischer Formen und Muster.
   - Erweiterbar für weitere Pattern-Werkzeuge.

### Gruppe 3 – Trading Tools

7. **Long / Short Position Tool**
   - Long- und Short-Positionen grafisch im Chart darstellen.
   - Entry-Preis definieren.
   - Stop-Loss definieren.
   - Take-Profit definieren.
   - Risk/Reward-Verhältnis anzeigen.
   - Gewinn- und Verlustbereiche visuell unterscheiden.

8. **Rectangle Tool**
   - Rechtecke im Chart zeichnen.
   - Für Support-/Resistance-Zonen und Supply-/Demand-Zonen verwenden.

### Gruppe 4 – Zeichenoptionen

9. **Magnet Mode**
   - Wenn aktiviert, werden Zeichnungspunkte automatisch an nahegelegene Candlestick-Preise bzw. relevante Chart-Punkte angepasst.
   - Ein- und ausschaltbar.

10. **Visibility**
    - Zeichnungen im Chart ein- und ausblenden.
    - Erneutes Aktivieren stellt die Zeichnungen wieder dar.

### Gruppe 5 – Aktionen

11. **Undo**
    - Letzte Zeichenaktion rückgängig machen.

12. **Delete**
    - Ausgewähltes Zeichenobjekt löschen.
    - Bei Bedarf alle Zeichnungen löschen (mit Sicherheitsabfrage).

## 4. Funktionales Verhalten

### Werkzeugauswahl
- Immer nur ein aktives Zeichenwerkzeug gleichzeitig.
- Das ausgewählte Werkzeug wird visuell hervorgehoben.
- Beim Wechsel des Werkzeugs wird das vorherige Werkzeug deaktiviert.
- Cursor-Darstellung entsprechend dem aktiven Werkzeug anpassen.
- ESC beendet den aktuellen Zeichenmodus und aktiviert Select.

### Zeichnen
- Zeichnungen müssen direkt im vorhandenen Chart erfolgen.
- Zeichnungen müssen an die tatsächlichen Preis- und Zeitkoordinaten des Charts gebunden sein.
- Beim Zoomen und Verschieben müssen sie korrekt an ihrer Position bleiben.
- Zeichnungen dürfen nicht an festen Bildschirmkoordinaten gespeichert werden.

### Speicherung
- Zeichnungen sollen beim Wechsel des Timeframes erhalten bleiben.
- Zeichnungen sollen beim Wechsel des Symbols nicht versehentlich auf andere Märkte übertragen werden.
- Zeichnungsdaten sollen dem jeweiligen Symbol und Timeframe bzw. Chart-Kontext zugeordnet werden.
- Falls bereits ein Persistenzsystem existiert, dieses wiederverwenden.

## 5. Technische Anforderungen

- Zuerst die bestehende Chart-Architektur analysieren.
- Vorhandene Chart-API und Drawing-Funktionen wiederverwenden.
- Keine zweite Chart-Instanz erstellen.
- Keine unnötigen Änderungen an bestehenden Komponenten.
- Toolbar als eigenständige, wiederverwendbare UI-Komponente implementieren.
- Werkzeugzustand zentral verwalten.
- Drawing-Logik möglichst modular aufbauen.
- Icons aus der bereits verwendeten Icon-Bibliothek verwenden.
- Keine zusätzlichen Abhängigkeiten installieren, wenn die bestehende Technologie ausreicht.

## 6. UX-Anforderungen

- Toolbar muss sich wie ein nativer Bestandteil des Charts anfühlen.
- Keine Überlagerung wichtiger Chart-Elemente.
- Werkzeugauswahl muss sofort visuell erkennbar sein.
- Tooltips sollen die Werkzeugnamen anzeigen.
- Klicks auf die Toolbar dürfen keine unbeabsichtigten Chart-Aktionen auslösen.
- Zeichnen, Zoomen, Panning und Auswahl müssen sauber voneinander getrennt sein.

## 7. Akzeptanzkriterien

Die Implementierung gilt als abgeschlossen, wenn:

- [ ] Die linke Toolbar entsprechend der Referenz angezeigt wird.
- [ ] Die Toolbar innerhalb des vorhandenen Chart-Bereichs sitzt.
- [ ] Alle Icons Tooltips besitzen.
- [ ] Die Werkzeugauswahl funktioniert.
- [ ] Aktive Werkzeuge visuell hervorgehoben werden.
- [ ] Zeichnungen korrekt im vorhandenen Chart erstellt werden.
- [ ] Zeichnungen beim Zoomen und Verschieben korrekt positioniert bleiben.
- [ ] Undo und Delete funktionieren.
- [ ] Magnet und Visibility funktionieren.
- [ ] Der bestehende Chart weiterhin vollständig funktioniert.
- [ ] Es keine Regressionen bei bestehenden Chart-Funktionen gibt.

## 8. Scope und Priorität

**Priorität 1:** Toolbar-Layout, Positionierung, Design und Werkzeugauswahl.

**Priorität 2:** Trendline, Horizontal Line, Rectangle und Long/Short Position.

**Priorität 3:** Fibonacci, Magnet, Visibility, Undo und Delete.

**Priorität 4:** Speicherung und Wiederherstellung der Zeichnungen.

**Abschließende Anweisung:**

Arbeite ausschließlich an der Erweiterung des bestehenden Charts. Analysiere zuerst die vorhandenen Komponenten und die verwendete Chart-Library. Passe die Implementierung an die bestehende Architektur an. Verändere keine bereits funktionierenden Chart-Funktionen und führe keine unnötige Refaktorierung durch.