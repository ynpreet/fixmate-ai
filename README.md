# FixMate AI — The Intelligent Equipment Maintenance Agent

**Tagline:** *Diagnose faster. Fix smarter. Keep every store running.*

Demo 6 of 6, Agentic AI Workshop.

> **FICTIONAL:** BrewPoint Retail is a fictional company, invented for this
> demo so the story feels real without tying to any real business. Every
> machine, manual, error code, part, store, and person in this demo is
> synthetic.

---

> **🚀 OPEN IN CHROME (live demo):**
>
> ```bash
> cd ~/workspace/agentic-ai-workshop/fixmate-ai
> python3 app.py
> ```
>
> then open **http://localhost:8006** in Google Chrome and click
> **"Run live demo"**. The agent's plan → tool → observe trace renders with
> highlighted plans, tool calls, and safety gates, plus a scored
> results table. Stdlib only, fully offline — `app.py` runs `demo.py`
> on your machine and shows its (byte-identical) output in the browser.

---

## Real-world problem, target users, market need, and differentiation

**The problem.** It's 7 a.m. at a BrewPoint Retail convenience store. The
coffee machine is down, the display says **Error E17**, and customers are
arriving. The store manager doesn't know what E17 means, which part it
needs, or whether a technician is required. Today, that manager flips
through a binder, calls a district supervisor, and loses the morning coffee
rush.

**Target users.** Frontline store employees and shift supervisors at
multi-site retail/food-service chains — the people who face broken
equipment first and know the manuals least.

**Market need.** Equipment downtime is lost revenue, but the bigger cost is
*unsafe* fixes: a store employee walking through a 120-volt repair because
a search result said so. The need is instant access to maintenance
knowledge that is **cited** (from the actual manual, the current version),
**safety-gated** (some procedures are technician-only, full stop), and
**honest about gaps** (when the manual lacks the answer, it says so and
escalates instead of inventing a procedure).

**Differentiation.** FixMate is not document search with a chat box. Its
core principle — enforced in code, visible in output — is: **internal
documents FIRST, web SECOND.** Internal search → is the answer supported?
→ YES: validate + guide with citation. NO: *prove* the search was
conclusive (right model? right doc version? fully indexed?) → approved
external sources (manufacturer docs first) → present external guidance
explicitly labeled EXTERNAL, never as approved procedure → escalate if
uncertain. **Never invent a maintenance procedure to fill a documentation
gap.** And the loop closes: recurring gaps get flagged for the
documentation team, an expert publishes a manual update, the new version is
indexed, and the same question now resolves internally — field problem →
AI investigation → technician resolution → documentation update → better
troubleshooting.

---

## Meaningful Agentic AI functionality

**Why an agent, not a chatbot?** A chatbot would answer "E17 means descale
the brew group." FixMate *does the work*, in a printed plan → tool →
observe → re-plan loop:

- **Identifies** the exact equipment model first (procedures differ by
  model) and checks the (simulated) photo — as *evidence, never proof*
  (0.62 confidence is supporting; 0.41 is rejected outright).
- **Searches the internal manual first**, confirms the doc version is
  current, and passes a **deterministic safety gate** before guiding
  anyone — the "LLM" cannot bypass it (a bypass attempt raises
  `PermissionError`, demonstrated live).
- **Guides the fix with citation** (BrewPoint CP-200 Service Manual v3.2,
  §4.7) — or **stops**, explains why a technician is required in plain
  language, retrieves the part, checks inventory, and files a structured
  ticket with a **SUSPECTED → CONFIRMED** diagnosis trail.
- **Proves** a missing answer is a documentation gap (not a search miss),
  labels external findings EXTERNAL, escalates, and **logs the knowledge
  gap** so the manual gets better.

A chatbot answers; an agent investigates, gates, escalates, tickets, and
learns. The close of the demo's own scoreboard: the baseline search is
faster — one step versus six — but it cites nothing, gates nothing, and
would have walked a store employee through a 120-volt repair. Speed isn't
the metric that matters here.

---

## Project scope, inputs, outputs, constraints, success criteria, and definition of done

**Scope.** A deterministic, offline maintenance agent demo: three scenarios
(A: answer in the manual → cited guided fix; B: missing from the manual →
proven gap → external labeled → escalated → gap logged → expert update →
resolved internally; C: technician required → safety denial → ticket →
verified resolution) plus a 12-case evaluation vs a naive keyword baseline.

**Inputs (all synthetic).**

- Knowledge base: 3 coffee-machine models (CP-100, CP-200, CP-300),
  versioned service manuals, 8 error codes + procedures, 5 parts, inventory
  counts, superseded docs (to trap naive search), one manufacturer
  bulletin (SB-CP300-026, 2026-08-15).
- Scenario inputs: model + error code (+ simulated photo metadata in A).
- User role for authorization: `store_employee` / `qualified_technician`.

**Outputs.**

- Scenario A: E17 CONFIRMED (error code + manual match), cited guided fix,
  resolution recorded.
- Scenario B: proven documentation gap, EXTERNAL-labeled bulletin,
  escalation ticket, logged gap → manual v1.5 published and re-indexed →
  same question resolves internally.
- Scenario C: safety-gate DENIAL, plain-language stop explanation, ticket
  with SUSPECTED → CONFIRMED trail, part ordered only after on-site
  technician verification, resolution verified.
- Evaluation: FixMate vs naive keyword search on 7 metrics over a fixed
  12-case set.

**Constraints.** Stdlib only, fully offline, zero API keys. The
orchestrator's "LLM" is a deterministic policy engine (deliberately — so
the demo is offline, free, and byte-identical). The safety layer is
deterministic code the reasoning policy cannot bypass. Simulated vision:
structured image metadata, not a real model.

**Success criteria.** All three scenarios print their full loops and exit
0; the bypass attempt raises `PermissionError` on screen; the evaluation
table shows FixMate winning on accuracy/citation/escalation/gap-detection
while honestly losing on speed (steps); `TEST-LOG.md` records 10/10
byte-identical runs.

**Definition of done.** Three scenarios + evaluation run end to end and
exit 0; README carries all 10 checklist sections; `TEST-LOG.md` shows the
10/10 determinism gate passing.

---

## Documented single-agent or multi-agent workflow

**Single-agent workflow** — one FixMate Orchestrator (deterministic policy
standing in for an LLM) + 8 tools + a deterministic safety layer + a
Knowledge Gap Agent loop. (One decision-maker, one audit trail.)

```
                        ┌─────────────────────────────┐
                        │   FixMate Orchestrator       │
                        │  (deterministic policy       │
                        │   standing in for an LLM)    │
                        └──────────────┬──────────────┘
                                       │ plan → tool → observe → re-plan
        ┌──────────────┬───────────────┼───────────────┬───────────────┐
        ▼              ▼               ▼               ▼               ▼
 identify_      search_internal_  check_document_  retrieve_part_  search_approved_
 equipment      manual            version          details         external_sources
        │              │               │               │               │
        └──────────────┴───────────────┼───────────────┴───────────────┘
                                       ▼
                        ┌─────────────────────────────┐
                        │  DETERMINISTIC SAFETY LAYER  │
                        │  authorize() mints a token;  │
                        │  tools verify it. No token,  │
                        │  no execution. The "LLM"     │
                        │  cannot bypass it.           │
                        └──────────────┬──────────────┘
                                       ▼
        ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
        │ Guided self-      │   │ Maintenance      │   │ Knowledge Gap    │
        │ service (cited)   │   │ ticket lifecycle │   │ Agent: log gaps, │
        │ or STOP + explain │   │ SUSPECTED→       │   │ flag recurring,  │
        │                   │   │ CONFIRMED→order→ │   │ re-index expert  │
        │                   │   │ verify           │   │ manual updates   │
        └──────────────────┘   └──────────────────┘   └──────────────────┘
```

**Tools (8):** `identify_equipment`, `search_internal_manual`,
`check_document_version`, `retrieve_part_details`,
`search_approved_external_sources`, `create_maintenance_ticket`,
`check_part_availability`, `verify_resolution` — plus `vision_describe`
through the pluggable (simulated) vision interface.

**Safety classes:** ROUTINE and HOT_WATER_CAUTION (any trained store role);
ELECTRICAL and PRESSURIZED (qualified technician only). Every guided step
requires an authorization token minted by `SafetyLayer.authorize()` and
verified inside the tool — a bypass attempt raises `PermissionError`
(demonstrated in Scenario C).

**Confirmed vs. suspected:** every diagnosis carries a status. Error-code +
manual matches are CONFIRMED; everything else (photos, external bulletins,
pre-inspection guesses) is SUSPECTED until a human or the manual confirms
it.

---

## Working prototype evidence, source code, and setup instructions

### Setup (MacBook, zero setup)

**Live in Chrome (the demo path):**

```bash
cd ~/workspace/agentic-ai-workshop/fixmate-ai
python3 app.py      # stdlib-only web UI on http://localhost:8006
```

Open **http://localhost:8006** in Google Chrome, click **"Run live demo"**,
and narrate the trace as it renders: `[PLAN]` steps in yellow, `[TOOL]`
calls in green, `[SAFETY]` gates in red, `[DECIDE]` calls in purple — then
the results panel shows the FixMate-vs-naive-search scoreboard as a table.
If port 8006 is already in use, the server exits with a clear error and a
fix hint instead of a traceback.

**Terminal fallback (same demo):**

```bash
python3 demo.py
```

That's it. Requirements:

- Python 3 (any recent version; stdlib only — `requirements.txt` is
  intentionally empty)
- No internet, no API keys, no installs (`demo.py` itself needs no browser)
- Runs in well under a second; output is byte-identical on every run
  (proven in `TEST-LOG.md`: 10/10 consecutive runs, same SHA-256; the web
  UI was verified in 12/12 end-to-end rounds)

### What you'll see

`demo.py` prints the orchestrator's plan and every tool call, so the
agentic loop is visible on screen:

1. **Scenario A — CP-200 + Error E17 (answer in the manual).** Identify
   equipment → check the (simulated) photo → search the internal manual →
   confirm the doc version → pass the safety gate → guided fix **with
   citation** (BrewPoint CP-200 Service Manual v3.2, §4.7) → record the
   resolution.
2. **Scenario B — CP-300 + Error E42 (missing from the manual).** The agent
   *proves* the search was conclusive (right model, right manual, current
   version, fully indexed) before touching external sources; finds a
   manufacturer bulletin (2026-08-15); labels it **EXTERNAL** — never as
   approved procedure — escalates, and logs a knowledge gap. Then the
   standout loop runs: recurring gaps get flagged for the documentation
   team, an expert publishes manual v1.5, the new version is indexed, and
   the same question now resolves internally.
3. **Scenario C — CP-200 + Error E31 (technician required).** The manual has
   a procedure, but its safety class is ELECTRICAL. The safety gate **denies**
   self-service for a store employee (and a bypass attempt is shown failing).
   The agent stops, explains why in plain language, retrieves the part,
   checks inventory, creates a structured ticket with a
   **SUSPECTED → CONFIRMED** diagnosis trail, and tracks it to resolution —
   the part is ordered only *after* the technician verifies the failure
   on-site.
4. **Evaluation.** FixMate vs. a naive keyword document search on a fixed
   12-case test set, scored by real code on: internal-doc accuracy, citation
   accuracy, correct escalation rate, first-contact resolution, time to
   diagnosis, knowledge-gap detection, and ticket completeness.

### Files

| File | What |
|---|---|
| `demo.py` | The whole demo — orchestrator, 8 tools, safety layer, 3 scenarios, evaluation. `python3 demo.py` |
| `app.py` | Stdlib-only localhost web UI (`http.server`, port 8006): serves the demo page and runs `demo.py` via `GET /api/run`. `python3 app.py`, then open http://localhost:8006 in Chrome |
| `requirements.txt` | Intentionally empty — stdlib only, nothing to install |
| `TEST-LOG.md` | 10 consecutive runs: exit codes + output hashes (10/10 byte-identical) + 12/12 web-UI end-to-end rounds |
| `RUBRIC.md` | Self-score against the hackathon judging rubric, with evidence per score |

### Speaker notes (narrate the printed loop)

- **Open with the 7 a.m. beat.** "Coffee machine down, E17 on the display,
  customers arriving — the manager knows none of the three things that
  matter: the code, the part, or whether a tech is needed."
- **Point at `[PLAN]` / `[TOOL]` / `[OBS]`.** "This is the agentic loop,
  printed live: the orchestrator plans, calls a tool, observes, and
  re-plans. A chatbot would just answer; an agent *does the work*."
- **Land the safety beat (Scenario C).** "Watch this: the agent found the
  procedure — and then the safety layer said *no*. Not the LLM being
  careful; a deterministic gate the reasoning policy cannot bypass. We even
  show a bypass attempt failing."
- **Land the honesty beat (Scenario B).** "The agent could have invented an
  E42 procedure. Instead it proved the manual truly lacks it, labeled the
  web result EXTERNAL, escalated — and logged the gap so the *manual gets
  better*. That's the loop: field problem → AI investigation → technician
  resolution → documentation update → better troubleshooting."
- **Land the vision beat (Scenario A).** "The photo is evidence, never
  proof. 0.62 confidence is *supporting*; 0.41 is rejected outright. The
  diagnosis is confirmed by the error code plus the manual — never by the
  image alone."
- **Close with the scoreboard.** "The baseline search is faster — one step
  versus six — but it cites nothing, gates nothing, and would have walked a
  store employee through a 120-volt repair. Speed isn't the metric that
  matters here."

---

## Functional and end-to-end testing, realistic scenarios, failure cases, reliability, and human oversight

**Realistic scenarios (end to end).** Three store-floor scenarios plus the
12-case evaluation: the 7 a.m. breakdown (A), the unknown code on the new
model (B), the electrical fault (C) — each a full plan → tool → observe →
re-plan loop, all exiting 0.

**Failure cases the demo handles** (all from `demo.py` behavior):

- **Unknown equipment model.** `identify_equipment` returns `None` with
  "UNKNOWN MODEL — no manual indexed" — the loop stops instead of guessing
  procedures for a machine it doesn't know.
- **Error code missing from the manual (E42).** `prove_search_conclusive`
  runs four checks (right model? service manual not quick-start card?
  current version? fully indexed?) before anything external is touched —
  then the external result is labeled EXTERNAL, never presented as
  approved procedure, and a knowledge gap is logged.
- **Technician-only procedure requested by a store employee.**
  `safety_authorize` DENIES ELECTRICAL/PRESSURIZED for `store_employee`;
  the demonstrated bypass attempt raises `PermissionError` — the tool
  itself enforces the gate, not the orchestrator's goodwill.
- **Weak visual evidence.** The 0.41-confidence heating-element detection
  is REJECTED (below the 0.50 support threshold); the agent explicitly
  refuses to claim component damage from it.
- **Unknown part number.** `retrieve_part_details` reports "UNKNOWN PART
  NUMBER" instead of inventing specs; `check_part_availability` reports
  OUT OF STOCK when the count is zero.
- **Unverified diagnosis.** External-bulletin and photo-based diagnoses
  stay SUSPECTED; the ticket's part is ordered only *after* the technician
  verifies the failure on-site (SUSPECTED → CONFIRMED trail).

**Reliability gate.** `TEST-LOG.md` records 10 consecutive runs of
`python3 demo.py` — exit codes + SHA-256 of full output — with the result
**10/10 PASSED, byte-identical output on every run**.

**Human oversight.** The safety gate routes ELECTRICAL/PRESSURIZED work to
qualified technicians; the ticket lifecycle ends with on-site human
verification; the knowledge-gap loop ends with the documentation team's
expert update. And the demo's own limitation says it plainly: the safety
policy must be reviewed and signed off by qualified engineers — a demo
policy must never be mistaken for an engineering control.

---

## Focus, feasibility, and avoidance of unnecessary complexity

One file, stdlib only, a hand-built knowledge base, a deterministic policy
engine instead of an LLM. Deliberately *not* built:

- **No real LLM.** The orchestrator is a deterministic policy — the plan →
  tool → observe loop is real code, the reasoning is fixed. The demo is
  honest that production would swap in an LLM behind the *same* safety
  layer.
- **No real vision model.** Structured image metadata stands in for a
  multimodal model; the policy (vision is evidence, never proof) is what's
  actually being taught.
- **No ticket-system integration.** Tickets are dicts with a deterministic
  counter (`FM-2026-0847+`); the lifecycle states are the lesson, not the
  API.
- **No invented procedures, ever.** The conclusive-search proof exists
  precisely so "not found" can never be papered over.

Feasibility: ~1,200 lines a student can read end to end — and the
pluggable `VisionInterface.describe()` shows exactly where a real model
would slot in without changing the policy around it.

---

## Interdisciplinary team roles and division of labor

| Role | Owns in this demo | Concrete component |
|---|---|---|
| **Domain researcher** | Maintenance-domain correctness | Safety classes (ROUTINE/HOT_WATER_CAUTION/ELECTRICAL/PRESSURIZED), manual structure (versions, sections, citations), the internal-first/external-second doctrine, ticket lifecycle states, "never invent a procedure" principle |
| **Agent engineer** | Orchestrator, tools, and the unbypassable safety layer | FixMate Orchestrator policy, the 8 tools + `vision_describe`, `SafetyLayer.authorize` token minting + in-tool verification, `prove_search_conclusive`, the Knowledge Gap Agent loop |
| **Data engineer** | The synthetic knowledge base and eval set | `build_kb` (manuals/procedures/parts/inventory), superseded-doc traps for the baseline, the 12-case `TEST_SET` with ground truth, deterministic ticket counter |
| **UX / storyteller** | The 7 a.m. scenario beats | Speaker notes (7 a.m. beat, safety beat, honesty beat, vision beat, scoreboard close), the three-scenario arc, EXTERNAL labeling language |
| **QA** | Determinism gate and the 7-metric evaluation | `TEST-LOG.md` 10/10 byte-identical gate, the 12-case FixMate-vs-baseline scoreboard (accuracy, citation, escalation, resolution, steps, gap detection, ticket completeness) |

---

## Limitations, risks, and responsible AI (ethics, privacy, security, safety)

**Honesty section — read this before judging.**

- **Synthetic data.** Every fact in this demo is invented: the three
  coffee-machine models (CP-100, CP-200, CP-300), the manuals and their
  versions, all error codes and procedures, part numbers, inventory counts,
  store numbers, ticket IDs, and the manufacturer bulletin. The evaluation
  numbers are computed by real code, but they measure performance on
  synthetic data — a *demonstration of the method*, not a claim about the
  real world.
- **Simulated vision.** The "uploaded photo" is structured image metadata,
  and `SimulatedVisionModel` just returns the detections embedded in it —
  there is no real vision model here (offline constraint). The interface
  is pluggable: implement `VisionInterface.describe()` with a real
  multimodal model and swap it in; the policy around it (vision is
  evidence, never proof; confidence thresholds; manual cross-check) is the
  part this demo is actually teaching.
- **Simulated "LLM".** The orchestrator's reasoning is a deterministic
  policy engine, not a language model — deliberately, so the demo is
  offline, free, and byte-identical across runs.

**Limitations (what a real deployment would still need):**

- Real manuals with real versions, indexed from the manufacturer's actual
  document pipeline (not hand-written dicts).
- A real multimodal model behind `VisionInterface`, plus adversarial-image
  handling and photo privacy rules.
- Human-in-the-loop approval for ticket dispatch and parts ordering at real
  dollar amounts.
- The safety policy reviewed and signed off by qualified engineers — a
  demo policy must never be mistaken for an engineering control.
- Store-system integrations (identity/roles, inventory, dispatch) behind
  authenticated APIs.

---

## Practical value, adoption path, and measurable outcomes

**Practical value.** Downtime measured in minutes instead of a lost morning
rush — and, more importantly, *safe* downtime handling: cited procedures,
technician-only gates that can't be bypassed, and a system that gets
smarter every time the manual fails (the knowledge-gap loop turns field
failures into documentation updates).

**Adoption path** (from the demo's own design):

1. Index real manuals with real versions from the manufacturer's document
   pipeline; `check_document_version` already models the version contract.
2. Implement `VisionInterface.describe()` with a real multimodal model —
   the confidence-threshold policy stays the same.
3. Put ticket dispatch and parts ordering behind human-in-the-loop
   approval at real dollar amounts.
4. Have qualified engineers review and sign off the safety policy before
   it governs real work.

**Measurable outcomes.** Today: byte-identical determinism (10/10) and the
12-case evaluation table — internal-doc accuracy, citation accuracy,
correct escalation rate, first-contact resolution, time to diagnosis,
knowledge-gap detection, ticket completeness — computed by real code
against a fixed set. In production: mean time to diagnosis, first-contact
resolution rate, escalation appropriateness, and manual-coverage growth
from the gap loop.

---

*Built for the Agentic AI Workshop · Demo 6 of 6*
