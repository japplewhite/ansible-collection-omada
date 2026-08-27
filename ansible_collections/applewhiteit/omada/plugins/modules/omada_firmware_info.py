#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Jeff Applewhite <jeff.applewhite@gmail.com>
# MIT License (see LICENSE)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: omada_firmware_info
short_description: Report firmware version and available-upgrade status for Omada devices
version_added: "1.0.0"
description:
  - Retrieve current/latest firmware version and release notes for one device,
    or every device on the site.
  - Read-only; makes no changes. To trigger an upgrade, see the collection's
    device-upgrade tooling (not yet implemented - see the capability matrix).
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
    description: Report on only this device. Omit to report on every device on the site.
    type: str
    required: false
author:
  - Jeff Applewhite (@japplewhite)
requirements:
  - tplink-omada-client
"""

EXAMPLES = r"""
- name: Firmware status for one switch
  applewhiteit.omada.omada_firmware_info:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    mac: "AA-BB-CC-00-00-01"
  register: fw

- name: Firmware status for every device on the site
  applewhiteit.omada.omada_firmware_info:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
  register: fw_all

- name: Flag devices that need an upgrade
  debug:
    msg: "{{ item.mac }} can upgrade {{ item.current_version }} -> {{ item.latest_version }}"
  loop: "{{ fw_all.devices | selectattr('needs_upgrade') | list }}"
"""

RETURN = r"""
devices:
  description: Firmware status per device queried.
  returned: success
  type: list
  elements: dict
  contains:
    mac:
      description: Device MAC address.
      type: str
    current_version:
      description: Currently installed firmware version.
      type: str
    latest_version:
      description: Latest firmware version available from the controller, if any.
      type: str
    needs_upgrade:
      description: Whether C(latest_version) differs from C(current_version).
      type: bool
    release_notes:
      description: Release notes for the latest available firmware.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.applewhiteit.omada.plugins.module_utils.omada import (
    omada_argument_spec,
    run_omada_task,
)


def _serialize(mac, firmware):
    return {
        "mac": mac,
        "current_version": firmware.current_version,
        "latest_version": firmware.latest_version,
        "needs_upgrade": bool(firmware.latest_version)
        and firmware.latest_version != firmware.current_version,
        "release_notes": firmware.release_notes,
    }


def main():
    argument_spec = omada_argument_spec()
    argument_spec.update(mac=dict(type="str", required=False))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    async def _list_firmware(site_client):
        if module.params["mac"]:
            macs = [module.params["mac"]]
        else:
            devices = await site_client.get_devices()
            macs = [d.mac for d in devices]

        results = []
        for mac in macs:
            firmware = await site_client.get_firmware_details(mac)
            results.append(_serialize(mac, firmware))
        return results

    devices = run_omada_task(module, _list_firmware)
    module.exit_json(changed=False, devices=devices)


if __name__ == "__main__":
    main()
