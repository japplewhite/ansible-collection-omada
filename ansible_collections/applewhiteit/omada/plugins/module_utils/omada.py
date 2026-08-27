# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Jeff Applewhite <jeff.applewhite@gmail.com>
# MIT License (see LICENSE)
"""Shared connection helpers for Omada modules.

Modules should reach the upstream ``tplink_omada_client`` library only
through this module, not import it directly. That keeps one seam here if a
future transport (e.g. TP-Link's official OpenAPI) needs to be swapped in
without changing every module's argument spec or call sites.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import asyncio
import traceback

from ansible.module_utils.basic import env_fallback

OMADA_CLIENT_IMPORT_ERROR = None
try:
    from tplink_omada_client.definitions import Eth802Dot1X, LedSetting, LinkDuplex, LinkSpeed, PoEMode
    from tplink_omada_client.exceptions import OmadaClientException
    from tplink_omada_client.omadaclient import OmadaClient
    from tplink_omada_client.omadasiteclient import (
        AccessPointPortSettings,
        GatewayPortSettings,
        SwitchPortOverrides,
    )

    HAS_OMADA_CLIENT = True
except ImportError:
    HAS_OMADA_CLIENT = False
    OMADA_CLIENT_IMPORT_ERROR = traceback.format_exc()


def omada_argument_spec():
    """Connection arguments shared by every module in this collection."""
    return dict(
        controller_url=dict(
            type="str",
            required=True,
            fallback=(env_fallback, ["OMADA_CONTROLLER_URL"]),
        ),
        username=dict(
            type="str",
            required=True,
            fallback=(env_fallback, ["OMADA_USERNAME"]),
        ),
        password=dict(
            type="str",
            required=True,
            no_log=True,
            fallback=(env_fallback, ["OMADA_PASSWORD"]),
        ),
        site=dict(
            type="str",
            required=True,
            fallback=(env_fallback, ["OMADA_SITE"]),
        ),
        validate_certs=dict(
            type="bool",
            default=True,
            fallback=(env_fallback, ["OMADA_VALIDATE_CERTS"]),
        ),
    )


def check_omada_client_dependency(module):
    """Fail cleanly if tplink-omada-client isn't installed."""
    if not HAS_OMADA_CLIENT:
        module.fail_json(
            msg="The tplink-omada-client Python library is required for this module. "
            "Install it with: pip install tplink-omada-client",
            exception=OMADA_CLIENT_IMPORT_ERROR,
        )


def _run_with_client(module, coro_factory):
    """Open a connection, run ``coro_factory(client)``, and handle errors uniformly."""
    check_omada_client_dependency(module)

    params = module.params

    async def _run():
        async with OmadaClient(
            params["controller_url"],
            params["username"],
            params["password"],
            verify_ssl=params["validate_certs"],
        ) as client:
            return await coro_factory(client)

    try:
        return asyncio.run(_run())
    except OmadaClientException as exc:
        module.fail_json(msg="Omada API error: %s" % to_native_message(exc))
    except Exception as exc:  # noqa: BLE001 - surfaced to the playbook, not swallowed
        module.fail_json(
            msg="Unexpected error talking to the Omada controller: %s" % to_native_message(exc),
            exception=traceback.format_exc(),
        )


def run_omada_client_task(module, coro_factory):
    """Run an async task against the top-level controller client (not site-scoped).

    Use this for operations that aren't tied to a single site, such as
    listing the sites a credential can see. ``coro_factory`` is called as
    ``coro_factory(client)``.
    """
    return _run_with_client(module, coro_factory)


def run_omada_task(module, coro_factory):
    """Run an async task against the configured site and return its result.

    ``coro_factory`` is called as ``coro_factory(site_client)`` and must
    return an awaitable. Connection setup/teardown and Omada-specific
    exceptions are handled here so individual modules only implement the
    actual site_client calls they need.
    """

    async def _with_site_client(client):
        site_client = await client.get_site_client(module.params["site"])
        return await coro_factory(site_client)

    return _run_with_client(module, _with_site_client)


def enum_display(value):
    """Render an IntEnum from tplink_omada_client as a lowercase string for module output."""
    if value is None:
        return None
    name = getattr(value, "name", None)
    return name.lower() if name else value


if HAS_OMADA_CLIENT:
    DOT1X_MODE_CHOICES = {
        "force_unauthorized": Eth802Dot1X.FORCE_UNAUTHORIZED,
        "force_authorized": Eth802Dot1X.FORCE_AUTHORIZED,
        "auto": Eth802Dot1X.AUTO,
    }
    DUPLEX_CHOICES = {
        "auto": LinkDuplex.AUTO,
        "half": LinkDuplex.HALF,
        "full": LinkDuplex.FULL,
    }
    LINK_SPEED_CHOICES = {
        "auto": LinkSpeed.SPEED_AUTO,
        "10mbps": LinkSpeed.SPEED_10_MBPS,
        "100mbps": LinkSpeed.SPEED_100_MBPS,
        "1gbps": LinkSpeed.SPEED_1_GBPS,
        "2.5gbps": LinkSpeed.SPEED_2_5_GBPS,
        "10gbps": LinkSpeed.SPEED_10_GBPS,
    }
    LED_SETTING_CHOICES = {
        "off": LedSetting.OFF,
        "on": LedSetting.ON,
        "site_settings": LedSetting.SITE_SETTINGS,
    }
else:
    # Argument specs still need the choice lists at import time even when the
    # optional dependency is missing (e.g. during `ansible-doc` collection
    # scanning) - check_omada_client_dependency() fails the module before any
    # of these values would actually be used against a real enum.
    DOT1X_MODE_CHOICES = {"force_unauthorized": None, "force_authorized": None, "auto": None}
    DUPLEX_CHOICES = {"auto": None, "half": None, "full": None}
    LINK_SPEED_CHOICES = {
        "auto": None,
        "10mbps": None,
        "100mbps": None,
        "1gbps": None,
        "2.5gbps": None,
        "10gbps": None,
    }
    LED_SETTING_CHOICES = {"off": None, "on": None, "site_settings": None}


def to_native_message(exc):
    """Best-effort plain-text message from an exception, for fail_json."""
    return str(exc) if str(exc) else exc.__class__.__name__
