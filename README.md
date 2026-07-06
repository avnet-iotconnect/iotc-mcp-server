# iotc-mcp-server

An [MCP](https://modelcontextprotocol.io) server that puts an Avnet
**/IOTCONNECT** account in front of an LLM, by wrapping the typed
[`iotconnect-rest-api`](https://pypi.org/project/iotconnect-rest-api/) Python library.
Ask in plain language; the model resolves your device names, templates and entities,
calls the right REST endpoints, and hands back a shaped, human-readable answer instead
of raw API JSON.

This project can be used by configuring your favorite LLM client or Agent (Claude, ChatGPT, etc.)
to use this server as a local MCP endpoint. For example, to use with the Claude Code CLI, 
you only need to configure, start this MCP server (see below) and run:
```bash
claude mcp add --transport http iotconnect http://127.0.0.1:8000/mcp
```


A few examples of things you can do with this project:
- **Walk the fleet like a status board.** "Which devices under Denver Office haven't
  reported in the last day?" expands the entity tree floor by floor, lists devices per
  floor, and flags the ones gone quiet by last-communication time.
- **Turn raw telemetry into an answer.** "What's the latest reading from every sensor
  on gateway-04?" returns one clean value per mapped attribute instead of a firehose of
  JSON — follow up with "how did temperature trend over the last hour?" and the model
  reasons over the historical feed for you.
- **Provision a device in one prompt.** "Register a new device 'sensor-12' on template
  'envmon' and give me its cert" creates the device, generates the key pair, and returns
  the SDK config block your firmware needs — no console screens.
- **Act on what it finds.** "Reboot every inactive device in Room23" resolves the room,
  finds the offline devices, and sends the template-defined command to each one.

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

## Install

```
pip install iotconnect-mcp-server
```

Requires Python >= 3.11.

The server does not collect credentials. Log in only once, out-of-band, with the 
[iotconenct-rest-api](https://pypi.org/project/iotconnect-rest-api/)
library's CLI (installed along with iotconnect-mcp-server).

See the iotconenct-rest-api documentation on how to configure the CLI with your account credentials
and how to obtain the required Solution Key:

```
iotconnect-cli configure --help
```

This stores a session token in the library's config (`~/.config/iotconnect/apicfg.ini`),
which the library auto-refreshes on use indefinitely. The `auth_status` tool reports the logged-in
user, account CPID and token validity without exposing secrets. If a tool reports an
auth error, re-run `iotconnect-cli configure`.



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

Reads (safe): `device_list`, `device_get`, `entity_list`, `entity_get`,
`entity_descendants`, `user_list`, `template_list`, `template_get`,
`telemetry_latest_value`, `telemetry_recent`, `telemetry_history`, `auth_status`.

Writes (destructive): `device_create`, `device_delete`, `device_set_active`,
`generate_device_cert`, `template_create`, `template_delete`, `command_send`.

All tools accept **friendly identifiers** (DUID, template code, entity name, user
email) — never invent GUIDs. Conceptual guidance is served on demand through the
`iotc://guide/*` resources (overview, identifiers, entities, telemetry, devices,
recipes).
