# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Command tool: send a template-defined command to a device."""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import command, device

from ..errors import call_lib

_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def command_send(duid: str, command_name: str, args: Optional[str] = None) -> dict:
        """Send a command to a device. DESTRUCTIVE: acts on the physical/edge device.

        `command_name` is the template's command identifier (not its display name).
        `args` are the optional command parameters. Confirm intent with the user first.
        """
        dev = await call_lib(device.get_by_duid, duid)
        if dev is None:
            raise ToolError(f'No device with DUID "{duid}".')

        cmd = await call_lib(command.get_with_name, dev.deviceTemplateGuid, command_name)
        if cmd is None:
            available = await call_lib(command.get_all, dev.deviceTemplateGuid)
            names = [c.command for c in available]
            raise ToolError(
                f'No command "{command_name}" on this device\'s template. Available: {names}'
            )

        await call_lib(command.send, cmd.guid, dev.guid, args)
        return {"duid": duid, "command": command_name, "sent": True}
