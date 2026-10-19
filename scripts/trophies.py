#!/usr/bin/env python3
"""Generate assets/trophies.svg from live GitHub stats (REST only)."""
import json, os, shutil, subprocess, sys, urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "Blhasn-Sehli")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "trophies-script",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception:
        if shutil.which("gh"):  # local fallback
            return json.loads(subprocess.check_output(["gh", "api", path.lstrip("/")]))
        raise

if os.environ.get("TROPHY_DEMO"):  # layout preview only, no network
    user = {"followers": 100, "public_repos": 15, "created_at": "2021-11-04T00:00:00Z"}
    stars, prs, commits, years = 17, 130, 800, 5
else:
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        chunk = api(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    stars = sum(r["stargazers_count"] for r in repos)
    prs = api(f"/search/issues?q=author:{USER}+type:pr&per_page=1")["total_count"]
    try:
        commits = api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"]
    except Exception:
        commits = 0
    years = (datetime.now(timezone.utc) - datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))).days // 365

TIERS = ["-", "C", "B", "A", "S", "SS"]
COLORS = {"-": "#30363d", "C": "#6e7681", "B": "#00e5ff", "A": "#39d353", "S": "#ffd740", "SS": "#ff6e40"}

def rank(v, th):
    r = 0
    for i, t in enumerate(th, 1):
        if v >= t:
            r = i
    return TIERS[r]

items = [
    ("Stars", stars, [1, 5, 15, 50, 100]),
    ("Commits", commits, [1, 100, 500, 1000, 2000]),
    ("Followers", user["followers"], [1, 10, 50, 100, 500]),
    ("Pull Requests", prs, [1, 10, 50, 100, 500]),
    ("Repositories", user["public_repos"], [1, 5, 20, 40, 80]),
    ("Account Age", years, [1, 2, 3, 5, 8]),
]

CW, CH, GAP = 128, 150, 12
W = len(items) * CW + (len(items) - 1) * GAP
mono = "font-family=\"'Fira Code','DejaVu Sans Mono',Consolas,monospace\""
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{CH}" viewBox="0 0 {W} {CH}" role="img" aria-label="GitHub trophies">']
for i, (title, val, th) in enumerate(items):
    rk = rank(val, th)
    col = COLORS[rk]
    x = i * (CW + GAP)
    cx = x + CW / 2
    out.append(f'<g transform="translate({x},0)">')
    out.append(f'<rect x="0.5" y="0.5" width="{CW-1}" height="{CH-1}" rx="10" fill="#0d1117" stroke="#30363d"/>')
    out.append(f'<rect x="0.5" y="0.5" width="{CW-1}" height="4" rx="2" fill="{col}" opacity="0.9"/>')
    # trophy icon (48x48 box centred)
    out.append(f'<g transform="translate({CW/2-24},16)" fill="{col}">'
               '<path d="M12 4h24v14c0 7-5 12-12 12S12 25 12 18z"/>'
               f'<path d="M12 8H4v4c0 5 3 8 8 9M36 8h8v4c0 5-3 8-8 9" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="round"/>'
               '<rect x="21" y="30" width="6" height="8"/><rect x="14" y="38" width="20" height="5" rx="2"/>'
               f'<text x="24" y="22" text-anchor="middle" font-size="13" font-weight="800" fill="#0d1117" {mono}>{rk if rk!="-" else ""}</text>'
               '</g>')
    out.append(f'<text x="{CW/2}" y="92" text-anchor="middle" font-size="12" fill="#c9d1d9" font-weight="700" {mono}>{title}</text>')
    out.append(f'<text x="{CW/2}" y="118" text-anchor="middle" font-size="22" fill="{col}" font-weight="800" {mono}>{val}</text>')
    out.append(f'<text x="{CW/2}" y="137" text-anchor="middle" font-size="10" fill="#6e7681" letter-spacing="2" {mono}>RANK {rk}</text>')
    out.append('</g>')
out.append('</svg>')
os.makedirs("assets", exist_ok=True)
open("assets/trophies.svg", "w").write("\n".join(out))
print({t: (v, rank(v, th)) for t, v, th in items})
