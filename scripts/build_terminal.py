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
PAD = 28         # left text margin
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
    ("languages", ["Python", "TypeScript", "JavaScript", "C++", "Go"]),
    ("ai / llm", ["Claude Code", "LangChain", "LangGraph", "ChromaDB"]),
    ("backend", ["FastAPI", "React", "gRPC", "PostgreSQL", "SQLite"]),
    ("infra", ["Docker", "Kubernetes", "AWS", "Cloud Run", "Airflow"]),
]


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def ago(iso, now):
    then = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    mins = int((now - then).total_seconds() // 60)
    if mins < 60:
        return f"{max(mins, 1)}m ago"
    if mins < 60 * 24:
        return f"{mins // 60}h ago"
    return f"{mins // (60 * 24)}d ago"


def recent_pushes(now, limit=3):
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
        out.append((repo, msg, ago(ev["created_at"], now)))
        if len(out) == limit:
            break
    return out


def profile_stats():
    user = api(f"/users/{USER}")
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    counts = {}
    for r in repos:
        if r["language"]:
            counts[r["language"]] = counts.get(r["language"], 0) + 1
    langs = sorted(counts.items(), key=lambda kv: -kv[1])[:5]
    stars = sum(r["stargazers_count"] for r in repos)
    return langs, {"repos": len(repos), "followers": user["followers"], "stars": stars}


def clip(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


class Term:
    """Accumulates terminal lines; each fades in one after another."""

    def __init__(self, y):
        self.y, self.n, self.out = y, 0, []

    def line(self, inner, x=PAD, gap=LH, cls="muted", right=None, extra=""):
        delay = 0.2 + self.n * 0.06
        self.out.append(f'<g class="in" style="animation-delay:{delay:.2f}s">')
        self.out.append(extra)
        self.out.append(f'<text x="{x}" y="{self.y}" class="{cls}">{inner}</text>')
        if right:
            self.out.append(
                f'<text x="{W - PAD}" y="{self.y}" text-anchor="end" class="dim" font-size="12">{right}</text>'
            )
        self.out.append("</g>\n")
        self.y += gap
        self.n += 1

    def prompt(self, cmd):
        self.y += 12
        self.line(f'<tspan class="accent">❯</tspan> <tspan class="fg" font-weight="bold">{escape(cmd)}</tspan>')

    def tool(self, name, arg, right=None):
        self.line(f'<tspan class="green">⏺</tspan> <tspan class="fg">{name}</tspan>'
                  f'<tspan class="dim">(</tspan>{escape(arg)}<tspan class="dim">)</tspan>', right=right)

    def _mark(self, first):
        if not first:
            return ""
        return f'<text x="{PAD + 16}" y="{self.y}" class="dim">⎿</text>'

    def result(self, text, first=False, cls="muted", right=None, gap=LH):
        self.line(text, x=PAD + 38, cls=cls, right=right, gap=gap, extra=self._mark(first))

    def chips(self, label, items, first=False):
        x = PAD + CH * 16
        parts = []
        for it in items:
            w = 7.2 * len(it) + 18
            parts.append(
                f'<rect x="{x:.1f}" y="{self.y - 14}" width="{w:.1f}" height="20" rx="10" class="chip"/>'
                f'<text x="{x + 9:.1f}" y="{self.y}" class="fg" font-size="13">{escape(it)}</text>'
            )
            x += w + 6
        self.line(escape(label), x=PAD + 38, cls="accent", gap=LH + 7,
                  extra=self._mark(first) + "".join(parts))


def build(pushes, langs, stats, today):
    rng = random.Random(today.isoformat())
    words = rng.sample(WORDS, 12)
    session = (today - FIRST_DAY).days + 1
    tokens = f"{rng.uniform(1.2, 9.8):.1f}k"

    t = Term(160)

    t.prompt("whoami")
    t.tool("Bash", "whoami --verbose")
    for i, s in enumerate(ABOUT):
        t.result(escape(s), first=i == 0, cls="fg" if i == 0 else "muted")

    t.prompt("cat principles.md")
    t.tool("Read", "principles.md", right="4 lines")
    for i, (head, body) in enumerate(PRINCIPLES):
        t.result(f'<tspan class="accent">{escape(head):<23}</tspan>{escape(body)}', first=i == 0)

    t.prompt("ls ~/featured")
    t.tool("Bash", "ls ~/featured", right=f"{len(FEATURED)} of {stats['repos']} repos")
    for i, (name, stack, desc) in enumerate(FEATURED):
        t.result(f'<tspan class="accent" font-weight="bold">{escape(name)}</tspan>',
                 first=i == 0, cls="fg", right=escape(stack), gap=19)
        t.line(escape(clip(desc, 92)), x=PAD + 38, gap=LH + 5)
    t.result(f'<tspan class="dim">+ {escape(ALSO)}</tspan>')

    t.prompt("git log --all-repos --recent")
    if not pushes:
        pushes = [(USER, "quiet day, thinking deeply", "today")]
    for repo, msg, when in pushes:
        t.tool("Push", clip(repo, 40), right=when)
        t.result(escape(clip(msg, 92)), first=True)

    t.prompt("cat toolbox.txt")
    t.tool("Read", "toolbox.txt")
    t.y += 4
    for i, (cat, items) in enumerate(TOOLBOX):
        t.chips(cat, items, first=i == 0)

    # spinner
    t.y += 12
    spin_y = t.y
    cycle = 2 * len(words)
    glyphs = "".join(
        f'<text x="{PAD}" y="{spin_y}" class="g" style="animation-delay:-{i * 0.2:.1f}s">{g}</text>'
        for i, g in enumerate(GLYPHS)
    )
    word_els = "".join(
        f'<text x="{PAD + 22}" y="{spin_y}" class="w" style="animation-delay:-{(cycle - i * 2) % cycle}s">{w}…</text>'
        for i, w in enumerate(words)
    )
    box_y = spin_y + 22
    height = box_y + 70
    pct = 100 / len(words)

    # language bar in the header
    total = sum(c for _, c in langs) or 1
    bx0 = 512
    bw = W - PAD - bx0
    bar, x, legend, lx = [], float(bx0), [], bx0
    for name, c in langs:
        w = bw * c / total
        color = LANG_COLORS.get(name, "#8b8b8b")
        bar.append(f'<rect x="{x:.1f}" y="78" width="{max(w - 2, 1):.1f}" height="8" fill="{color}"/>')
        legend.append(
            f'<circle cx="{lx + 4}" cy="106" r="3.5" fill="{color}"/>'
            f'<text x="{lx + 11}" y="110" class="muted" font-size="11">{escape(name)}</text>'
        )
        x += w
        lx += 11 + int(6.7 * len(name)) + 16

    input_text = "open to AI engineering roles · ssschauhan.me"
    caret_x = PAD + 16 + CH * (len(input_text) + 2)
    statline = f"{stats['repos']} repos · {stats['followers']} followers · ★ {stats['stars']}"
    body = "".join(t.out)
    bar_svg = "".join(bar)
    legend_svg = "".join(legend)
    esc_x = PAD + 22 + 8.6 * (max(map(len, words)) + 1) + 12

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" font-family="ui-monospace, 'JetBrains Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace" font-size="14">
  <defs>
    <linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="s1"/><stop offset="1" class="s2"/></linearGradient>
    <linearGradient id="glow" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#D97757" stop-opacity=".16"/><stop offset=".6" stop-color="#D97757" stop-opacity="0"/></linearGradient>
    <clipPath id="langclip"><rect x="{bx0}" y="78" width="{bw}" height="8" rx="4"/></clipPath>
  </defs>
  <style>
    text {{ white-space: pre; }}
    .bg {{ fill: #141414; }} .frame {{ stroke: #2e2e2e; }} .s1 {{ stop-color: #2a2a2a; }} .s2 {{ stop-color: #222222; }}
    .muted {{ fill: #a3a3a3; }} .dim {{ fill: #6b6b6b; }} .fg {{ fill: #f2f2f2; }}
    .accent {{ fill: #E08A6A; }} .green {{ fill: #7cc47f; }}
    .chip {{ fill: #212121; stroke: #333333; }} .box {{ stroke: #3d3d3d; }} .card {{ fill: url(#glow); stroke: #D97757; }}
    .cursor {{ fill: #f2f2f2; }}
    @media (prefers-color-scheme: light) {{
      .bg {{ fill: #fbfaf8; }} .frame {{ stroke: #e2ded8; }} .s1 {{ stop-color: #f1eee9; }} .s2 {{ stop-color: #ebe7e1; }}
      .muted {{ fill: #5c5c5c; }} .dim {{ fill: #9a9690; }} .fg {{ fill: #1f1f1f; }}
      .accent {{ fill: #C15F3C; }} .green {{ fill: #3f8f45; }}
      .chip {{ fill: #f2efea; stroke: #e2ded8; }} .box {{ stroke: #d6d1ca; }} .cursor {{ fill: #1f1f1f; }}
    }}
    .in {{ opacity: 0; animation: in .4s ease-out forwards; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}
    .w {{ opacity: 0; animation: word {cycle}s infinite; }}
    @keyframes word {{ 0%, {pct - 0.1:.2f}% {{ opacity: 1; }} {pct:.2f}%, 100% {{ opacity: 0; }} }}
    .g {{ opacity: 0; animation: glyph 1.2s infinite; }}
    @keyframes glyph {{ 0%, 16.6% {{ opacity: 1; }} 16.7%, 100% {{ opacity: 0; }} }}
    .shimmer {{ animation: shim 2s ease-in-out infinite; }}
    @keyframes shim {{ 0%, 100% {{ fill-opacity: 1; }} 50% {{ fill-opacity: .55; }} }}
    .caret {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .in {{ animation: none; opacity: 1; }} }}
  </style>

  <rect x=".5" y=".5" width="{W - 1}" height="{height - 1}" rx="12" class="bg frame" stroke-width="1"/>
  <path d="M1 38V13a12 12 0 0 1 12-12h{W - 26}a12 12 0 0 1 12 12V38z" fill="url(#bar)"/>
  <line x1="1" y1="38.5" x2="{W - 1}" y2="38.5" class="frame"/>
  <circle cx="22" cy="19" r="6" fill="#ff5f57"/><circle cx="42" cy="19" r="6" fill="#febc2e"/><circle cx="62" cy="19" r="6" fill="#28c840"/>
  <text x="{W // 2}" y="24" text-anchor="middle" class="muted" font-size="12">shlok@lucknow: ~/theshloksschauhan</text>
  <text x="{W - 20}" y="24" text-anchor="end" class="dim" font-size="11">session #{session}</text>

  <rect x="{PAD - 4}" y="56" width="460" height="72" rx="10" class="card" stroke-width="1.2"/>
  <text x="{PAD + 14}" y="86" class="accent" font-size="17">✻ <tspan class="fg" font-weight="bold" font-size="16">Welcome back, Shlok!</tspan></text>
  <text x="{PAD + 14}" y="111" class="muted" font-size="12">{statline} · {today:%a %d %b %Y}</text>
  <text x="{bx0}" y="66" class="dim" font-size="11">languages across my repos</text>
  <g clip-path="url(#langclip)">{bar_svg}</g>
  {legend_svg}

{body}
  <g class="accent" font-size="16">{glyphs}</g>
  <g class="accent shimmer" font-weight="bold">{word_els}</g>
  <text x="{esc_x:.0f}" y="{spin_y}" class="dim" font-size="12">(esc to interrupt · ↑ {tokens} tokens)</text>

  <rect x="{PAD - 4}" y="{box_y}" width="{W - 2 * PAD + 8}" height="44" rx="10" fill="none" class="box" stroke-width="1.2"/>
  <text x="{PAD + 12}" y="{box_y + 27}" class="accent">❯ <tspan class="muted">{escape(input_text)}</tspan></text>
  <rect x="{caret_x:.0f}" y="{box_y + 13}" width="8" height="18" class="cursor caret"/>
  <text x="{PAD}" y="{height - 10}" class="dim" font-size="11">? for shortcuts</text>
  <text x="{W - PAD}" y="{height - 10}" text-anchor="end" class="dim" font-size="11">auto-rebuilt daily · GitHub Actions</text>
</svg>
"""


if __name__ == "__main__":
    now = dt.datetime.now(dt.timezone.utc)
    langs, stats = profile_stats()
    svg = build(recent_pushes(now), langs, stats, now.astimezone(IST).date())
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote", os.path.abspath(OUT))
