# TEST-LOG.md — Determinism verification

**Date:** 2026-10-10
**Command:** `python3 demo.py` (10 consecutive runs, same machine, same session)
**Method:** each run's stdout+stderr captured to a file; recorded exit code and SHA-256 of full output.

| Run | Exit code | SHA-256 of output | Result |
|-----|-----------|-------------------|--------|
| 1 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 2 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 3 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 4 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 5 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 6 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 7 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 8 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 9 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |
| 10 | 0 | `b295c47c25b60b4ecf8bce907622e2b4ae9989331c82f620dabe8b184fe8c1d0` | PASS |

**Result: 10/10 PASS** — exit code 0 and byte-identical output on every run.

Determinism sources: no timestamps, no `random`, no network; all dict
iteration over sorted keys; ticket IDs from a deterministic counter;
authorization tokens from SHA-256 of fixed inputs.


---

# Web UI test log

**Date:** 2026-10-10
**What:** `app.py` (stdlib-only `http.server` web UI, port 8006, localhost) — 12 consecutive end-to-end rounds.

**Method (each round):**
1. `python3 demo.py` — must exit 0 and produce byte-identical stdout
   (SHA-256 compared across all 12 rounds).
2. Start `python3 app.py` in the background; then:
   - `GET http://localhost:8006/` → HTTP 200, page contains title + demo JS
   - `GET http://localhost:8006/api/run` → HTTP 200, JSON `{"ok": true}`,
     output contains all markers: `SCENARIO A/B/C`, `[PLAN]`, `[TOOL]`,
     `[SAFETY]`, `EVALUATION -- FixMate`, `Internal-doc accuracy`, `FM-2026-`
3. Kill the server; repeat.

Also verified separately: unknown path → 404; second `python3 app.py`
while port 8006 is held → clear "could not bind 127.0.0.1:8006 — Address
already in use" error with a fix hint, exit code 2.

**Result: 12/12 PASS** — no failures, no flakiness found, no fixes required.

Determinism held: demo.py output SHA-256 identical on all 12 rounds
(evaluation excluded — `app.py` only reads the file, never changes it).
