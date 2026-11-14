# Source research ledger

This is a lead list for independent Specta adapter research. The names/domains were discovered from the public `iptv-org/epg` site inventory and then checked against public guide pages. No scraper code or framework is imported.

| Market | Candidate | Public guide evidence | Data access / adapter status |
|---|---|---|---|
| MENA | beIN SPORTS MENA | Official TV guide | Native JSON API adapter implemented; live run still required |
| UK | My Telly | Public channel and regional listings pages | HTML/data endpoint, access conditions and stable IDs need verification |
| UK | tv24.co.uk | Public UK TV listings guide | HTML/data endpoint, access conditions and stable IDs need verification |
| UK | Freeview | Official TV Guide | No public schedule API confirmed; investigate before implementation |
| US | TV Passport | Public station schedule pages | HTML/data endpoint, access conditions and stable IDs need verification |
| US | On TV Tonight | Public station schedule pages | HTML/data endpoint, access conditions and stable IDs need verification |
| US | tvtv.us | Listed as an EPG source lead | Current public guide and data access need verification |
| US | TV Guide | Listed as an EPG source lead | Current public guide and data access need verification |

## Research procedure

For each candidate, confirm the actual schedule endpoint, coverage, timezone, freshness, channel identity, terms/access conditions and request limits. Prefer official broadcaster/provider sources where available. Do not infer that a source is suitable merely because it appears in a source directory. Do not attempt to bypass authentication, anti-bot controls or access restrictions.

Source discovery references:
- `https://github.com/iptv-org/epg/blob/master/SITES.md`
- `https://www.mytelly.co.uk/`
- `https://tv24.co.uk/`
- `https://www.freeview.co.uk/`
- `https://www.tvpassport.com/`
- `https://www.ontvtonight.com/`
