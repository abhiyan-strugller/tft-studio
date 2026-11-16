"""Build one Nepal day: render cards (+ any reels), write the Post Planner sheet.

  python3 scripts/build_day.py --date 2026-11-17

Reads input/<date>.json. `date` and every `slot` are NEPAL time (Asia/Kathmandu).
The sheet's POSTING TIME is written in the Post Planner account's zone
(config/postplanner.json, America/Edmonton) — the code converts; never edit
that column by hand.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render as R  # noqa: E402

ROOT = R.ROOT
NPT = ZoneInfo("Asia/Kathmandu")
CFG = json.loads((ROOT / "config" / "postplanner.json").read_text())
PLANNER = ZoneInfo(CFG["timeZone"])
MEDIA_BASE = CFG["mediaBase"]
ROW1 = ["## This is a comment row. Any row starting with ## will be ignored when your posts are uploaded. "
        "You can use comment rows to add notes.", "BULK UPLOAD VERSION 3.1 — Please DO NOT EDIT this cell.",
        "", "", "", "", "", "", ""]
ROW2 = ["## POSTING TIME", "CAPTION", "LINK", "MEDIA", "TITLE", "FIRST COMMENT", "FIRST COMMENT DELAY",
        "TOBI BACKGROUND", "REEL OR STORY"]
BANNED_TAGS = {"#goviral", "#viral", "#fyp", "#foryou", "#likeforlike", "#follow4follow", "#viralreels"}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def planner_time(date: str, hhmm: str) -> tuple[str, datetime]:
    h, m = map(int, hhmm.split(":"))
    local = datetime.fromisoformat(date).replace(hour=h, minute=m, tzinfo=NPT)
    p = local.astimezone(PLANNER)
    return f"{p:%m/%d/%Y}  {p.hour}:{p:%M}", local


def caption_text(post: dict) -> str:
    tags = post.get("hashtags", [])
    bad = [t for t in tags if t.lower() in BANNED_TAGS or not t.startswith("#") or " " in t]
    if bad:
        raise SystemExit(f"bad hashtags {bad} in post {post.get('slot')}")
    if not 8 <= len(tags) <= 18:
        raise SystemExit(f"post {post.get('slot')}: use 8-18 hashtags (has {len(tags)})")
    cap = post["caption"].strip()
    return cap + "\n\n" + " ".join(tags)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    a = ap.parse_args()
    day = json.loads((ROOT / "input" / f"{a.date}.json").read_text())
    assert day["date"] == a.date
    out = ROOT / "output" / a.date
    out.mkdir(parents=True, exist_ok=True)
    rows, cards = [], []
    errors = []
    for i, post in enumerate(day["posts"], 1):
        name = f"{a.date}-{i:02d}-{slug(post.get('name') or post.get('title') or post['template'])}.png"
        try:
            R.render(post, out / name)
        except Exception as e:  # collect all overflow / glyph errors in one pass
            errors.append(f"post {i} ({post['template']}): {e}")
            continue
        when, local = planner_time(a.date, post["slot"])
        rows.append((local, [when, caption_text(post), "", f"{MEDIA_BASE}/{a.date}/{name}", "",
                             post.get("first_comment", ""), "", "", ""]))
        cards.append((post, name, local))
    for r in day.get("reels", []):
        doc = json.loads((ROOT / "input" / "reels" / f"{r['slug']}.json").read_text())
        mp4 = out / f"{r['slug']}.mp4"
        if not mp4.exists():
            from render_reel import render_reel
            render_reel(doc, mp4)
        when, local = planner_time(a.date, r["slot"])
        rows.append((local, [when, caption_text(r), "", f"{MEDIA_BASE}/{a.date}/{mp4.name}", "",
                             r.get("first_comment", ""), "", "", "reel"]))
        cards.append((r, mp4.name, local))
    if errors:
        raise SystemExit("FIX AND REBUILD:\n" + "\n".join(errors))
    rows.sort(key=lambda x: x[0])
    times = [x[0] for x in rows]
    if len(set(times)) != len(times):
        raise SystemExit("two rows share a posting time")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(ROW1)
    w.writerow(ROW2)
    for _, row in rows:
        w.writerow(row)
    (out / "postplanner.csv").write_bytes(("﻿" + buf.getvalue()).encode("utf-8"))
    # contact sheet for review
    html = [f"<html><meta charset=utf-8><title>TFT {a.date}</title><body style='font-family:sans-serif;"
            "background:#F8F1E4;max-width:1100px;margin:auto'>",
            f"<h1>TempleFront — {a.date} (Nepal time)</h1>"]
    for post, name, local in sorted(cards, key=lambda c: c[2]):
        media = (f"<video src='{name}' controls width=300></video>" if name.endswith(".mp4")
                 else f"<img src='{name}' width=300>")
        html.append(f"<div style='display:flex;gap:20px;margin:24px 0'>{media}<div><b>{local:%H:%M} NPT</b>"
                    f"<pre style='white-space:pre-wrap'>{caption_text(post)}</pre>"
                    f"<i>First comment:</i> {post.get('first_comment','')}</div></div>")
    (out / "index.html").write_text("\n".join(html), encoding="utf-8")
    with open(out / "run-log.txt", "a") as log:
        log.write(f"{datetime.now(PLANNER):%Y-%m-%d %H:%M} build ok: {len(rows)} rows "
                  f"({sum(1 for c in cards if c[1].endswith('.png'))} cards, "
                  f"{sum(1 for c in cards if c[1].endswith('.mp4'))} reels)\n")
    print(f"built {len(rows)} rows -> {out}/postplanner.csv")


if __name__ == "__main__":
    main()
