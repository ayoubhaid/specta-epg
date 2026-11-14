from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must include a timezone: {value}")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class InventoryChannel:
    id: str
    name: str
    tvg_id: str = ""
    language: str = ""
    country: str = ""
    region: str = ""
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Programme:
    id: str
    channel_id: str
    title: str
    description: str
    start: datetime
    end: datetime
    source: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Programme title cannot be empty")
        if self.end <= self.start:
            raise ValueError("Programme end must be after start")
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("Programme timestamps must be timezone-aware")

    def json_dict(self) -> dict:
        start = self.start.astimezone(timezone.utc)
        end = self.end.astimezone(timezone.utc)
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
            "startEpochSeconds": int(start.timestamp()),
            "endEpochSeconds": int(end.timestamp()),
            "source": self.source,
        }


@dataclass
class ChannelSchedule:
    channel: InventoryChannel
    programmes: list[Programme] = field(default_factory=list)
