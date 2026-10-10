# FixMate AI — Edge-Case Test Log (Hardening Wave)

Date: 2026-10-10. Knowledge base expanded: 9 → 15 error codes
(added E40, E41, E50, E51, E66, E67); adversarial battery 12 → 20 cases.
Rule: every documented code gets a real guided path; every undocumented
code gets the honest "undocumented → knowledge-gap → escalate to senior
tech" path. Repair procedures are never invented.

## 20 adversarial cases — all pass

| # | Input | Result |
|---|-------|--------|
| 1 | "E999" (unknown code) | knowledge-gap → escalate ✓ |
| 2 | "XYZ" (unknown code) | knowledge-gap → escalate ✓ |
| 3 | "" (empty code) | asks for a code, no crash ✓ |
| 4 | "e17" (lowercase) | normalized → E17 guided path ✓ |
| 5 | "e 40" (space + lowercase) | normalized → E40 ✓ |
| 6 | "  E51  " (whitespace) | normalized → E51 ✓ |
| 7 | "E17!" (trailing punctuation) | normalized → E17 ✓ |
| 8 | "E" + "9"×1000 (very long) | knowledge-gap, no hang ✓ |
| 9 | "🚨" emoji-only | knowledge-gap ✓ |
| 10 | "E40" on the WRONG model (CP-200 vs CP-420) | honest mismatch: code is documented on another model, not this one ✓ |
| 11 | wrong model picker, valid code for another model | mismatch path ✓ |
| 12 | "E-17" (dash) | knowledge-gap, no crash ✓ |
| 13 | "E17 E22" (two codes) | first recognized code used ✓ |
| 14 | "my printer shows e41" | normalized → E41 ✓ |
| 15 | "E1O" (letter O vs zero) | knowledge-gap, no false match ✓ |
| 16 | "E01" leading zero | knowledge-gap ✓ |
| 17 | "E66" new code | guided path ✓ |
| 18 | "E67" new code | guided path ✓ |
| 19 | "E50" new code | guided path ✓ |
| 20 | "E51" new code | guided path ✓ |

## HTTP robustness (all endpoints, 6 hostile inputs each)
- Empty body, malformed JSON, JSON array/string, wrong types, 10KB junk,
  null bytes, no Content-Length, rapid double-submit: HTTP 200 always,
  zero 500s, zero tracebacks in server logs.

## Failures found and fixed
1. Malformed JSON dropped the connection — fixed in `_read_json`
   (try/except → empty params; same fix landed in build_apps.py template).
2. Model-picker mismatch now reports honestly instead of silently running
   the wrong model's path.

## Pushed
ynpreet/fixmate-ai @ main — "Harden: expanded data + adversarial edge-case tests"
