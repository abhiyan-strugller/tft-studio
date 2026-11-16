# TempleFront daily brief — what to make and how

Page: **Temple front tours & travel** (Facebook, ~650 followers, Stars active).
Business: TempleFront Tours & Travel Pvt. Ltd., Kathmandu — family agency
founded by Mitra Lal Ghimire, guiding since 1996. Private tours only.
Audience: pilgrims and families from Nepal and India first, then
international trekkers and travellers. Goals, in order: **enquiries on
WhatsApp**, followers, then content that earns under Facebook monetization.

## Cadence (all NEPAL time, Asia/Kathmandu)

| Slot | What |
| --- | --- |
| 08:15 | card |
| 13:30 | card |
| 19:45 | card |
| 18:30 Tue / Thu / Sat only | reel (3 a week, never more) |

Cards are the priority. Reels are 3 a week, 15–25 s, 4–6 slides.

## The weekly mix (21 cards)

Rotate so no two neighbouring posts share a pillar, and never repeat a
destination within 3 days (check the last 3 days in `input/`).

1. **Destination postcard** (~6/wk) — `postcard`. One place, one feeling,
   one true detail. Reach + monetization content.
2. **Package spotlight** (~4/wk, max 1/day) — `tour`. A real package from
   `content/tours.json`: its name, its real duration, its real stops. Price
   line only if `price` is a number ("From USD 1,750 per person"); otherwise
   "Private yatra · Ask for your price" / "Private trip · Ask for your price".
3. **Know-before-you-go** (~4/wk) — `tips` or `fact`. Seasons, permits,
   altitude, packing, etiquette, visas for Indian nationals. Built to be
   saved and shared.
4. **Faith & culture** (~3/wk) — `postcard`/`fact`. Shiva, Buddha, festivals,
   temples, rituals — respectful, never mocking, never sensational.
5. **Choose one** (~2/wk) — `versus`. Two real places, a real trade-off,
   "Comment A or B".
6. **Real journeys / trust** (~2/wk) — `trust`, using ONLY the agency's own
   photos (`"own": true` in `library/library.json`). 5.0 on Google from 19
   reviews is the only review number allowed.

Timely hooks beat evergreen when real: an upcoming festival (verify the
2026 date from two sources), a season opening (e.g. trekking season, Kailash
yatra bookings), a permit/fee change from an official source. No news? Use
evergreen — never invent a hook.

## Captions — the voice

Warm, devotional where it fits, specific. Shape:
1. A first line that stops the scroll (a feeling, a true surprising detail,
   or a question). 2. Two to four short lines of story or facts, emojis as
   bullets are fine. 3. What we offer, in one line, private to your group.
4. A question that invites comments (comments outweigh likes).
5. `📲 WhatsApp +977 985-1007885` on its own line.

Hashtags: **10–15**, in the `hashtags` array (build rejects <8 or >18): place
tags (#Muktinath #Mustang), theme tags (#NepalPilgrimage #FamilyTrek), broad
(#Nepal #VisitNepal #Himalayas), always **#TempleFrontTours**. Never
engagement-bait tags (#goviral #fyp #viral — the build rejects them; they
signal spam to Facebook's ranking and hurt monetization).

`first_comment`: the matching page on
`https://www.templefronttours.com/en/tours/<slug>` (or `/en/reviews`).
Links go in the first comment, never in the caption.

## Facts — non-negotiable

- Package facts come ONLY from `content/tours.json` (the website's own data).
- Any other number (altitude, distance, fee, date, species count) must be
  confirmed by a reputable source (official/government, UNESCO, Nepal Tourism
  Board, major outlet) and named in the run-log; if two sources disagree,
  use the website's figure or drop the number.
- Never invent reviews, testimonials, guest quotes, prices, discounts,
  departures or "seats left". No fake urgency.
- Photos only from `library/` — Pexels License or the agency's own. Never
  pull a photo from Google, Instagram or other pages. Never put an identifiable
  person who isn't in our own photos into a "trust" post.
- A photo must actually show (or honestly represent the region of) what the
  card names. Check `library/contact-sheet.jpg`; open the photo if unsure.

## The day file

`input/<YYYY-MM-DD>.json` (Nepal date). See any existing day for the shape.
Template fields: see the docstring at the top of `scripts/render.py`.
Reels: `input/reels/<date>-<slug>.json` + an entry in the day's `reels` list
with its own caption/hashtags/first_comment and `"slot": "18:30"`.
