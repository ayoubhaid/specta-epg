#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from specta_epg.pipeline import build, discover, suggest_mappings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Specta's independent EPG pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    discover_parser = sub.add_parser("discover", help="List provider channel IDs for mapping review")
    discover_parser.add_argument("--provider", required=True)
    discover_parser.add_argument("--output", default="build/provider-catalog.json")

    suggest_parser = sub.add_parser("suggest", help="Create a review-only exact-name mapping report")
    suggest_parser.add_argument("--provider", required=True)
    suggest_parser.add_argument("--inventory", default="inventory/channels.xml")
    suggest_parser.add_argument("--output", default="build/mapping-review.csv")

    build_parser = sub.add_parser("build", help="Build curated XMLTV and JSON feeds")
    build_parser.add_argument("--inventory", default="inventory/channels.xml")
    build_parser.add_argument("--mapping", default="config/channel-mapping.json")
    build_parser.add_argument("--output-dir", default="public")
    build_parser.add_argument("--days", type=int, default=5)

    args = parser.parse_args()
    if args.command == "discover":
        records = discover(args.provider)
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
        print(f"Discovered {len(records)} channels from {args.provider}: {destination}")
        return 0

    if args.command == "suggest":
        counts = suggest_mappings(args.inventory, args.provider, args.output)
        print(json.dumps(counts, indent=2))
        print(f"Review suggestions manually: {args.output}")
        return 0

    if not 1 <= args.days <= 14:
        parser.error("--days must be between 1 and 14")
    coverage = build(args.inventory, args.mapping, args.output_dir, args.days)
    print(json.dumps(coverage, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
