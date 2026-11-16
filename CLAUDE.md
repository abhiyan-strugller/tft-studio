# TempleFront Tours — Facebook content pipeline

Separate from Follow the Money (`ftm-studio` / `ftm-media`). Never mix the
two: different page, different repos, different scheduled tasks.

Abhiyan's role is review. The pipeline runs unattended and puts **3 photo
cards a day + 3 reels a week** on the Facebook page **Temple front tours &
travel** (profile id 100049547155610), scheduled in **Nepal time**.
Content rules: `prompts/daily.md`. Read it before writing any post.

## Flow

| | Task | Runs (Edmonton) | Does |
| --- | --- | --- | --- |
| A | `TFT Build & Publish (Task A)` — cloud, both repos attached | 10:17 AM daily (= 22:02 Nepal) | builds the NEXT Nepal day, publishes media + sheet to tft-media |
| B | `TFT Upload (Task B)` — bound to LAPTOP-DGLF08U0 | 12:23 / 2:23 / 4:23 PM | injects that sheet into Post Planner for the TFT page, reads the queue back |

The Nepal day's first post (08:15 NPT) is 8:30 PM Edmonton the same
Edmonton day, so the upload always lands hours before anything is due.
Two tasks for the same reason as FTM: a task that can push has no browser,
and a device-bound task cannot push.

Commands:
```
python3 scripts/build_day.py --date <nepal-date>   # render + postplanner.csv + index.html
python3 scripts/publish.py   --date <nepal-date>   # push media, sha256-verify, publish sheet
python3 scripts/render_reel.py --input input/reels/<slug>.json
```
`pip install -r requirements.txt` (Pillow, numpy, fonttools); ffmpeg required.

## Guards (do not weaken)

- **Time zones:** slots are Nepal time; the CSV is written in the Post
  Planner account zone (`config/postplanner.json`, America/Edmonton). The
  code converts. Never hand-edit POSTING TIME.
- **Past-row guard:** publish refuses a sheet with any row already in the
  past — Post Planner publishes past-dated rows instantly.
- **Content-addressed sheets + sha256 check of served bytes.** A 200 is not
  proof.
- **Overflow/glyph guard:** a card whose text doesn't fit, or uses a glyph
  the font lacks, fails the build. Shorten and rebuild; never ship a clipped card.
- **Never delete from tft-media** — Post Planner fetches media at publish time.
- **Never post to Facebook directly.** Post Planner only.
- **Post Planner bulk upload must target the TFT page only** — never Follow
  the Money. Read the queue back and confirm the page avatar on every row.
- A republished sheet does not change what's already queued in Post Planner:
  delete the day's queued posts there first, then upload.

## Post Planner format

Positional 9 columns; rows 1–2 are `##` comment rows; POSTING TIME text
`MM/DD/YYYY  H:MM` (two spaces, 24 h, hour not padded); MEDIA a public URL
ending .png/.mp4 (GitHub Pages: abhiyan-strugller.github.io/tft-media);
REEL OR STORY = `reel` for reels. Upload by injecting the CSV into the bulk
composer's file input with javascript (File + DataTransfer, dispatch
input/change) — a file-upload tool can't drive it.

## Photos

`library/library.json` — 180+ photos from the website: Pexels License (free
commercial use; credits in `library/CREDITS-*.md`) or the agency's own
(`own: true`). Add Mitra Ji's real trip photos to `library/photos/` with
`own: true` whenever Abhiyan provides them — own photos beat stock for both
trust and Facebook's originality ranking.
