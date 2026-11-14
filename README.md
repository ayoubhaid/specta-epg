# Specta EPG

Specta's independent, curated electronic programme guide pipeline.

This repository owns its inventory contract, provider adapters, channel matching, programme normalization, validation, and XMLTV/JSON output. The project may use public EPG directories (including iptv-org's source listings) to **discover candidate sources**, but it does not import or execute iptv-org code.

## Architecture

1. Specta exports a channel inventory XML file. It contains stable channel IDs and metadata only — never stream URLs, playlist credentials, or provider login data.
2. The inventory parser validates the schema and rejects stream/credential fields.
3. Provider adapters independently collect schedule metadata from selected sources.
4. `config/channel-mapping.json` explicitly maps Specta inventory IDs to provider channel IDs. Only reviewed mappings are used.
5. The pipeline normalizes and validates programmes, then writes XMLTV and Specta JSON.
6. GitHub Actions publishes only after a successful, non-empty build.

## Repository layout

- `src/specta_epg/`: inventory, provider interface, adapters, matching, serialization, validation, pipeline.
- `providers/`: provider/source documentation and future adapter notes.
- `config/`: provider registry and reviewed channel mappings.
- `inventory/channels.example.xml`: public schema example only.
- `tests/`: offline tests; no live source calls.
- `public/`: generated Pages output (never hand-edit).

## Current provider status

| Provider | Adapter | Status |
|---|---|---|
| beIN SPORTS MENA | `bein_mena` | Initial native adapter implemented; API availability must be verified by a live workflow run |
| UK sources | — | Research/implementation pending |
| US sources | — | Research/implementation pending |

The beIN adapter is an independent implementation of the public beIN guide API pattern already used in the Specta beIN prototype. It does not import that repository or iptv-org code.

## Local use

Requires Python 3.12+; runtime uses only the Python standard library.

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/run_epg.py discover --provider bein_mena --output build/bein-catalog.json
```

To build locally, provide a private inventory file and reviewed mappings:

```bash
SPECTA_INVENTORY_PATH=/secure/path/channels.xml \
python scripts/run_epg.py build --mapping config/channel-mapping.json --output-dir public
```

Set `BEIN_REGION`, `EPG_DAYS`, and `REQUEST_DELAY_MS` to configure the beIN adapter.

## Private inventory in GitHub Actions

Do not commit the real TREX-derived inventory to this public repository. Configure a private repository containing `channels.xml`, then add these Actions secrets:

- `SPECTA_INVENTORY_REPO`: private repository in `owner/repo` form.
- `SPECTA_INVENTORY_TOKEN`: fine-grained token with read-only Contents access to that repository.

The workflow checks out that private repository into a temporary runner directory. It is not copied into the public Pages artifact. If these secrets are absent, the scheduled build fails safely rather than publishing an example or stale/empty feed.

The inventory contract is documented in `inventory/channels.example.xml`.

## Mapping policy

Mappings are explicit and reviewed. No fuzzy name matching is performed during production builds. Similar names, HD/SD variants, regional feeds, and channels with different Specta IDs remain distinct unless a human approves a mapping. Do not use stream URLs as identity.

See `config/channel-mapping.example.json`. Run the provider `discover` command to obtain real provider channel IDs before adding reviewed mappings.

## Outputs

- `public/guide.xml` and `public/guide.xml.gz`: XMLTV.
- `public/epg.json`: normalized Specta JSON.
- `public/coverage.json`: per-channel mapping and programme coverage, without private inventory source paths.

All timestamps are UTC ISO-8601 in JSON and XMLTV UTC timestamps in XML.

## Safety and reliability

- Conservative sequential requests and configurable delays.
- Request timeouts and bounded date windows.
- Invalid or empty source responses fail the build.
- Output is built and validated before publication.
- GitHub Pages deployment happens only after the build succeeds, preserving the last deployed site on failure.
- Use only sources and access methods that are publicly available and permitted. Respect source terms, rate limits, and access restrictions; do not attempt to bypass authentication or technical controls.
