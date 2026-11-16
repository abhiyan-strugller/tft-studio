# Real Photos — Credits

All images in this folder are **original TempleFront Tours and Travels photographs** —
founder **Mitra Lal Ji** with real travellers he personally welcomed and guided.

- **Owner:** TempleFront Tours and Travels (own property)
- **License:** None required — first-party photos, used with permission.
- **Source originals:** `public/images/real tour collection/` (untouched uploads).
- **Processing:** optimised via `scripts/process-real-photos.mjs`
  (sharp: max 1200px long edge, `normalize` + light `sharpen`, JPEG q85 mozjpeg).

| File | Scene |
|---|---|
| `real-mitraji-airport-welcome.jpg` | Welcoming travellers at Tribhuvan International Airport, Kathmandu |
| `real-mitraji-group-welcome.jpg` | Greeting a group with traditional Nepali welcome scarves |
| `real-mitraji-chitwan-safari.jpg` | On an elephant-back safari in Chitwan National Park |
| `real-mitraji-traveller-portrait.jpg` | With a traveller in Kathmandu |
| `real-mitraji-trekkers-airport.jpg` | Receiving trekkers at Tribhuvan International Airport |
| `real-mitraji-shiva-statue-group.jpg` | With a visiting group at a Shiva statue in Nepal |

## Logo

The official company logo (`public/images/real tour collection/logo.jpeg`) is a
dark-navy raster with no transparency. It's used as-is, just with the navy
background **keyed out to transparent** so it sits cleanly on any surface
(processed by `scripts/process-logo.mjs`):

- **`public/images/logo-mark.png`** — the official logo, transparent background.
  Used in Nav + Footer (reads on both the cream nav and the dark hero/footer).
- **`app/icon.png` / `app/apple-icon.png` / `public/images/logo-square.png`** —
  the same logo centred on a brand-navy square tile (favicons + JSON-LD logo).

These are original TempleFront brand assets — no license required.

**Usage rule:** these guest photos are for trust sections only (About, homepage trust
strip, Reviews). Do NOT use as hero backgrounds or tour card covers.
