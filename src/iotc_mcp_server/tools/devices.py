# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Avnet

"""Device tools: list / get (read) and create / delete / activate (write)."""

from __future__ import annotations

from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from avnet.iotconnect.restapi.lib import accesstoken, config, device
from avnet.iotconnect.restapi.lib.device import DeviceQuery, DeviceStatus

from ..errors import call_lib
from ..serialization import device_compact, full_record, paged_result

_READ = ToolAnnotations(readOnlyHint=True)
_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=_READ)
    async def device_list(
        duid_contains: Optional[str] = None,
        status: Optional[Literal["active", "inactive"]] = None,
        template: Optional[str] = None,
        entity: Optional[str] = None,
        is_edge: Optional[bool] = None,
        is_gateway: Optional[bool] = None,
        wireless: Optional[bool] = None,
        sort: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List devices with server-side filtering and paging.

        `duid_contains` matches devices whose DUID contains that text (case-insensitive
        substring); for one exact device use device_get instead. `template` accepts a
        template code or GUID; `entity` accepts an entity name or GUID (resolved for you -
        do not invent GUIDs). `sort` is a field plus direction, e.g. "displayName asc".
        Returns compact rows plus has_next (and total_count when the server reports one);
        use device_get for a single full record.
        """
        query = DeviceQuery(
            duid_contains=duid_contains, template=template, entity=entity,
            status=DeviceStatus(status) if status else None,
            is_edge=is_edge, is_gateway=is_gateway, wireless=wireless,
            page=page, page_size=page_size, sort_by=sort,
        )
        result = await call_lib(device.query, query)
        return paged_result("devices", [device_compact(d) for d in result.items], result)

    @mcp.tool(annotations=_READ)
    async def device_get(duid: Optional[str] = None, guid: Optional[str] = None) -> dict:
        """Get one device's full record by DUID (preferred) or GUID.

        Returns {"found": false} if no such device exists.
        """
        if duid:
            dev = await call_lib(device.get_by_duid, duid)
        elif guid:
            dev = await call_lib(device.get_by_guid, guid)
        else:
            return {"error": "Provide either duid or guid."}
        if dev is None:
            return {"found": False}
        return full_record(dev)

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def device_create(
        template: str,
        duid: str,
        name: Optional[str] = None,
        entity: Optional[str] = None,
        certificate: Optional[str] = None,
    ) -> dict:
        """Register a new x509 device. DESTRUCTIVE: creates a real account resource.

        `template` is a template code or GUID; `entity` is an entity name or GUID
        (defaults to the account root). `name` is the display label and defaults to the
        DUID. If `certificate` (a PEM string) is omitted, a self-signed EC cert + private
        key are generated and BOTH are returned to you - present the private_key to the
        user once and tell them to store it securely.

        The response includes an `sdk_config` block (platform, env, cpid, duid) - the
        non-secret values the device's SDK config needs alongside the certificate.
        """

        def _sdk_config(duid: str) -> dict:
            return {
                "platform": config.pf,
                "env": config.env,
                "cpid": accesstoken.decode_access_token().user.cpId,
                "duid": duid,
            }

        if certificate:
            result = await call_lib(
                device.create, template, duid,
                device_certificate=certificate, name=name, entity_guid=entity,
            )
            return {
                "duid": result.uniqueId,
                "device_guid": result.newid,
                "entity_guid": result.entityGuid,
                "certificate_provided": True,
                "sdk_config": _sdk_config(result.uniqueId),
            }

        private_key, cert_pem = await call_lib(config.generate_ec_cert_and_pkey, duid)
        result = await call_lib(
            device.create, template, duid,
            device_certificate=cert_pem, name=name, entity_guid=entity,
        )
        return {
            "duid": result.uniqueId,
            "device_guid": result.newid,
            "entity_guid": result.entityGuid,
            "certificate": cert_pem,
            "private_key": private_key,
            "sdk_config": _sdk_config(result.uniqueId),
            "warning": "Store the private_key now (shown once), then delete this chat - the key persists in history.",
        }

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def device_delete(duid: str) -> dict:
        """Delete a device by DUID. DESTRUCTIVE and irreversible.

        Note: REST-created devices cannot be removed from the /IOTCONNECT UI, so this
        is the intended deletion path. Confirm with the user before calling.
        """
        await call_lib(device.delete_match_duid, duid)
        return {"deleted": True, "duid": duid}

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def device_set_active(duid: str, active: bool) -> dict:
        """Activate (active=true) or deactivate (active=false) a device by DUID."""
        await call_lib(device.set_active_match_duid, duid, active)
        return {"duid": duid, "active": active}

    @mcp.tool(annotations=_READ)
    async def generate_device_cert(duid: str) -> dict:
        """Generate a self-signed EC cert + private key for a DUID WITHOUT creating a device.

        Makes no account changes, but returns a private_key - present it to the user
        once and tell them to store it securely. Requires an active login (the cert's
        common name is derived from the account CPID).
        """
        private_key, cert_pem = await call_lib(config.generate_ec_cert_and_pkey, duid)
        return {
            "duid": duid,
            "certificate": cert_pem,
            "private_key": private_key,
            "warning": "Store the private_key now (shown once), then delete this chat - the key persists in history.",
        }
