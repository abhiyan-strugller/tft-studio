"""Publish a built day to tft-media and verify it byte-for-byte.

  python3 scripts/publish.py --date 2026-11-17

1. Copies output/<date>/*.png|*.mp4 to tft-media/<date>/, pushes (plain git).
2. Re-downloads every file from raw.githubusercontent.com and compares sha256.
3. Refuses if any row's posting time has already passed (Post Planner publishes
   a past-dated row IMMEDIATELY — that is how ten wrong posts went live on
   Follow the Money on 2026-11-10).
4. Publishes the sheet under a content-addressed name sheets/<date>-<sha10>.csv,
   verifies its served bytes, and appends SHEET_URL / SHA256 / ROWS to
   tft-media/<date>/run-log.txt — the upload task reads those last lines.

Never deletes anything from tft-media: Post Planner fetches media at publish time.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import json

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "postplanner.json").read_text())
PLANNER = ZoneInfo(CFG["timeZone"])
OWNER, REPO = CFG["owner"], "tft-media"
WORK = ROOT / ".media-repo"
RAW = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main"


def git(*args, cwd=WORK):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str, tries: int = 12) -> bytes:
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url + f"?t={time.time()}", timeout=30) as r:
                return r.read()
        except Exception as e:  # raw can lag a few seconds after a push
            last = e
            time.sleep(5)
    raise SystemExit(f"could not fetch {url}: {last}")


def verify(rel: str, local: bytes) -> None:
    for _ in range(12):
        if sha(fetch(f"{RAW}/{rel}")) == sha(local):
            return
        time.sleep(5)
    raise SystemExit(f"SERVED BYTES DIFFER for {rel} — a 200 is not proof; refusing")


def past_rows(sheet: Path) -> list[str]:
    now = datetime.now(PLANNER)
    bad = []
    for r in list(csv.reader(sheet.open(encoding="utf-8-sig")))[2:]:
        if not r or r[0].startswith("##"):
            continue
        t = datetime.strptime(r[0], "%m/%d/%Y  %H:%M").replace(tzinfo=PLANNER)
        if t <= now:
            bad.append(r[0])
    return bad


def push(msg: str) -> None:
    git("add", "-A")
    if not git("status", "--porcelain").strip():
        return
    git("-c", "user.name=TFT Studio", "-c", "user.email=noreply@anthropic.com", "commit", "-q", "-m", msg)
    for i in range(3):
        r = subprocess.run(["git", "-c", "push.negotiate=true", "push", "origin", "HEAD:main"], cwd=WORK,
                           capture_output=True, text=True)
        if r.returncode == 0:
            return
        git("pull", "-q", "--rebase", "origin", "main")
    raise SystemExit(f"PUSH FAILED: {r.stderr}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    a = ap.parse_args()
    out = ROOT / "output" / a.date
    sheet = out / "postplanner.csv"
    if not sheet.exists():
        raise SystemExit("build the day first")
    bad = past_rows(sheet)
    if bad:
        raise SystemExit(f"REFUSING: rows already in the past (would publish instantly): {bad}")
    if not (WORK / ".git").exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"https://github.com/{OWNER}/{REPO}", str(WORK)],
                       check=True)
    else:
        git("pull", "-q", "--rebase", "origin", "main")
    dest = WORK / a.date
    dest.mkdir(exist_ok=True)
    media = sorted([p for p in out.iterdir() if p.suffix in (".png", ".mp4")])
    for p in media:
        shutil.copy2(p, dest / p.name)
    push(f"media {a.date}")
    for p in media:
        verify(f"{a.date}/{p.name}", p.read_bytes())
    log = dest / "run-log.txt"
    with log.open("a") as f:
        f.write(f"{datetime.now(PLANNER):%Y-%m-%d %H:%M} media ok: {len(media)} files sha256-verified\n")
    body = sheet.read_bytes()
    h = sha(body)
    rel = f"sheets/{a.date}-{h[:10]}.csv"
    (WORK / "sheets").mkdir(exist_ok=True)
    (WORK / rel).write_bytes(body)
    push(f"sheet {a.date}")
    verify(rel, body)
    rows = sum(1 for r in list(csv.reader(sheet.open(encoding='utf-8-sig')))[2:] if r)
    with log.open("a") as f:
        f.write(f"SHEET_URL={RAW}/{rel}\nSHA256={h}\nROWS={rows}\n")
    push(f"run-log {a.date}")
    print(f"SHEET_URL={RAW}/{rel}\nSHA256={h}\nROWS={rows}")


if __name__ == "__main__":
    main()
