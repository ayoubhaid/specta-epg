# specta-epg

Self-hosted XMLTV guide for sports channels, rebuilt every 6 hours by GitHub Actions.

## Setup
1. Create a GitHub repo, push this folder.
2. Settings → Pages → Source: **GitHub Actions**.
3. Actions tab → **Build EPG** → Run workflow.
4. In Specta, set the EPG URL to `https://<user>.github.io/<repo>/guide.xml.gz`
   (plain `guide.xml` also works).

## How it works
- `data/channels.csv` – your provider's sports channels.
- `scripts/build_channels.py` – matches each channel to a scraper in iptv-org/epg
  (by provider EPG id, then exact name, then fuzzy name). Writes `coverage.csv`.
- iptv-org's grabber scrapes the matched sites.
- `scripts/merge_guide.py` – re-keys the guide to your channels. XMLTV channel id =
  your provider's tvg-id when it has one, otherwise the `sp-xxxx` id; all playlist
  names are added as display-names.
- `public/coverage.csv` (published next to the guide) lists every channel's status.

## Filling gaps
Check `coverage.csv` for `unmatched`. For those, add a scraper under `custom_sites/`
(see its README) or add a row in `data/site_priority.txt` to prefer a better source.
Rows flagged `skipped_vod` are UFC/event-replay entries that have no schedule.
