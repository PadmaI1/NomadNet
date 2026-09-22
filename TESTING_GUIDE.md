# NomadNet — Testing Guide

## What's in the database

- **20 users**, all with Unsplash avatars, bios, and a shared login password.
- **14 locations** across 8 countries (Bali, Ubud, Bangkok, Chiang Mai, Phuket, Kyoto,
  Hoi An, Da Lat, Lisbon, Porto, Lauterbrunnen, Interlaken, Oaxaca, Barcelona).
- **~104 posts** with Unsplash photos, spread over the last ~30 days.
- **~850 likes**, **~286 comments**, **~99 user follows**, **~88 location follows**.

All data lives in `instance/nomadnet.db` — that's the file Flask actually reads
(`SQLALCHEMY_DATABASE_URI = "sqlite:///nomadnet.db"` resolves relative to the
Flask `instance/` folder, not the repo root).

## Login credentials

Every seeded account shares the same password:

```
Password: NomadNet2026!
```

Usernames: `alex_explorer`, `luna_traveler`, `marco_nomad`, `jasmine_adventure`,
`kai_island`, `elena_vance`, `marcus_reyes`, `hilda_novak`, `priya_desai`,
`tomas_silva`, `sofia_martins`, `daniel_kim`, `amara_okafor`, `felix_bauer`,
`nina_petrova`, `ravi_kumar`, `camila_torres`, `liam_oconnor`, `yuki_tanaka`,
`zara_ahmed`.

## How to run

```bash
cd /home/padmaiy/NomadNet
python app.py
# visit http://localhost:5000
```

## How to regenerate / reload seed data

```bash
python generate_seed_data.py   # regenerates seed_data.sql from scratch
python load_seed_data.py       # wipes instance/nomadnet.db and reloads it
```

`generate_seed_data.py` is the source of truth (usernames, bios, locations, post
templates, comment templates). Edit it and re-run both scripts to change the data.

## Homepage design

`templates/locations/home_stitch.html` is built from the actual generated code of
the Stitch project **"NomadNet Homepage Design"** (screen: *NomadNet —
Location-First Travel Discovery & Stories*), fetched directly via the Stitch MCP
tools rather than approximated. It keeps the exact color tokens, type scale, and
section layout from that export (hero + destination carousel, trending-places
strip, interactive map/spatial-radar section, location-first feed, sidebar).

Two things were deliberately **not** carried over 1:1, since they implied
functionality the app doesn't have:
- The decorative "ambient sound player" bar in the hero (fake audio scrubber).
- Fictional per-post stats not in the schema (Wi-Fi Mbps, noise dB, outlet count).

Everything else is wired to live data: the destination carousel, trending strip,
map panel, feed, and sidebar all render real locations/posts/users from the
database (via `utils/location_enricher.py` for computed rating/nomad-count/etc.).

## Bugs fixed along the way (pre-existing, not introduced by this work)

- **Login/signup were completely broken.** `{{ csrf_token() }}` was used bare in
  every form across the app (not wrapped in a hidden input), so no `csrf_token`
  field was ever actually submitted — every POST request, including login and
  signup, was rejected with a 400. Fixed everywhere it appeared (10 templates).
- Two of those bare `{{ csrf_token() }}` calls were inside
  `<meta name="csrf-token" content="...">` tags — fixed to keep emitting the raw
  token there instead of a nested `<input>`.
- `routes/locations.py`: the no-query branch of `/locations/search` rendered
  `search_locations.html` instead of `locations/search_locations.html` → 500 on
  a bare visit to Location Search.
- `templates/locations/search_locations.html`: the "add location from search"
  form posted to `api.create_location` (doesn't exist — the real endpoint is
  `api.api_create_location`, and it expects JSON, not form data) and had no CSRF
  token. Pointed it at `locations.create_location` instead, which matches the
  form fields and behavior.
- `templates/locations/home.html` had a stray shell command with a **live Stitch
  API key** pasted at the end of the file (accidental paste, not related to page
  content). Removed it. If that key was ever pushed anywhere, rotate it.
- `instance/nomadnet.db` (the DB Flask uses) vs. a stray `nomadnet.db` at the repo
  root (unused, created by a prior ad-hoc script) had drifted out of sync. The
  stray root-level file was removed; `load_seed_data.py` now targets
  `instance/nomadnet.db` explicitly.

## Key URLs

| Page | URL |
|------|-----|
| Home | `/` |
| Location detail | `/location/<id>` |
| User profile | `/user/<username>` |
| Location search | `/locations/search?q=...` |
| Login / Signup | `/login`, `/signup` |
