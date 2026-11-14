# Source research ledger

This file records source-discovery leads and implementation status. It is not a scraper catalogue copied from another project.

| Market | Candidate/source | Format | Specta adapter | Status |
|---|---|---|---|---|
| MENA | beIN SPORTS public TV guide | JSON API | `bein_mena` | Native adapter implemented; live verification pending |
| UK | To be investigated | — | — | Research pending |
| US | To be investigated | — | — | Research pending |

## Research procedure

For each candidate, record its official guide page, publicly documented data endpoint or downloadable schedule, territory, timezone, update cadence, access conditions, and rate limits. Prefer official broadcaster/provider sources. Implement a native adapter only after the source and its permitted access method have been checked.

Public EPG source directories can be used to find candidate URLs and source names. They are references for research, not runtime dependencies or code libraries.
