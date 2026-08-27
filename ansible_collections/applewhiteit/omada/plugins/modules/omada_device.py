#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Jeff Applewhite <jeff.applewhite@gmail.com>
# MIT License (see LICENSE)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: omada_device
short_description: Manage device-level settings on an Omada switch, access point, or gateway
version_added: "1.0.0"
description:
  - Currently manages the onboard LED setting for a device. Idempotent.
  - >-
    Device-level renaming and per-device reboot/adopt/forget actions are not
    exposed by the upstream tplink-omada-client library today (see this
    project's capability matrix); this module only covers what's actually
    supported. Renaming a *client* (not a device) is supported and belongs to
    a future client-management module instead.
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
    description: MAC address of the device.
    type: str
    required: true
  led:
    description: Onboard LED setting for the device.
    type: str
    choices: [on, off, site_settings]
    required: false
author:
  - Jeff Applewhite (@japplewhite)
requirements:
  - tplink-omada-client
"""

EXAMPLES = r"""
- name: Turn off a switch's status LED
  applewhiteit.omada.omada_device:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    mac: "AA-BB-CC-00-00-01"
    led: "off"

- name: Follow the site-wide LED setting
  applewhiteit.omada.omada_device:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    mac: "AA-BB-CC-00-00-01"
    led: "site_settings"
"""

RETURN = r"""
before:
  description: Device state before the change.
  returned: success
  type: dict
  contains:
    mac:
      type: str
    type:
      description: Device type (C(ap), C(gateway), or C(switch)).
      type: str
    led:
      type: str
after:
  description: Device state after the change (same as C(before) when nothing changed, or in check mode).
  returned: success
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.applewhiteit.omada.plugins.module_utils.omada import (
    LED_SETTING_CHOICES,
    enum_display,
    omada_argument_spec,
    run_omada_task,
)

DETAIL_GETTERS = {
    "switch": "get_switch",
    "ap": "get_access_point",
    "gateway": "get_gateway",
}


async def _get_detailed_device(site_client, mac):
    device = await site_client.get_device(mac)
    getter_name = DETAIL_GETTERS.get(device.type)
    if getter_name is None:
        return None, device.type
    getter = getattr(site_client, getter_name)
    return await getter(mac), device.type


def _serialize(mac, device_type, detailed):
    return {
        "mac": mac,
        "type": device_type,
        "led": enum_display(detailed.led_setting) if detailed is not None else None,
    }


def main():
    argument_spec = omada_argument_spec()
    argument_spec.update(
        mac=dict(type="str", required=True),
        led=dict(type="str", required=False, choices=list(LED_SETTING_CHOICES)),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    async def _apply(site_client):
        mac = module.params["mac"]
        detailed, device_type = await _get_detailed_device(site_client, mac)

        if detailed is None:
            module.fail_json(
                msg="Device %s has an unrecognized type %r; this module supports "
                "switch, ap, and gateway devices only." % (mac, device_type)
            )

        before = _serialize(mac, device_type, detailed)

        desired_led = module.params["led"]
        led_changed = desired_led is not None and LED_SETTING_CHOICES[desired_led] != detailed.led_setting

        if not led_changed or module.check_mode:
            return {"changed": led_changed, "before": before, "after": before}

        await site_client.set_led_setting(mac, LED_SETTING_CHOICES[desired_led])
        after = dict(before)
        after["led"] = desired_led
        return {"changed": True, "before": before, "after": after}

    result = run_omada_task(module, _apply)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
