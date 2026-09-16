# Riddler

Seed-basierte Rätselbox — 5 Rätseltypen, deterministisch generiert aus einem Integer-Seed.

## Features
- **Symbol-Arithmetik** — Symbole → Zahlen
- **Buchstabensalat** — Anagramm entschlüsseln
- **Kreuzworträtsel** — deterministischer Lexikon-Fill (CSP) mit DE/EN-Umschalter und NYT-Nummerierung
- **Labyrinth** — Recursive-Backtracker (16×10), per Pfeiltasten spielbar, auch im Druck horizontal
- **Sudoku** — Rotation + seed-gesteuertes Löschen

## Nutzung
- **Gleicher Seed = gleiches Rätsel** — deterministisch über `Mulberry32`
- **Rätsel des Tages**: leeres Eingabefeld lädt automatisch den aktuellen Datums-Seed (YYYYMMDD)
- **Schwierigkeitsgrade**: Easy → Extreme steuern Zahlenräume, Wortlängen und sichtbare Sudoku-Zellen
- **Drucken / PDF**: Sauberes DIN-A4-Print-Layout mit kompakter Lösungsleiste (aufrecht) und hochkantem Labyrinth

## Live
https://xxxn3m3s1sxxx.github.io/riddler-pages/

## Direkt-Links
- **Spielen (Seed 17071986):** https://xxxn3m3s1sxxx.github.io/riddler-pages/index.html?seed=17071986
- **Drucken / PDF (Seed 17071986):** https://xxxn3m3s1sxxx.github.io/riddler-pages/index.html?seed=17071986&print=1