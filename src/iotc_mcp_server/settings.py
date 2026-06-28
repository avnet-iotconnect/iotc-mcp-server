# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""
Server transport/bind settings, read from the environment.

Network-first defaults (see work/DECISIONS.md): the HTTP endpoint is unauthenticated,
so it binds to localhost and operators opt into wider exposure explicitly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

TRANSPORTS = ("streamable-http", "sse", "stdio")


@dataclass(frozen=True)
class Settings:
    transport: str
    host: str
    port: int

    @staticmethod
    def from_env() -> "Settings":
        transport = os.environ.get("IOTC_MCP_TRANSPORT", "streamable-http").strip().lower()
        if transport not in TRANSPORTS:
            raise ValueError(
                f'IOTC_MCP_TRANSPORT="{transport}" is not one of {", ".join(TRANSPORTS)}'
            )
        host = os.environ.get("IOTC_MCP_HOST", "127.0.0.1").strip()
        try:
            port = int(os.environ.get("IOTC_MCP_PORT", "8000"))
        except ValueError:
            raise ValueError("IOTC_MCP_PORT must be an integer")
        return Settings(transport=transport, host=host, port=port)
