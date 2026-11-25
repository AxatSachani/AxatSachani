#!/usr/bin/env python3
"""Fetch live GitHub stats for the profile README and write data/stats.json.

Uses only the Python standard library. Needs a token in GH_TOKEN (or GITHUB_TOKEN).
- The default Actions token works for public data.
- A fine-grained / classic PAT stored as secret GH_STATS_TOKEN adds private-repo
  language + commit-hour data (aggregated only — no private repo names are ever rendered).
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json")))
LOGIN = CFG["login"]
TZ = timezone(timedelta(hours=CFG.get("tz_offset_hours", 0)))
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
API = "https://api.github.com"


def _req(url, body=None):
    headers = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "profile-pipeline",
               "Accept": "application/vnd.github+json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) and attempt < 3:
                time.sleep(3 * (attempt + 1)); continue
            raise


def gql(query, **variables):
    res = _req(f"{API}/graphql", {"query": query, "variables": variables})
    if res.get("errors"):
        raise RuntimeError(json.dumps(res["errors"])[:800])
    return res["data"]


Q_USER = """
query($login:String!){
  user(login:$login){
    id name login createdAt
    followers{ totalCount }
    pullRequests{ totalCount }
    merged: pullRequests(states:MERGED){ totalCount }
    issues{ totalCount }
    repositoriesContributedTo(includeUserRepositories:true, contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,REPOSITORY]){ totalCount }
    pinnedItems(first:6, types:REPOSITORY){ nodes{ ... on Repository{ name description url stargazerCount forkCount isFork pushedAt primaryLanguage{ name color } } } }
    repositories(ownerAffiliations:OWNER, isFork:false, first:100, orderBy:{field:PUSHED_AT, direction:DESC}){
      totalCount
      nodes{
        stargazerCount
        languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name color } } }
      }
    }
  }
}"""

Q_YEAR = """
query($login:String!, $from:DateTime!, $to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      totalCommitContributions restrictedContributionsCount
      totalPullRequestReviewContributions
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
    }
  }
}"""

Q_LASTYEAR = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
    }
  }
}"""

Q_REPOS30 = """
query($login:String!, $from:DateTime!, $to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      commitContributionsByRepository(maxRepositories:6){
        repository{ name isPrivate primaryLanguage{ name color } }
        contributions{ totalCount }
      }
    }
  }
}"""

Q_HOURS = """
query($login:String!, $uid:ID!){
  user(login:$login){
    repositories(ownerAffiliations:OWNER, first:25, orderBy:{field:PUSHED_AT, direction:DESC}){
      nodes{ defaultBranchRef{ target{ ... on Commit{ history(first:100, author:{id:$uid}){ nodes{ committedDate } } } } } }
    }
  }
}"""


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_posts():
    """Latest articles from the RSS feeds in config.json (Medium etc.)."""
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    posts = []
    for feed in CFG.get("feeds", []):
        try:
            req = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0 profile-pipeline"})
            root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
            for it in root.iter("item"):
                d = parsedate_to_datetime(it.findtext("pubDate"))
                posts.append({"title": (it.findtext("title") or "").strip(), "url": (it.findtext("link") or "").split("?")[0],
                              "date": d.strftime("%Y-%m-%d"), "tags": [c.text for c in it.findall("category")][:3]})
        except Exception as ex:
            print("feed failed:", feed, ex)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts[:6]


def check_uptime():
    """Pings every product URL and keeps a rolling history (one sample per pipeline run)."""
    path = os.path.join(ROOT, "data", "uptime.json")
    hist = json.load(open(path)) if os.path.exists(path) else {}
    for p in CFG.get("products", []):
        url = p.get("check")
        if not url:
            continue
        t0, ok, code = time.time(), False, 0
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 uptime-check"})
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status; ok = 200 <= code < 400
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception:
            code = 0
        ms = int((time.time() - t0) * 1000)
        h = hist.setdefault(p["id"], [])
        h.append({"t": iso(datetime.now(timezone.utc)), "ok": ok, "ms": ms, "code": code})
        hist[p["id"]] = h[-56:]  # 7 days at one check every 3h
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(hist, open(path, "w"), indent=1)
    print("uptime ok:", {k: v[-1] for k, v in hist.items()})


def main():
    if not TOKEN:
        sys.exit("GH_TOKEN / GITHUB_TOKEN is not set")
    now = datetime.now(timezone.utc)
    u = gql(Q_USER, login=LOGIN)["user"]

    # ---- all-time commits / reviews / day map (one query per calendar year)
    created = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    commits_all = reviews_all = 0
    days = {}
    for y in range(created.year, now.year + 1):
        start = max(datetime(y, 1, 1, tzinfo=timezone.utc), created)
        end = min(datetime(y, 12, 31, 23, 59, 59, tzinfo=timezone.utc), now)
        cc = gql(Q_YEAR, login=LOGIN, **{"from": iso(start), "to": iso(end)})["user"]["contributionsCollection"]
        commits_all += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
        reviews_all += cc["totalPullRequestReviewContributions"]
        for w in cc["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = max(days.get(d["date"], 0), d["contributionCount"])

    # ---- rolling last-year calendar (what github shows on the profile)
    cal = gql(Q_LASTYEAR, login=LOGIN)["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[{"date": d["date"], "count": d["contributionCount"]} for d in w["contributionDays"]] for w in cal["weeks"]]
    for w in weeks:
        for d in w:
            days[d["date"]] = max(days.get(d["date"], 0), d["count"])

    # ---- streaks
    today = now.astimezone(TZ).date()
    cur, dd = 0, today
    if days.get(dd.isoformat(), 0) == 0:
        dd -= timedelta(days=1)
    while days.get(dd.isoformat(), 0) > 0:
        cur += 1; dd -= timedelta(days=1)
    longest = run = 0
    prev = None
    for k in sorted(days):
        if days[k] > 0:
            dk = date.fromisoformat(k)
            run = run + 1 if prev and (dk - prev).days == 1 else 1
            prev = dk
            longest = max(longest, run)
        else:
            prev = None; run = 0
    flat = [d for w in weeks for d in w]
    active_year = sum(1 for d in flat if d["count"] > 0)
    best = max(flat, key=lambda d: d["count"]) if flat else {"date": "", "count": 0}
    weekday = [0] * 7
    for d in flat:
        weekday[date.fromisoformat(d["date"]).weekday()] += d["count"]

    # ---- languages + stars (aggregated across owned, non-fork repos)
    langs, stars = {}, 0
    for r in u["repositories"]["nodes"]:
        stars += r["stargazerCount"]
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, {"name": n, "color": e["node"]["color"] or "#8b949e", "bytes": 0})
            langs[n]["bytes"] += e["size"]
    languages = sorted(langs.values(), key=lambda x: -x["bytes"])

    # ---- commit hour-of-day histogram (local timezone)
    hours = [0] * 24
    punch = [[0] * 24 for _ in range(7)]  # [weekday Mon=0][hour]
    last_commit = None
    try:
        hr = gql(Q_HOURS, login=LOGIN, uid=u["id"])["user"]["repositories"]["nodes"]
        for r in hr:
            t = (r.get("defaultBranchRef") or {}).get("target") or {}
            for c in (t.get("history") or {}).get("nodes", []):
                ct = datetime.fromisoformat(c["committedDate"].replace("Z", "+00:00"))
                lt = ct.astimezone(TZ)
                hours[lt.hour] += 1
                punch[lt.weekday()][lt.hour] += 1
                if last_commit is None or ct > last_commit:
                    last_commit = ct
    except Exception as ex:  # never fail the whole build for this panel
        print("hours query failed:", ex)

    # ---- recent PUBLIC activity only (never leaks private repo names)
    events = []
    try:
        raw = _req(f"{API}/users/{LOGIN}/events/public?per_page=40")
        for e in raw:
            t, repo, p = e["type"], e["repo"]["name"], e.get("payload", {})
            detail = None
            if t == "PushEvent":
                commits = p.get("commits") or []
                branch = (p.get("ref") or "").split("/")[-1]
                if commits:  # older payloads carry commit summaries; newer ones may not
                    n = p.get("size") or len(commits)
                    msg = commits[-1].get("message", "").split("\n")[0]
                    detail = f'{n} commit{"s" if n != 1 else ""}' + (f' · "{msg}"' if msg else "")
                else:
                    detail = f"pushed to {branch}" if branch else "pushed"
                kind = "PUSH"
            elif t == "PullRequestEvent":
                pr = p.get("pull_request", {})
                act = "merged" if pr.get("merged") else p.get("action", "")
                detail, kind = f'{act} #{pr.get("number", "")} · "{pr.get("title", "")}"', "PR"
            elif t == "PullRequestReviewEvent":
                detail, kind = f'reviewed #{p.get("pull_request", {}).get("number", "")}', "REVIEW"
            elif t == "CreateEvent":
                detail, kind = f'created {p.get("ref_type", "")} {p.get("ref") or ""}'.strip(), "CREATE"
            elif t == "WatchEvent":
                detail, kind = "starred", "STAR"
            elif t == "IssuesEvent":
                detail, kind = f'{p.get("action", "")} issue #{p.get("issue", {}).get("number", "")}', "ISSUE"
            elif t == "ReleaseEvent":
                detail, kind = f'released {p.get("release", {}).get("tag_name", "")}', "RELEASE"
            elif t == "ForkEvent":
                detail, kind = "forked", "FORK"
            if detail:
                events.append({"time": e["created_at"], "type": kind, "repo": repo, "detail": detail})
    except Exception as ex:
        print("events fetch failed:", ex)

    # ---- where commits went in the last 30 days (private repos are anonymised)
    focus = []
    try:
        cc = gql(Q_REPOS30, login=LOGIN, **{"from": iso(now - timedelta(days=30)), "to": iso(now)})["user"]["contributionsCollection"]
        for r in cc["commitContributionsByRepository"]:
            repo = r["repository"]; lang = repo.get("primaryLanguage") or {}
            focus.append({"name": None if repo["isPrivate"] else repo["name"], "private": repo["isPrivate"],
                          "lang": lang.get("name"), "color": lang.get("color") or "#8b949e",
                          "commits": r["contributions"]["totalCount"]})
    except Exception as ex:
        print("focus query failed:", ex)

    pinned = []
    for r in (u.get("pinnedItems") or {}).get("nodes", []):
        if not r: continue
        lang = r.get("primaryLanguage") or {}
        pinned.append({"name": r["name"], "description": r.get("description") or "", "url": r["url"],
                       "stars": r["stargazerCount"], "forks": r["forkCount"], "fork": r["isFork"],
                       "pushed": r["pushedAt"], "lang": lang.get("name"), "color": lang.get("color") or "#8b949e"})

    stats = {
        "demo": False,
        "generated_at": iso(now),
        "login": u["login"], "name": u["name"] or u["login"],
        "totals": {
            "commits_all": commits_all, "prs": u["pullRequests"]["totalCount"],
            "merged": u["merged"]["totalCount"], "reviews": reviews_all,
            "issues": u["issues"]["totalCount"], "stars": stars,
            "repos": u["repositories"]["totalCount"], "followers": u["followers"]["totalCount"],
            "contribs_year": cal["totalContributions"],
            "contributed_to": u["repositoriesContributedTo"]["totalCount"],
        },
        "streak": {"current": cur, "longest": longest, "active_days_year": active_year},
        "best_day": best, "weekday": weekday, "calendar": weeks,
        "hours": hours, "punch": punch, "last_commit": iso(last_commit) if last_commit else None,
        "focus": focus, "pinned": pinned,
        "languages": languages[:10], "events": events[:12],
    }
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    stats["posts"] = fetch_posts()
    json.dump(stats, open(os.path.join(ROOT, "data", "stats.json"), "w"), indent=1)
    print("stats ok:", json.dumps(stats["totals"]))


if __name__ == "__main__":
    try:
        check_uptime()  # independent of the GitHub API
    except Exception as ex:
        print("uptime failed:", ex)
    main()
