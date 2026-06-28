# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Telemetry tools: current snapshot, recent points, and historical feed."""

from __future__ import annotations

from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import telemetry
from avnet.iotconnect.restapi.lib.telemetry import TelemetryQuery

from ..errors import call_lib
from ..serialization import parse_duration, sensor_value, telemetry_record

_READ = ToolAnnotations(readOnlyHint=True)

_HISTORY_DEFAULT_MAX = 200


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=_READ)
    async def telemetry_current(duid: str) -> dict:
        """Get the latest value of each of a device's attributes (its sensor snapshot)."""
        values = await call_lib(telemetry.get_current_values, duid)
        return {"duid": duid, "attributes": [sensor_value(v) for v in values]}

    @mcp.tool(annotations=_READ)
    async def telemetry_recent(
        duid: str,
        count: int = 10,
        attributes: Optional[List[str]] = None,
    ) -> dict:
        """Get the most recent N raw data points for a device (count must be 10-50).

        Optionally restrict to specific `attributes` by name.
        """
        points = await call_lib(telemetry.get_recent, duid, count, None, attributes)
        return {"duid": duid, "count": len(points), "points": points}

    @mcp.tool(annotations=_READ)
    async def telemetry_history(
        duids: List[str],
        last: Optional[str] = None,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
        max_records: int = _HISTORY_DEFAULT_MAX,
    ) -> dict:
        """Get historical telemetry for one or more devices, newest-first.

        Give the range as EITHER `last` (a relative duration like "15m", "2h", "1d")
        OR `from_time`/`to_time` (ISO-8601, e.g. "2026-06-24T17:00:00Z"). The window
        must be <= 7 days. Results are capped at `max_records`; ask for more explicitly.
        """
        if last and (from_time or to_time):
            raise ToolError('Use either "last" or "from_time"/"to_time", not both.')

        start = None
        if last:
            try:
                start = parse_duration(last)
            except ValueError as exc:
                raise ToolError(str(exc))
        elif from_time:
            start = from_time

        query = TelemetryQuery(duids=duids, from_time=start, to_time=to_time)
        records = await call_lib(telemetry.get_history, query)
        truncated = len(records) > max_records
        records = records[:max_records]
        return {
            "records": [telemetry_record(r) for r in records],
            "returned": len(records),
            "truncated": truncated,
        }
