# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Template tools: list / get device templates, and create one from a JSON definition."""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import template
from avnet.iotconnect.restapi.lib.template import TemplateQuery

from ..errors import call_lib
from ..serialization import full_record, template_compact

_READ = ToolAnnotations(readOnlyHint=True)
_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


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

    @mcp.tool(annotations=_READ)
    async def template_get(code: Optional[str] = None, guid: Optional[str] = None) -> dict:
        """Get one template's full record by template code (preferred) or GUID.

        Use the GUID when you already have one (e.g. from a device record). Returns
        {"found": false}if no such template exists.
        """
        if code:
            t = await call_lib(template.get_by_template_code, code)
        elif guid:
            t = await call_lib(template.get_by_guid, guid)
        else:
            return {"error": "Provide either code or guid."}
        if t is None:
            return {"found": False}
        return full_record(t)

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def template_create(
        template_json: str,
        code: Optional[str] = None,
        name: Optional[str] = None,
    ) -> dict:
        """Create a device template from a full template JSON definition. DESTRUCTIVE.

        `template_json` is the complete template definition; ask the user to paste it -
        it is too detailed to author from a description. `code` (1-10 alphanumeric chars)
        and `name` optionally override the code/name in the JSON. Returns the new
        template GUID.
        """
        result = await call_lib(template.create_from_json_str, template_json, code, name)
        return {"template_guid": result.deviceTemplateGuid}

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def template_delete(code: Optional[str] = None, guid: Optional[str] = None) -> dict:
        """Delete a template by template code (preferred) or GUID. DESTRUCTIVE and irreversible.

        A template still attached to devices cannot be deleted (the API reports a
        conflict). Confirm with the user before calling.
        """
        if code:
            await call_lib(template.delete_match_code, code)
            return {"deleted": True, "code": code}
        elif guid:
            await call_lib(template.delete_match_guid, guid)
            return {"deleted": True, "guid": guid}
        else:
            return {"error": "Provide either code or guid."}
