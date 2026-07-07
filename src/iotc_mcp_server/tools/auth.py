# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Auth/health tool: refresh the session and report login status, without exposing secrets."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import accesstoken, config, credentials

from ..errors import call_lib

_READ = ToolAnnotations(readOnlyHint=True)


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=_READ)
    async def auth_status() -> dict:
        """Report login status, refreshing the session if needed.

        Call this before other work and to recover from a tool's auth error: it validates
        the session and, if the token has expired, refreshes it with the stored refresh
        token - so retry the failed call once logged_in is true. If logged_in is false,
        the user must run `iotconnect-cli configure` out-of-band. Never exposes the token.
        """
        try:
            await call_lib(credentials.check)
        except ToolError:
            try:
                await call_lib(credentials.refresh)
            except ToolError:
                return {"logged_in": False, "message": "Not logged in. Run `iotconnect-cli configure` to authenticate."}
        token = await call_lib(accesstoken.decode_access_token)
        return {
            "logged_in": True,
            "configured_username": config.username,
            "cpid": token.user.cpId,
            "entity_guid": token.user.entityGuid,
            "role": token.user.roleName,
        }
