"""Rebuild assets/terminal.svg from live GitHub activity.

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


def languages():
    counts = {}
    for repo in api(f"/users/{USER}/repos?per_page=100&type=owner"):
        if repo["fork"] or not repo["language"]:
            continue
        counts[repo["language"]] = counts.get(repo["language"], 0) + 1
    return sorted(counts.items(), key=lambda kv: -kv[1])[:5]


def clip(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


def build(pushes, langs, today):
    rng = random.Random(today.isoformat())
    words = rng.sample(WORDS, 12)
    session = (today - FIRST_DAY).days + 1
    tokens = f"{rng.uniform(1.2, 9.8):.1f}k"
    step, cycle = 2, 2 * len(words)

    lines = []
    y = 176
    if not pushes:
        pushes = [("theshloksschauhan", "quiet day, thinking deeply")]
    for repo, msg in pushes:
        lines.append(
            f'<text x="24" y="{y}" class="green">⏺ <tspan class="fg">Push</tspan>'
            f'<tspan class="muted">({escape(clip(repo, 40))})</tspan></text>'
            f'<text x="24" y="{y + 20}" class="muted">  ⎿  {escape(clip(msg, 80))}</text>'
        )
        y += 46

    # language bar
    total = sum(c for _, c in langs) or 1
    bar, x, legend, lx = [], 470.0, [], 470
    for name, c in langs:
        w = 366 * c / total
        color = LANG_COLORS.get(name, "#8b8b8b")
        bar.append(f'<rect x="{x:.1f}" y="66" width="{w:.1f}" height="10" fill="{color}"/>')
        legend.append(
            f'<circle cx="{lx + 4}" cy="97" r="4" fill="{color}"/>'
            f'<text x="{lx + 12}" y="101" class="muted" font-size="11">{escape(name)}</text>'
        )
        x += w
        lx += 12 + 7 * len(name) + 16

    spin_y = y + 14
    glyphs = "".join(
        f'<text x="24" y="{spin_y}" class="g" style="animation-delay:-{i * 0.2:.1f}s">{g}</text>'
        for i, g in enumerate(GLYPHS)
    )
    word_els = "".join(
        f'<text x="46" y="{spin_y}" class="w" style="animation-delay:-{(cycle - i * step) % cycle}s">'
        f"{w}…</text>"
        for i, w in enumerate(words)
    )
    box_y = spin_y + 22
    height = box_y + 62
    pct = 100 / len(words)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace" font-size="15">
  <style>
    .muted {{ fill: #8b8b8b; }} .fg {{ fill: #e6e6e6; }} .accent {{ fill: #D97757; }} .green {{ fill: #7cc47f; }}
    .w {{ opacity: 0; animation: word {cycle}s infinite; }}
    @keyframes word {{ 0%, {pct - 0.1:.2f}% {{ opacity: 1; }} {pct:.2f}%, 100% {{ opacity: 0; }} }}
    .g {{ opacity: 0; animation: glyph 1.2s infinite; }}
    @keyframes glyph {{ 0%, 16.6% {{ opacity: 1; }} 16.7%, 100% {{ opacity: 0; }} }}
    .shimmer {{ animation: shim 2s ease-in-out infinite; }}
    @keyframes shim {{ 0%, 100% {{ fill: #D97757; }} 50% {{ fill: #f0b49c; }} }}
    .caret {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
  </style>
  <rect width="860" height="{height}" rx="12" fill="#1a1a1a"/>
  <rect width="860" height="36" rx="12" fill="#262626"/><rect y="24" width="860" height="12" fill="#262626"/>
  <circle cx="22" cy="18" r="6" fill="#ff5f57"/><circle cx="42" cy="18" r="6" fill="#febc2e"/><circle cx="62" cy="18" r="6" fill="#28c840"/>
  <text x="430" y="23" text-anchor="middle" class="muted" font-size="13">shlok@lucknow: ~/theshloksschauhan — session #{session}</text>

  <rect x="24" y="52" width="420" height="62" rx="8" fill="none" stroke="#D97757" stroke-width="1.2"/>
  <text x="42" y="78" class="accent">✻ <tspan class="fg" font-weight="bold">Welcome back, Shlok!</tspan></text>
  <text x="42" y="100" class="muted" font-size="13">{today:%a %d %b %Y} · live from the GitHub API</text>
  <text x="470" y="58" class="muted" font-size="11">languages across my repos</text>
  {''.join(bar)}
  {''.join(legend)}

  <text x="24" y="146" class="muted">&gt; <tspan class="fg">what did Shlok ship recently?</tspan></text>
  {''.join(lines)}

  <g class="accent" font-size="16">{glyphs}</g>
  <g class="shimmer" font-weight="bold">{word_els}</g>
  <text x="230" y="{spin_y}" class="muted" font-size="13">(esc to interrupt · ↑ {tokens} tokens)</text>

  <rect x="24" y="{box_y}" width="812" height="44" rx="8" fill="none" stroke="#4a4a4a" stroke-width="1.2"/>
  <text x="40" y="{box_y + 27}" class="fg">&gt; <tspan class="muted">open to AI engineering roles · ssschauhan.me</tspan></text>
  <rect x="472" y="{box_y + 13}" width="9" height="18" fill="#e6e6e6" class="caret"/>
  <text x="836" y="{height - 10}" text-anchor="end" class="muted" font-size="11">auto-rebuilt daily by GitHub Actions</text>
</svg>
"""


if __name__ == "__main__":
    svg = build(recent_pushes(), languages(), dt.date.today())
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote", os.path.abspath(OUT))
