# RUBRIC.md — Self-score vs. the PEAAII Hackathon Judging Rubric

Scored 1–5 per criterion against `~/workspace/peaii-hackathon/judging-rubric.md`, with concrete evidence, one honest gap per criterion, and how a student could close it.

| # | Criterion (weight) | Score | Points |
|---|---|---|---|
| 1 | Problem Definition & Real-World Impact (25) | 5/5 | 25 |
| 2 | Meaningful Agentic AI Behavior (20) | 4/5 | 16 |
| 3 | Working Prototype (15) | 5/5 | 15 |
| 4 | Innovation & Creativity (15) | 4/5 | 12 |
| 5 | Presentation & Communication (15) | 5/5 | 15 |
| 6 | Responsible AI & Feasibility (10) | 5/5 | 10 |
| | **TOTAL** | | **93/100** |

---

## 1. Problem Definition & Real-World Impact — 5/5 (25 pts)

**Evidence:** A specific user with a concrete, time-pressured problem: a
convenience-store manager at 7 a.m. with a dead coffee machine, an E17 code
she doesn't understand, customers arriving. The README names the "today"
workflow (binder, call the district supervisor, lose the morning rush) and
what changes (instant cited guidance, or a ticket filed for her). The user is
a frontline worker, not "everyone."

**Honest gap:** The demo never quantifies the stakes (what an hour of a dead
coffee machine costs a store), so the impact is vivid but not measured.

**Close it:** Add one README/demo line with a plausible downtime cost
("the morning coffee rush is ~40% of a convenience store's beverage sales")
and cite the source.

## 2. Meaningful Agentic AI Behavior — 4/5 (16 pts)

**Evidence:** The loop is the centerpiece and it's *printed*: the
orchestrator prints a numbered plan, calls 8 distinct tools with visible
inputs/outputs (`identify_equipment`, `search_internal_manual`,
`check_document_version`, `retrieve_part_details`,
`search_approved_external_sources`, `create_maintenance_ticket`,
`check_part_availability`, `verify_resolution`), re-plans on observations
(Scenario B pivots internal → external → escalate → log gap), keeps memory
across scenarios (the gap log persists and drives the expert-update loop),
and takes semi-autonomous actions (creates and tracks tickets). A chatbot
could not do this.

**Honest gap:** The "LLM" is a deterministic policy engine, not a real
language model — a judge probing hard could call the reasoning scripted
rather than emergent.

**Close it:** Swap the policy for a real LLM call behind the same tool
interface (the architecture already isolates it), keeping the deterministic
safety layer — then the demo shows identical behavior with genuine
reasoning.

## 3. Working Prototype — 5/5 (15 pts)

**Evidence:** `python3 demo.py` is the entire demo — stdlib only, fully
offline, zero API keys, completes in well under a second, and TEST-LOG.md
proves 10/10 byte-identical runs with exit code 0. All three scenarios and
the baseline evaluation execute end-to-end with no manual steps.

**Honest gap:** Terminal-only; there is no interactive mode, so a student
demoing live can't take a judge's own "my machine shows E23" question.

**Close it:** Add an optional `--ask "CP-200 E23"` flag that runs the
orchestrator policy on an arbitrary model/code pair — still deterministic
given the same args.

## 4. Innovation & Creativity — 4/5 (12 pts)

**Evidence:** Three design choices go beyond a generic troubleshooting bot:
(1) the Knowledge Gap Agent's continuous-improvement loop (field problem →
AI investigation → technician resolution → documentation update → better
troubleshooting), demonstrated live with the v1.4 → v1.5 manual update;
(2) the safety layer as a *token-enforced gate inside the tools* rather than
a prompt instruction, with a bypass attempt shown failing; (3) the
internal-first / external-labeled / never-invent policy made demo-visible.

**Honest gap:** Maintenance copilots exist in industry; the novelty is in the
packaging (the loop + the gate), not in inventing a new product category —
and the vision step is simulated, not real.

**Close it:** Plug a real multimodal model into `VisionInterface` and demo
the 0.62-vs-0.41 confidence policy on genuine photos; that turns the most
"simulated" part into the most impressive live beat.

## 5. Presentation & Communication — 5/5 (15 pts)

**Evidence:** README carries the full non-technical story: a 30-second
setup, MacBook run steps assuming zero setup, speaker notes with exact
beats to narrate ("watch the safety layer say *no*"), an ASCII architecture
diagram, and a "say the honesty beat out loud" prompt. The demo's own
output explains decisions in plain English ("STOPPING self-service. Why, in
plain language: …") that a non-technical judge can follow, with tool calls
a technical judge can audit.

**Honest gap:** No visuals — it's a terminal demo, and a live room responds
to at least one picture.

**Close it:** Add a one-slide diagram of the architecture (the ASCII art as
a real slide) and a printed "ticket card" view for Scenario C's ticket.

## 6. Responsible AI & Feasibility — 5/5 (10 pts)

**Evidence:** Safety is the demo's spine, not a slide: a deterministic,
unbypassable authorization layer for electrical/pressurized work; a
never-invent-a-procedure rule; external guidance always labeled EXTERNAL;
confirmed-vs-suspected diagnosis discipline; vision output treated as
evidence, never proof; escalation whenever uncertain. The README's honesty
section states plainly what is synthetic, what is simulated, and what a real
deployment would still need (real manuals, real vision model, human
approval for spend, engineer sign-off on the safety policy).

**Honest gap:** No threat model: what happens with an adversarial photo, a
poisoned manual entry, or a user who lies about their role to pass the gate
(the demo trusts the `role` string).

**Close it:** Add role authentication (not just a string) and one demo beat
where the agent refuses a photo that contradicts the error code, requesting
human confirmation — showing the policy under adversarial input.
