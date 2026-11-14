# Custom provider adapters

Custom integrations belong in `src/specta_epg/providers/` and implement the native Specta adapter interface in `base.py`.

Do not copy third-party scraper implementations or their framework-specific directory formats. Document each source, implement its own parser/client, add offline fixtures, and use reviewed channel mappings.