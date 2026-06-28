# iotc-mcp-server

An [MCP](https://modelcontextprotocol.io) server that exposes an Avnet
**/IOTCONNECT** account to an LLM, by wrapping the typed
[`iotconnect-rest-api`](https://pypi.org/project/iotconnect-rest-api/) Python library.

It lets a user operate their account through natural-language chat, for example:
- "give me the latest telemetry for all devices under Room23"
- "register a new device 'sensor-12' on template 'envmon'"
- "which devices in Room23 are inactive?"

The server is a thin, clear adapter: the library already does filtering, paging,
friendly-name resolution, validation and error mapping, so each tool just flattens
parameters, calls one library function and shapes a compact result.

## Security — read this first

- **The MCP server has no authentication of its own.** It acts with the full
  privileges of the logged-in /IOTCONNECT user.
  It therefore binds to `127.0.0.1` by default; only expose it on a trusted
  network, behind your own auth, if you change that.
- **Write tools are real and irreversible** (delete a device, deactivate it, send a
  command). They are annotated so the client can require confirmation — confirm
  before running them. REST-created devices cannot be deleted from the web UI, so
  `device_delete` here is the intended deletion path.
- **`device_create` and `generate_device_cert` return a private key.** It is shown
  once, never logged. Store it securely.

## Authentication

The server does not collect credentials. Log in once, out-of-band, with the
library's CLI:

```
iotconnect-cli configure
```

This stores a session token in the library's config (`~/.config/iotconnect/apicfg.ini`),
which the library auto-refreshes on use. The `auth_status` tool reports the logged-in
user, account CPID and token validity without exposing secrets. If a tool reports an
auth error, re-run `iotconnect-cli configure`.

## Install

```
pip install iotc-mcp-server
```

Requires Python >= 3.11.

## Run

```
iotc-mcp-server
```

Configuration is via environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `IOTC_MCP_TRANSPORT` | `streamable-http` | `streamable-http`, `sse` or `stdio` |
| `IOTC_MCP_HOST` | `127.0.0.1` | Bind address |
| `IOTC_MCP_PORT` | `8000` | Bind port |

With the default transport the endpoint is `http://127.0.0.1:8000/mcp`. Point a
client at it — see [mcp.example.json](mcp.example.json).

## Tools

Reads (safe): `device_list`, `device_get`, `entity_list`, `entity_descendants`,
`user_list`, `template_list`, `telemetry_current`, `telemetry_recent`,
`telemetry_history`, `auth_status`.

Writes (destructive): `device_create`, `device_delete`, `device_set_active`,
`generate_device_cert`, `command_send`.

All tools accept **friendly identifiers** (DUID, template code, entity name, user
email) — never invent GUIDs. Conceptual guidance is served on demand through the
`iotc://guide/*` resources (overview, identifiers, entities, telemetry, devices,
recipes).
