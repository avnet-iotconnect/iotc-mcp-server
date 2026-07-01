# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""User tools: list account users with filtering."""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import user
from avnet.iotconnect.restapi.lib.user import UserQuery

from ..errors import call_lib
from ..serialization import paged_result, user_compact

_READ = ToolAnnotations(readOnlyHint=True)


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=_READ)
    async def user_list(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        entity: Optional[str] = None,
        status: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List account users with server-side filtering and paging.

        `entity` and `role` are matched by name. `status` is e.g. "active"/"inactive".
        Returns compact rows plus has_next (and total_count when the server reports one).
        """
        query = UserQuery(
            first_name=first_name, last_name=last_name, email=email,
            role=role, entity=entity, status=status,
            page=page, page_size=page_size, sort_by=sort,
        )
        result = await call_lib(user.query, query)
        return paged_result("users", [user_compact(u) for u in result.items], result)
