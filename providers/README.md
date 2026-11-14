# Provider adapters

Each adapter is native Specta code under `src/specta_epg/providers/` and implements the small interface in `base.py`.

## Adding a provider

1. Identify an appropriate public schedule source and document its URL, data format, region, timezone, and usage constraints.
2. Implement a dedicated adapter. Do not copy an adapter implementation from another repository.
3. Normalize source records into the shared `Programme` model.
4. Add offline fixtures and tests. Tests must not depend on the live source.
5. Discover provider channel IDs and add only manually reviewed mappings.
6. Enable the provider in `config/providers.json`.

A source appearing in a public EPG directory is a research lead, not proof that its API is stable or that every collection method is permitted. Never bypass access controls.
