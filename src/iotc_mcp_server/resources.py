# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""
On-demand guidance, kept out of the always-on footprint.

The server `instructions` string is the tiny always-on orientation; the deeper
conceptual knowledge lives in `iotc://guide/*` resources, read by the client only
when relevant. Keeping it here means tool docstrings stay one or two lines.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

INSTRUCTIONS = (
    "This server wraps a single /IOTCONNECT account through the iotconnect-rest-api "
    "library. Use friendly identifiers, never GUIDs: device DUID, template code, "
    "entity name, user email - they are resolved for you, so do not invent GUIDs. "
    "Entities form a tree, so 'under entity X' means X plus all its descendants - "
    "expand with entity_descendants first. List tools return compact projections "
    "plus paging info; use the matching *_get for a full record. Read iotc://guide/* for "
    "concepts. Writes (create/delete/activate device, send command) are real and "
    "irreversible - confirm with the user before calling them. If a tool reports an "
    "auth error, call auth_status - it will try to refresh the session so you can retry; "
    "only if it still fails must the user run `iotconnect-cli configure` out-of-band."
)

_OVERVIEW = """\
# /IOTCONNECT MCP server

Operates one /IOTCONNECT account (devices, telemetry, templates, users, entities,
commands) over natural language. Domains and their tools:

- Devices: device_list, device_get, device_create, device_delete, device_set_active
- Telemetry: telemetry_current, telemetry_recent, telemetry_history
- Org tree: entity_list, entity_get, entity_descendants
- Templates: template_list, template_get, template_create, template_delete
- Users: user_list
- Commands: command_send
- Certs: generate_device_cert
- Health: auth_status

Reads are safe and compact; writes are real and irreversible. See the other
iotc://guide/* resources for identifiers, entities, telemetry, devices and recipes.
"""

_IDENTIFIERS = """\
# Identifiers

Always pass friendly identifiers; the library resolves them to GUIDs. Never
fabricate a GUID.

- Device: DUID (unique id, e.g. "sensor-12"). Prefer it over the device GUID.
- Template: template code (1-10 alphanumeric chars, e.g. "envmon").
- Entity: entity name (e.g. "Room23"). Names must be unique to resolve.
- User: email / username.

Where a tool offers both a friendly param and a `guid`, use the friendly one unless
you genuinely hold a GUID. Listings include the GUID for the rare case you need it.
"""

_ENTITIES = """\
# Entities (the org tree)

Entities form a tree via `parent_guid`; the root entity has `parent_guid` null.
"Under entity X" or "in X" means X PLUS all of its descendants, not just X.

To act on devices under an entity:
1. entity_descendants(name="X") -> X and every descendant entity.
2. For each returned entity guid, device_list(entity=<guid>).
3. Aggregate the devices.

entity_list returns the whole tree at once (it is small and unpaged); use entity_get
(by name or guid) for one entity's full record, including its address.
"""

_TELEMETRY = """\
# Telemetry

Three reads, by intent:

- telemetry_current(duid): the latest value of each attribute - the sensor
  snapshot. Use for "what is it reading now".
- telemetry_recent(duid, count): the last N raw points (count 10-50). Use for a
  short recent trend on one device.
- telemetry_history(duids, last|from_time/to_time): the historical feed, newest
  first, for one or more devices. Give EITHER `last` ("15m"/"2h"/"1d") OR an ISO
  `from_time`/`to_time`. Window <= 7 days. Results are capped by `max_records`.

Times are UTC. History iterates per device, so large device lists cost more calls.
"""

_DEVICES = """\
# Device lifecycle

- Create (device_create): needs a template (code/GUID) and a DUID; the auth mode must
  match the template's auth type:
  - default (no cert): server generates a self-signed EC cert + private key, registers,
    and returns BOTH - show the private key once, tell the user to store it, then clear
    the chat;
  - `certificate` (PEM): register the caller's own self-signed cert;
  - `ca_signed=true`: CA-signed device - no cert is passed, generated, or returned.
  The response carries an `sdk_config` block (platform, env, cpid, duid, auth_type) for
  the device's SDK config (iotcDeviceConfig.json).
- Activate/deactivate (device_set_active): toggles connectivity status.
- Delete (device_delete): irreversible. REST-created devices cannot be deleted from
  the web UI, so this tool is the intended path.

Finding devices: `device_list` `duid_contains` is a case-insensitive substring match,
so use device_get for one exact DUID. Lists give `has_next` (and `total_count` only when
the server reports one) - page by has_next.

`status` is active/inactive (connectivity). Auth types are numeric on templates:
2=CA-signed, 3=self-signed, 4=TPM, 5=symmetric-key, 7=CA-individual.
"""

_RECIPES = """\
# Recipes

## Latest telemetry for all devices under entity Room23 (incl. children)
1. entity_descendants(name="Room23")
2. device_list(entity=<guid>) for each returned entity guid; collect DUIDs
3. telemetry_current(duid) per device (or telemetry_history(duids=[...], last="15m"))
4. Interpret and summarize for the user

## Register a new device 'sensor-12' on template 'envmon'
1. device_create(template="envmon", duid="sensor-12")  # no certificate
2. Present the returned certificate AND private_key, with a secure-storage reminder

## Which devices in Room23 are inactive?
1. entity_descendants(name="Room23")
2. device_list(entity=<guid>, status="inactive") per entity guid
3. List them

## What telemetry / commands does template 'envmon' support?
1. template_get(code="envmon") -> metadata, `attributes` (telemetry schema), `commands`
"""

_GUIDES = {
    "iotc://guide/overview": ("IOTCONNECT overview", _OVERVIEW),
    "iotc://guide/identifiers": ("Identifiers", _IDENTIFIERS),
    "iotc://guide/entities": ("Entities (org tree)", _ENTITIES),
    "iotc://guide/telemetry": ("Telemetry", _TELEMETRY),
    "iotc://guide/devices": ("Device lifecycle", _DEVICES),
    "iotc://guide/recipes": ("Recipes", _RECIPES),
}


def _make_reader(text: str):
    """A zero-arg reader closure (FastMCP treats reader params as URI template vars)."""
    def read() -> str:
        return text
    return read


def register(mcp: FastMCP) -> None:
    for uri, (title, text) in _GUIDES.items():
        mcp.resource(uri, title=title, mime_type="text/markdown")(_make_reader(text))
