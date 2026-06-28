# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Entity tools: the account org tree and descendant expansion."""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import entity
from avnet.iotconnect.restapi.lib.query import is_guid

from ..errors import call_lib
from ..serialization import entity_compact

_READ = ToolAnnotations(readOnlyHint=True)


def _collect_descendants(entities: list, root_guid: str) -> list:
    """Return the root entity plus every entity reachable through parentEntityGuid."""
    by_parent: dict[Optional[str], list] = {}
    for e in entities:
        by_parent.setdefault(e.parentEntityGuid, []).append(e)

    selected, stack = [], [root_guid]
    seen: set[str] = set()
    while stack:
        guid = stack.pop()
        if guid in seen:
            continue
        seen.add(guid)
        for child in by_parent.get(guid, []):
            selected.append(child)
            stack.append(child.guid)
    return selected


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=_READ)
    async def entity_list() -> dict:
        """List every entity in the account (the org tree).

        Entities form a tree via parent_guid; the root entity has parent_guid null.
        """
        entities = await call_lib(entity.query)
        return {"entities": [entity_compact(e) for e in entities], "total_count": len(entities)}

    @mcp.tool(annotations=_READ)
    async def entity_descendants(name: Optional[str] = None, guid: Optional[str] = None) -> dict:
        """Get an entity and ALL of its descendants (children, grandchildren, ...).

        "under entity X" / "in X" means X plus everything below it - expand here, then
        query devices per returned entity guid. Accepts an entity name or GUID.
        """
        if not name and not guid:
            return {"error": "Provide either name or guid."}
        entities = await call_lib(entity.query)

        root = None
        if guid and is_guid(guid):
            root = next((e for e in entities if e.guid == guid), None)
        if root is None:
            target = name or guid
            matches = [e for e in entities if e.name == target]
            if len(matches) == 1:
                root = matches[0]
            elif len(matches) > 1:
                return {"error": f'Entity name "{target}" is ambiguous; pass its guid instead.'}
        if root is None:
            alternatives = sorted({e.name for e in entities})[:10]
            return {"found": False, "did_you_mean": alternatives}

        descendants = _collect_descendants(entities, root.guid)
        members = [root] + descendants
        return {
            "root": entity_compact(root),
            "entities": [entity_compact(e) for e in members],
            "total_count": len(members),
        }
