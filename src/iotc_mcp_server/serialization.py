# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""
Compact projections of the library's dataclasses for the tool surface.

List tools return small, stable field subsets (plus counts) so a naive call cannot
flood the model's context; the full record is available via the matching ``*_get``
tool. Projections use friendly, self-describing keys (duid, not uniqueId).
"""

from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from datetime import timedelta
from typing import Any, Optional

from avnet.iotconnect.restapi.lib.command import Command
from avnet.iotconnect.restapi.lib.device import Device
from avnet.iotconnect.restapi.lib.entity import Entity
from avnet.iotconnect.restapi.lib.query import Page
from avnet.iotconnect.restapi.lib.telemetry import DeviceSensorValue, TelemetryRecord
from avnet.iotconnect.restapi.lib.template import Template
from avnet.iotconnect.restapi.lib.user import User


def full_record(obj: Any) -> Any:
    """Dump a full dataclass record (used by ``*_get`` tools), dropping null fields."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: v for k, v in asdict(obj).items() if v is not None}
    return obj


def paged_result(key: str, items: list, page: Page) -> dict:
    """Shape a list tool's response: always page/page_size/has_next; total_count only if known."""
    result = {
        key: items,
        "page": page.page_number,
        "page_size": page.page_size,
        "has_next": page.has_next,
    }
    if page.total_count is not None:
        result["total_count"] = page.total_count
    return result


def _status(is_active: Optional[bool]) -> Optional[str]:
    if is_active is None:
        return None
    return "active" if is_active else "inactive"


def device_compact(d: Device) -> dict:
    return {
        "duid": d.uniqueId,
        "name": d.displayName,
        "status": _status(d.isActive),
        "template_guid": d.deviceTemplateGuid,
        "guid": d.guid,
    }


def entity_compact(e: Entity) -> dict:
    return {
        "guid": e.guid,
        "name": e.name,
        "parent_guid": e.parentEntityGuid,
    }


def user_compact(u: User) -> dict:
    return {
        "email": u.userId,
        "first_name": u.firstName,
        "last_name": u.lastName,
        "role": u.roleName,
        "entity": u.entityName,
        "status": _status(u.isActive),
        "guid": u.id,
    }


def template_compact(t: Template) -> dict:
    return {
        "code": t.templateCode,
        "name": t.templateName,
        "guid": t.guid,
        "auth_type": t.authType,
        "is_edge": t.isEdgeSupport,
        "message_version": t.messageVersion,
    }


def sensor_value(v: DeviceSensorValue) -> dict:
    return {
        "attribute": v.attributeName,
        "value": v.attributeValue,
        "display_name": v.displayName,
        "data_type": v.DataType,
        "updated": v.deviceUpdatedDate,
    }


def telemetry_record(r: TelemetryRecord) -> dict:
    return {"duid": r.uniqueId, "time": r.dTime, "attr": r.attr}


def command_compact(c: Command) -> dict:
    return {"command": c.command, "name": c.name, "requires_param": c.requiredParam}


_DURATION_RE = re.compile(r"^\s*(\d+)\s*([smhdw])\s*$", re.IGNORECASE)
_DURATION_UNITS = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}


def parse_duration(text: str) -> timedelta:
    """Parse a relative duration like '15m', '2h', '1d', '30s', '1w' into a timedelta."""
    match = _DURATION_RE.match(text or "")
    if not match:
        raise ValueError(
            f'Could not parse duration "{text}". Use a number plus a unit, e.g. "15m", "2h", "1d".'
        )
    amount, unit = int(match.group(1)), match.group(2).lower()
    return timedelta(**{_DURATION_UNITS[unit]: amount})
