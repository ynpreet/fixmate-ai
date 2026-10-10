#!/usr/bin/env python3
"""
FixMate AI -- localhost web UI (Demo 6 of 6, Agentic AI Workshop).

STDLIB ONLY. Serves a single-page UI in Google Chrome; the "Run live
demo" button executes demo.py via subprocess and renders the
plan -> tool -> observe agent trace with highlighting.

Usage:
    python3 app.py
Then open in Chrome: http://localhost:8006

Endpoints:
    GET /         -> the demo page (inline CSS/JS, no external assets)
    GET /api/run  -> {"ok": true, "output": "<demo.py stdout>"} (or ok:false)
"""

import http.server
import json
import os
import subprocess
import sys
import threading

HOST = "127.0.0.1"
PORT = 8006

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.join(HERE, "demo.py")

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FixMate AI — The Intelligent Equipment Maintenance Agent</title>
<style>
  :root {
    --bg: #0e1116; --panel: #161b22; --border: #2a3240; --text: #e6edf3;
    --muted: #9aa4b2; --accent: #f0a431; --accent2: #58a6ff;
    --plan: #ffd479; --tool: #7ee787; --obs: #79c0ff; --safety: #ff7b72;
    --decide: #d2a8ff; --gap: #ffa657; --section: #f0a431;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text);
         font-family: "Segoe UI", system-ui, -apple-system, Arial, sans-serif;
         line-height: 1.55; }
  header { background: linear-gradient(135deg, #1a2230, #10151d);
           border-bottom: 3px solid var(--accent); padding: 34px 24px 26px;
           text-align: center; }
  header h1 { margin: 0 0 6px; font-size: 2rem; letter-spacing: .5px; }
  header h1 .wrench { color: var(--accent); }
  header .tagline { color: var(--accent); font-style: italic; margin: 0 0 10px; }
  header .meta { color: var(--muted); font-size: .9rem; margin: 0; }
  main { max-width: 1080px; margin: 0 auto; padding: 24px; }
  .story { background: var(--panel); border: 1px solid var(--border);
           border-radius: 12px; padding: 20px 22px; margin-bottom: 20px; }
  .story h2 { margin-top: 0; color: var(--accent); font-size: 1.15rem; }
  .story p { margin: .5em 0; color: #d6dde6; }
  .controls { text-align: center; margin: 26px 0; }
  #runBtn { background: var(--accent); color: #1a1206; border: none;
            border-radius: 10px; padding: 14px 34px; font-size: 1.1rem;
            font-weight: 700; cursor: pointer; transition: transform .1s, opacity .2s; }
  #runBtn:hover:not(:disabled) { transform: scale(1.03); }
  #runBtn:disabled { opacity: .55; cursor: wait; }
  .note { color: var(--muted); font-size: .85rem; margin-top: 10px; }
  #spinner { display: none; margin: 18px auto; text-align: center; color: var(--muted); }
  #spinner .ring { width: 42px; height: 42px; margin: 0 auto 10px;
                   border: 4px solid var(--border); border-top-color: var(--accent);
                   border-radius: 50%; animation: spin 0.9s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .panel { background: var(--panel); border: 1px solid var(--border);
           border-radius: 12px; margin: 20px 0; overflow: hidden; }
  .panel h2 { margin: 0; padding: 14px 20px; background: #1d2531;
              font-size: 1.05rem; border-bottom: 1px solid var(--border); }
  #trace { padding: 16px 20px; font-family: Consolas, "Courier New", monospace;
           font-size: .83rem; white-space: pre-wrap; word-break: break-word;
           max-height: 70vh; overflow-y: auto; }
  #trace .section { color: var(--section); font-weight: 700; margin-top: 12px;
                    border-top: 1px solid var(--border); padding-top: 10px; display: block; }
  #trace .plan { color: var(--plan); font-weight: 700; }
  #trace .tool { color: var(--tool); }
  #trace .obs { color: var(--obs); }
  #trace .safety { color: var(--safety); font-weight: 700; }
  #trace .decide { color: var(--decide); font-weight: 700; }
  #trace .gap { color: var(--gap); }
  #trace .think { color: var(--muted); font-style: italic; }
  #results { padding: 18px 22px; }
  #results table { width: 100%; border-collapse: collapse; font-size: .88rem; }
  #results th, #results td { border: 1px solid var(--border); padding: 8px 10px;
                             text-align: left; }
  #results th { background: #1d2531; color: var(--accent); }
  .placeholder { color: var(--muted); font-style: italic; }
  .legend { display: flex; flex-wrap: wrap; gap: 14px; padding: 12px 20px;
            border-bottom: 1px solid var(--border); font-size: .8rem;
            font-family: Consolas, monospace; }
  .legend span b { font-weight: 700; }
  footer { text-align: center; color: var(--muted); font-size: .8rem;
           padding: 24px; }
</style>
</head>
<body>
<header>
  <h1><span class="wrench">&#9881;</span> FixMate AI</h1>
  <p class="tagline">Diagnose faster. Fix smarter. Keep every store running.</p>
  <p class="meta">The Intelligent Equipment Maintenance Agent &middot; Demo 6 of 6, Agentic AI Workshop</p>
</header>
<main>
  <section class="story">
    <h2>The story (30 seconds)</h2>
    <p>It's 7 a.m. at a fictional BrewPoint Retail convenience store. The coffee
    machine is down, the display says <strong>Error E17</strong>, and customers are
    arriving. The store manager doesn't know what E17 means, which part it needs,
    or whether a technician is required.</p>
    <p><strong>FixMate</strong> gives frontline employees instant access to maintenance
    knowledge: it identifies the exact equipment, checks the internal service manual
    <em>first</em>, guides the fix with a citation &mdash; or stops, explains why a
    technician is required, and files the ticket itself.</p>
    <p style="color:var(--muted);font-size:.85rem">All data is synthetic and fictional.
    The orchestrator is a deterministic policy engine standing in for an LLM; the
    plan &rarr; tool &rarr; observe loop is real code. Stdlib only, offline, no API keys.</p>
  </section>

  <div class="controls">
    <button id="runBtn" onclick="runDemo()">&#9654; Run live demo</button>
    <div class="note">Runs <code>demo.py</code> on this machine (same output as the terminal) &mdash; ~3 scenarios + evaluation, under a second.</div>
  </div>

  <div id="spinner"><div class="ring"></div>Agent working &mdash; planning, calling tools, observing&hellip;</div>

  <section class="panel" id="tracePanel" style="display:none">
    <h2>&#129302; Agent trace &mdash; plan, tool calls, observations</h2>
    <div class="legend">
      <span><b style="color:var(--plan)">[PLAN]</b> orchestrator plan</span>
      <span><b style="color:var(--tool)">[TOOL]</b> tool call</span>
      <span><b style="color:var(--obs)">[OBS ]</b> observation</span>
      <span><b style="color:var(--safety)">[SAFETY]</b> safety gate</span>
      <span><b style="color:var(--decide)">[DECIDE]</b> decision</span>
      <span><b style="color:var(--gap)">[GAP ]</b> knowledge gap</span>
    </div>
    <div id="trace"></div>
  </section>

  <section class="panel" id="resultsPanel" style="display:none">
    <h2>&#128202; Results &mdash; FixMate vs naive document search (12-case eval)</h2>
    <div id="results"></div>
  </section>
</main>
<footer>Fictional BrewPoint Retail &middot; fully offline &middot; stdlib only</footer>

<script>
function classify(line) {
  if (/^[=-]{20,}$/.test(line)) return null;
  if (line.startsWith("SCENARIO") || line.startsWith("EVALUATION")) return "section";
  if (line.startsWith("[PLAN]")) return "plan";
  if (line.startsWith("[TOOL]")) return "tool";
  if (line.startsWith("[OBS ]")) return "obs";
  if (line.startsWith("[SAFETY]")) return "safety";
  if (line.startsWith("[DECIDE]")) return "decide";
  if (line.startsWith("[GAP ]")) return "gap";
  if (line.startsWith("[THINK]")) return "think";
  if (line.startsWith("       ")) return "tool";
  return "";
}

function renderTrace(output) {
  const trace = document.getElementById("trace");
  trace.innerHTML = "";
  output.split("\n").forEach(function(line) {
    const cls = classify(line);
    if (cls === null) return; // divider line: spacing handled by .section
    const div = document.createElement("div");
    if (cls) div.className = cls;
    div.textContent = line === "" ? "\u00a0" : line;
    trace.appendChild(div);
  });
}

function renderResults(output) {
  const box = document.getElementById("results");
  box.innerHTML = "";
  const start = output.indexOf("EVALUATION -- FixMate");
  if (start === -1) {
    const p = document.createElement("p");
    p.className = "placeholder";
    p.textContent = "Evaluation table not found in output — see trace above.";
    box.appendChild(p);
    return;
  }
  const lines = output.slice(start).split("\n");
  const rows = [];
  let inTable = false, cur = null;
  for (const line of lines) {
    if (!inTable) { if (/^Metric\s+FixMate\s+Baseline/.test(line)) inTable = true; continue; }
    if (/^[-=]{10,}$/.test(line) || line.trim() === "") continue;
    if (/^\s/.test(line)) {
      if (cur) cur.notes += " " + line.trim();
      continue;
    }
    const m = /^(.*?)\s{2,}([\d.]+%?)\s{2,}([\d.]+%?)\s*$/.exec(line);
    if (m) {
      cur = { metric: m[1].trim(), fix: m[2], base: m[3], notes: "" };
      rows.push(cur);
    } else {
      cur = null; // "Reading the table honestly:" prose — stop the table
    }
  }
  if (rows.length === 0) {
    const pre = document.createElement("pre");
    pre.style.whiteSpace = "pre-wrap"; pre.style.fontSize = ".8rem";
    pre.textContent = output.slice(start);
    box.appendChild(pre);
    return;
  }
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const hr = document.createElement("tr");
  ["Metric", "FixMate", "Naive search", "Notes"].forEach(function(h) {
    const th = document.createElement("th"); th.textContent = h; hr.appendChild(th);
  });
  thead.appendChild(hr); table.appendChild(thead);
  const tbody = document.createElement("tbody");
  rows.forEach(function(r) {
    const tr = document.createElement("tr");
    [["metric",""], ["fix","var(--tool)"], ["base","var(--safety)"], ["notes",""]].forEach(function(pair) {
      const td = document.createElement("td");
      td.textContent = r[pair[0]];
      if (pair[1]) td.style.color = pair[1];
      if (pair[0] === "metric") td.style.fontWeight = "600";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  box.appendChild(table);
}

async function runDemo() {
  const btn = document.getElementById("runBtn");
  const spinner = document.getElementById("spinner");
  btn.disabled = true;
  document.getElementById("tracePanel").style.display = "none";
  document.getElementById("resultsPanel").style.display = "none";
  spinner.style.display = "block";
  try {
    const resp = await fetch("/api/run");
    if (!resp.ok) throw new Error("server returned " + resp.status);
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || "demo failed");
    renderTrace(data.output);
    document.getElementById("tracePanel").style.display = "block";
    renderResults(data.output);
    document.getElementById("resultsPanel").style.display = "block";
    document.getElementById("tracePanel").scrollIntoView({behavior: "smooth"});
  } catch (e) {
    document.getElementById("tracePanel").style.display = "block";
    const trace = document.getElementById("trace");
    trace.innerHTML = "";
    const div = document.createElement("div");
    div.className = "safety";
    div.textContent = "ERROR: " + e.message + " — is demo.py present next to app.py?";
    trace.appendChild(div);
  } finally {
    spinner.style.display = "none";
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""


def run_demo():
    """Run demo.py as a subprocess; return (ok, output_or_error)."""
    try:
        proc = subprocess.run(
            [sys.executable, DEMO],
            cwd=HERE,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        return False, "demo.py not found at %s" % DEMO
    except subprocess.TimeoutExpired:
        return False, "demo.py timed out after 120s"
    if proc.returncode != 0:
        return False, ("demo.py exited with code %d\nSTDERR:\n%s"
                       % (proc.returncode, proc.stderr))
    return True, proc.stdout


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "FixMateUI/1.0"

    def log_message(self, fmt, *args):  # keep terminal output clean
        pass

    def _send(self, code, body, ctype):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html")
        elif path == "/api/run":
            ok, out = run_demo()
            payload = {"ok": ok, ("output" if ok else "error"): out}
            self._send(200, json.dumps(payload), "application/json")
        else:
            self._send(404, "Not found", "text/plain")


def main():
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    print(flush=True)
    print("=" * 60)
    print("  FixMate AI -- web UI")
    print("  Open in Chrome: http://localhost:%d" % PORT, flush=True)
    print("=" * 60)
    print("  Press Ctrl+C to stop.")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    try:
        main()
    except OSError as e:
        # Most common cause: the port is already in use.
        print("", file=sys.stderr)
        print("ERROR: could not bind %s:%d -- %s" % (HOST, PORT, e),
              file=sys.stderr)
        print("Another copy of app.py (or something else) is already using "
              "port %d." % PORT, file=sys.stderr)
        print("Find it with:  lsof -ti:%d   then stop it with:  kill <PID>"
              % PORT, file=sys.stderr)
        print("(Do not 'pkill -f app.py' -- that can kill the wrong process.)",
              file=sys.stderr)
        sys.exit(2)
