# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Tool registration. Each domain module exposes ``register(mcp)``."""

from mcp.server.fastmcp import FastMCP

from . import auth, commands, devices, entities, telemetry, templates, users


def register_all(mcp: FastMCP) -> None:
    auth.register(mcp)
    devices.register(mcp)
    entities.register(mcp)
    users.register(mcp)
    templates.register(mcp)
    telemetry.register(mcp)
    commands.register(mcp)
