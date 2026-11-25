"""Rebuild assets/terminal.svg, the whole profile drawn as one terminal session.

Runs daily in GitHub Actions. Standard library only.
"""
import datetime as dt
import json
import os
import random
import urllib.request
from xml.sax.saxutils import escape

USER = "theshloksschauhan"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "terminal.svg")
FIRST_DAY = dt.date(2026, 11, 26)
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
W = 900          # canvas width
LH = 21          # line height
CH = 7.75        # approx char width at 14px

WORDS = [
    "Thinking", "Retrieving", "Grounding", "Pondering", "Evaluating", "Guardrailing",
    "Shipping", "Brewing", "Hashing", "Cascading", "Reticulating", "Moonwalking",
    "Embedding", "Chunking", "Reranking", "Tokenizing", "Compiling", "Refactoring",
    "Caching", "Sharding", "Replicating", "Backpropagating", "Distilling", "Vectorizing",
    "Orchestrating", "Debugging", "Untangling", "Percolating", "Simmering", "Noodling",
    "Conjuring", "Calibrating", "Bootstrapping", "Deploying", "Containerizing", "Benchmarking",
    "Castling", "Checkmating", "Daydreaming", "Caffeinating",
]
GLYPHS = ["·", "✢", "✳", "✶", "✻", "✽"]
LANG_COLORS = {
    "Python": "#3776AB", "JavaScript": "#F7DF1E", "TypeScript": "#3178C6", "C++": "#00599C",
    "Go": "#00ADD8", "HTML": "#E34F26", "CSS": "#663399", "Dockerfile": "#2496ED",
}

ABOUT = [
    "AI engineer · Lucknow, India",
    "I build LLM agents, retrieval systems and backend services.",
    "Most of my time goes to the unglamorous parts: evals, guardrails,",
    "cost control and failure handling.",
]
PRINCIPLES = [
    ("Grounded answers", "cite sources; say \"I don't know\" instead of guessing"),
    ("Cheap first, LLM last", "rules settle the easy 80%, the model gets the rest"),
    ("Failing safely", "guardrails, human-review gates, fail-closed services"),
    ("Proof, not vibes", "eval gates run before anything ships"),
]
FEATURED = [
    ("coverwise", "Python · LangGraph · ChromaDB · K8s",
     "Cited Medicare coverage agent: hybrid RAG, PII guardrails, eval gate"),
    ("support-triage", "Python · SQLite",
     "Answer from docs or escalate: BM25 over ~8k chunks + cost-weighted model"),
    ("echoroute", "Python",
     "6-stage cascade picks notify / digest / mute before any LLM call"),
    ("distrocache", "Python · gRPC · FastAPI",
     "Distributed KV cache: consistent hashing, replicated nodes"),
    ("careeros", "React · FastAPI",
     "AI job platform: fit analysis, resume rewrite, ATS scoring (live demo)"),
    ("document-pile-analyst", "Python",
     "Multi-agent MSA/SLA analyst: OCR, extraction, human approval gate"),
    ("project-terminus", "Go · Docker",
     "Containerized tasks for a benchmark of frontier AI coding agents"),
]
ALSO = "ats-hris-integration · recruiting-workflow-engine · deep-packet-analyzer · +6 more"
TOOLBOX = [
    ("languages", "Python  TypeScript  JavaScript  C++  Go"),
    ("ai / llm", "Claude Code  LangChain  LangGraph  ChromaDB"),
    ("backend", "FastAPI  React  gRPC  PostgreSQL  SQLite"),
    ("infra", "Docker  Kubernetes  AWS  Cloud Run  Airflow"),
]


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def recent_pushes(limit=3):
    seen, out = set(), []
    for ev in api(f"/users/{USER}/events/public?per_page=100"):
        if ev["type"] != "PushEvent":
            continue
        repo = ev["repo"]["name"].split("/", 1)[1]
        if repo in seen or repo == USER:
            continue
        msg = "pushed changes"
        head = ev["payload"].get("head")
        if head:
            try:
                commit = api(f"/repos/{ev['repo']['name']}/commits/{head}")
                parts = [l for l in commit["commit"]["message"].splitlines() if l.strip()]
                msg = parts[0]
                if msg.startswith("Merge pull request") and len(parts) > 1:
                    msg = parts[1]  # the PR title
            except Exception:
                pass
        seen.add(repo)
        out.append((repo, msg))
        if len(out) == limit:
            break
    return out


def profile_stats():
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    counts = {}
    for r in repos:
        if r["language"]:
            counts[r["language"]] = counts.get(r["language"], 0) + 1
    langs = sorted(counts.items(), key=lambda kv: -kv[1])[:5]
    return langs, len(repos)


def clip(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


class Term:
    """Accumulates terminal lines; each fades in one after another."""

    def __init__(self, y):
        self.y, self.n, self.out = y, 0, []

    def line(self, inner, x=24, gap=LH, cls="muted"):
        delay = 0.25 + self.n * 0.09
        self.out.append(
            f'<text x="{x}" y="{self.y}" class="{cls} in" style="animation-delay:{delay:.2f}s">{inner}</text>'
        )
        self.y += gap
        self.n += 1

    def prompt(self, cmd):
        self.y += 8
        self.line(f'&gt; <tspan class="fg">{escape(cmd)}</tspan>')

    def tool(self, name, arg):
        self.line(f'<tspan class="green">⏺</tspan> <tspan class="fg">{name}</tspan>({escape(arg)})')

    def result(self, text, first=False, cls="muted"):
        mark = "⎿" if first else " "
        self.line(f'  {mark}  <tspan class="{cls}">{text}</tspan>')


def build(pushes, langs, repo_count, today):
    rng = random.Random(today.isoformat())
    words = rng.sample(WORDS, 12)
    session = (today - FIRST_DAY).days + 1
    tokens = f"{rng.uniform(1.2, 9.8):.1f}k"

    t = Term(150)

    t.prompt("whoami")
    t.tool("Bash", "whoami --verbose")
    for i, s in enumerate(ABOUT):
        t.result(escape(s), first=i == 0, cls="fg" if i == 0 else "muted")

    t.prompt("cat principles.md")
    t.tool("Read", "principles.md")
    for i, (head, body) in enumerate(PRINCIPLES):
        t.result(f'<tspan class="accent">{escape(head)}</tspan> — {escape(body)}', first=i == 0)

    t.prompt("ls ~/featured")
    t.tool("Bash", f"ls ~/featured  # {repo_count} repos total")
    for i, (name, stack, desc) in enumerate(FEATURED):
        t.result(
            f'<tspan class="accent" font-weight="bold">{escape(name)}</tspan>'
            f'<tspan class="dim"> · {escape(stack)}</tspan>',
            first=i == 0, cls="fg",
        )
        t.line(f'        {escape(clip(desc, 88))}', gap=LH + 3)
    t.result(f'<tspan class="dim">also: {escape(ALSO)}</tspan>')

    t.prompt("git log --all-repos --recent")
    if not pushes:
        pushes = [(USER, "quiet day, thinking deeply")]
    for repo, msg in pushes:
        t.tool("Push", clip(repo, 40))
        t.result(escape(clip(msg, 88)), first=True)

    t.prompt("cat toolbox.txt")
    t.tool("Read", "toolbox.txt")
    for i, (cat, items) in enumerate(TOOLBOX):
        t.result(f'<tspan class="accent">{cat:<10}</tspan> <tspan class="fg">{escape(items)}</tspan>'
                 , first=i == 0)

    # spinner
    t.y += 14
    spin_y = t.y
    cycle = 2 * len(words)
    glyphs = "".join(
        f'<text x="24" y="{spin_y}" class="g" style="animation-delay:-{i * 0.2:.1f}s">{g}</text>'
        for i, g in enumerate(GLYPHS)
    )
    word_els = "".join(
        f'<text x="46" y="{spin_y}" class="w" style="animation-delay:-{(cycle - i * 2) % cycle}s">{w}…</text>'
        for i, w in enumerate(words)
    )
    box_y = spin_y + 22
    height = box_y + 66
    pct = 100 / len(words)

    # language bar in the header
    total = sum(c for _, c in langs) or 1
    bar, x, legend, lx = [], 500.0, [], 500
    for name, c in langs:
        w = 376 * c / total
        color = LANG_COLORS.get(name, "#8b8b8b")
        bar.append(f'<rect x="{x:.1f}" y="70" width="{w:.1f}" height="10" fill="{color}"/>')
        legend.append(
            f'<circle cx="{lx + 4}" cy="101" r="4" fill="{color}"/>'
            f'<text x="{lx + 12}" y="105" class="muted" font-size="11">{escape(name)}</text>'
        )
        x += w
        lx += 12 + int(6.7 * len(name)) + 18

    input_text = "open to AI engineering roles · ssschauhan.me"
    caret_x = 40 + CH * (len(input_text) + 3)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace" font-size="14" xml:space="preserve">
  <style>
    text {{ white-space: pre; }}
    .muted {{ fill: #9a9a9a; }} .dim {{ fill: #6f6f6f; }} .fg {{ fill: #ececec; }}
    .accent {{ fill: #D97757; }} .green {{ fill: #7cc47f; }}
    .in {{ opacity: 0; animation: in .35s ease-out forwards; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}
    .w {{ opacity: 0; animation: word {cycle}s infinite; }}
    @keyframes word {{ 0%, {pct - 0.1:.2f}% {{ opacity: 1; }} {pct:.2f}%, 100% {{ opacity: 0; }} }}
    .g {{ opacity: 0; animation: glyph 1.2s infinite; }}
    @keyframes glyph {{ 0%, 16.6% {{ opacity: 1; }} 16.7%, 100% {{ opacity: 0; }} }}
    .shimmer {{ animation: shim 2s ease-in-out infinite; }}
    @keyframes shim {{ 0%, 100% {{ fill: #D97757; }} 50% {{ fill: #f0b49c; }} }}
    .caret {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .in {{ animation: none; opacity: 1; }} }}
  </style>
  <rect width="{W}" height="{height}" rx="12" fill="#1a1a1a"/>
  <rect width="{W}" height="36" rx="12" fill="#262626"/><rect y="24" width="{W}" height="12" fill="#262626"/>
  <circle cx="22" cy="18" r="6" fill="#ff5f57"/><circle cx="42" cy="18" r="6" fill="#febc2e"/><circle cx="62" cy="18" r="6" fill="#28c840"/>
  <text x="{W // 2}" y="23" text-anchor="middle" class="muted" font-size="13">shlok@lucknow: ~/theshloksschauhan — session #{session}</text>

  <rect x="24" y="54" width="452" height="66" rx="8" fill="none" stroke="#D97757" stroke-width="1.2"/>
  <text x="42" y="81" class="accent" font-size="15">✻ <tspan class="fg" font-weight="bold">Welcome back, Shlok!</tspan></text>
  <text x="42" y="104" class="muted" font-size="12">{today:%a %d %b %Y} · live from the GitHub API</text>
  <text x="500" y="62" class="muted" font-size="11">languages across my repos</text>
  {''.join(bar)}
  {''.join(legend)}

  {''.join(t.out)}

  <g class="accent" font-size="16">{glyphs}</g>
  <g class="shimmer" font-weight="bold">{word_els}</g>
  <text x="{46 + 9.2 * (max(map(len, words)) + 1) + 14:.0f}" y="{spin_y}" class="dim" font-size="13">(esc to interrupt · ↑ {tokens} tokens)</text>

  <rect x="24" y="{box_y}" width="{W - 48}" height="44" rx="8" fill="none" stroke="#4a4a4a" stroke-width="1.2"/>
  <text x="40" y="{box_y + 27}" class="fg">&gt; <tspan class="muted">{escape(input_text)}</tspan></text>
  <rect x="{caret_x:.0f}" y="{box_y + 13}" width="8" height="18" fill="#ececec" class="caret"/>
  <text x="{W - 24}" y="{height - 10}" text-anchor="end" class="dim" font-size="11">? for shortcuts · auto-rebuilt daily by GitHub Actions</text>
</svg>
"""


if __name__ == "__main__":
    langs, repo_count = profile_stats()
    svg = build(recent_pushes(), langs, repo_count, dt.datetime.now(IST).date())
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote", os.path.abspath(OUT))
