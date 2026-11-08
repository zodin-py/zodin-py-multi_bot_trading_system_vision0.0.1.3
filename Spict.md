# SPECIFICATION: Interactive TradingView-Style Candlestick Chart

## 1. Ziel des Features

Der aktuell implementierte Candlestick-Chart zeigt die Kerzen bereits korrekt an, ist aber statisch.

Ich möchte diesen Chart in einen vollständig interaktiven Trading-Chart umwandeln, dessen Bedienung sich möglichst ähnlich wie TradingView anfühlt.

**Wichtig:** Der bestehende Chart und die bereits funktionierende Binance-Datenverbindung sollen erhalten bleiben. Es geht um eine Erweiterung des bestehenden Systems, nicht um eine komplette Neuentwicklung.

## 2. Interaktive Chart-Steuerung

Implementiere folgende Funktionen:

### 2.1 Drag & Pan
- Mit der linken Maustaste den Chart greifen und horizontal verschieben.
- Historische Kerzen links sichtbar machen.
- Zu neueren Kerzen rechts navigieren.
- Vertikales Verschieben der Preisskala ermöglichen.
- Flüssige Bewegung ohne Verzögerungen.
- Kein automatisches Zurückspringen während der manuellen Navigation.

### 2.2 Zoom
- Mausrad zum Hinein- und Herauszoomen.
- Zoom soll sich an der aktuellen Mausposition orientieren.
- Beim Hineinzoomen werden weniger Kerzen mit mehr Details angezeigt.
- Beim Herauszoomen werden mehr historische Kerzen angezeigt.
- Zoom auf der Zeitachse und Preisskala ermöglichen.
- Optional Buttons für Zoom In, Zoom Out und Reset View.

### 2.3 Crosshair
Wenn ich mit der Maus über den Chart fahre:
- Eine vertikale Linie zeigt die Position der jeweiligen Kerze.
- Eine horizontale Linie zeigt das aktuelle Preisniveau.
- Angezeigte Informationen:
  - Open
  - High
  - Low
  - Close
  - Volume
  - Zeitstempel
- Preis und Zeit sollen sich dynamisch mit dem Crosshair aktualisieren.

### 2.4 Zeitachse
- Datum und Uhrzeit unterhalb des Charts anzeigen.
- Beim Zoomen die Zeitbeschriftung dynamisch anpassen.
- Historische Zeiträume korrekt darstellen.
- Keine überlappenden Zeitbeschriftungen.

### 2.5 Preisskala
- Preisachse rechts neben dem Chart.
- Dynamische Anpassung der Preisskala beim Zoomen und Verschieben.
- Aktuellen Preis deutlich markieren.
- Automatische Skalierung als Option.
- Manuelle Skalierung ermöglichen.

## 3. Chart-Darstellung

Die Darstellung soll professionell und TradingView-ähnlich sein.

Folgende Elemente sollen vorhanden sein:

- Grüne Kerzen für steigende Kurse.
- Rote Kerzen für fallende Kurse.
- Dochte (Wicks) korrekt darstellen.
- Dezentes Hintergrund-Grid.
- Preisachse rechts.
- Zeitachse unten.
- Volume-Bars unterhalb des Hauptcharts.
- Aktueller Preis als horizontale Linie.
- Klare und gut lesbare Schrift.
- Dark Mode passend zu einem Trading-Dashboard.

## 4. Datenintegration

Die vorhandene Binance-Verbindung muss weiterhin verwendet werden.

Die Chart-Komponente soll die bereits gespeicherten historischen Candlestick-Daten nutzen.

Anforderungen:

- Bis zu 1000 historische Kerzen laden und darstellen.
- Neue Daten nur nach dem Schließen einer Kerze übernehmen.
- Keine unvollständigen Kerzen in die historische Datenbasis schreiben.
- Beim Navigieren durch historische Daten keine unnötigen API-Anfragen auslösen.
- Beim Erreichen des ältesten geladenen Datenbereichs optional weitere historische Kerzen nachladen.
- Bereits geladene Daten lokal verwenden.

**Wichtig:** Die Chart-Navigation darf die Binance-Datenaktualisierung nicht beeinflussen.

## 5. Live-Update-Verhalten

Der Chart soll automatisch aktuell bleiben.

- Neue geschlossene Kerzen werden am rechten Rand hinzugefügt.
- Die aktuelle Ansicht bleibt erhalten, wenn der Benutzer historische Daten betrachtet.
- Wenn der Benutzer am rechten Rand ist und dem aktuellen Markt folgt, soll der Chart automatisch mit neuen Kerzen weiterlaufen.
- Wenn der Benutzer manuell nach links navigiert, darf der Chart nicht automatisch zurück zur neuesten Kerze springen.
- Eine Schaltfläche "Go to Live" soll jederzeit zur neuesten Kerze zurückführen.

## 6. Interaktionsdetails

Implementiere zusätzlich:

- Doppelklick auf den Chart: Reset der Ansicht.
- Doppelklick auf die Preisskala: automatische Preisskalierung.
- Drag auf der Preisskala: vertikales Verschieben.
- Drag auf der Zeitachse: horizontales Verschieben.
- Responsive Darstellung bei Größenänderung des Browserfensters.
- Sinnvolle Mauszeiger (Grab/Grabbing).
- Smoothes Rendering ohne unnötige Re-Renders.

## 7. Technische Anforderungen

Untersuche zuerst die vorhandene Projektstruktur.

Finde heraus:
- Welche Bibliothek aktuell für Candlestick-Charts verwendet wird.
- Wie die historischen Kerzen gespeichert werden.
- Wie die Binance-Daten an den Chart übergeben werden.
- Wie die Chart-Komponente in das bestehende Frontend eingebunden ist.

Prüfe anschließend, ob die vorhandene Bibliothek die benötigten Interaktionen unterstützt.

Falls die aktuelle Bibliothek dafür ungeeignet ist, prüfe bevorzugt:

**TradingView Lightweight Charts**

Dokumentation: https://www.tradingview.com/lightweight-charts/

Alternativ kann eine andere geeignete Bibliothek verwendet werden, wenn sie die Anforderungen besser erfüllt.

Keine unnötige Migration des gesamten Frontends.

## 8. Performance

Der Chart muss auch mit 1000 oder mehr Candlesticks flüssig funktionieren.

- Keine unnötigen kompletten Chart-Neuberechnungen.
- Nur neue Datenpunkte aktualisieren, wenn möglich.
- Keine unnötigen API-Requests.
- Pan und Zoom müssen flüssig sein.
- Daten und Darstellung sauber voneinander trennen.
- Keine Verzögerungen bei Mausbewegungen.

## 9. Architektur

Trenne die Verantwortlichkeiten sauber:

1. **Data Layer:** Historische und neue Binance-Kerzen.
2. **Chart Layer:** Candlestick-Darstellung.
3. **Interaction Layer:** Pan, Zoom, Crosshair und Navigation.
4. **Update Layer:** Aktualisierung nach Kerzenschluss.

Die Chart-Interaktionen dürfen nicht direkt die Binance-Daten verändern.

## 10. Akzeptanzkriterien

Das Feature gilt erst als fertig, wenn alle folgenden Punkte funktionieren:

- [ ] Chart lässt sich horizontal mit der Maus verschieben.
- [ ] Historische Candlesticks können betrachtet werden.
- [ ] Mausrad-Zoom funktioniert.
- [ ] Zoom orientiert sich an der Mausposition.
- [ ] Crosshair zeigt korrekte OHLCV-Daten.
- [ ] Zeitachse passt sich dem Zoom an.
- [ ] Preisskala lässt sich verschieben.
- [ ] Volume wird unter dem Candlestick-Chart angezeigt.
- [ ] Neue geschlossene Kerzen werden automatisch ergänzt.
- [ ] Historische Navigation wird durch Live-Updates nicht unterbrochen.
- [ ] Go to Live funktioniert.
- [ ] Reset View funktioniert.
- [ ] Chart bleibt bei 1000+ Kerzen performant.
- [ ] Bestehende Binance-Verbindung funktioniert weiterhin.

## 11. Arbeitsweise

Arbeite in folgenden Phasen:

**Phase 1 – Analyse**
Untersuche das bestehende Projekt und identifiziere die aktuelle Chart-Implementierung.

**Phase 2 – Technische Entscheidung**
Entscheide, ob die vorhandene Bibliothek erweitert werden kann oder eine andere Chart-Bibliothek sinnvoller ist.

**Phase 3 – Implementierung**
Implementiere die Interaktionen und das TradingView-ähnliche Verhalten.

**Phase 4 – Integration**
Verbinde den interaktiven Chart mit der bestehenden Binance-Datenquelle.

**Phase 5 – Tests**
Teste sämtliche Interaktionen und das Verhalten bei Live-Updates.

**Phase 6 – Dokumentation**
Dokumentiere die geänderten Dateien, die Architektur und die Bedienung.

### Wichtige Regeln

- Bestehende Funktionen nicht zerstören.
- Keine unnötige Änderung an der Binance-Integration.
- Keine Fake-Daten verwenden.
- Keine Funktionen nur visuell simulieren.
- Bestehenden Code zuerst verstehen, dann verändern.
- Bei Problemen die Ursache analysieren, statt Workarounds einzubauen.
- Änderungen schrittweise und nachvollziehbar durchführen.

**Endziel:** Ein professioneller, flüssiger, interaktiver Kryptowährungs-Candlestick-Chart, der sich in der Bedienung möglichst nah an TradingView orientiert.