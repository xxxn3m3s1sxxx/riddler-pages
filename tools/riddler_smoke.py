#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Riddler.io Verification Smoke Test (Playwright, Python)

BASELINE-FIRST design:
  - Run on the CURRENT (pre-redesign) index.html  -> captures BASELINE_FINGERPRINTS.json
  - Run again AFTER the redesign with --baseline BASELINE_FINGERPRINTS.json
    -> fails if any puzzle fingerprint changed (logic regression)

Checks:
  1. page loads, no console errors, no page errors
  2. all 7 puzzle sections populated after generate()
  3. determinism: same seed twice -> identical fingerprint (intra-run)
  4. cross-version determinism: fingerprint == baseline (when --baseline given)
  5. solved-pill mechanics (math puzzle: enter solution -> pill visible)
  6. URL sharing: shareBtn -> urlHint shows 'Link mit Seed ... kopiert'
  7. draft persistence: input 'mathInput' -> reload -> value restored
  8. @media print block present (static, via inline CSS scan)

Usage:
  python riddler_smoke.py <index.html> [--baseline fingerprints.json] [--seed 12345]
Exit: 0 = all checks passed, 1 = any check failed.

NOTE (redesign adaptivity):
  The redesign hides puzzles behind a mode toggle (math mode / puzzle ark).
  This script probes for a mode-switch control generically:
    - buttons with [data-mode] attribute, or
    - element with id containing 'mode' (id*="mode"), or
    - '.mode-btn' / '.ark' / '.puzzle-ark' class
  If found, it switches modes before asserting each puzzle group ("math" vs "ark")
  so the content checks cover BOTH modes. Absent such a control (baseline),
  all 7 sections are expected visible at once.
"""
import argparse
import json
import pathlib
import sys

# Windows console default (cp1252) cannot print '✓'/'→'; force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from playwright.sync_api import sync_playwright

P = pathlib.Path(__file__).resolve().parent

# Static CSS invariants that must survive the redesign
CSS_INVARIANTS = [
    "@media print",          # print stylesheet block intact
    "@page",                 # page size for PDF export
    ".print-line",           # blank answer lines for print
    ".print-logo",           # print logo img
    "#solutions",            # solutions legend (print-only)
]


def read_static_css(html: str) -> list[str]:
    m = []
    for inv in CSS_INVARIANTS:
        m.append(f"{'OK ' if inv in html else 'MISS'} static-css: {inv}")
    return m


def collect_fingerprint(page) -> dict:
    """Deterministic snapshot of every puzzle's rendered output for the current seed."""
    return page.evaluate(
        """() => {
            const txt = (id) => {
                const el = document.getElementById(id);
                return el ? el.innerText : null;
            };
            const cw = (() => {
                const g = document.getElementById('cwGrid');
                if (!g) return null;
                const cells = g.querySelectorAll('.cw-letter');
                const pattern = [];
                cells.forEach(c => {
                    pattern.push((c.dataset.r || '?') + ':' + (c.dataset.c || '?') + '=' + (c.dataset.solution || c.value || ''));
                });
                return { cellCount: cells.length, pattern: pattern.sort() };
            })();
            const sdk = (() => {
                const g = document.getElementById('sudokuGrid');
                if (!g) return null;
                const cells = g.querySelectorAll('.sdk-cell');
                return {
                    cellCount: cells.length,
                    values: Array.from(cells).map(c => c.dataset.solution || c.textContent || '')
                };
            })();
            const maze = (typeof mazeGrid !== 'undefined') ? JSON.stringify(mazeGrid) : null;
            const sdkSol = (typeof sdkUserCells !== 'undefined')
                ? Array.from(sdkUserCells).map(c => c.dataset.solution || '').join(',')
                : null;
            return {
                seed: (document.getElementById('seedInput') || {}).value || '',
                math: txt('mathDisplay'),
                math2: txt('mathDisplay2'),
                word: txt('wordTiles'),
                word2: txt('wordTiles2'),
                cw: cw,
                sdk: sdk,
                sdkSol: sdkSol,
                maze: maze,
                mathSolution: (typeof mathSolution !== 'undefined') ? mathSolution : null,
                mathSolution2: (typeof mathSolution2 !== 'undefined') ? mathSolution2 : null,
                wordSolution: (typeof wordSolution !== 'undefined') ? wordSolution : null,
                wordSolution2: (typeof wordSolution2 !== 'undefined') ? wordSolution2 : null,
            };
        }"""
    )


def has_mode_control(page) -> str | None:
    """Detect a mode toggle introduced by the redesign. Returns 'math'/'ark' or None if absent."""
    found = page.evaluate(
        """() => {
            const sel = ['[data-mode]', '[id*="mode" i]', '.mode-btn', '.puzzle-ark', '.ark-btn', '.panel-tab'];
            for (const s of sel) {
                const el = document.querySelector(s);
                if (el) return { selector: s, text: el.textContent.trim().slice(0, 40), count: document.querySelectorAll(s).length };
            }
            return null;
        }"""
    )
    return found


def switch_mode(page, target: str):
    """Try to activate the given mode. target in {'math', 'ark'}."""
    ok = page.evaluate(
        """(target) => {
            const els = document.querySelectorAll('[data-mode]');
            for (const el of els) {
                const v = (el.getAttribute('data-mode') || '').toLowerCase();
                if (v === target || (target === 'ark' && (v === 'puzzle-ark' || v === 'ark'))) {
                    el.click();
                    return true;
                }
            }
            const idEls = document.querySelectorAll('[id*="mode" i]');
            for (const el of idEls) {
                const v = (el.id || '').toLowerCase();
                if (v.includes(target)) { el.click(); return true; }
            }
            return false;
        }""",
        target,
    )
    if not ok:
        raise AssertionError(f"mode control for '{target}' not found/clickable")


def run_checks(args) -> int:
    failures: list[str] = []
    assertions_run = 0

    def check(cond: bool, name: str, detail: str = ""):
        nonlocal assertions_run
        assertions_run += 1
        if not cond:
            failures.append(f"FAIL: {name} {detail}".rstrip())
            print(f"  FAIL  {name} {detail}".rstrip())
        else:
            print(f"  ok    {name} {detail}".rstrip())

    html_src = pathlib.Path(args.file).read_text(encoding="utf-8")

    print(f"== static CSS invariants ({args.file}) ==")
    for line in read_static_css(html_src):
        print(" ", line, "(pass)" if line.startswith("OK") else "(FAIL)")
        if line.startswith("MISS"):
            failures.append("static-css: " + line)
    assertions_run += len(CSS_INVARIANTS)

    url = pathlib.Path(args.file).resolve().as_uri()
    print(f"== launching chromium on {url} ==")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = ctx.new_page()

        console_errors: list[str] = []
        page_errors: list[str] = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        page.goto(url, wait_until="load")
        page.wait_for_timeout(400)  # let DOMContentLoaded init + generate() settle

        # --- 1. load errors ---
        check(len(console_errors) == 0, "no console errors",
              "| ".join(console_errors[:5]) if console_errors else "")
        check(len(page_errors) == 0, "no page errors",
              "| ".join(page_errors[:5]) if page_errors else "")

        # --- 3. determinism (same seed twice within this run) ---
        seed = args.seed
        page.fill("#seedInput", str(seed))
        page.click("#genBtn")
        page.wait_for_timeout(200)
        fp1 = collect_fingerprint(page)

        page.fill("#seedInput", str(seed))
        page.click("#genBtn")
        page.wait_for_timeout(200)
        fp2 = collect_fingerprint(page)
        check(fp1 == fp2, "intra-run determinism seed=" + str(seed),
              "" if fp1 == fp2 else "→ fingerprints differ")

        # --- 2. puzzle sections populated (mode-aware) ---
        mode_ctrl = has_mode_control(page)
        print(f"  info  mode-control detected: {mode_ctrl}")
        groups = {"math": ["p-math", "p-math2"], "ark": ["p-word", "p-word2", "p-crossword", "p-maze", "p-sudoku"]}
        if mode_ctrl:
            for m in ("math", "ark"):
                switch_mode(page, m)
                page.wait_for_timeout(120)
                for pid in groups[m]:
                    populated = page.evaluate(
                        """(pid) => {
                            const el = document.getElementById(pid);
                            if (!el) return { exists: false };
                            const vis = el.offsetParent !== null;
                            const inner = el.innerText || '';
                            const kids = el.children.length;
                            return { exists: true, visible: vis, textLen: inner.length, children: kids };
                        }""",
                        pid,
                    )
                    check(populated["exists"] and populated["textLen"] > 3,
                          f"puzzle {pid} has content (mode={m})", json.dumps(populated, ensure_ascii=True))
        else:
            for pid in groups["math"] + groups["ark"]:
                populated = page.evaluate(
                    """(pid) => {
                        const el = document.getElementById(pid);
                        if (!el) return { exists: false };
                        const inner = el.innerText || '';
                        return { exists: true, textLen: inner.length, children: el.children.length };
                    }""",
                    pid,
                )
                check(populated["exists"] and populated["textLen"] > 3,
                      f"puzzle {pid} has content", json.dumps(populated, ensure_ascii=True))

        # grid-specific structural checks (count MATCHED elements, not descendants)
        grid_checks = {
            "cwGrid .cw-letter cells": "#cwGrid .cw-letter",
            "sudokuGrid .sdk-cell cells": "#sudokuGrid .sdk-cell",
            "wordTiles .tile tiles": "#wordTiles .tile",
            "wordTiles2 .tile tiles": "#wordTiles2 .tile",
            "mazeSvg exists": "#mazeSvg",
            "mazeSvg walls": "#mazeSvg line",
        }
        for name, sel in grid_checks.items():
            n = page.evaluate(
                """(sel) => document.querySelectorAll(sel).length""",
                sel,
            )
            check(n > 0, f"grid structure: {name}", f"({n} matched)")

        # maze SVG actually rendered (wall lines present; canvas->SVG migration c58e582)
        painted = page.evaluate(
            """() => {
                const s = document.getElementById('mazeSvg');
                if (!s) return -1;
                return s.querySelectorAll('line').length;
            }"""
        )
        check(painted > 0, "mazeSvg painted", f"({painted} wall lines)")

        # --- 4. cross-version determinism vs baseline ---
        if args.baseline:
            base_raw = json.loads(pathlib.Path(args.baseline).read_text(encoding="utf-8"))
            base_fp = base_raw.get("fingerprint", base_raw)  # handle wrapper {seed,diff,fingerprint} or flat
            cur = collect_fingerprint(page)
            diffs = [k for k in base_fp if json.dumps(base_fp[k], sort_keys=True, ensure_ascii=True) != json.dumps(cur.get(k), sort_keys=True, ensure_ascii=True)]
            check(not diffs, "cross-version determinism vs baseline", f"changed keys: {diffs}" if diffs else "")
            if diffs:
                for k in diffs:
                    print(f"    baseline {k}: {json.dumps(base_fp[k], ensure_ascii=True)[:200]}")
                    print(f"    current  {k}: {json.dumps(cur.get(k), ensure_ascii=True)[:200]}")

        # --- 4b. emulated print: all 7 puzzles + solutions must be printable ---
        page.emulate_media(media="print")
        page.wait_for_timeout(120)
        if mode_ctrl:
            # whichever mode is selected, print must STILL expose every puzzle card
            for m in ("math", "ark"):
                switch_mode(page, m)
                page.wait_for_timeout(80)
            # leave ark active, then assert all cards visible in print regardless
        print_state = page.evaluate(
            """() => {
                const ids = ['p-math','p-word','p-word2','p-crossword','p-maze','p-sudoku','p-math2','solutions'];
                const out = {};
                for (const id of ids) {
                    const el = document.getElementById(id);
                    if (!el) { out[id] = 'MISSING'; continue; }
                    const cs = getComputedStyle(el);
                    out[id] = { display: cs.display, visible: el.offsetParent !== null };
                }
                const pl = document.querySelector('.print-line');
                const ctl = document.querySelector('.panel, .btn, #seedInput, .seg, .result');
                return {
                    cards: out,
                    printLineDisplay: pl ? getComputedStyle(pl).display : null,
                    controlsVisible: ctl ? ctl.offsetParent !== null : null,
                };
            }"""
        )
        for pid, st in print_state["cards"].items():
            ok = st != "MISSING" and st["visible"]
            check(ok, f"print media: {pid} visible", json.dumps(st, ensure_ascii=True))
        check(print_state["printLineDisplay"] == "block",
              "print media: .print-line display:block", f"(got {print_state['printLineDisplay']})")
        check(print_state["controlsVisible"] is False,
              "print media: controls hidden", f"(controls visible={print_state['controlsVisible']})")
        page.emulate_media(media="screen")

        # --- 4c. palette + footer statics ---
        lime_old = html_src.count("#7CFF2A")
        lime_new = html_src.count("#6EFF3A")
        purple = html_src.count("#B026FF")
        print(f"  info  palette occurrences: #7CFF2A(old lime)={lime_old}  #6EFF3A(new lime)={lime_new}  #B026FF={purple}")
        footer_new = "A Riddle A Day Keeps The Knight Away" in html_src
        check(footer_new, "footer carries new signature text",
              "(baseline: runs the old copyright block; after redesign this must flip to pass)")

        # --- 5. solved-pill mechanics (math puzzle) ---
        page.click("#genBtn")
        page.wait_for_timeout(150)
        sol = page.evaluate("typeof mathSolution !== 'undefined' ? mathSolution : null")
        if sol is not None:
            page.fill("#mathInput", str(sol))
            page.click("#mathCheck")
            page.wait_for_timeout(150)
            pill_visible = page.evaluate(
                """() => {
                    const el = document.getElementById('solved-math');
                    return el ? !el.classList.contains('hidden') : null;
                }"""
            )
            check(pill_visible is True, "solved-math pill becomes visible after correct answer",
                  f"(mathSolution={sol})")
            res_txt = page.evaluate("document.getElementById('mathResult').textContent")
            check(len(res_txt) > 0, "mathResult shows feedback")
        else:
            print("  warn  skipped pill test (mathSolution not readable)")

        # --- 6. URL sharing ---
        page.fill("#seedInput", str(seed))
        page.click("#shareBtn")
        page.wait_for_timeout(300)
        hint_txt = page.evaluate(
            """() => {
                const h = document.getElementById('urlHint');
                return h ? h.textContent : '';
            }"""
        )
        check("Link mit Seed" in hint_txt and str(seed) in hint_txt,
              "shareBtn URL sharing feedback", f"urlHint={hint_txt!r}")
        # clipboard content (chromium grants clipboard-read in this context)
        clip = page.evaluate("navigator.clipboard.readText().catch(() => '')")
        check("?seed=" in clip, "clipboard holds share URL", f"clip={clip!r}")

        # --- 7. draft persistence (reload MUST carry ?seed= so the draft key matches) ---
        page.fill("#seedInput", str(seed))
        page.click("#genBtn")
        page.wait_for_timeout(150)
        page.fill("#mathInput", "42")
        page.dispatch_event("#mathInput", "input")   # triggers saveDraft via window listener
        page.goto(url + "?seed=" + str(seed), wait_until="load")
        page.wait_for_timeout(400)
        got = page.evaluate("document.getElementById('mathInput').value")
        check(got == "42", "draft persisted across reload", f"(mathInput={got!r})")

        browser.close()

    print(f"\n== {assertions_run} assertions, {len(failures)} failures ==")
    for f in failures:
        print("  " + f)
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="path to index.html")
    ap.add_argument("--baseline", help="path to BASELINE_FINGERPRINTS.json for cross-version determinism")
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--emit-baseline", help="also write current fingerprints to this json file")
    args = ap.parse_args()

    rc = run_checks(args)
    if args.emit_baseline:
        # re-collect fingerprints in a minimal second pass to emit baseline json
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context()
            page = ctx.new_page()
            url = pathlib.Path(args.file).resolve().as_uri()
            page.goto(url, wait_until="load")
            page.wait_for_timeout(400)
            page.fill("#seedInput", str(args.seed))
            page.click("#genBtn")
            page.wait_for_timeout(200)
            fp = collect_fingerprint(page)
            pathlib.Path(args.emit_baseline).write_text(
                json.dumps({"seed": args.seed, "diff": "medium", "fingerprint": fp},
                           ensure_ascii=True, indent=2),
                encoding="utf-8")
            browser.close()
        print("baseline written to", args.emit_baseline)
    sys.exit(rc)


if __name__ == "__main__":
    main()