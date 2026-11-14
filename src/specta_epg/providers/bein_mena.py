from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .base import ProviderAdapter
from ..models import Programme, parse_datetime


class BeinMenaAdapter(ProviderAdapter):
    provider_id = "bein_mena"
    api_base = "https://www.beinsports.com/api/opta"

    def __init__(self, region: str | None = None, delay_ms: int | None = None):
        self.region = region or os.getenv("BEIN_REGION", "en-mena")
        self.delay_ms = delay_ms if delay_ms is not None else int(os.getenv("REQUEST_DELAY_MS", "500"))
        self.user_agent = "SpectaEPG/2.0 (public TV guide ingestion)"

    def _get_json(self, url: str) -> dict:
        request = Request(url, headers={
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        })
        with urlopen(request, timeout=25) as response:
            if response.status != 200:
                raise RuntimeError(f"beIN endpoint returned HTTP {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Unexpected beIN response: expected a JSON object")
        time.sleep(max(0, self.delay_ms) / 1000)
        return payload

    def list_channels(self) -> list[dict]:
        query = urlencode({"region": self.region})
        payload = self._get_json(f"{self.api_base}/tv-channel?{query}")
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise ValueError("Unexpected beIN channel response: rows array missing")
        return [
            {"id": str(row["id"]), "name": str(row["name"]).strip(), "region": self.region}
            for row in rows
            if isinstance(row, dict) and row.get("id") and row.get("name")
        ]

    def fetch_programmes(self, provider_channel_id: str, days: int = 5) -> list[Programme]:
        if not 1 <= days <= 14:
            raise ValueError("days must be between 1 and 14")
        programmes: list[Programme] = []
        for offset in range(days):
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            start += timedelta(days=offset)
            end = start + timedelta(days=1)
            # The public guide endpoint expects the UTC timestamp followed by Z.
            fmt = lambda value: value.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            query = urlencode({
                "startBefore": f"{fmt(end)}Z",
                "endAfter": f"{fmt(start)}Z",
                "channelIds": provider_channel_id,
            })
            payload = self._get_json(f"{self.api_base}/tv-event?{query}")
            rows = payload.get("rows")
            if not isinstance(rows, list):
                raise ValueError(f"Unexpected beIN event response for channel {provider_channel_id}")
            for row in rows:
                if not isinstance(row, dict):
                    continue
                title = row.get("title")
                try:
                    if not isinstance(title, str) or not title.strip():
                        continue
                    programme_start = parse_datetime(str(row["startDate"]))
                    programme_end = parse_datetime(str(row["endDate"]))
                    if programme_end <= programme_start:
                        continue
                except (KeyError, TypeError, ValueError):
                    continue
                programme_id = f"{provider_channel_id}:{int(programme_start.timestamp())}:{title.casefold()}"
                programmes.append(Programme(
                    id=programme_id,
                    channel_id=provider_channel_id,
                    title=title.strip(),
                    description=str(row.get("description") or "").strip(),
                    start=programme_start,
                    end=programme_end,
                    source=self.provider_id,
                ))
        unique: dict[tuple, Programme] = {}
        for programme in programmes:
            key = (programme.start, programme.end, programme.title.casefold())
            unique[key] = programme
        return sorted(unique.values(), key=lambda item: item.start)
