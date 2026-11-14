# Specta channel inventory XML

Specta exports one XML document per playlist/provider inventory snapshot. The export is an identity catalogue, not a playlist backup.

## Contract

Root:
`<channelInventory schemaVersion="1" generatedAt="..." source="specta">`

Each `channel` requires:
- `id`: stable Specta-generated identity. It must remain stable when a stream URL or quality endpoint changes.
- `name`: display name.

Optional attributes:
- `tvg-id`
- `language`
- `country`
- `region`

Optional child:
- `<alias>`: alternative display name.

Example: `channels.example.xml`.

## Never export

Do not include stream URLs, playlist URLs, provider hostnames, usernames, passwords, tokens, cookies, authorization headers, or other credentials. The parser rejects common URL and credential field names as a guardrail, but the exporter must also enforce this contract.

Keep separate channel IDs for distinct logical channels, including same-name channels when they represent different services. Do not derive the stable ID from the stream URL.
