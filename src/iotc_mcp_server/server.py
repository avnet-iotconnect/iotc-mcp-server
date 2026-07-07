# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Build and run the /IOTCONNECT MCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import resources, tools
from .settings import Settings


def build_server(settings: Settings | None = None) -> FastMCP:
    settings = settings or Settings.from_env()
    mcp = FastMCP(
        "iotconnect",
        instructions=resources.INSTRUCTIONS,
        host=settings.host,
        port=settings.port,
    )
    tools.register_all(mcp)
    resources.register(mcp)
    return mcp


def main() -> None:
    settings = Settings.from_env()
    mcp = build_server(settings)
    mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
