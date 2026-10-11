#!/usr/bin/env python3
"""FixMate AI -- localhost web UI (stdlib only).

Run:  python3 app.py   then open http://localhost:8006
Serves a guided, personalized tour of demo.py (the tested artifact --
demo.py is never modified here; it is only imported as a module and its
canned subprocess run is unchanged).
"""

import contextlib
import http.server
import io
import json
import mimetypes
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8006
HERE = Path(__file__).resolve().parent
DEMO_PY = HERE / "demo.py"

sys.path.insert(0, str(HERE))
import demo as DEMO  # the tested artifact: imported, never modified

COND_RE = re.compile(
    r"(type 2 diabetes|type 1 diabetes|diabetes|hypertension|high blood pressure|"
    r"kidney disease|ckd|heart disease|depression|asthma|arthritis|copd|hyperlipidemia)"
)

def _capture_canned():
    """Run the canned demo exactly as before (subprocess), capture stdout."""
    proc = subprocess.run(
        [sys.executable, str(DEMO_PY)],
        cwd=str(HERE),
        capture_output=True,
        text=True,
        timeout=600,
    )
    return proc.stdout or proc.stderr

def _capture_fn(fn, params):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            return fn(params)
    except Exception as exc:  # never crash the page on a bad input
        return "[web-ui] The personalized run hit an error and stopped safely.\n%s: %s" % (type(exc).__name__, exc)

# _capture_custom: personalized handlers may return a dict carrying a follow-up decision.
def _capture_custom(fn, params):
    try:
        res = fn(params)
    except Exception as exc:  # never crash the page on a bad input
        return {"output": "[web-ui] The personalized run hit an error and stopped safely.", "decision": None}
    if isinstance(res, dict):
        res.setdefault("decision", None)
        return res
    return {"output": res, "decision": None}

# ---- personalized run: input handling lives in app.py; demo.py untouched ----

def _clean_str(v, default):
    return v.strip().upper() if isinstance(v, str) and v.strip() else default


def run_custom(params):
    model = _clean_str(params.get("model"), "CP-200")
    code = _clean_str(params.get("code"), "E17")
    if model not in ("CP-100", "CP-200", "CP-300"):
        model = "CP-200"
    kb = DEMO.build_kb()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        print("YOUR ERROR: %s shows %s" % (model, code))
        print("The same FixMate rules fire for YOUR selection:")
        print("internal documents first, web second, never invent; technician-gated safety.")
        print()
        machine = DEMO.identify_equipment(model, kb)
        print("Machine: %s | manual %s (v%s)" % (machine["model_name"], machine["manual_id"], machine["version"]))
        print()
        internal = DEMO.search_internal_manual(model, code, kb)
        if internal:
            ver = DEMO.check_document_version(model, kb)
            if ver.get("superseded_by"):
                print("GUARDRAIL: indexed manual v%s is SUPERSEDED by v%s -- the old "
                      "manual is NOT trusted. No guided fix; escalating to a qualified "
                      "technician for the current procedure."
                      % (ver["version"], ver["superseded_by"]))
                print()
                print("Same rules, your error code -- including codes the manual never heard of.")
                return out.getvalue()
            print("INTERNAL MANUAL HIT: %s" % internal["citation"])
            print("Fault: %s" % internal["title"])
            print("Safety class: %s" % internal["safety_class"])
            if internal["safety_class"] in ("ELECTRICAL", "PRESSURIZED"):
                print("GUARDRAIL: documented, but technician-gated -- self-service STOPPED, ticket opened.")
                print("Reason: %s" % DEMO.SAFETY_EXPLANATIONS[internal["safety_class"]])
            else:
                if internal.get("caution"):
                    print("CAUTION: %s" % internal["caution"])
                print("GUIDED FIX -- the manager follows the cited steps:")
                for i, step in enumerate(internal["steps"], 1):
                    print("  %d. %s" % (i, step))
        else:
            print("INTERNAL MANUAL MISS: no internal document covers %s / %s" % (model, code))
            DEMO.prove_search_conclusive(model, code, kb)
            print("GUARDRAIL: the gap is proven real -- the agent may check external sources, labeled EXTERNAL.")
            print("ESCALATION: no invented procedure. A technician ticket is opened with the evidence trail.")
        print()
        print("Same rules, your error code -- including codes the manual never heard of.")
    return out.getvalue()

PAGE = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>FixMate AI &mdash; Live Demo</title>\n<style>\n:root{\n  --bg:#0b1220; --bg2:#0e1626; --panel:#131e33; --panel2:#182742;\n  --ink:#eaf0f9; --muted:#9db0c9; --faint:#6b7f99;\n  --teal:#2dd4bf; --teal-dim:rgba(45,212,191,.12);\n  --accent:#5aa9ff; --warn:#fbbf24; --danger:#f87171; --ok:#34d399;\n  --line:#233451; --radius:14px;\n}\n*{box-sizing:border-box}\nbody{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;\n  background:var(--bg);color:var(--ink);line-height:1.6}\nheader{background:linear-gradient(135deg,#0a2540 0%,#0e3a5c 60%,#0b4f4a 100%);\n  padding:42px 32px 34px;border-bottom:1px solid var(--line)}\n.wrap{max-width:1060px;margin:0 auto}\nheader h1{margin:0 0 8px;font-size:30px;letter-spacing:-.01em}\nheader .sub{margin:0;color:#c8d6ea;font-size:16px;max-width:800px}\n.badge{display:inline-block;margin-top:14px;font-size:11.5px;letter-spacing:.1em;\n  text-transform:uppercase;color:#06281f;background:var(--teal);\n  padding:5px 14px;border-radius:999px;font-weight:800}\nmain{padding:8px 32px 48px}\nsection.card{background:var(--panel);border:1px solid var(--line);\n  border-radius:var(--radius);padding:26px 28px;margin:26px 0}\nsection.card h2{margin:0 0 12px;font-size:18px;color:var(--teal)}\nsection.card h2 .n{display:inline-block;width:28px;height:28px;border-radius:50%;\n  background:var(--teal-dim);border:1px solid var(--teal);color:var(--teal);\n  text-align:center;line-height:26px;font-size:14px;margin-right:10px}\nsection.card p{margin:0 0 12px;color:#d5e0f1;font-size:15.5px}\nsection.card p:last-child{margin-bottom:0}\n.watch{list-style:none;margin:6px 0 0;padding:0}\n.watch li{position:relative;padding:8px 0 8px 30px;color:#d5e0f1;font-size:15px;\n  border-bottom:1px dashed var(--line)}\n.watch li:last-child{border-bottom:0}\n.watch li::before{content:"\\25b8";position:absolute;left:8px;color:var(--teal);font-weight:700}\nlabel.f{display:block;margin:14px 0 6px;font-size:13px;font-weight:700;\n  letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}\ninput[type=text],input[type=number],select,textarea{\n  width:100%;background:var(--bg2);border:1px solid var(--line);color:var(--ink);\n  border-radius:10px;padding:11px 14px;font-size:15px;font-family:inherit}\ntextarea{min-height:76px;resize:vertical}\ninput:focus,select:focus,textarea:focus{outline:none;border-color:var(--teal)}\n.row2{display:grid;grid-template-columns:1fr 1fr;gap:14px}\n@media(max-width:700px){.row2{grid-template-columns:1fr}}\n.btnrow{display:flex;gap:14px;align-items:center;margin-top:20px;flex-wrap:wrap}\nbutton.run{background:linear-gradient(135deg,#14b8a6,#0d9488);border:0;\n  color:#04211c;font-weight:800;font-size:17px;padding:15px 34px;\n  border-radius:12px;cursor:pointer;box-shadow:0 6px 22px rgba(45,212,191,.25)}\nbutton.run:hover{filter:brightness(1.08)}\nbutton.run:disabled{opacity:.45;cursor:default;box-shadow:none}\nbutton.ghost{background:transparent;border:1px solid var(--teal);color:var(--teal);\n  font-weight:700;font-size:15px;padding:13px 26px;border-radius:12px;cursor:pointer}\nbutton.ghost:hover{background:var(--teal-dim)}\nbutton.ghost:disabled{opacity:.45;cursor:default}\n.hint{color:var(--muted);font-size:13.5px}\n.spinner{display:none;align-items:center;gap:10px;color:var(--muted);font-size:14px;margin-top:14px}\n.spinner.show{display:flex}\n.dot{width:12px;height:12px;border-radius:50%;background:var(--teal);\n  animation:pulse 1s infinite ease-in-out}\n@keyframes pulse{0%,100%{transform:scale(.6);opacity:.5}50%{transform:scale(1.2);opacity:1}}\n#output{display:none;margin-top:6px}\n#output.show{display:block}\n.out{background:#0a0f1c;border:1px solid var(--line);border-radius:12px;\n  padding:20px 22px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;\n  font-size:13px;line-height:1.6;white-space:pre-wrap;word-wrap:break-word;\n  max-height:640px;overflow:auto;color:#c9d6ea}\n.sechead{color:var(--accent);font-weight:800;margin:18px 0 2px;font-size:13.5px}\n.sechead:first-child{margin-top:0}\n.seccap{background:var(--teal-dim);border-left:3px solid var(--teal);\n  padding:8px 12px;margin:4px 0 12px;border-radius:0 8px 8px 0;\n  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;\n  font-size:13.5px;color:#bfe9e2}\n.tok-orch{color:var(--accent);font-weight:700}\n.tok-tool{color:var(--ok);font-weight:700}\n.tok-guard{color:var(--warn);font-weight:700}\n.tok-mem{color:#c084fc;font-weight:700}\n#takeaways{display:none}\n#takeaways.show{display:block}\n.take{background:rgba(52,211,153,.07);border:1px solid rgba(52,211,153,.4);\n  border-radius:var(--radius);padding:22px 26px;margin:26px 0}\n.take h2{color:var(--ok);margin:0 0 10px;font-size:18px}\n.take ul{margin:0;padding-left:20px}\n.take li{margin:8px 0;color:#d5e0f1;font-size:15px}\ntable.dec{width:100%;border-collapse:collapse;margin-top:12px;font-size:14px}\ntable.dec th{background:var(--panel2);color:var(--teal);text-align:left;\n  padding:10px 12px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;\n  border-bottom:1px solid var(--line)}\ntable.dec td{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}\n.pill{display:inline-block;padding:3px 12px;border-radius:999px;font-weight:800;font-size:12px}\n.pill.v{background:var(--ok);color:#04281c}\n.pill.s{background:var(--faint);color:#0b1220}\nfooter{padding:26px 32px 40px;color:var(--faint);font-size:13.5px;text-align:center}\nfooter a{color:var(--teal);text-decoration:none}\nfooter a:hover{text-decoration:underline}\ndetails.raw{margin-top:14px}\ndetails.raw summary{cursor:pointer;color:var(--muted);font-size:13.5px}/* --- fixmate revamp: why-section + sidebar layout --- */\n.fix-layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:26px;align-items:start}\n.fix-main{min-width:0}\n.fix-sidebar{position:sticky;top:20px;min-width:0}\n@media(max-width:960px){.fix-layout{grid-template-columns:1fr}.fix-sidebar{position:static}}\n.side-card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:20px;margin-bottom:20px}\n.side-card h3{margin:0 0 10px;font-size:15px;color:var(--teal)}\n.side-vid{margin-bottom:18px}\n.side-vid:last-child{margin-bottom:0}\n.side-vid-featured{border:1px solid var(--teal);border-radius:12px;padding:12px;background:var(--teal-dim);}\n    .real-tag{display:inline-block;font-size:10.5px;font-weight:800;letter-spacing:.08em;color:#04211c;background:var(--teal);border-radius:999px;padding:3px 10px;margin-bottom:8px;}\n    .side-vid iframe{width:100%;aspect-ratio:16/9;border:0;border-radius:10px;display:block;background:#000}\n.side-vid p{font-size:13px;color:var(--muted);margin:8px 0 0;line-height:1.5}\n.side-link{margin-bottom:16px}\n.side-link:last-child{margin-bottom:0}\n.side-link a{color:var(--accent);text-decoration:none;font-size:14px;font-weight:700;line-height:1.5}\n.side-link a:hover{text-decoration:underline}\n.side-link p{font-size:13px;color:var(--muted);margin:6px 0 0;line-height:1.5}\n.hero-fig{margin:2px 0 18px}\n.hero-fig img{width:100%;border-radius:12px;border:1px solid var(--line);display:block}\n.hero-fig figcaption{font-size:13px;color:var(--muted);margin-top:8px;line-height:1.5}\n.why-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:16px 0}\n@media(max-width:700px){.why-grid{grid-template-columns:1fr}}\n.why-grid figure{margin:0}\n.why-grid img{width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:10px;border:1px solid var(--line);display:block;background:#0a0f1c}\n.why-grid figcaption{font-size:12.5px;color:var(--muted);margin-top:6px;line-height:1.5}\n.chal{list-style:none;margin:10px 0 0;padding:0}\n.chal li{position:relative;padding:7px 0 7px 28px;color:#d5e0f1;font-size:15px}\n.chal li::before{content:"!";position:absolute;left:9px;color:var(--warn);font-weight:800}\n</style>\n</head>\n<body>\n<header><div class="wrap">\n  <h1>FixMate AI</h1>\n  <p class="sub">7 a.m., the coffee machine is down, Error E17. The manual knows — if you can reach it.</p>\n</div></header>\n<main><div class="wrap fix-layout"><div class="fix-main">\n\n<section class="card" id="why">\n  <h2><span class="n">&#9881;</span>Why does this matter in real life?</h2>\n  <figure class="hero-fig">\n    <img src="/assets/img/ai-maintenance-assistant.svg" alt="AI Maintenance Assistant: a technician uses a tablet-based diagnostic guide while servicing equipment" loading="lazy">\n    <figcaption><b>AI Maintenance Assistant:</b> using generative AI to troubleshoot equipment &mdash; the technician, the tablet, and the manual\u2019s knowledge, in one hand. (Original illustration made for this demo &mdash; no stock photo, no credit needed.)</figcaption>\n  </figure>\n  <p>When a machine breaks, the business stops with it. A dead coffee machine at the morning rush doesn\'t just cost that morning\'s sales &mdash; it sends regulars walking to the shop across the street, and some of them won\'t come back. The person on shift isn\'t a technician and shouldn\'t have to be one: they\'re a store manager, not a repair specialist, and handing them a 400-page manual doesn\'t help.</p>\n  <p>Meanwhile, the people who actually know these machines are quietly disappearing. Veteran technicians carry years of undocumented know-how &mdash; which error codes lie, which fixes are safe, which parts fail first &mdash; and when they retire, that knowledge walks out the door with them. An agent that reasons from the actual manuals preserves that knowledge: every procedure it follows is cited to a real document, it applies that knowledge in seconds, and &mdash; just as important &mdash; it knows when to stop and say &ldquo;call a human&rdquo; instead of guessing at a repair.</p>\n  <div class="why-grid">\n    <figure><img src="/assets/img/technician-repair.svg" alt="Service technician inspecting a commercial espresso machine" loading="lazy"><figcaption>A veteran technician at work &mdash; this is the expertise that walks out the door at retirement.</figcaption></figure>\n    <figure><img src="/assets/img/espresso-machine.svg" alt="Close-up of an espresso machine portafilter pouring a shot" loading="lazy"><figcaption>The machine at stake: when it stops during the rush, the whole store feels it.</figcaption></figure>\n    <figure><img src="/assets/img/tool-kit.svg" alt="An electrical tool kit with a digital multimeter" loading="lazy"><figcaption>The tools of the trade &mdash; every fix starts with the right diagnosis.</figcaption></figure>\n  </div>\n  <p><b>The purpose of this demo:</b> it shows an AI agent that troubleshoots from <b>your manuals first</b> &mdash; identifying the machine, citing the exact document, and guiding a safe fix &mdash; instead of guessing or burying staff in PDFs. Try it on your own error code below.</p>\n  <p><b>The challenges it tackles:</b></p>\n  <ul class="chal">\n    <li>Downtime during rush hour costs the whole morning</li>\n    <li>Manuals exist but nobody can find the right page under pressure</li>\n    <li>Guessing at repairs is worse than waiting</li>\n  </ul>\n</section>\n\n<section class="card" id="why-7eleven">\n  <h2><span class="n">\u2605</span>Why we\u2019re building this &mdash; lessons from 7-Eleven\u2019s real deployment</h2>\n  <p>7-Eleven runs thousands of stores, and every minute a machine is down, revenue stops. Their technicians work from mobile devices in the field &mdash; and the answers they need are buried across <b>thousands of maintenance documents</b>. Sound familiar? That is exactly the problem FixMate models.</p>\n  <p>Here is what 7-Eleven actually built, in a talk by their team at Databricks (video in the sidebar):</p>\n  <ul class="watch">\n    <li><b>The problem is knowledge access, not knowledge absence.</b> The manuals exist &mdash; technicians just can\u2019t find the right paragraph fast enough during a breakdown. Their agent searches across equipment catalogs, parts databases, and documents with hybrid search (keywords + meaning).</li>\n    <li><b>One agent is not enough &mdash; route the question.</b> Their system sends each equipment question through <b>specialized agents</b> (diagnosis, parts lookup, documentation), coordinated together &mdash; the same multi-step reasoning FixMate demonstrates.</li>\n    <li><b>Trust is engineered, not assumed.</b> They track every agent decision with observability traces and measure business KPIs &mdash; adoption only happened because technicians could see the agent\u2019s work. That is why FixMate shows its reasoning and escalates when the manual has no answer.</li>\n    <li><b>It scaled to 1,000+ technicians</b> because it met them where they are: on mobile, in plain language, in seconds &mdash; not in a PDF.</li>\n  </ul>\n  <p class="hint" style="margin-top:12px">Summary based on the talk\u2019s published description and chapter outline (&ldquo;AI Agents for the Frontline: 7-Eleven\u2019s GenAI Maintenance Assistant&rdquo;, Databricks Events). No transcript is published for the video.</p>\n</section>\n\n<section class="card" id="story">\n  <h2><span class="n">1</span>The story</h2>\n  <p>It\'s 7 a.m. at a BrewPoint convenience store. The coffee machine is down, the display says <b>Error E17</b>, and customers are arriving. The manager doesn\'t know what E17 means, which part it needs, or whether a technician is required.</p>\n<p>FixMate is the agent that puts the maintenance manual in the manager\'s hands: it identifies the machine, searches <b>internal documents FIRST</b> (citing the exact manual and section), and guides the fix step by step. When the manual doesn\'t have the answer, it <i>proves</i> the search was conclusive before checking external sources — labels them EXTERNAL — and escalates rather than inventing a procedure. One hard rule, enforced in code: <b>internal documents first, web second, never invent.</b></p>\n</section>\n\n<section class="card" id="watch">\n  <h2><span class="n">2</span>What to watch for</h2>\n  <ul class="watch">\n<li>Scenario A: the answer IS in the manual — watch the agent cite it and guide the fix.</li>\n<li>Scenario B: the answer is NOT in the manual — watch the agent prove the gap is real before touching the web, then escalate honestly.</li>\n<li>Scenario C: the fix needs a technician — watch the safety gate STOP self-service. Some procedures are technician-only, full stop.</li>\n<li>The finale: every unanswered question feeds a knowledge-gap loop — today\'s gap becomes tomorrow\'s manual update.</li>\n  </ul>\n</section>\n\n\n\n<section class="card" id="tryown">\n  <h2><span class="n">✎</span>Try your own</h2>\n  <p>Pick a machine and an error code — including codes the manual never heard of — and watch the agent\'s rules fire for <b>your</b> selection.</p>\n  <div class="row2">\n    <div><label class="f" for="x_model">Machine model</label>\n      <select id="x_model">\n        <option>CP-200</option><option>CP-100</option><option>CP-300</option>\n      </select></div>\n    <div><label class="f" for="x_code">Error code</label>\n      <select id="x_code">\n        <option>E17</option><option>E42</option><option>E99</option><option>E10</option><option>E11</option><option>E14</option><option>E20</option><option>E50</option>\n        <option>E05</option><option>E12</option><option>E18</option><option>E25</option><option>E23</option><option>E28</option><option>E31</option><option>E35</option>\n      </select></div>\n  </div>\n  <div class="btnrow">\n    <button class="ghost" id="customRun">Diagnose my error</button>\n    <span class="hint">Same inputs → same output. Deterministic.</span>\n  </div>\n  <div class="spinner" id="cspin"><div class="dot"></div>Checking the manuals…</div>\n</section>\n\n\n<section class="card" id="runbox">\n  <h2><span class="n">3</span>Run the demo</h2>\n  <p>Click below to run the full canned demonstration. It takes a few seconds.</p>\n  <div class="btnrow">\n    <button class="run" id="run">&#9654; Run live demo</button>\n  </div>\n  <div class="spinner" id="spin"><div class="dot"></div><span>The agent is checking the manuals…</span></div>\n  <div id="output">\n    <div class="out" id="outtext"></div>\n    <details class="raw"><summary>Show raw terminal output</summary>\n      <div class="out" id="rawtext"></div>\n    </details>\n  </div>\n</section>\n\n<section class="card" id="takeaways" style="display:none">\n  <div class="take">\n    <h2>What just happened</h2>\n    <ul>\n<li>Internal documents first, web second — enforced in code, visible in every scenario.</li>\n<li>The agent never invents a procedure: when the manual lacks E42, it says so and escalates.</li>\n<li>Safety is a gate, not a suggestion: the E31 fix was documented and still blocked for store staff.</li>\n<li>The knowledge-gap loop closes the system: recurring unanswered questions become manual updates.</li>\n<li>Try your own: pick a machine and an error code in “Try your own” — including ones the manual never heard of.</li>\n    </ul>\n  </div>\n</section>\n\n</div>\n<aside class="fix-sidebar">\n  <div class="side-card">\n    <h3>Learn more</h3>\n    <p style="font-size:13.5px;color:var(--muted);margin:0 0 14px">Want to go deeper on AI in maintenance and field service? Start with these.</p>\n    <div class="side-vid side-vid-featured">\n      <div class="real-tag">REAL DEPLOYMENT</div>\n      <iframe src="https://www.youtube-nocookie.com/embed/y-Dah_bzSUc" title="AI Agents for the Frontline: 7-Eleven\u2019s GenAI Maintenance Assistant (Databricks)" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>\n      <p><b>7-Eleven\u2019s GenAI Maintenance Assistant</b> &mdash; the real-world version of this demo: how 7-Eleven gives 1,000+ technicians an AI agent that finds answers across thousands of maintenance documents. Watch this first.</p>\n    </div>\n    <div class="side-vid">\n      <iframe src="https://www.youtube-nocookie.com/embed/qxbke5BeI-g" title="C3 AI Field Services" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>\n      <p>See how agentic AI gives technicians real-time troubleshooting guidance &mdash; manuals, asset data, and safety checks in one application.</p>\n    </div>\n    <div class="side-vid">\n      <iframe src="https://www.youtube-nocookie.com/embed/VlOli2XK1Ko" title="How AI Agents Cut Unplanned Downtime by 31% | Manufacturing Case Study" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>\n      <p>A manufacturing case study: AI agents turn equipment signals into engineer-approved repair actions before a breakdown.</p>\n    </div>\n    <div class="side-vid">\n      <iframe src="https://www.youtube-nocookie.com/embed/4m-DLypesxY" title="AI Predictive Maintenance Explained: Prevent Equipment Failure" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>\n      <p>A short explainer on predicting failures before they happen &mdash; reactive vs. preventive vs. predictive maintenance.</p>\n    </div>\n  </div>\n  <div class="side-card">\n    <h3>Go deeper &mdash; articles</h3>\n    <div class="side-link">\n      <a href="https://prophecyiot.com/predictive-maintenance/" target="_blank" rel="noopener">How Predictive Maintenance and IoT Save Manufacturers Money</a>\n      <p>ProphecyIoT &middot; A practical walkthrough of the predictive maintenance loop &mdash; instrument, stream, analyze, act, learn &mdash; and what it gives back.</p>\n    </div>\n    <div class="side-link">\n      <a href="https://iotbusinessnews.com/2026/06/16/industrial-ai-shifts-focus-from-predictive-maintenance-to-knowledge-preservation/" target="_blank" rel="noopener">Industrial AI Shifts Focus from Predictive Maintenance to Knowledge Preservation</a>\n      <p>IoT Business News &middot; Why industrial AI is becoming a knowledge-management story: digitizing technician expertise before it retires.</p>\n    </div>\n    <div class="side-link">\n      <a href="https://vocal.media/education/how-gen-ai-chatbots-assist-service-engineers-in-accessing-maintenance-documents" target="_blank" rel="noopener">How GenAI Chatbots Assist Service Engineers in Accessing Maintenance Documents</a>\n      <p>Vocal Media &middot; How chatbots answer engineers straight from the manuals &mdash; the same idea FixMate demonstrates.</p>\n    </div>\n  </div>\n</aside>\n</div></main>\n<footer><div class="wrap">\n  <a href="https://github.com/ynpreet/fixmate-ai" target="_blank" rel="noopener">View the project on GitHub</a>\n  &nbsp;&middot;&nbsp; All data in this demo is synthetic / fictional.\n</div></footer>\n\n<script>\nconst SECTIONS = [["SCENARIO A", "Error E17 on the CP-200: documented. Internal manual first, guided fix with citation."], ["SCENARIO B", "Error E42 on the CP-300: not in the manual. The agent proves the gap, checks external sources (labeled EXTERNAL), escalates."], ["SCENARIO C", "Error E31: the manual has a procedure, but it\'s electrical \\u2014 the safety gate stops self-service and opens a ticket."], ["EVALUATION", "FixMate vs. naive manual search on a fixed test set: speed with safety, measured honestly."], ["DEMO COMPLETE", "End of run."]];\nfunction esc(s){return s.replace(/&/g,\'&amp;\').replace(/</g,\'&lt;\').replace(/>/g,\'&gt;\');}\nfunction decorate(line){\n  let h = esc(line);\n  h = h.replace(/\\[ORCHESTRATOR\\]/g,\'<span class="tok-orch">[ORCHESTRATOR]</span>\');\n  h = h.replace(/\\[TOOL [^\\]]+\\]/g,function(m){return \'<span class="tok-tool">\'+m+\'</span>\';});\n  h = h.replace(/\\[MEMORY\\]/g,\'<span class="tok-mem">[MEMORY]</span>\');\n  h = h.replace(/GUARDRAIL/g,\'<span class="tok-guard">GUARDRAIL</span>\');\n  return h;\n}\nfunction renderOut(text){\n  document.getElementById(\'rawtext\').textContent = text;\n  const lines = text.split(\'\\n\');\n  let html = \'\';\n  for(const line of lines){\n    let matched = null;\n    for(const s of SECTIONS){ if(line.indexOf(s.m) !== -1){ matched = s; break; } }\n    if(matched){\n      html += \'<div class="sechead">\'+decorate(line)+\'</div>\'+\n              \'<div class="seccap">\'+matched.c+\'</div>\';\n      continue;\n    }\n    html += decorate(line) + \'\\n\';\n  }\n  document.getElementById(\'outtext\').innerHTML = html;\n  document.getElementById(\'output\').classList.add(\'show\');\n  document.getElementById(\'output\').scrollIntoView({behavior:\'smooth\',block:\'start\'});\n}\nfunction showTakeaways(){\n  const t = document.getElementById(\'takeaways\');\n  t.style.display=\'block\'; t.classList.add(\'show\');\n  t.scrollIntoView({behavior:\'smooth\',block:\'start\'});\n}\ndocument.getElementById(\'run\').addEventListener(\'click\',function(){\n  const btn=this, spin=document.getElementById(\'spin\');\n  btn.disabled=true; spin.classList.add(\'show\');\n  fetch(\'/api/run\').then(r=>r.json()).then(j=>{\n    spin.classList.remove(\'show\'); btn.disabled=false;\n    renderOut(j.output);\n    if(typeof loadDecisionTable===\'function\') loadDecisionTable();\n    showTakeaways();\n  }).catch(e=>{spin.classList.remove(\'show\');btn.disabled=false;alert(\'Run failed: \'+e);});\n});\n\nfunction collectCustom(){\n  return {model:document.getElementById(\'x_model\').value,\n          code:document.getElementById(\'x_code\').value.toUpperCase()};\n}\n\nfunction wireCustom(){\n  const b=document.getElementById(\'customRun\');\n  if(!b) return;\n  b.addEventListener(\'click\',function(){\n    const spin=document.getElementById(\'cspin\');\n    b.disabled=true; spin.classList.add(\'show\');\n    fetch(\'/api/custom\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},\n      body:JSON.stringify(collectCustom())})\n    .then(r=>r.json()).then(j=>{\n      spin.classList.remove(\'show\'); b.disabled=false;\n      if(j.error){alert(j.error);return;}\n      renderOut(j.output); showTakeaways();\n    }).catch(e=>{spin.classList.remove(\'show\');b.disabled=false;alert(\'Run failed: \'+e);});\n  });\n}\nwireCustom();\n</script>\n</body>\n</html>\n'

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "WorkshopUI/1.0"

    def _send(self, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj):
        self._send(json.dumps(obj), "application/json; charset=utf-8")

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            length = 0
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return {}

    def _serve_asset(self, path):
        safe = (HERE / path.lstrip("/")).resolve()
        try:
            safe.relative_to(HERE / "assets")
        except ValueError:
            return self.send_error(403, "forbidden")
        if not safe.is_file():
            return self.send_error(404, "not found")
        ctype, _ = mimetypes.guess_type(str(safe))
        data = safe.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path in ("/", "/index.html"):
            self._send(PAGE)
        elif path == "/api/run":
            self._json({"output": _capture_canned()})
        elif path.startswith("/assets/"):
            self._serve_asset(path)
        else:
            self.send_error(404, "not found")

    def do_POST(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/api/custom":
            params = self._read_json()
            self._json(_capture_custom(run_custom, params))
        else:
            self.send_error(404, "not found")

    def log_message(self, fmt, *args):
        sys.stderr.write("ui: " + (fmt % args) + "\n")


def main():
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    print("FixMate AI demo UI -> http://localhost:8006")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
