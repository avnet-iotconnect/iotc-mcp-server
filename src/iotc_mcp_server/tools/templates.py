# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Template tools: list device templates with filtering."""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import template
from avnet.iotconnect.restapi.lib.template import TemplateQuery

from ..errors import call_lib
from ..serialization import template_compact

_READ = ToolAnnotations(readOnlyHint=True)


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=_READ)
    async def template_list(
        name: Optional[str] = None,
        auth_type: Optional[int] = None,
        is_edge: Optional[bool] = None,
        is_gateway: Optional[bool] = None,
        wireless: Optional[bool] = None,
        sort: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List device templates with server-side filtering and paging.

        `auth_type` is the numeric x509/key auth type (2=CA-signed, 3=self-signed,
        4=TPM, 5=symmetric-key, 7=CA-individual). Returns compact rows with the
        template `code` (the friendly id used elsewhere) plus total_count and has_next.
        """
        query = TemplateQuery(
            name=name, auth_type=auth_type,
            is_edge=is_edge, is_gateway=is_gateway, wireless=wireless,
            page=page, page_size=page_size, sort_by=sort,
        )
        result = await call_lib(template.query, query)
        return {
            "templates": [template_compact(t) for t in result.items],
            "total_count": result.total_count,
            "page": result.page_number,
            "page_size": result.page_size,
            "has_next": result.has_next,
        }
