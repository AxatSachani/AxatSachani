#!/usr/bin/env python3
"""Interactive guestbook: a visitor opens an issue titled `deploy: <message>`.
This script validates + sanitises it, appends it to data/guestbook.json and writes
the bot's reply to comment.md. All untrusted input is read from the event JSON file —
never interpolated into shell commands.
"""
import json, os, re, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json")))
PREFIX = CFG.get("guestbook_prefix", "deploy:").lower()
KEEP = int(CFG.get("guestbook_keep", 20))
PATH = os.path.join(ROOT, "data", "guestbook.json")


def out(key, val):
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"{key}={val}\n")


def clean(msg):
    msg = re.sub(r"[^A-Za-z0-9 .,!?'@#&()+\-_:/]", "", msg)  # strip anything exotic
    msg = re.sub(r"https?://\S+", "[link]", msg)               # no link spam
    msg = re.sub(r"\s+", " ", msg).strip()
    return msg[:48]


def main():
    ev = json.load(open(os.environ["GITHUB_EVENT_PATH"]))
    issue = ev.get("issue") or {}
    title = (issue.get("title") or "").strip()
    user = (issue.get("user") or {}).get("login", "")
    number = issue.get("number")
    if not isinstance(number, int) or not title.lower().startswith(PREFIX) or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", user):
        out("accepted", "false"); return
    out("number", str(number))
    msg = clean(title[len(PREFIX):]) or "hello world"
    book = json.load(open(PATH)) if os.path.exists(PATH) else {"total": 0, "entries": []}
    book["total"] = book.get("total", 0) + 1
    entry = {"user": user, "msg": msg, "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "n": book["total"]}
    book["entries"] = ([entry] + book.get("entries", []))[:KEEP]
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    json.dump(book, open(PATH, "w"), indent=1)
    with open(os.path.join(ROOT, "comment.md"), "w") as f:
        f.write(f"""```console
$ kubectl apply -f visitor-{book['total']:04d}.yaml
deployment.apps/@{user} created
$ kubectl rollout status deployment/@{user}
deployment "@{user}" successfully rolled out ✅
```
Welcome aboard, @{user} — you are **visitor #{book['total']}**. Your message is now live on the profile (give it a minute to render).

<sub>Want to build something together? Find me on <a href="https://www.linkedin.com/in/akshatsachani">LinkedIn</a>.</sub>
""")
    out("accepted", "true")
    print("guestbook entry", entry)


if __name__ == "__main__":
    sys.exit(main())
