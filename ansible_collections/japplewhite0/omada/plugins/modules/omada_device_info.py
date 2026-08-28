#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Jeff Applewhite <jeff.applewhite@gmail.com>
# MIT License (see LICENSE)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: omada_device_info
short_description: List or describe devices (gateway, switches, access points) on an Omada site
version_added: "1.0.0"
description:
  - Retrieve devices adopted on an Omada site, optionally filtered by MAC address or device type.
  - Read-only; makes no changes.
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
    description: Omada site name to query.
    type: str
    required: true
  validate_certs:
    description: Whether to validate the controller's TLS certificate.
    type: bool
    default: true
  mac:
    description: Return only the device with this MAC address.
    type: str
    required: false
  device_type:
    description: Return only devices of this type.
    type: str
    required: false
    choices: [ap, gateway, switch]
author:
  - Jeff Applewhite (@japplewhite)
requirements:
  - tplink-omada-client
"""

EXAMPLES = r"""
- name: List all devices on the site
  japplewhite0.omada.omada_device_info:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
  register: device_result

- name: List only switches
  japplewhite0.omada.omada_device_info:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    device_type: switch
  register: switches

- name: Look up one device by MAC
  japplewhite0.omada.omada_device_info:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    mac: "AA-BB-CC-DD-EE-FF"
  register: one_device
"""

RETURN = r"""
devices:
  description: List of matching devices.
  returned: success
  type: list
  elements: dict
  contains:
    mac:
      description: Device MAC address.
      type: str
    name:
      description: Device name.
      type: str
    type:
      description: Device type (C(ap), C(gateway), or C(switch)).
      type: str
    model:
      description: Device model, e.g. C(SG3452XP).
      type: str
    model_display_name:
      description: Human-friendly model description.
      type: str
    status:
      description: Raw device status code.
      type: int
    status_category:
      description: High-level device status category.
      type: str
    ip_address:
      description: Device IP address.
      type: str
    firmware_version:
      description: Currently installed firmware version.
      type: str
    need_upgrade:
      description: Whether a firmware upgrade is available.
      type: bool
    uptime:
      description: Device uptime as a display string.
      type: str
    cpu_usage:
      description: Current CPU usage.
      type: float
    mem_usage:
      description: Current memory usage.
      type: float
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.japplewhite0.omada.plugins.module_utils.omada import (
    enum_display,
    omada_argument_spec,
    run_omada_task,
)


def _serialize_device(device):
    return {
        "mac": device.mac,
        "name": device.name,
        "type": device.type,
        "model": device.model,
        "model_display_name": device.model_display_name,
        "status": int(device.status) if device.status is not None else None,
        "status_category": enum_display(device.status_category),
        "ip_address": device.ip_address,
        "firmware_version": device.firmware_version,
        "need_upgrade": device.need_upgrade,
        "uptime": device.display_uptime,
        "cpu_usage": device.cpu_usage,
        "mem_usage": device.mem_usage,
    }


def main():
    argument_spec = omada_argument_spec()
    argument_spec.update(
        mac=dict(type="str", required=False),
        device_type=dict(type="str", required=False, choices=["ap", "gateway", "switch"]),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    async def _list_devices(site_client):
        if module.params["mac"]:
            device = await site_client.get_device(module.params["mac"])
            devices = [device]
        else:
            devices = await site_client.get_devices()

        if module.params["device_type"]:
            devices = [d for d in devices if d.type == module.params["device_type"]]

        return [_serialize_device(d) for d in devices]

    devices = run_omada_task(module, _list_devices)
    module.exit_json(changed=False, devices=devices)


if __name__ == "__main__":
    main()
