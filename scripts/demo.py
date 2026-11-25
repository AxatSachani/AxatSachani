#!/usr/bin/env python3
"""Writes placeholder data so the SVGs render before the first live sync.
Every SVG shows a 'DEMO DATA' marker while stats.json has demo=true.
The first run of the GitHub Action overwrites this with real numbers."""
import json, os, random
from datetime import datetime, timedelta, timezone, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(11)
today = date.today()
start = today - timedelta(days=364 + (today.weekday() + 1) % 7)
weeks, w, d = [], [], start
while d <= today:
    busy = 0.75 if d.weekday() < 5 else 0.35
    c = 0 if random.random() > busy else int(random.expovariate(1 / 4)) + 1
    w.append({"date": d.isoformat(), "count": c})
    if len(w) == 7: weeks.append(w); w = []
    d += timedelta(days=1)
if w: weeks.append(w)
flat = [x for wk in weeks for x in wk]
hours = [int(30 * (0.25 + 0.75 * max(0, __import__("math").sin((h - 9) / 24 * 6.283)) + (1.2 if h in (22, 23, 0, 1) else 0))) + random.randint(0, 6) for h in range(24)]
now = datetime.now(timezone.utc)
stats = {
    "demo": True, "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "login": "AxatSachani", "name": "Akshat Sachani",
    "totals": {"commits_all": 2847, "prs": 186, "merged": 171, "reviews": 94, "issues": 23, "stars": 9,
               "repos": 11, "followers": 4, "contribs_year": sum(x["count"] for x in flat), "contributed_to": 14},
    "streak": {"current": 12, "longest": 41, "active_days_year": sum(1 for x in flat if x["count"])},
    "best_day": max(flat, key=lambda x: x["count"]),
    "weekday": [sum(x["count"] for x in flat if date.fromisoformat(x["date"]).weekday() == i) for i in range(7)],
    "calendar": weeks, "hours": hours,
    "languages": [{"name": "TypeScript", "color": "#3178c6", "bytes": 912000}, {"name": "JavaScript", "color": "#f1e05a", "bytes": 655000},
                  {"name": "Python", "color": "#3572A5", "bytes": 241000}, {"name": "HTML", "color": "#e34c26", "bytes": 88000},
                  {"name": "CSS", "color": "#563d7c", "bytes": 41000}, {"name": "Kotlin", "color": "#A97BFF", "bytes": 36000},
                  {"name": "Shell", "color": "#89e051", "bytes": 9000}, {"name": "Dockerfile", "color": "#384d54", "bytes": 3000}],
    "events": [
        {"time": (now - timedelta(hours=2)).isoformat(), "type": "PUSH", "repo": "AxatSachani/AxatSachani", "detail": "3 commits · \"blueprint pipeline v2\""},
        {"time": (now - timedelta(hours=9)).isoformat(), "type": "PR", "repo": "AxatSachani/Project-Management", "detail": "merged #42 · \"rbac: tenant-scoped roles\""},
        {"time": (now - timedelta(hours=20)).isoformat(), "type": "CREATE", "repo": "AxatSachani/solarradar", "detail": "created repository"},
        {"time": (now - timedelta(days=1, hours=3)).isoformat(), "type": "REVIEW", "repo": "AxatSachani/CodeTalk", "detail": "reviewed #17"},
        {"time": (now - timedelta(days=2)).isoformat(), "type": "STAR", "repo": "nestjs/nest", "detail": "starred"},
        {"time": (now - timedelta(days=2, hours=5)).isoformat(), "type": "PUSH", "repo": "AxatSachani/Event-Management", "detail": "2 commits · \"multi-image upload: stream to s3\""},
        {"time": (now - timedelta(days=3)).isoformat(), "type": "RELEASE", "repo": "AxatSachani/LeetCode", "detail": "released v1.4.0"},
        {"time": (now - timedelta(days=4)).isoformat(), "type": "ISSUE", "repo": "AxatSachani/CodeTalk", "detail": "closed issue #9"},
    ],
}
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
json.dump(stats, open(os.path.join(ROOT, "data", "stats.json"), "w"), indent=1)
gb = os.path.join(ROOT, "data", "guestbook.json")
if not os.path.exists(gb):
    json.dump({"total": 0, "entries": []}, open(gb, "w"), indent=1)
print("demo data written")
