# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Auth/health tool: report login status without exposing secrets."""

from __future__ import annotations

from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import accesstoken, config, user

from ..errors import call_lib

_READ = ToolAnnotations(readOnlyHint=True)


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=_READ)
    async def auth_status() -> dict:
        """Report login status: the logged-in user, account CPID and token validity.

        Use this for orientation or when other tools report an auth error. Never
        exposes the token or any secret. If not logged in, the user must run
        `iotconnect-cli configure` out-of-band.
        """
        token = await call_lib(accesstoken.decode_access_token)
        if token is None:
            return {
                "logged_in": False,
                "message": "Not logged in. Run `iotconnect-cli configure` to authenticate.",
            }

        now = datetime.now(timezone.utc)
        expiry = (
            datetime.fromtimestamp(config.token_expiry, tz=timezone.utc)
            if config.token_expiry
            else None
        )
        status = {
            "logged_in": True,
            "configured_username": config.username,
            "cpid": token.user.cpId,
            "entity_guid": token.user.entityGuid,
            "role": token.user.roleName,
            "token_valid": bool(expiry and expiry > now),
            "token_expires_at": expiry.isoformat() if expiry else None,
        }
        try:
            own = await call_lib(user.get_own_user)
            if own is not None:
                status["user_email"] = own.userId
                status["name"] = " ".join(filter(None, [own.firstName, own.lastName])) or None
        except ToolError as exc:
            status["user_lookup_error"] = str(exc)
        return status
