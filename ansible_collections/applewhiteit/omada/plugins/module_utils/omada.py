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
    from tplink_omada_client.exceptions import OmadaClientException
    from tplink_omada_client.omadaclient import OmadaClient

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


def to_native_message(exc):
    """Best-effort plain-text message from an exception, for fail_json."""
    return str(exc) if str(exc) else exc.__class__.__name__
