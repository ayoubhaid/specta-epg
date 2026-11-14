# Architecture and operations

## Identity flow

The inventory ID is the canonical Specta identity. Provider channel IDs are source-specific identifiers and are stored only in the reviewed mapping file. Provider IDs never replace inventory IDs in the published feed.

## Mapping workflow

1. Run `python scripts/run_epg.py discover --provider bein_mena --output build/bein-catalog.json`.
2. Run `python scripts/run_epg.py suggest --provider bein_mena --inventory /path/to/private/channels.xml --output build/bein-mapping-review.csv`.
3. Review each candidate against region, channel variant and schedule. Suggestions are never automatically approved.
4. Add verified rows to `config/channel-mapping.json` with `reviewed: true`.
5. Run the build and inspect `coverage.json` before enabling Pages deployment.

Example mapping:

```json
{
  "schemaVersion": 1,
  "mappings": [
    {
      "inventoryId": "specta-channel-stable-id",
      "provider": "bein_mena",
      "providerChannelId": "provider-source-id",
      "reviewed": true
    }
  ]
}
```

## Adding providers

Implement the `ProviderAdapter` interface:
- `list_channels()` returns provider IDs and names for mapping review.
- `fetch_programmes(provider_channel_id, days)` returns normalized `Programme` objects.

Keep requests sequential unless the source documents a safe higher rate. Use bounded timeouts, UTC-aware times, offline fixtures, and a dedicated test module. A provider is not production-ready until its endpoint has been verified live and its coverage has been measured.

## Publication gate

A build with no programmes fails. GitHub Pages is deployed only after tests, private inventory validation, provider collection and output generation all succeed. A failed build therefore does not replace the last published guide.
