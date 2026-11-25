#!/usr/bin/env python3
"""Renders every generated/*.svg from data/stats.json + data/guestbook.json.
Theme: BLUEPRINT x TERMINAL. Pure SVG + SMIL (animations work inside GitHub READMEs)."""
import json, math, os, html
from datetime import datetime, timedelta, timezone, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json")))
S = json.load(open(os.path.join(ROOT, "data", "stats.json")))
GBP = os.path.join(ROOT, "data", "guestbook.json")
GB = json.load(open(GBP)) if os.path.exists(GBP) else {"total": 0, "entries": []}
OUT = os.path.join(ROOT, "generated")
os.makedirs(OUT, exist_ok=True)

TZ = timezone(timedelta(hours=CFG.get("tz_offset_hours", 0)))
TZN = CFG.get("tz_name", "UTC")
NOW = datetime.fromisoformat(S["generated_at"].replace("Z", "+00:00")).astimezone(TZ)
DEMO = S.get("demo", False)
T = S["totals"]

# ------------------------------------------------------------------ palette
BG, BG2 = "#061633", "#0a2a5c"
LINE, BLUE, DIM = "#eaf2ff", "#7fb3ff", "#3d63a3"
GREEN, AMBER, CYAN, PINK, RED = "#39ff14", "#ffb000", "#5ce1e6", "#ff6ad5", "#ff4d6d"
TERM = "#020b08"
MONO = "font-family:'JetBrains Mono','SF Mono','Fira Code',Consolas,'Liberation Mono',monospace"
SANS = "font-family:'Inter',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
e = lambda s: html.escape(str(s), quote=True)
fmt = lambda n: f"{int(n):,}"


def defs(extra=""):
    return f'''<defs>
<pattern id="g1" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="{LINE}" stroke-opacity=".06"/></pattern>
<pattern id="g2" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M100 0H0V100" fill="none" stroke="{LINE}" stroke-opacity=".14"/></pattern>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".35"/></pattern>
<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 1L9 5L0 9" fill="none" stroke="{LINE}" stroke-width="1.4"/></marker>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="bigglow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>
{extra}</defs>'''


def svg(W, H, body, extra_defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="{MONO}">'
            f'{defs(extra_defs)}{body}</svg>')


def paper(W, H, double=True):
    s = (f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/><rect width="{W}" height="{H}" rx="8" fill="url(#g1)"/>'
         f'<rect width="{W}" height="{H}" rx="8" fill="url(#g2)"/>')
    if double:
        s += (f'<rect x="12" y="12" width="{W-24}" height="{H-24}" fill="none" stroke="{LINE}" stroke-width="1.8"/>'
              f'<rect x="18" y="18" width="{W-36}" height="{H-36}" fill="none" stroke="{LINE}" stroke-opacity=".35"/>')
    # corner registration marks
    for (x, y) in ((30, 30), (W - 30, 30), (30, H - 30), (W - 30, H - 30)):
        s += f'<path d="M{x-6} {y}H{x+6}M{x} {y-6}V{y+6}" stroke="{BLUE}" stroke-opacity=".6"/>'
    return s


def fig(x, y, label, sub=None):
    s = f'<text x="{x}" y="{y}" fill="{BLUE}" font-size="13" letter-spacing="3">{e(label)}</text>'
    if sub:
        s += f'<text x="{x}" y="{y+20}" fill="{LINE}" fill-opacity=".7" font-size="12">{e(sub)}</text>'
    return s


def demo_stamp(cx, cy, rot=0):
    if not DEMO:
        return ""
    return (f'<g transform="translate({cx} {cy})"><rect x="-125" y="-11" width="250" height="22" rx="11" fill="{BG}" stroke="{AMBER}" stroke-width="1.5"/>'
            f'<text y="4" fill="{AMBER}" font-size="10.5" text-anchor="middle" letter-spacing="1.5">DEMO DATA · AWAITING FIRST SYNC</text></g>')


def sync_label():
    return f"{NOW:%Y-%m-%d %H:%M} {TZN}"


def write(name, s):
    open(os.path.join(OUT, name), "w").write(s)


def typed(lines, x, y0, lh, fs, start=0.4, cps=26, prefix="t"):
    """Terminal typing effect. lines = [(segments, is_cmd)] where segments=[(text,color)]"""
    clips, body, t, y = [], [], start, y0
    cw = fs * 0.602
    for i, (segs, is_cmd) in enumerate(lines):
        n = sum(len(s) for s, _ in segs)
        dur = max(0.05, n / cps) if is_cmd else 0.08
        width = n * cw + 14
        clips.append(f'<clipPath id="{prefix}{i}"><rect x="{x-2}" y="{y-fs}" height="{fs+8}" width="0"><animate attributeName="width" from="0" to="{width:.0f}" begin="{t:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>')
        spans = "".join(f'<tspan fill="{c}">{e(s)}</tspan>' for s, c in segs)
        body.append(f'<text x="{x}" y="{y}" font-size="{fs}" clip-path="url(#{prefix}{i})" xml:space="preserve">{spans}</text>')
        t += dur + (0.25 if is_cmd else 0.12)
        y += lh
    return "".join(clips), "".join(body), t, y


def cursor(x, y, fs, begin, color=GREEN):
    return (f'<rect x="{x:.0f}" y="{y-fs+2}" width="{fs*0.55:.0f}" height="{fs}" fill="{color}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.01;.5;.51" dur="1s" begin="{begin:.2f}s" repeatCount="indefinite"/></rect>')


def term_window(x, y, w, h, title):
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{TERM}" stroke="{GREEN}" stroke-opacity=".45"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="28" rx="10" fill="#0c1a12"/><rect x="{x}" y="{y+18}" width="{w}" height="10" fill="#0c1a12"/>'
            f'<circle cx="{x+18}" cy="{y+14}" r="5" fill="#ff5f56"/><circle cx="{x+36}" cy="{y+14}" r="5" fill="#ffbd2e"/><circle cx="{x+54}" cy="{y+14}" r="5" fill="#27c93f"/>'
            f'<text x="{x+w/2}" y="{y+18}" fill="#5b7a5b" font-size="11" text-anchor="middle">{e(title)}</text></g>')


def term_fx(x, y, w, h, cid):
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/></clipPath>'
            f'<g clip-path="url(#{cid})"><rect x="{x}" y="{y+28}" width="{w}" height="{h}" fill="url(#scan)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="50" fill="{GREEN}" opacity=".035"><animate attributeName="y" from="{y-50}" to="{y+h}" dur="6s" repeatCount="indefinite"/></rect></g>')


def operator_status():
    last = None
    for ev in S.get("events", []):
        t = datetime.fromisoformat(ev["time"].replace("Z", "+00:00"))
        last = t if last is None or t > last else last
    h = NOW.hour
    if last and (NOW - last.astimezone(TZ)) < timedelta(hours=3):
        return "ACTIVE · shipping right now", GREEN
    if 1 <= h < 7:
        return "OFFLINE · asleep (or debugging prod)", AMBER
    if 9 <= h < 19 and NOW.weekday() < 5:
        return "IN THE ZONE · building", GREEN
    return "ONLINE · night shift", CYAN


def ago(t):
    d = NOW - datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(TZ)
    s = d.total_seconds()
    if s < 3600: return f"{max(1, int(s // 60))}m ago"
    if s < 86400: return f"{int(s // 3600)}h ago"
    return f"{int(s // 86400)}d ago"


def trunc(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def gear(cx, cy, r, teeth=12):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        rr = r if (i % 4) in (0, 1) else r * 0.82
        pts.append(f"{cx + rr*math.cos(a):.1f},{cy + rr*math.sin(a):.1f}")
    return "M" + " L".join(pts) + "Z"


# ======================================================================  1. HERO
def hero_svg():
    W, H = 1200, 480
    name = CFG["display_name"]
    status, scol = operator_status()
    prods = CFG.get("products", [])
    lines = [([("AKSHAT-OS 2026 · kernel 6.18-backend (tty1)", "#9fbf9f")], False),
             ([("[  OK  ] ", GREEN), ("Mounted /dev/coffee · /dev/focus", "#d7ffd7")], False)]
    for p in prods:
        st = p.get("status")
        tag = ("[  OK  ] ", GREEN) if st == "live" else (("[ LOCK ] ", CYAN) if st == "invite" else ("[ WAIT ] ", AMBER))
        lines.append(([tag, (f"{p['name'].lower()}.service".ljust(22), "#d7ffd7"), (p.get("boot", ""), "#6f9f7f")], False))
    lines.append(([("[ SYNC ] ", CYAN), (f"{fmt(T['commits_all'])} commits · {fmt(T['contribs_year'])} contributions/yr", "#d7ffd7")], False))
    lines.append(([("status: ", "#6f9f7f"), (status, scol)], False))
    prompt_cmd = "./build --scale=∞"
    lines.append(([("akshat@ahmedabad", GREEN), (":", "#d7ffd7"), ("~", CYAN), ("$ ", "#d7ffd7"), (prompt_cmd, "#ffffff")], True))
    tx, ty, tw, th = 668, 48, 494, 384
    clips, tbody, tend, yend = typed(lines, tx + 20, ty + 58, 31, 14, start=0.6, cps=30, prefix="h")
    cur = cursor(tx + 20 + 14 * 0.602 * len("akshat@ahmedabad:~$ " + prompt_cmd) + 4, yend - 31, 14, tend)

    tb = [("LAST SYNC", sync_label()), ("OPERATOR", "A. SACHANI"), ("LOCATION", CFG["location"]),
          ("DWG NO.", f"AS-{NOW:%Y}-{NOW:%j}"), ("UPTIME", f"{S['streak']['current']}d STREAK"), ("SCALE", "10× LOAD")]
    tbx, tby, tbw = 40, 368, 600
    cells = ""
    for i, (k, v) in enumerate(tb):
        cx, cy = tbx + (i % 3) * (tbw / 3), tby + (i // 3) * 36
        cells += (f'<text x="{cx+10}" y="{cy+14}" fill="{BLUE}" font-size="9" letter-spacing="1.5">{k}</text>'
                  f'<text x="{cx+10}" y="{cy+30}" fill="{LINE}" font-size="13">{e(v)}</text>')
    grid = (f'<rect x="{tbx}" y="{tby}" width="{tbw}" height="72" fill="{BG}" stroke="{LINE}" stroke-width="1.4"/>'
            f'<line x1="{tbx}" y1="{tby+36}" x2="{tbx+tbw}" y2="{tby+36}" stroke="{LINE}" stroke-opacity=".5"/>'
            f'<line x1="{tbx+tbw/3:.0f}" y1="{tby}" x2="{tbx+tbw/3:.0f}" y2="{tby+72}" stroke="{LINE}" stroke-opacity=".5"/>'
            f'<line x1="{tbx+2*tbw/3:.0f}" y1="{tby}" x2="{tbx+2*tbw/3:.0f}" y2="{tby+72}" stroke="{LINE}" stroke-opacity=".5"/>')
    live = (f'<circle cx="{tbx+tbw-6}" cy="{tby-14}" r="4" fill="{GREEN}"><animate attributeName="opacity" values="1;.2;1" dur="1.4s" repeatCount="indefinite"/></circle>'
            f'<text x="{tbx+tbw-16}" y="{tby-10}" fill="{GREEN}" font-size="11" text-anchor="end" letter-spacing="2">LIVE · AUTO-SYNCED EVERY 3H</text>')
    big = f'font-size="57" font-weight="800" letter-spacing="2" style="{SANS}"'
    nm = (f'<text x="40" y="150" fill="none" stroke="{LINE}" stroke-width="1.4" {big} stroke-dasharray="700" stroke-dashoffset="700">{e(name)}'
          f'<animate attributeName="stroke-dashoffset" from="700" to="0" dur="2.8s" fill="freeze"/></text>'
          f'<text x="40" y="150" fill="{LINE}" {big} opacity="0">{e(name)}<animate attributeName="opacity" from="0" to="1" begin="2.3s" dur=".9s" fill="freeze"/></text>'
          f'<g opacity="0"><animate attributeName="opacity" values="0;.9;0;.7;0" keyTimes="0;.2;.4;.6;1" dur=".45s" begin="3.4s;9s;15s;21s"/>'
          f'<text x="45" y="148" fill="{PINK}" {big} opacity=".7">{e(name)}</text>'
          f'<text x="35" y="152" fill="{CYAN}" {big} opacity=".7">{e(name)}</text></g>')
    dim = (f'<line x1="40" y1="180" x2="630" y2="180" stroke="{LINE}" marker-start="url(#ar)" marker-end="url(#ar)"/>'
           f'<line x1="40" y1="168" x2="40" y2="190" stroke="{LINE}"/><line x1="630" y1="168" x2="630" y2="190" stroke="{LINE}"/>'
           f'<rect x="250" y="171" width="170" height="18" fill="{BG}"/><text x="335" y="184" fill="{BLUE}" font-size="11" text-anchor="middle" letter-spacing="1">SCALES HORIZONTALLY</text>')
    role = (f'<text x="42" y="226" fill="{LINE}" font-size="18">{e(CFG["role"])}</text>'
            f'<text x="42" y="252" fill="{BLUE}" font-size="13">{e(CFG["subline"])}</text>'
            f'<g fill="{BLUE}" font-size="11"><text x="42" y="298">NOTES:</text>'
            f'<text x="42" y="316">1. ALL SYSTEMS DESIGNED FOR 10× LOAD UNLESS NOTED.</text>'
            f'<text x="42" y="334">2. IF IT ISN&apos;T IN PRODUCTION, IT ISN&apos;T DONE.</text></g>')
    gr = (f'<g transform="translate(590 300)" opacity=".6"><g><path d="{gear(0,0,32,12)}" fill="none" stroke="{BLUE}"/><circle r="9" fill="none" stroke="{BLUE}"/>'
          f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="18s" repeatCount="indefinite"/></g></g>')
    body = (paper(W, H) + fig(40, 58, "FIG. 00 — THE OPERATOR · FRONT ELEVATION") + nm + dim + role + gr + grid + cells + live
            + term_window(tx, ty, tw, th, "akshat@ahmedabad: ~ — boot")
            + f'<g filter="url(#glow)">{tbody}{cur}</g>' + term_fx(tx, ty, tw, th, "hc") + demo_stamp(915, 448))
    write("hero.svg", svg(W, H, body, clips))


# ======================================================================  2. TELEMETRY
def odometer(x, y, value, fs, color, begin, pid):
    s = fmt(value)
    cw, lh = fs * 0.62, fs * 1.2
    total_w = len(s) * cw
    clip = f'<clipPath id="{pid}"><rect x="{x-2}" y="{y-fs}" width="{total_w+4:.0f}" height="{fs*1.28:.0f}"/></clipPath>'
    out = [f'<g clip-path="url(#{pid})">']
    digits = [c for c in s if c.isdigit()]
    di = 0
    for i, ch in enumerate(s):
        cx = x + i * cw
        if not ch.isdigit():
            out.append(f'<text x="{cx:.1f}" y="{y}" fill="{color}" font-size="{fs}">{ch}</text>'); continue
        spins = min(3, len(digits) - di)
        di += 1
        seq = list(range(10)) * spins + list(range(int(ch) + 1))
        off = (len(seq) - 1) * lh
        dur = 1.6 + spins * 0.35
        spans = "".join(f'<tspan x="{cx:.1f}" y="{y + k*lh:.1f}">{d}</tspan>' for k, d in enumerate(seq))
        out.append(f'<g transform="translate(0 0)"><animateTransform attributeName="transform" type="translate" values="0 0;0 {-off:.1f}" keyTimes="0;1" '
                   f'calcMode="spline" keySplines=".1 .7 .2 1" dur="{dur:.2f}s" begin="{begin:.2f}s" fill="freeze"/>'
                   f'<text fill="{color}" font-size="{fs}">{spans}</text></g>')
    out.append("</g>")
    return clip, "".join(out)


def xp_level():
    xp = T["commits_all"] + T["prs"] * 5 + T["merged"] * 3 + T["reviews"] * 4 + T["issues"] * 2 + T["stars"] * 10 + T["contribs_year"] // 2
    lvl = int(math.sqrt(xp) / 3) + 1
    lo, hi = ((lvl - 1) * 3) ** 2, (lvl * 3) ** 2
    pct = (xp - lo) / max(1, hi - lo)
    titles = [(5, "INTERN DAEMON"), (10, "JUNIOR SYSADMIN"), (15, "API ARTISAN"), (20, "BACKEND MAGE"), (30, "DISTRIBUTED SORCERER"), (999, "PRINCIPAL DEMIGOD")]
    title = next(t for lim, t in titles if lvl < lim)
    return xp, lvl, pct, hi, title


def chronotype():
    h = S.get("hours") or [0] * 24
    tot = sum(h) or 1
    night = sum(h[i] for i in (22, 23, 0, 1, 2, 3, 4)) / tot
    vamp = sum(h[i] for i in (0, 1, 2, 3, 4)) / tot
    morning = sum(h[i] for i in range(5, 11)) / tot
    evening = sum(h[i] for i in range(17, 22)) / tot
    if sum(h) == 0: return "UNKNOWN", night
    # label by the busiest 3-hour window, so the title always matches the chart
    c = max(range(24), key=lambda i: h[i] + h[(i + 1) % 24] + h[(i + 2) % 24])
    mid = (c + 1) % 24
    if 2 <= mid < 5: return "VAMPIRE MODE", night
    if 5 <= mid < 10: return "EARLY BIRD", night
    if 10 <= mid < 17: return "DAY SHIFTER", night
    if 17 <= mid < 22: return "EVENING ENGINEER", night
    return "NIGHT OWL", night


def achievements():
    _, night = chronotype()
    langs = len([l for l in S.get("languages", []) if l["bytes"] > 0])
    return [
        ("◆", "FOUNDER", True, "MoonlightDevs · DomainDock"),
        ("⇡", "FIRST MERGE", T["merged"] >= 1, "1+ merged PR"),
        ("⇶", "PR MACHINE", T["prs"] >= 50, "50+ pull requests"),
        ("◎", "CODE CRITIC", T["reviews"] >= 25, "25+ reviews"),
        ("7", "WEEK STREAK", S["streak"]["longest"] >= 7, "7-day streak"),
        ("30", "IRON STREAK", S["streak"]["longest"] >= 30, "30-day streak"),
        ("☾", "NIGHT OWL", night > .3, "30%+ commits after 10pm"),
        ("λ", "POLYGLOT", langs >= 5, "5+ languages"),
        ("★", "STARGAZER", T["stars"] >= 25, "25+ stars"),
        ("K", "1K CLUB", T["commits_all"] >= 1000, "1,000+ commits"),
    ]


def telemetry_svg():
    W, H = 1200, 640
    tiles = [("COMMITS", T["commits_all"], "all-time", GREEN),
             ("PULL REQUESTS", T["prs"], f"{fmt(T['merged'])} merged", CYAN),
             ("CONTRIBUTED TO", T["contributed_to"], "repositories, own + others", CYAN),
             ("CONTRIBUTIONS", T["contribs_year"], "last 365 days", GREEN),
             ("CURRENT STREAK", S["streak"]["current"], f"longest {S['streak']['longest']} days", AMBER),
             ("ACTIVE DAYS", S["streak"]["active_days_year"], f"{S['streak']['active_days_year']*100//365}% uptime this year", AMBER),
             ("ISSUES", T["issues"], f"opened · {fmt(T['reviews'])} code reviews", CYAN),
             ("STARS EARNED", T["stars"], f"across {fmt(T['repos'])} repos", PINK)]
    defs_, body = [], []
    tw, th, gx, gy = 268, 112, 20, 20
    x0, y0 = 40, 92
    for i, (lab, val, sub, col) in enumerate(tiles):
        x, y = x0 + (i % 4) * (tw + gx), y0 + (i // 4) * (th + gy)
        c, o = odometer(x + 18, y + 72, val, 40, col, 0.4 + i * 0.12, f"o{i}")
        defs_.append(c)
        body.append(f'<g><rect x="{x}" y="{y}" width="{tw}" height="{th}" fill="{BG}" fill-opacity=".85" stroke="{LINE}" stroke-opacity=".55"/>'
                    f'<path d="M{x} {y+14}V{y}H{x+14}M{x+tw-14} {y+th}H{x+tw}V{y+th-14}" stroke="{col}" stroke-width="2" fill="none"/>'
                    f'<text x="{x+18}" y="{y+24}" fill="{BLUE}" font-size="11" letter-spacing="2">{lab}</text>'
                    f'<text x="{x+tw-14}" y="{y+24}" fill="{col}" font-size="10" text-anchor="end">● LIVE<animate attributeName="opacity" values="1;.3;1" dur="{1.2+i*.1:.1f}s" repeatCount="indefinite"/></text>'
                    f'{o}<text x="{x+18}" y="{y+97}" fill="{LINE}" fill-opacity=".65" font-size="11">{e(sub)}</text></g>')
    # sparkline (last 30 days) inside the CONTRIBUTIONS tile area -> separate band
    flat = [d for w in S["calendar"] for d in w][-30:]
    mx = max([d["count"] for d in flat] + [1])
    # XP bar
    xp, lvl, pct, nxt, title = xp_level()
    yb = 372
    bw = 1120
    body.append(f'<text x="40" y="{yb}" fill="{BLUE}" font-size="11" letter-spacing="2">OPERATOR LEVEL</text>'
                f'<text x="40" y="{yb+34}" fill="{LINE}" font-size="28" font-weight="700">LVL {lvl}</text>'
                f'<text x="160" y="{yb+34}" fill="{GREEN}" font-size="20" filter="url(#glow)">{title}</text>'
                f'<text x="{40+bw}" y="{yb+34}" fill="{LINE}" fill-opacity=".7" font-size="13" text-anchor="end">{fmt(xp)} / {fmt(nxt)} XP → LVL {lvl+1}</text>'
                f'<rect x="40" y="{yb+48}" width="{bw}" height="16" fill="none" stroke="{LINE}" stroke-opacity=".6"/>'
                f'<rect x="42" y="{yb+50}" width="0" height="12" fill="{GREEN}"><animate attributeName="width" from="0" to="{(bw-4)*pct:.0f}" begin="1s" dur="2.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/></rect>'
                + "".join(f'<line x1="{40+bw*k/20:.0f}" y1="{yb+48}" x2="{40+bw*k/20:.0f}" y2="{yb+64}" stroke="{BG}" stroke-width="2"/>' for k in range(1, 20))
                + f'<text x="40" y="{yb+84}" fill="{BLUE}" font-size="10">XP = commits + 5·PRs + 3·merged + 4·reviews + 2·issues + 10·stars + ½·contributions(365d)</text>')
    # achievements
    ya = 500
    body.append(f'<text x="40" y="{ya}" fill="{BLUE}" font-size="11" letter-spacing="2">ACHIEVEMENTS · {sum(1 for a in achievements() if a[2])}/{len(achievements())} UNLOCKED</text>')
    for i, (gl, nm, ok, how) in enumerate(achievements()):
        cx, cy = 92 + i * 112, ya + 58
        r = 30
        hexp = " ".join(f"{cx + r*math.cos(math.radians(60*k-30)):.1f},{cy + r*math.sin(math.radians(60*k-30)):.1f}" for k in range(6))
        col = GREEN if ok else DIM
        anim = f'<animate attributeName="opacity" from="0" to="1" begin="{1.2+i*.15:.2f}s" dur=".4s" fill="freeze"/>'
        body.append(f'<g opacity="0">{anim}<polygon points="{hexp}" fill="{col if ok else BG}" fill-opacity="{.14 if ok else .6}" stroke="{col}" stroke-width="{1.8 if ok else 1}" {"stroke-dasharray=\"4 3\"" if not ok else ""}/>'
                    f'<text x="{cx}" y="{cy+7}" fill="{col if ok else DIM}" font-size="{18 if len(gl)==1 else 15}" font-weight="700" text-anchor="middle" {"filter=\"url(#glow)\"" if ok else ""}>{e(gl if ok else "?")}</text>'
                    f'<text x="{cx}" y="{cy+48}" fill="{LINE if ok else DIM}" font-size="10" text-anchor="middle" letter-spacing="1">{nm if ok else "LOCKED"}</text>'
                    f'<text x="{cx}" y="{cy+62}" fill="{BLUE}" fill-opacity="{.8 if ok else .5}" font-size="8.5" text-anchor="middle">{e(how)}</text></g>')
    head = (fig(40, 54, "FIG. 02 — LIVE TELEMETRY", None)
            + f'<text x="{W-40}" y="54" fill="{GREEN}" font-size="12" text-anchor="end">● SYNCED {e(sync_label())}<animate attributeName="opacity" values="1;.35;1" dur="1.6s" repeatCount="indefinite"/></text>'
            + f'<text x="40" y="74" fill="{LINE}" fill-opacity=".7" font-size="12">pulled from the GitHub GraphQL API by a scheduled Action — numbers roll in on every page load</text>')
    write("telemetry.svg", svg(W, H, paper(W, H) + head + "".join(body) + demo_stamp(1035, 366), "".join(defs_)))


# ======================================================================  3. SKYLINE
def skyline_svg():
    W, H = 1200, 560
    weeks = S["calendar"]
    flat = [d["count"] for w in weeks for d in w]
    mx = max(flat + [1])
    # levels like github: quartiles of non-zero
    nz = sorted(c for c in flat if c > 0)
    q = [nz[int(len(nz) * k / 4)] if nz else 1 for k in (1, 2, 3)]
    def level(c):
        if c == 0: return 0
        return 1 + sum(1 for t in q if c > t)
    top_col = {0: BG2, 1: "#1d4f9c", 2: "#2f74d6", 3: "#6fb0ff", 4: GREEN}
    ux, uy = 15.5, 4.2   # week axis
    vx, vy = -9.5, 7.0   # day axis
    sz = 0.82
    ox, oy = 150, 230
    zmax = 150
    items = []
    for c, w in enumerate(weeks):
        for d in w:
            r = date.fromisoformat(d["date"]).weekday()  # 0 Mon
            r = (r + 1) % 7  # Sunday first like GitHub
            items.append((c, r, d["count"], d["date"]))
    items.sort(key=lambda t: (t[1] + t[0] * 0.3, t[0]))
    blds = []
    for (c, r, cnt, dt) in items:
        bx, by = ox + c * ux + r * vx, oy + c * uy + r * vy
        h = 0 if cnt == 0 else 6 + (cnt / mx) * zmax
        U, V = (ux * sz, uy * sz), (vx * sz, vy * sz)
        p0 = (bx, by); p1 = (bx + U[0], by + U[1]); p2 = (p1[0] + V[0], p1[1] + V[1]); p3 = (bx + V[0], by + V[1])
        lv = level(cnt)
        col = top_col[lv]
        if h == 0:
            blds.append(f'<polygon points="{p0[0]:.1f},{p0[1]:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}" fill="{BG2}" fill-opacity=".55" stroke="{LINE}" stroke-opacity=".12" stroke-width=".5"/>')
            continue
        tp = lambda p: f"{p[0]:.1f},{p[1]-h:.1f}"
        bp = lambda p: f"{p[0]:.1f},{p[1]:.1f}"
        top = f'<polygon points="{tp(p0)} {tp(p1)} {tp(p2)} {tp(p3)}" fill="{col}" fill-opacity="{.95 if lv==4 else .85}" stroke="{LINE}" stroke-opacity=".55" stroke-width=".5"/>'
        front = f'<polygon points="{tp(p3)} {tp(p2)} {bp(p2)} {bp(p3)}" fill="{col}" fill-opacity=".45" stroke="{LINE}" stroke-opacity=".35" stroke-width=".5"/>'
        right = f'<polygon points="{tp(p1)} {tp(p2)} {bp(p2)} {bp(p1)}" fill="{col}" fill-opacity=".28" stroke="{LINE}" stroke-opacity=".35" stroke-width=".5"/>'
        ax, ay = p2[0], p2[1]
        begin = 0.3 + c * 0.035 + r * 0.02
        blds.append(f'<g transform="translate({ax:.1f} {ay:.1f})"><g transform="scale(1 0)">'
                    f'<animateTransform attributeName="transform" type="scale" values="1 0;1 1.08;1 1" keyTimes="0;.8;1" dur=".9s" begin="{begin:.2f}s" fill="freeze"/>'
                    f'<g transform="translate({-ax:.1f} {-ay:.1f})">{front}{right}{top}</g></g></g>')
    # axes / dimension lines
    end_c = len(weeks)
    a0 = (ox + 6 * vx + 0 * ux - 14, oy + 7 * vy + 18)
    a1 = (ox + 6 * vx + end_c * ux - 14, oy + 7 * vy + end_c * uy + 18)
    dims = (f'<line x1="{a0[0]:.0f}" y1="{a0[1]:.0f}" x2="{a1[0]:.0f}" y2="{a1[1]:.0f}" stroke="{LINE}" marker-start="url(#ar)" marker-end="url(#ar)"/>'
            f'<text transform="translate({(a0[0]+a1[0])/2:.0f} {(a0[1]+a1[1])/2+18:.0f}) rotate({math.degrees(math.atan2(uy, ux)):.1f})" fill="{BLUE}" font-size="11" text-anchor="middle" letter-spacing="2">52 WEEKS →</text>')
    best = S.get("best_day") or {}
    wd = S.get("weekday") or [0] * 7
    wdn = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][wd.index(max(wd))] if any(wd) else "—"
    # info panel
    px = 860
    info = [("TOTAL (365D)", fmt(T["contribs_year"])), ("PEAK DAY", f"{best.get('count', 0)} on {best.get('date', '—')}"),
            ("BUSIEST WEEKDAY", wdn), ("ACTIVE DAYS", f"{S['streak']['active_days_year']} / 365"),
            ("LONGEST STREAK", f"{S['streak']['longest']} days")]
    panel = (f'<rect x="{px}" y="70" width="300" height="{len(info)*38+20}" fill="{BG}" stroke="{LINE}" stroke-opacity=".6"/>'
             + "".join(f'<text x="{px+16}" y="{96+i*38}" fill="{BLUE}" font-size="9.5" letter-spacing="1.5">{k}</text>'
                       f'<text x="{px+16}" y="{113+i*38}" fill="{GREEN if i==0 else LINE}" font-size="14">{e(v)}</text>' for i, (k, v) in enumerate(info)))
    legend = "".join(f'<rect x="{px+16+i*28}" y="{100+len(info)*38}" width="18" height="18" fill="{top_col[i]}" stroke="{LINE}" stroke-opacity=".4"/>' for i in range(5))
    legend += f'<text x="{px+16+5*28+4}" y="{113+len(info)*38}" fill="{BLUE}" font-size="10">LESS → MORE</text>'
    laser = (f'<linearGradient id="lz" x1="0" x2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset=".5" stop-color="{GREEN}" stop-opacity=".22"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>')
    scan = (f'<rect x="-80" y="40" width="80" height="{H-80}" fill="url(#lz)"><animate attributeName="x" values="-80;{W};{W}" keyTimes="0;.6;1" dur="7s" begin="3s" repeatCount="indefinite"/></rect>')
    head = fig(40, 54, "FIG. 03 — 52-WEEK CONTRIBUTION SKYLINE", "every building is a day · height = contributions · live from GitHub")
    write("skyline.svg", svg(W, H, paper(W, H) + head + "".join(blds) + dims + panel + legend + scan + demo_stamp(1010, 336), laser))


# ======================================================================  4. CIRCADIAN CLOCK
def clock_svg():
    W, H = 590, 560
    cx, cy, r0, r1 = 295, 318, 60, 182
    hrs = S.get("hours") or [0] * 24
    mx = max(hrs + [1])
    parts = []
    # night shading 18:00-06:00 (angle: hour*15 - 90, 0h at top)
    def pt(rr, ang):
        a = math.radians(ang - 90)
        return cx + rr * math.cos(a), cy + rr * math.sin(a)
    def arc(ra, rb, a0, a1):
        p0, p1, p2, p3 = pt(rb, a0), pt(rb, a1), pt(ra, a1), pt(ra, a0)
        large = 1 if (a1 - a0) > 180 else 0
        return (f"M{p0[0]:.1f} {p0[1]:.1f} A{rb} {rb} 0 {large} 1 {p1[0]:.1f} {p1[1]:.1f} "
                f"L{p2[0]:.1f} {p2[1]:.1f} A{ra} {ra} 0 {large} 0 {p3[0]:.1f} {p3[1]:.1f}Z")
    parts.append(f'<path d="{arc(r0, r1+12, 270, 450)}" fill="#000" fill-opacity=".25"/>')
    for rr in (r0, (r0 + r1) / 2, r1, r1 + 12):
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{rr:.0f}" fill="none" stroke="{LINE}" stroke-opacity=".18"/>')
    for h in range(24):
        a = h * 15
        p, q = pt(r1 + 12, a), pt(r1 + (22 if h % 3 == 0 else 17), a)
        parts.append(f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="{LINE}" stroke-opacity=".6"/>')
        if h % 3 == 0:
            t = pt(r1 + 36, a)
            parts.append(f'<text x="{t[0]:.1f}" y="{t[1]+4:.1f}" fill="{BLUE}" font-size="11" text-anchor="middle">{h:02d}</text>')
        v = hrs[h] / mx
        rb = r0 + 4 + v * (r1 - r0 - 4)
        col = GREEN if v > .75 else (CYAN if v > .4 else BLUE)
        d = arc(r0 + 2, rb, a + 1.5, a + 13.5)
        parts.append(f'<g transform="translate({cx} {cy})"><g transform="scale(0)"><animateTransform attributeName="transform" type="scale" from="0" to="1" begin="{.3+h*.05:.2f}s" dur=".8s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/>'
                     f'<g transform="translate({-cx} {-cy})"><path d="{d}" fill="{col}" fill-opacity="{.35+.55*v:.2f}" stroke="{col}" stroke-width=".8"/></g></g></g>')
    # sweep hand
    p = pt(r1 + 10, 0)
    parts.append(f'<g><line x1="{cx}" y1="{cy}" x2="{p[0]:.1f}" y2="{p[1]:.1f}" stroke="{GREEN}" stroke-width="1.6" filter="url(#glow)"/>'
                 f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="10s" repeatCount="indefinite"/></g>')
    # now marker
    nowa = (NOW.hour + NOW.minute / 60) * 15
    n0, n1 = pt(r1 + 12, nowa), pt(r1 + 26, nowa)
    parts.append(f'<line x1="{n0[0]:.1f}" y1="{n0[1]:.1f}" x2="{n1[0]:.1f}" y2="{n1[1]:.1f}" stroke="{AMBER}" stroke-width="3"/>')
    ct, _ = chronotype()
    pk0 = max(range(24), key=lambda i: hrs[i] + hrs[(i + 1) % 24] + hrs[(i + 2) % 24]) if any(hrs) else 0
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r0-6}" fill="{BG}" stroke="{LINE}" stroke-opacity=".5"/>'
                 f'<text x="{cx}" y="{cy-10}" fill="{BLUE}" font-size="9" text-anchor="middle" letter-spacing="1.5">CHRONOTYPE</text>'
                 f'<text x="{cx}" y="{cy+8}" fill="{GREEN}" font-size="{13 if len(ct) < 12 else 10}" font-weight="700" text-anchor="middle" filter="url(#glow)">{ct}</text>'
                 f'<text x="{cx}" y="{cy+26}" fill="{LINE}" fill-opacity=".7" font-size="10" text-anchor="middle">peak {pk0:02d}–{(pk0+3)%24:02d}h</text>')
    head = (fig(30, 50, "FIG. 04 — CIRCADIAN PROFILE", f"when the commits land · {TZN} · {sum(hrs)} recent commits")
            + f'<g font-size="10"><rect x="30" y="{H-46}" width="10" height="10" fill="{AMBER}"/><text x="46" y="{H-37}" fill="{BLUE}">NOW ({NOW:%H:%M})</text>'
              f'<rect x="150" y="{H-46}" width="10" height="10" fill="#000" fill-opacity=".4" stroke="{LINE}" stroke-opacity=".3"/><text x="166" y="{H-37}" fill="{BLUE}">NIGHT 18–06</text></g>')
    write("clock.svg", svg(W, H, paper(W, H) + head + "".join(parts) + demo_stamp(440, 526)))


# ======================================================================  6. ARCHITECTURE
def arch_svg():
    W, H = 1200, 520
    def box(x, y, w, h, title, sub, hard=False):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BG}" stroke="{LINE}" stroke-width="{1.8 if hard else 1.1}"/>'
                f'<text x="{x+w/2}" y="{y+h/2-3}" fill="{LINE}" font-size="14" text-anchor="middle" font-weight="700">{title}</text>'
                f'<text x="{x+w/2}" y="{y+h/2+15}" fill="{BLUE}" font-size="11" text-anchor="middle">{sub}</text>')
    nodes = [box(40, 210, 150, 80, "CLIENTS", "web · CLI · GitHub PRs"), box(250, 210, 170, 80, "EDGE", "Traefik · auto-TLS · DNS", True),
             box(480, 210, 190, 80, "API LAYER", "Node.js · NestJS · GraphQL", True)]
    svc = [("AUTH + RBAC", "multi-role access"), ("PAYMENTS", "Razorpay flows"), ("REAL-TIME", "Socket.IO"), ("AI WORKERS", "LLM review · search")]
    dat = [("POSTGRESQL", "relational core"), ("MONGODB", "documents"), ("REDIS", "cache · sessions"), ("RABBITMQ", "queues · jobs")]
    for i, (t, s) in enumerate(svc): nodes.append(box(740, 82 + i * 95, 180, 66, t, s))
    for i, (t, s) in enumerate(dat): nodes.append(box(990, 82 + i * 95, 170, 66, t, s))
    paths = ["M190 250 H250", "M420 250 H480"]
    for i in range(4):
        y = 115 + i * 95
        paths += [f"M670 250 C705 250 705 {y} 740 {y}", f"M920 {y} H990"]
    paths += ["M920 400 C955 400 955 305 990 305", "M920 115 C955 115 955 210 990 210"]
    edges = "".join(f'<path d="{d}" fill="none" stroke="{LINE}" stroke-opacity=".65" stroke-width="1.1" marker-end="url(#ar)"/>' for d in paths)
    pk = []
    for i, d in enumerate(paths):
        for k in range(2):
            dur = 1.5 + (i % 3) * .45
            col = GREEN if i % 3 else AMBER
            pk.append(f'<circle r="3.5" fill="{col}" filter="url(#glow)"><animateMotion dur="{dur:.2f}s" begin="{(i*.37 + k*dur/2):.2f}s" repeatCount="indefinite" path="{d}"/></circle>')
    rps = T["contribs_year"]
    head = (fig(40, 54, "FIG. 08 — REFERENCE ARCHITECTURE", "the shape most of my systems take")
            + f'<text x="740" y="70" fill="{BLUE}" font-size="11" letter-spacing="2">SERVICES</text><text x="990" y="70" fill="{BLUE}" font-size="11" letter-spacing="2">DATA + MESSAGING</text>')
    meter = (f'<rect x="40" y="350" width="630" height="96" fill="{TERM}" stroke="{GREEN}" stroke-opacity=".4" rx="6"/>'
             f'<text x="56" y="376" fill="#6f9f7f" font-size="12">$ watch -n 3h throughput</text>'
             f'<text x="56" y="402" fill="{GREEN}" font-size="14">commits/yr  <tspan fill="#fff">{fmt(rps)}</tspan>   PRs  <tspan fill="#fff">{fmt(T["prs"])}</tspan>   merged  <tspan fill="#fff">{fmt(T["merged"])}</tspan>   reviews  <tspan fill="#fff">{fmt(T["reviews"])}</tspan></text>'
             f'<text x="56" y="428" fill="#6f9f7f" font-size="12">p99 latency: low · error budget: healthy · coffee: critical</text>')
    leg = (f'<g transform="translate(40 480)" font-size="11"><circle cx="6" cy="-4" r="4" fill="{GREEN}"/><text x="18" y="0" fill="{BLUE}">LIVE REQUEST</text>'
           f'<line x1="130" y1="-4" x2="170" y2="-4" stroke="{LINE}" marker-end="url(#ar)"/><text x="180" y="0" fill="{BLUE}">DATA FLOW</text>'
           f'<rect x="270" y="-12" width="22" height="14" fill="none" stroke="{LINE}" stroke-width="1.8"/><text x="300" y="0" fill="{BLUE}">HARDENED LAYER</text></g>'
           f'<text x="{W-40}" y="{H-40}" fill="{BLUE}" font-size="11" text-anchor="end">SIMPLIFIED · NOT TO SCALE · SCALES ANYWAY</text>')
    write("architecture.svg", svg(W, H, paper(W, H) + head + edges + "".join(nodes) + "".join(pk) + meter + leg))


# ======================================================================  9. FOOTER
def footer_svg():
    W, H = 1200, 170
    stamp = (f'<g transform="translate(980 86) rotate(-9)"><g opacity="0"><animate attributeName="opacity" values="0;1" begin="1.2s" dur=".15s" fill="freeze"/>'
             f'<animateTransform attributeName="transform" type="scale" values="2.2;.95;1" keyTimes="0;.7;1" begin="1.2s" dur=".35s" fill="freeze"/>'
             f'<rect x="-150" y="-36" width="300" height="72" rx="6" fill="none" stroke="{GREEN}" stroke-width="3"/>'
             f'<rect x="-143" y="-29" width="286" height="58" rx="4" fill="none" stroke="{GREEN}" stroke-width="1"/>'
             f'<text y="-4" fill="{GREEN}" font-size="20" font-weight="800" text-anchor="middle" letter-spacing="3">APPROVED</text>'
             f'<text y="18" fill="{GREEN}" font-size="11" text-anchor="middle" letter-spacing="2">FOR PRODUCTION · {NOW:%Y-%m-%d}</text></g></g>')
    txt = (f'<text x="48" y="74" fill="{LINE}" font-size="18" letter-spacing="6">END OF DRAWING</text>'
           f'<text x="48" y="102" fill="{BLUE}" font-size="12">designed in Ahmedabad · rendered by GitHub Actions · regenerated every 3 hours</text>'
           f'<text x="48" y="126" fill="#6f9f7f" font-size="12">akshat@ahmedabad:~$ logout<tspan fill="{GREEN}"> █<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan></text>')
    write("footer.svg", svg(W, H, paper(W, H) + txt + stamp))


# ======================================================================  helpers (v2)
import base64, re, random as _rnd

UP = json.load(open(os.path.join(ROOT, "data", "uptime.json"))) if os.path.exists(os.path.join(ROOT, "data", "uptime.json")) else {}


def wrap(text, n):
    out, cur = [], ""
    for w in str(text).split():
        if len(cur) + len(w) + 1 > n:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + ([cur] if cur else [])


def data_uri(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return None
    mime = "image/png" if path.endswith(".png") else "image/svg+xml"
    return f"data:{mime};base64," + base64.b64encode(open(full, "rb").read()).decode()


def pill(x, y, text, color, fs=10, fill_op=.12, anchor="start"):
    w = len(text) * fs * 0.62 + 16
    x0 = x if anchor == "start" else x - w
    return (f'<rect x="{x0:.0f}" y="{y-fs-4}" width="{w:.0f}" height="{fs+9}" rx="{(fs+9)/2:.1f}" fill="{color}" fill-opacity="{fill_op}" stroke="{color}" stroke-opacity=".7"/>'
            f'<text x="{x0+8:.0f}" y="{y}" fill="{color}" font-size="{fs}" letter-spacing=".6">{e(text)}</text>'), w


def blink_dot(cx, cy, color, r=5):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="2">'
            f'<animate attributeName="r" values="{r};{r*3}" dur="1.6s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values=".9;0" dur="1.6s" repeatCount="indefinite"/></circle>')


def glyph(kind, x, y, s):
    cx, cy = x + s / 2, y + s / 2
    if kind == "target":
        return (f'<circle cx="{cx}" cy="{cy}" r="{s*.38:.1f}" fill="none" stroke="{CYAN}" stroke-width="2"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{s*.24:.1f}" fill="none" stroke="{CYAN}" stroke-width="2"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{s*.09:.1f}" fill="{GREEN}"><animate attributeName="opacity" values="1;.3;1" dur="1.2s" repeatCount="indefinite"/></circle>'
                f'<path d="M{cx+s*.42:.1f} {cy-s*.42:.1f} L{cx+s*.06:.1f} {cy-s*.06:.1f}" stroke="{AMBER}" stroke-width="2.5"/>'
                f'<path d="M{cx+s*.42:.1f} {cy-s*.42:.1f} l-{s*.14:.1f} 0 M{cx+s*.42:.1f} {cy-s*.42:.1f} l0 {s*.14:.1f}" stroke="{AMBER}" stroke-width="2.5"/>')
    rays = "".join(f'<line x1="{cx + s*.3*math.cos(math.radians(a)):.1f}" y1="{cy + s*.3*math.sin(math.radians(a)):.1f}" '
                   f'x2="{cx + s*.44*math.cos(math.radians(a)):.1f}" y2="{cy + s*.44*math.sin(math.radians(a)):.1f}" stroke="{AMBER}" stroke-width="2.5" stroke-linecap="round"/>'
                   for a in range(0, 360, 45))
    return (f'<g><g>{rays}<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="16s" repeatCount="indefinite"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="{s*.2:.1f}" fill="{AMBER}" fill-opacity=".9"/></g>')


# ======================================================================  06. PRODUCT CARDS
def product_card_svg(p):
    W, H = 590, 350
    st = p.get("status")
    body = [paper(W, H)]
    # logo
    body.append(f'<rect x="36" y="40" width="76" height="76" rx="16" fill="{BG2}" stroke="{LINE}" stroke-opacity=".5"/>')
    uri = data_uri(p["logo"]) if p.get("logo") else None
    if uri:
        body.append(f'<clipPath id="lg"><rect x="42" y="46" width="64" height="64" rx="12"/></clipPath>'
                    f'<image href="{uri}" x="42" y="46" width="64" height="64" clip-path="url(#lg)" preserveAspectRatio="xMidYMid meet"/>')
    else:
        body.append(glyph(p.get("glyph", "sun"), 42, 46, 64))
    body.append(f'<text x="132" y="74" fill="{LINE}" font-size="27" font-weight="800" style="{SANS}">{e(p["name"])}</text>')
    rc = {"FOUNDER": GREEN, "INVITE ONLY": CYAN, "OPEN SOURCE": AMBER}.get(p.get("role", ""), BLUE)
    body.append(pill(134, 104, p.get("role", ""), rc)[0])
    # status (top-right)
    hist = UP.get(p["id"], [])
    last = hist[-1] if hist else None
    if st == "live":
        ok = (last or {}).get("ok", True)
        col, label = (GREEN, "ONLINE") if ok else (RED, "DOWN")
        body.append(blink_dot(W - 120, 56, col) + f'<text x="{W-106}" y="61" fill="{col}" font-size="13" font-weight="700" letter-spacing="1.5">{label}</text>')
    elif st == "invite":
        body.append(f'<g transform="translate({W-164} 46)"><rect x="0" y="6" width="14" height="11" rx="2" fill="{CYAN}"/><path d="M3 6V3a4 4 0 0 1 8 0v3" fill="none" stroke="{CYAN}" stroke-width="2"/></g>'
                    f'<text x="{W-142}" y="61" fill="{CYAN}" font-size="13" font-weight="700" letter-spacing="1.5">PRIVATE BETA</text>')
    else:
        body.append(blink_dot(W - 130, 56, AMBER) + f'<text x="{W-116}" y="61" fill="{AMBER}" font-size="13" font-weight="700" letter-spacing="1.5">BUILDING</text>')
    host = re.sub(r"^(https?://|mailto:)", "", p.get("url", "")).split("/")[0].split("?")[0]
    if st == "invite": host = "request access →"
    if host:
        body.append(f'<text x="{W-36}" y="84" fill="{BLUE}" font-size="11.5" text-anchor="end">{e(host)}</text>')
    # copy
    body.append(f'<text x="36" y="152" fill="{LINE}" font-size="15" font-weight="600" style="{SANS}">{e(p.get("tagline", ""))}</text>')
    for i, l in enumerate(wrap(p.get("desc", ""), 72)[:4]):
        body.append(f'<text x="36" y="{178 + i*18}" fill="{BLUE}" font-size="12">{e(l)}</text>')
    tx = 36
    for t in p.get("tags", []):
        g, w = pill(tx, 264, t, LINE, fs=10, fill_op=.05)
        body.append(g); tx += w + 8
    # bottom band
    yb = 284
    if st == "live":
        n, x0, bw = 56, 36, W - 72
        slot = bw / n
        pad = [None] * (n - len(hist)) + hist[-n:]
        for i, h in enumerate(pad):
            col = DIM if h is None else (GREEN if h["ok"] else RED)
            op = .35 if h is None else .9
            body.append(f'<rect x="{x0 + i*slot:.1f}" y="{yb}" width="{slot-2:.1f}" height="18" rx="1.5" fill="{col}" fill-opacity="{op}"/>')
        if hist:
            up = sum(1 for h in hist if h["ok"]) / len(hist) * 100
            ms = [h["ms"] for h in hist if h["ok"]][-8:]
            avg = int(sum(ms) / len(ms)) if ms else 0
            span = "7d" if len(hist) >= 56 else f"{len(hist)} checks"
            txt = f"UPTIME {span}: {up:.1f}%  ·  avg response {avg} ms  ·  last check {sync_label()}"
        else:
            txt = "uptime monitor starts on the next sync"
        body.append(f'<text x="36" y="{yb+36}" fill="{BLUE}" font-size="10.5">{e(txt)}</text>')
    elif st == "invite":
        rng = _rnd.Random(p["id"]); price = 50.0
        n, x0, bw = 44, 36, W - 72
        slot = bw / n
        cs = []
        for i in range(n):
            o = price; c = o + rng.uniform(-4, 4.4); hi = max(o, c) + rng.uniform(0, 2.5); lo = min(o, c) - rng.uniform(0, 2.5); price = c
            cs.append((o, c, hi, lo))
        mn = min(c[3] for c in cs); mx = max(c[2] for c in cs)
        Y = lambda v: yb + 26 - (v - mn) / (mx - mn) * 30
        for i, (o, c, hi, lo) in enumerate(cs):
            col = GREEN if c >= o else RED
            cx = x0 + i * slot + slot / 2
            begin = i * 0.08
            body.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.05;.9;1" dur="6s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
                        f'<line x1="{cx:.1f}" y1="{Y(hi):.1f}" x2="{cx:.1f}" y2="{Y(lo):.1f}" stroke="{col}"/>'
                        f'<rect x="{cx - slot*.3:.1f}" y="{min(Y(o), Y(c)):.1f}" width="{slot*.6:.1f}" height="{max(1.2, abs(Y(o)-Y(c))):.1f}" fill="{col}"/></g>')
        body.append(f'<text x="36" y="{yb+40}" fill="{BLUE}" font-size="10.5">private repository · invite-only access · click the card to request an invite</text>')
    else:
        body.append(f'<clipPath id="tape"><rect x="36" y="{yb}" width="{W-72}" height="22"/></clipPath>'
                    f'<pattern id="hz" width="28" height="22" patternUnits="userSpaceOnUse"><rect width="28" height="22" fill="#111"/><path d="M0 22 L14 0 H28 L14 22Z" fill="{AMBER}"/>'
                    f'<animateTransform attributeName="patternTransform" type="translate" from="0 0" to="28 0" dur="1.2s" repeatCount="indefinite"/></pattern>'
                    f'<g clip-path="url(#tape)"><rect x="36" y="{yb}" width="{W-72}" height="22" fill="url(#hz)"/>'
                    f'<rect x="{W/2-120}" y="{yb+2}" width="240" height="18" fill="#111"/>'
                    f'<text x="{W/2}" y="{yb+15}" fill="{AMBER}" font-size="11" font-weight="700" text-anchor="middle" letter-spacing="2">UNDER CONSTRUCTION</text></g>'
                    f'<text x="36" y="{yb+40}" fill="{BLUE}" font-size="10.5">being built in the open · public release coming soon</text>')
    write(f"product-{p['id']}.svg", svg(W, H, "".join(body)))


# ======================================================================  04b. PUNCH CARD
def punchcard_svg():
    W, H = 590, 560
    pc = S.get("punch")
    parts = [paper(W, H), fig(30, 50, "FIG. 04B — WEEKLY PUNCH CARD", f"commits by weekday × hour · {TZN}")]
    if not pc:
        parts.append(f'<text x="{W/2}" y="300" fill="{BLUE}" text-anchor="middle">awaiting next sync</text>')
        write("punchcard.svg", svg(W, H, "".join(parts))); return
    mx = max(max(r) for r in pc) or 1
    x0, y0, cw, rh = 82, 108, 20, 44
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    best = max(((d, h) for d in range(7) for h in range(24)), key=lambda t: pc[t[0]][t[1]])
    for d in range(7):
        y = y0 + d * rh
        parts.append(f'<text x="{x0-16}" y="{y+4}" fill="{BLUE}" font-size="11" text-anchor="end">{days[d]}</text>'
                     f'<line x1="{x0-6}" y1="{y}" x2="{x0 + 23*cw + 6}" y2="{y}" stroke="{LINE}" stroke-opacity=".08"/>')
        for h in range(24):
            v = pc[d][h]
            cx = x0 + h * cw
            if v == 0:
                parts.append(f'<circle cx="{cx}" cy="{y}" r="1.2" fill="{LINE}" fill-opacity=".25"/>'); continue
            r = 2.5 + math.sqrt(v / mx) * 7.5
            col = GREEN if v / mx > .66 else (CYAN if v / mx > .33 else BLUE)
            parts.append(f'<circle cx="{cx}" cy="{y}" r="{r:.1f}" fill="{col}" fill-opacity=".85" opacity="0">'
                         f'<animate attributeName="opacity" from="0" to="1" begin="{.2 + h*.04 + d*.03:.2f}s" dur=".4s" fill="freeze"/></circle>')
    for h in range(0, 24, 3):
        parts.append(f'<text x="{x0 + h*cw}" y="{y0 + 7*rh - 14}" fill="{BLUE}" font-size="10" text-anchor="middle">{h:02d}</text>')
    bd, bh = best
    parts.append(f'<circle cx="{x0 + bh*cw}" cy="{y0 + bd*rh}" r="13" fill="none" stroke="{AMBER}" stroke-width="1.5" stroke-dasharray="3 2">'
                 f'<animateTransform attributeName="transform" type="rotate" from="0 {x0 + bh*cw} {y0 + bd*rh}" to="360 {x0 + bh*cw} {y0 + bd*rh}" dur="8s" repeatCount="indefinite"/></circle>')
    # period split
    hrs = S.get("hours") or [0] * 24
    tot = sum(hrs) or 1
    periods = [("MORNING 05–12", range(5, 12)), ("AFTERNOON 12–17", range(12, 17)), ("EVENING 17–22", range(17, 22)), ("NIGHT 22–05", [22, 23, 0, 1, 2, 3, 4])]
    yp = 440
    parts.append(f'<text x="30" y="{yp}" fill="{BLUE}" font-size="10" letter-spacing="1.5">BUSIEST SLOT: <tspan fill="{AMBER}">{days[bd]} {bh:02d}:00</tspan>   ·   SHARE OF COMMITS BY TIME OF DAY</text>')
    for i, (lab, rg) in enumerate(periods):
        share = sum(hrs[h] for h in rg) / tot
        y = yp + 22 + i * 20
        parts.append(f'<text x="30" y="{y+4}" fill="{LINE}" font-size="10.5">{lab}</text>'
                     f'<rect x="170" y="{y-6}" width="330" height="10" fill="{LINE}" fill-opacity=".06"/>'
                     f'<rect x="170" y="{y-6}" width="0" height="10" fill="{GREEN if share == max(sum(hrs[h] for h in r)/tot for _, r in periods) else CYAN}">'
                     f'<animate attributeName="width" from="0" to="{330*share:.1f}" begin="{.8+i*.15:.2f}s" dur=".9s" fill="freeze"/></rect>'
                     f'<text x="{W-30}" y="{y+4}" fill="{LINE}" font-size="10.5" text-anchor="end">{share*100:.0f}%</text>')
    write("punchcard.svg", svg(W, H, "".join(parts)))


# ======================================================================  06b. BILL OF MATERIALS (wide)
def bom_svg():
    W, H = 1200, 420
    langs = [l for l in S.get("languages", []) if l["bytes"] > 0][:6]
    tot = sum(l["bytes"] for l in langs) or 1
    parts = [paper(W, H), fig(40, 54, "FIG. 05 — BILL OF MATERIALS", "languages by bytes across my repos  ·  sub-assemblies I build with")]
    x, bw, acc = 40, 540, 0
    for i, l in enumerate(langs):
        wv = bw * l["bytes"] / tot
        parts.append(f'<rect x="{x+acc:.1f}" y="96" width="0" height="20" fill="{l["color"]}"><animate attributeName="width" from="0" to="{max(wv-1,0):.1f}" begin="{.3+i*.12:.2f}s" dur=".6s" fill="freeze"/></rect>')
        acc += wv
    parts.append(f'<rect x="{x}" y="96" width="{bw}" height="20" fill="none" stroke="{LINE}" stroke-opacity=".7"/>')
    y0 = 150
    parts.append(f'<text x="40" y="{y0}" fill="{BLUE}" font-size="10" letter-spacing="1.5">ITEM  MATERIAL</text><text x="{40+bw}" y="{y0}" fill="{BLUE}" font-size="10" letter-spacing="1.5" text-anchor="end">QTY · SHARE</text>'
                 f'<line x1="40" y1="{y0+10}" x2="{40+bw}" y2="{y0+10}" stroke="{LINE}" stroke-opacity=".5"/>')
    for i, l in enumerate(langs):
        y = y0 + 38 + i * 36
        pct = l["bytes"] / tot; kb = l["bytes"] / 1024
        qty = f"{kb/1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"
        parts.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{.5+i*.1:.2f}s" dur=".4s" fill="freeze"/>'
                     f'<text x="40" y="{y}" fill="{BLUE}" font-size="12">{i+1:02d}</text><rect x="74" y="{y-10}" width="10" height="10" fill="{l["color"]}"/>'
                     f'<text x="92" y="{y}" fill="{LINE}" font-size="14">{e(l["name"])}</text>'
                     f'<text x="{40+bw-70}" y="{y}" fill="{LINE}" fill-opacity=".6" font-size="12" text-anchor="end">{qty}</text>'
                     f'<text x="{40+bw}" y="{y}" fill="{GREEN}" font-size="14" text-anchor="end">{pct*100:.1f}%</text>'
                     f'<rect x="74" y="{y+7}" width="{bw-34}" height="3" fill="{LINE}" fill-opacity=".08"/>'
                     f'<rect x="74" y="{y+7}" width="0" height="3" fill="{l["color"]}"><animate attributeName="width" from="0" to="{(bw-34)*pct:.1f}" begin="{.7+i*.1:.2f}s" dur="1s" fill="freeze"/></rect></g>')
    # sub-assemblies
    sx = 640
    parts.append(f'<rect x="{sx}" y="88" width="{W-40-sx}" height="{H-128}" fill="{BG}" stroke="{LINE}" stroke-opacity=".5"/>'
                 f'<text x="{sx+18}" y="112" fill="{BLUE}" font-size="10" letter-spacing="1.5">SUB-ASSEMBLIES</text>')
    for i, (k, v) in enumerate(CFG.get("stack", [])[:7]):
        y = 146 + i * 34
        parts.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{.6+i*.1:.2f}s" dur=".4s" fill="freeze"/>'
                     f'<text x="{sx+18}" y="{y}" fill="{CYAN}" font-size="11" letter-spacing="1">{e(k)}</text>'
                     f'<text x="{sx+130}" y="{y}" fill="{LINE}" font-size="13">{e(v)}</text>'
                     f'<line x1="{sx+18}" y1="{y+12}" x2="{W-58}" y2="{y+12}" stroke="{LINE}" stroke-opacity=".08"/></g>')
    write("languages.svg", svg(W, H, "".join(parts)))


# ======================================================================  07. PULSE
def pulse_svg():
    W, H = 1200, 560
    flat = [d for w in S.get("calendar", []) for d in w]
    days = flat[-30:]
    counts = [d["count"] for d in days]
    wk, prev = sum(counts[-7:]), sum(counts[-14:-7])
    delta = ((wk - prev) / prev * 100) if prev else (100.0 if wk else 0.0)
    today = counts[-1] if counts else 0
    active = sum(1 for c in counts if c)
    lc = S.get("last_commit")
    if not lc and S.get("events"): lc = S["events"][0]["time"]
    cmp = (f"{'▲' if delta >= 0 else '▼'} {abs(delta):.0f}% vs last week ({prev})") if prev >= 5 else f"last week: {prev}"
    kpis = [("THIS WEEK", fmt(wk), cmp, GREEN if delta >= 0 else AMBER),
            ("TODAY", fmt(today), f"contributions · {NOW:%a %d %b}", CYAN),
            ("LAST 30 DAYS", fmt(sum(counts)), f"{sum(counts)/30:.1f} per day on average", GREEN),
            ("ACTIVE DAYS", f"{active}/30", "days with a contribution", AMBER),
            ("LAST COMMIT", ago(lc) if lc else "—", "most recent commit I authored", PINK)]
    parts = [paper(W, H), fig(40, 54, "FIG. 07 — PULSE · LAST 30 DAYS", "what I shipped recently — real contribution data, refreshed every 3 hours")]
    kw = (W - 80 - 4 * 16) / 5
    for i, (lab, val, sub, col) in enumerate(kpis):
        x = 40 + i * (kw + 16)
        parts.append(f'<rect x="{x:.0f}" y="84" width="{kw:.0f}" height="86" fill="{BG}" stroke="{LINE}" stroke-opacity=".5"/>'
                     f'<path d="M{x:.0f} 96V84H{x+12:.0f}" stroke="{col}" stroke-width="2" fill="none"/>'
                     f'<text x="{x+14:.0f}" y="104" fill="{BLUE}" font-size="10" letter-spacing="1.5">{lab}</text>'
                     f'<text x="{x+14:.0f}" y="138" fill="{col}" font-size="26" font-weight="700" filter="url(#glow)">{e(val)}</text>'
                     f'<text x="{x+14:.0f}" y="158" fill="{LINE}" fill-opacity=".6" font-size="9.5">{e(sub)}</text>')
    # bar chart
    cx0, cy0, cw_, ch = 40, 470, 660, 240
    mx = max(counts + [1])
    slot = cw_ / max(1, len(counts))
    avg = sum(counts) / max(1, len(counts))
    parts.append(f'<line x1="{cx0}" y1="{cy0}" x2="{cx0+cw_}" y2="{cy0}" stroke="{LINE}" stroke-opacity=".6"/>')
    for i, d in enumerate(days):
        v = d["count"]; h = (v / mx) * ch
        x = cx0 + i * slot + 2
        wd = date.fromisoformat(d["date"]).weekday()
        col = AMBER if i == len(days) - 1 else (GREEN if v >= avg and v > 0 else (BLUE if wd < 5 else DIM))
        if v:
            parts.append(f'<g transform="translate(0 {cy0})"><g transform="scale(1 0)"><animateTransform attributeName="transform" type="scale" from="1 0" to="1 1" begin="{.3+i*.04:.2f}s" dur=".6s" fill="freeze"/>'
                         f'<rect x="{x:.1f}" y="{-h:.1f}" width="{slot-4:.1f}" height="{h:.1f}" fill="{col}" fill-opacity=".85"/></g></g>')
        if (wd == 0 and i < len(days) - 3) or i == len(days) - 1:
            parts.append(f'<text x="{x + (slot-4)/2:.1f}" y="{cy0+16}" fill="{BLUE}" font-size="9.5" text-anchor="middle">{"TODAY" if i == len(days)-1 else date.fromisoformat(d["date"]).strftime("%d %b")}</text>')
    ya = cy0 - (avg / mx) * ch
    parts.append(f'<line x1="{cx0}" y1="{ya:.1f}" x2="{cx0+cw_}" y2="{ya:.1f}" stroke="{AMBER}" stroke-dasharray="5 4" stroke-opacity=".8"/>'
                 f'<rect x="{cx0}" y="{ya-17:.1f}" width="86" height="14" fill="{BG}"/><text x="{cx0+4}" y="{ya-6:.1f}" fill="{AMBER}" font-size="10">avg {avg:.1f}/day</text>'
                 f'<text x="{cx0}" y="214" fill="{BLUE}" font-size="10" letter-spacing="1.5">DAILY CONTRIBUTIONS</text>')
    # where the commits went
    fx = 740
    parts.append(f'<rect x="{fx}" y="200" width="{W-40-fx}" height="296" fill="{BG}" stroke="{LINE}" stroke-opacity=".5"/>'
                 f'<text x="{fx+18}" y="224" fill="{BLUE}" font-size="10" letter-spacing="1.5">WHERE THE COMMITS WENT · 30D</text>')
    focus = S.get("focus") or []
    fmx = max([f["commits"] for f in focus] + [1])
    for i, f in enumerate(focus[:6]):
        y = 262 + i * 38
        nm = f["name"] if not f["private"] else "private repo"
        lk = (f'<g transform="translate({fx+18} {y-11})"><rect x="0" y="5" width="10" height="8" rx="1.5" fill="{CYAN}"/><path d="M2 5V3a3 3 0 0 1 6 0v2" fill="none" stroke="{CYAN}" stroke-width="1.6"/></g>') if f["private"] else ""
        parts.append(lk + f'<text x="{fx+18+(16 if f["private"] else 0)}" y="{y}" fill="{LINE}" font-size="13">{e(trunc(nm, 24))}</text>'
                     f'<text x="{W-58}" y="{y}" fill="{GREEN}" font-size="13" text-anchor="end">{f["commits"]}</text>'
                     + (f'<circle cx="{fx+22}" cy="{y+12}" r="3.5" fill="{f["color"]}"/><text x="{fx+30}" y="{y+15}" fill="{BLUE}" font-size="9.5">{e(f.get("lang") or "")}</text>' if f.get("lang") else "")
                     + f'<rect x="{fx+130}" y="{y+8}" width="{W-58-fx-130}" height="4" fill="{LINE}" fill-opacity=".08"/>'
                     f'<rect x="{fx+130}" y="{y+8}" width="0" height="4" fill="{f["color"]}"><animate attributeName="width" from="0" to="{(W-58-fx-130)*f["commits"]/fmx:.1f}" begin="{.6+i*.12:.2f}s" dur=".8s" fill="freeze"/></rect>')
    if not focus:
        parts.append(f'<text x="{fx+18}" y="270" fill="{BLUE}" font-size="12">no commits in the last 30 days visible to the token</text>')
    parts.append(f'<text x="40" y="{H-38}" fill="{BLUE}" font-size="10.5">private work is counted but never named · add a GH_STATS_TOKEN secret to include private repositories</text>')
    write("pulse.svg", svg(W, H, "".join(parts)))


# ======================================================================  09. PINNED REPO CARDS
def repo_card_svg(i, r):
    W, H = 590, 180
    parts = [f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{LINE}" stroke-opacity=".35"/>'
             f'<rect width="{W}" height="{H}" rx="10" fill="url(#g1)"/>',
             f'<path d="M28 34h14v18H28z" fill="none" stroke="{BLUE}" stroke-width="1.6"/><path d="M31 38h8M31 42h8M31 46h5" stroke="{BLUE}" stroke-width="1.2"/>',
             f'<text x="54" y="49" fill="{CYAN}" font-size="19" font-weight="700">{e(trunc(r["name"], 34))}</text>']
    parts.append(pill(W - 28, 47, "FORK" if r.get("fork") else "PINNED", AMBER if r.get("fork") else GREEN, fs=9.5, anchor="end")[0])
    desc = r.get("description") or "No description yet."
    for j, l in enumerate(wrap(desc, 66)[:2]):
        parts.append(f'<text x="28" y="{86 + j*20}" fill="{LINE}" fill-opacity=".85" font-size="13">{e(l)}</text>')
    y = 148
    x = 28
    if r.get("lang"):
        parts.append(f'<circle cx="{x+6}" cy="{y-4}" r="6" fill="{r["color"]}"/><text x="{x+18}" y="{y}" fill="{LINE}" font-size="12">{e(r["lang"])}</text>')
        x += 30 + len(r["lang"]) * 7.5
    parts.append(f'<text x="{x+10}" y="{y}" fill="{AMBER}" font-size="12">★ {r["stars"]}</text><text x="{x+70}" y="{y}" fill="{BLUE}" font-size="12">⑂ {r["forks"]}</text>')
    pd = datetime.fromisoformat(r["pushed"].replace("Z", "+00:00")).astimezone(TZ)
    upd = ago(r["pushed"]) if (NOW - pd).days < 60 else pd.strftime("%b %Y")
    parts.append(f'<text x="{W-28}" y="{y}" fill="{BLUE}" font-size="11.5" text-anchor="end">updated {upd}</text>')
    parts.append(f'<rect x="0" y="0" width="3" height="{H}" fill="{GREEN}" opacity=".0"><animate attributeName="opacity" values="0;.9;0" dur="3s" begin="{i*.5:.1f}s" repeatCount="indefinite"/></rect>')
    write(f"repo-{i+1}.svg", svg(W, H, "".join(parts)))


# ======================================================================  11. GUESTBOOK
def guestbook_svg():
    W = 1200
    ents = GB.get("entries", [])[:8]
    x, y = 40, 90
    th = 56 + (2 + max(1, len(ents))) * 32
    H = y + th + 96
    tw = W - 80
    lines = [([("akshat@ahmedabad", GREEN), (":~$ ", "#d7ffd7"), ("cat guestbook.log | tail -8", "#ffffff")], True),
             ([("#".ljust(7), "#6f9f7f"), ("VISITOR".ljust(24), "#6f9f7f"), ("MESSAGE".ljust(52), "#6f9f7f"), ("SIGNED", "#6f9f7f")], False)]
    for en in ents:
        lines.append(([(f"{en.get('n', 0):04d}".ljust(7), "#6f9f7f"), (trunc("@" + en["user"], 22).ljust(24), CYAN),
                       (trunc(f'"{en["msg"]}"', 50).ljust(52), "#ffffff"), (ago(en["time"]), GREEN)], False))
    if not ents:
        lines.append(([("guestbook.log is empty — ", AMBER), ("be the first developer to sign it.", "#ffffff")], False))
    clips, body, tend, yend = typed(lines, x + 20, y + 56, 32, 14, start=.5, cps=40, prefix="g")
    body += cursor(x + 20, yend, 14, tend)
    head = (fig(40, 54, "FIG. 10 — GUESTBOOK", None)
            + f'<text x="{W-40}" y="54" fill="{AMBER}" font-size="13" text-anchor="end">SIGNED BY {GB.get("total", 0)} DEVELOPER{"S" if GB.get("total", 0) != 1 else ""}</text>'
            + f'<text x="{x}" y="{H-62}" fill="{LINE}" font-size="12.5">HOW IT WORKS  <tspan fill="{BLUE}">click </tspan><tspan fill="{GREEN}">SIGN THE GUESTBOOK</tspan><tspan fill="{BLUE}"> below → GitHub opens a pre-filled issue → press Submit.</tspan></text>'
            + f'<text x="{x}" y="{H-40}" fill="{BLUE}" font-size="12.5">A GitHub Action reads it, adds your name + message to this log, replies to thank you and closes the issue — about a minute, end to end.</text>')
    write("guestbook.svg", svg(W, H, paper(W, H) + head + term_window(x, y, tw, th, "guestbook.log") + f'<g filter="url(#glow)">{body}</g>' + term_fx(x, y, tw, th, "gc"), clips))


# ======================================================================  README markers
def update_readme():
    path = os.path.join(ROOT, "README.md")
    if not os.path.exists(path):
        return
    md = open(path).read()

    def put(tag, content):
        nonlocal md
        a, b = f"<!-- {tag}:START -->", f"<!-- {tag}:END -->"
        if a in md and b in md:
            md = md[: md.index(a) + len(a)] + "\n" + content + "\n" + md[md.index(b):]

    pins = [r for r in S.get("pinned", [])][:6]
    if pins:
        cells = "\n".join(f'  <a href="{e(r["url"])}"><img src="./generated/repo-{i+1}.svg" width="49%" alt="{e(r["name"])} — {e(r.get("description") or "")}"/></a>' for i, r in enumerate(pins))
        put("REPOS", f'<p align="center">\n{cells}\n</p>')
    posts = S.get("posts") or []
    if posts:
        def nice(d):
            return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y")
        rows = "\n".join(f'- **[{p["title"]}]({p["url"]})**  \n  <sub>{nice(p["date"])} · {" · ".join("#" + t for t in p.get("tags", []))}</sub>' for p in posts)
        put("BLOG-POST-LIST", rows)
    open(path, "w").write(md)


if __name__ == "__main__":
    hero_svg(); telemetry_svg(); skyline_svg(); clock_svg(); punchcard_svg(); bom_svg(); arch_svg(); pulse_svg(); guestbook_svg(); footer_svg()
    for p in CFG.get("products", []):
        product_card_svg(p)
    keep = {f"product-{p['id']}.svg" for p in CFG.get("products", [])}
    for f in os.listdir(OUT):  # drop panels that no longer exist
        if (f.startswith(("product-", "repo-")) and f not in keep) or f == "activity.svg":
            os.remove(os.path.join(OUT, f))
    update_readme()
    print("rendered:", ", ".join(sorted(os.listdir(OUT))))
