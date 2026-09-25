# Riddler

Seed-basierte Rätselbox — 5 Rätseltypen (8 Rätsel pro Seed), deterministisch generiert aus einem Integer-Seed.

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
- **Drucken / PDF**: Sauberes DIN-A4-Print-Layout mit kompakter Lösungsleiste (aufrecht) und horizontalem Labyrinth

## Live
https://xxxn3m3s1sxxx.github.io/riddler-pages/

## Direkt-Links
- **Spielen (Seed 17071986):** https://xxxn3m3s1sxxx.github.io/riddler-pages/index.html?seed=17071986
- **Drucken / PDF (Seed 17071986):** https://xxxn3m3s1sxxx.github.io/riddler-pages/index.html?seed=17071986&print=1

## Verifikation (Smoke-Test)

Setup: `pip install playwright && python -m playwright install chromium`

```bash
# 1) Smoke gegen die eingecheckte Baseline — Seed wird aus der Baseline gelesen (17071986)
python tools/riddler_smoke.py index.html --baseline tools/BASELINE_FINGERPRINTS.json

# 2) Expliziter Seed überschreibt den Baseline-Seed
python tools/riddler_smoke.py index.html --baseline tools/BASELINE_FINGERPRINTS.json --seed 12345

# 3) Baseline neu erzeugen — bestehende Datei nur mit --force überschreiben
python tools/riddler_smoke.py index.html --emit-baseline tools/BASELINE_FINGERPRINTS.json --seed 17071986 --force
```

**Erneute Erzeugung vor dem Commit prüfen:** Nach Schritt 3 ist verpflichtend:
1. `git diff -- tools/BASELINE_FINGERPRINTS.json` ausführen und bestätigen, dass nur beabsichtigte Fingerprint-Ergänzungen/-Änderungen erscheinen.
2. `python tools/riddler_smoke.py index.html --baseline tools/BASELINE_FINGERPRINTS.json` erneut ausführen.

**Seed-Regel:** explizites `--seed` gewinnt, sonst der in `--baseline` hinterlegte Seed (aktuell 17071986), sonst `12345`. Ohne `--seed` und ohne `--baseline` läuft der lokale Smoke-Test mit `12345`; ein Baseline-Vergleich findet nur mit `--baseline` statt.

Exit-Codes: `0` alle Checks grün · `1` Check fehlgeschlagen · `2` Überschreiben verweigert (fehlendes `--force`).

Abgedeckt sind alle 8 Rätsel-Sektionen, das Print-Layout und die 15 Fingerprint-Keys der Baseline (inkl. `word3`/`wordSolution3`).