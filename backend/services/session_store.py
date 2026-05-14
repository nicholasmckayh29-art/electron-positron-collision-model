"""Shared in-memory session for uploaded collision data (used by data + quantum routers)."""

from __future__ import annotations

from typing import Optional

from models.types import OutlierEvent, Stats

session_data: list[dict] = []
session_stats: Optional[Stats] = None
session_outliers: list[OutlierEvent] = []
