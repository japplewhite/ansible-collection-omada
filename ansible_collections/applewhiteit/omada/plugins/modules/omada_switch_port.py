#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Jeff Applewhite <jeff.applewhite@gmail.com>
# MIT License (see LICENSE)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: omada_switch_port
short_description: Configure an individual switch port on an Omada switch
version_added: "1.0.0"
description:
  - Configure name, port profile, and per-port overrides (PoE, duplex, link speed,
    802.1x, LLDP-MED, loopback detection, spanning tree, port isolation) on a
    single switch port.
  - Idempotent - only options you set are compared and changed; unset options
    are left exactly as they currently are.
  - >-
    The underlying API replaces the entire override object on write, so this
    module always reads the port's current overrides first and merges your
    requested changes on top before writing, rather than clobbering unrelated
    override settings.
options:
  controller_url:
    description: Base URL of the Omada controller, e.g. C(https://omada.example.com:8043).
    type: str
    required: true
  username:
    description: Omada controller username.
    type: str
    required: true
  password:
    description: Omada controller password.
    type: str
    required: true
  site:
    description: Omada site name to operate on.
    type: str
    required: true
  validate_certs:
    description: Whether to validate the controller's TLS certificate.
    type: bool
    default: true
  mac:
    description: MAC address of the switch.
    type: str
    required: true
  port:
    description: Port number on the switch.
    type: int
    required: true
  name:
    description: Description/name for the port.
    type: str
    required: false
  profile_id:
    description: ID of an existing port profile to apply to this port.
    type: str
    required: false
  enable_poe:
    description: Enable or disable PoE output on this port.
    type: bool
    required: false
  dot1x_mode:
    description: 802.1x authentication mode for this port.
    type: str
    choices: [force_unauthorized, force_authorized, auto]
    required: false
  duplex:
    description: Duplex mode for this port.
    type: str
    choices: [auto, half, full]
    required: false
  link_speed:
    description: Forced link speed for this port.
    type: str
    choices: [auto, 10mbps, 100mbps, 1gbps, 2.5gbps, 10gbps]
    required: false
  lldp_med_enable:
    description: Enable LLDP-MED on this port.
    type: bool
    required: false
  loopback_detect:
    description: Enable loopback detection on this port.
    type: bool
    required: false
  spanning_tree_enable:
    description: Enable spanning tree protection on this port.
    type: bool
    required: false
  port_isolation:
    description: Enable port isolation on this port. Isolates the port from other ports on the switch.
    type: bool
    required: false
author:
  - Jeff Applewhite (@japplewhite)
requirements:
  - tplink-omada-client
"""

EXAMPLES = r"""
- name: Rename a port and enable PoE, leaving everything else untouched
  applewhiteit.omada.omada_switch_port:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    mac: "AA-BB-CC-00-00-01"
    port: 1
    name: "Camera 1 - front porch"
    enable_poe: true

- name: Apply a port profile
  applewhiteit.omada.omada_switch_port:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    mac: "AA-BB-CC-00-00-01"
    port: 12
    profile_id: "{{ ap_profile_id }}"

- name: Isolate an unused port (check mode - no changes made)
  applewhiteit.omada.omada_switch_port:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    mac: "AA-BB-CC-00-00-01"
    port: 20
    port_isolation: true
  check_mode: true
"""

RETURN = r"""
before:
  description: Port state before the change.
  returned: success
  type: dict
after:
  description: Port state after the change (same as C(before) when nothing changed, or in check mode).
  returned: success
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.applewhiteit.omada.plugins.module_utils.omada import (
    DOT1X_MODE_CHOICES,
    DUPLEX_CHOICES,
    LINK_SPEED_CHOICES,
    PoEMode,
    SwitchPortOverrides,
    enum_display,
    omada_argument_spec,
    run_omada_task,
)

OVERRIDE_PARAM_NAMES = (
    "enable_poe",
    "dot1x_mode",
    "duplex",
    "link_speed",
    "lldp_med_enable",
    "loopback_detect",
    "spanning_tree_enable",
    "port_isolation",
)


def _serialize(port_details):
    return {
        "port": port_details.port,
        "name": port_details.name,
        "profile_id": port_details.profile_id,
        "profile_name": port_details.profile_name,
        "has_profile_override": port_details.has_profile_override,
        "is_disabled": port_details.is_disabled,
        "poe_mode": enum_display(port_details.poe_mode),
        "duplex": enum_display(port_details.duplex),
        "link_speed": enum_display(port_details.link_speed),
        "dot1x_mode": enum_display(port_details.eth_802_1x_control),
        "lldp_med_enable": port_details.lldp_med_enabled,
        "loopback_detect": port_details.loopback_detect_enabled,
        "spanning_tree_enable": port_details.spanning_tree_enabled,
        "port_isolation": port_details.port_isolation_enabled,
    }


def _desired_override_value(param_name, raw_value):
    if param_name == "enable_poe":
        return raw_value  # stays a plain bool, compared against poe_mode separately
    if param_name == "dot1x_mode":
        return DOT1X_MODE_CHOICES[raw_value]
    if param_name == "duplex":
        return DUPLEX_CHOICES[raw_value]
    if param_name == "link_speed":
        return LINK_SPEED_CHOICES[raw_value]
    return raw_value  # remaining override fields are plain bools, no enum mapping needed


def _current_value_for_comparison(param_name, current):
    if param_name == "enable_poe":
        return current.poe_mode == PoEMode.ENABLED
    if param_name == "dot1x_mode":
        return current.eth_802_1x_control
    if param_name == "duplex":
        return current.duplex
    if param_name == "link_speed":
        return current.link_speed
    if param_name == "lldp_med_enable":
        return current.lldp_med_enabled
    if param_name == "loopback_detect":
        return current.loopback_detect_enabled
    if param_name == "spanning_tree_enable":
        return current.spanning_tree_enabled
    if param_name == "port_isolation":
        return current.port_isolation_enabled
    raise AssertionError(param_name)  # pragma: no cover - exhaustive above


def main():
    argument_spec = omada_argument_spec()
    argument_spec.update(
        mac=dict(type="str", required=True),
        port=dict(type="int", required=True),
        name=dict(type="str", required=False),
        profile_id=dict(type="str", required=False),
        enable_poe=dict(type="bool", required=False),
        dot1x_mode=dict(type="str", required=False, choices=list(DOT1X_MODE_CHOICES)),
        duplex=dict(type="str", required=False, choices=list(DUPLEX_CHOICES)),
        link_speed=dict(type="str", required=False, choices=list(LINK_SPEED_CHOICES)),
        lldp_med_enable=dict(type="bool", required=False),
        loopback_detect=dict(type="bool", required=False),
        spanning_tree_enable=dict(type="bool", required=False),
        port_isolation=dict(type="bool", required=False),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    async def _apply(site_client):
        mac = module.params["mac"]
        port = module.params["port"]
        current = await site_client.get_switch_port(mac, port)
        before = _serialize(current)

        new_name = module.params["name"]
        name_changed = new_name is not None and new_name != current.name

        new_profile_id = module.params["profile_id"]
        profile_changed = new_profile_id is not None and new_profile_id != current.profile_id

        override_changes = {}
        for param_name in OVERRIDE_PARAM_NAMES:
            raw_value = module.params[param_name]
            if raw_value is None:
                continue
            desired = _desired_override_value(param_name, raw_value)
            if _current_value_for_comparison(param_name, current) != desired:
                override_changes[param_name] = desired

        changed = name_changed or profile_changed or bool(override_changes)

        if not changed or module.check_mode:
            return {"changed": changed, "before": before, "after": before}

        overrides = None
        if override_changes:
            base = await site_client.get_switch_port_overrides(mac, port)
            overrides = SwitchPortOverrides(
                enable_poe=override_changes.get("enable_poe", base.enable_poe),
                dot1x_mode=override_changes.get("dot1x_mode", base.dot1x_mode),
                duplex=override_changes.get("duplex", base.duplex),
                link_speed=override_changes.get("link_speed", base.link_speed),
                lldp_med_enable=override_changes.get("lldp_med_enable", base.lldp_med_enable),
                loopback_detect=override_changes.get("loopback_detect", base.loopback_detect),
                spanning_tree_enable=override_changes.get(
                    "spanning_tree_enable", base.spanning_tree_enable
                ),
                port_isolation=override_changes.get("port_isolation", base.port_isolation),
            )

        updated = await site_client.update_switch_port(
            mac,
            port,
            new_name=new_name if name_changed else None,
            profile_id=new_profile_id if profile_changed else None,
            overrides=overrides,
        )
        return {"changed": True, "before": before, "after": _serialize(updated)}

    result = run_omada_task(module, _apply)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
