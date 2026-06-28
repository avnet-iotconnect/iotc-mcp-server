# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""
Bridge between the (blocking, exception-raising) library and the async MCP layer.

* :func:`call_lib` runs a blocking library call on a worker thread so a single
  in-flight request does not stall the async server, and translates the library's
  typed exceptions into clean :class:`ToolError` messages an agent can act on.
* No stack traces or secrets are surfaced - only the library's own message text.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

import anyio
from mcp.server.fastmcp.exceptions import ToolError

from avnet.iotconnect.restapi.lib.error import (
    ApiException,
    AuthError,
    ConflictResponseError,
    NotFoundResponseError,
    UsageError,
)

T = TypeVar("T")

CONFIGURE_HINT = "Run `iotconnect-cli configure` to (re)authenticate."


def _is_auth_usage_error(exc: UsageError) -> bool:
    """A UsageError that really means 'not logged in' rather than 'bad argument'."""
    text = str(exc).lower()
    return "access token" in text or "not logged in" in text or "configure the api" in text


async def call_lib(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a blocking library function off-thread and map its errors to ToolError."""
    try:
        return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kwargs))
    except AuthError as exc:
        raise ToolError(f"Authentication failed: {exc.message or 'token rejected'}. {CONFIGURE_HINT}")
    except NotFoundResponseError as exc:
        raise ToolError(f"Not found: {exc.message or 'the requested resource does not exist'}.")
    except ConflictResponseError as exc:
        raise ToolError(f"Conflict: {exc.message or 'the operation conflicts with current state'}.")
    except UsageError as exc:
        if _is_auth_usage_error(exc):
            raise ToolError(f"Not logged in: {exc}. {CONFIGURE_HINT}")
        raise ToolError(f"Invalid input: {exc}")
    except ApiException as exc:
        raise ToolError(f"IoTConnect API error: {exc.message or 'request failed'} (HTTP {exc.status}).")
