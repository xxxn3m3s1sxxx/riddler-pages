# Riddler

Seed-basierte Rätselbox — 5 Rätseltypen, deterministisch generiert aus einem Integer-Seed.

## Features
- **Symbol-Arithmetik** — Symbole → Zahlen
- **Buchstabensalat** — Anagramm entschlüsseln
- **Kreuzworträtsel** — Template-basiert
- **Labyrinth** — Recursive-Backtracker, per Pfeiltasten spielbar
- **Sudoku** — Rotation + seed-gesteuertes Löschen

## Nutzung
- **Gleicher Seed = gleiches Rätsel** — deterministisch über `Mulberry32`
- **Rätsel des Tages**: leeres Eingabefeld lädt automatisch den aktuellen Datums-Seed (YYYYMMDD)
- **Schwierigkeitsgrade**: Easy → Extreme steuern Zahlenräume, Wortlängen und sichtbare Sudoku-Zellen
- **Drucken / PDF**: Sauberes DIN-A4-Print-Layout ohne Lösungen

## Live
https://xxxn3m3s1sxxx.github.io/riddler/