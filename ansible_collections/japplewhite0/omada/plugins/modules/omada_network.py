#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Jeff Applewhite <jeff.applewhite@gmail.com>
# MIT License (see LICENSE)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: omada_network
short_description: Create a LAN network (VLAN) on an Omada site
version_added: "1.0.0"
description:
  - Create a LAN network/VLAN on a site.
  - Idempotent by O(name) only - if a network with that name already
    exists, this module reports no change and returns it as-is. It does
    B(not) compare or reconcile any other field (VLAN ID, subnet, DHCP
    settings, labels) against an existing network of the same name,
    because the underlying C(tplink-omada-client) library has no update
    operation for networks yet. Renaming or reconfiguring an existing
    network must still be done by hand in the controller UI.
  - There is likewise no delete operation - this module can only create.
  - >-
    B(This module depends on unreleased upstream code.) It requires our
    private fork's C(feature/vlan-network-support) branch, not any released
    version of tplink-omada-client. Verified 2026-08-28 against a live
    controller (firmware 6.2.14.12), including O(tag_ids).
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
  name:
    description: Name for the new network. Used to detect whether it already exists.
    type: str
    required: true
  vlan_id:
    description: 802.1Q VLAN ID for the network.
    type: int
    required: true
  gateway_subnet:
    description: Gateway IP and subnet for the network, e.g. C(192.168.20.1/24).
    type: str
    required: true
  dhcp_enabled:
    description: Whether to run a DHCP server on this network.
    type: bool
    default: true
  dhcp_start:
    description: Start of the DHCP range. Required when O(dhcp_enabled=true).
    type: str
    required: false
  dhcp_end:
    description: End of the DHCP range. Required when O(dhcp_enabled=true).
    type: str
    required: false
  tag_ids:
    description:
      - IDs of port labels ("tags") to associate with the network. No
        Ansible module currently creates or lists these IDs; look them up
        with the underlying C(tplink-omada-client) library's
        C(get_port_labels())/C(create_port_label()) until one exists.
      - Unconfirmed whether this has any visible effect, since the
        underlying request always sends an empty device list separately
        from the label - see the C(tag_ids) note in C(create_network())'s
        docstring in the fork.
    type: list
    elements: str
    required: false
author:
  - Jeff Applewhite (@japplewhite)
requirements:
  - tplink-omada-client (private fork, feature/vlan-network-support branch)
"""

EXAMPLES = r"""
- name: Create the Business LAN VLAN
  japplewhite0.omada.omada_network:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    name: "Business LAN"
    vlan_id: 20
    gateway_subnet: "192.168.20.1/24"
    dhcp_start: "192.168.20.100"
    dhcp_end: "192.168.20.199"

- name: Create a network with a port label attached
  japplewhite0.omada.omada_network:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    name: "Business LAN"
    vlan_id: 20
    gateway_subnet: "192.168.20.1/24"
    dhcp_start: "192.168.20.100"
    dhcp_end: "192.168.20.199"
    tag_ids:
      - "{{ foo_label_id }}"

- name: Create a network with DHCP disabled (check mode - no changes made)
  japplewhite0.omada.omada_network:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
    name: "Point to Point"
    vlan_id: 50
    gateway_subnet: "10.50.0.1/30"
    dhcp_enabled: false
  check_mode: true
"""

RETURN = r"""
network:
  description: The network after this module ran (existing or newly created).
  returned: success
  type: dict
  contains:
    id:
      description: Network ID.
      type: str
    name:
      description: Network name.
      type: str
    vlan_id:
      description: 802.1Q VLAN ID.
      type: int
    purpose:
      description: Network purpose, e.g. C(interface) for a standard LAN network.
      type: str
    gateway_subnet:
      description: Gateway IP / subnet for the network.
      type: str
    dhcp_enabled:
      description: Whether this network's own DHCP server is enabled.
      type: bool
    is_primary:
      description: Whether this is the site's primary/default network.
      type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.japplewhite0.omada.plugins.module_utils.omada import (
    omada_argument_spec,
    run_omada_task,
)


def _serialize(network):
    return {
        "id": network.id,
        "name": network.name,
        "vlan_id": network.vlan_id,
        "purpose": network.purpose,
        "gateway_subnet": network.gateway_subnet,
        "dhcp_enabled": network.dhcp_enabled,
        "is_primary": network.is_primary,
    }


def main():
    argument_spec = omada_argument_spec()
    argument_spec.update(
        name=dict(type="str", required=True),
        vlan_id=dict(type="int", required=True),
        gateway_subnet=dict(type="str", required=True),
        dhcp_enabled=dict(type="bool", default=True),
        dhcp_start=dict(type="str", required=False),
        dhcp_end=dict(type="str", required=False),
        tag_ids=dict(type="list", elements="str", required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("dhcp_enabled", True, ("dhcp_start", "dhcp_end"), False),
        ],
    )

    async def _apply(site_client):
        name = module.params["name"]
        existing = next((n for n in await site_client.get_networks() if n.name == name), None)

        if existing is not None:
            return {"changed": False, "network": _serialize(existing)}

        if module.check_mode:
            return {"changed": True, "network": None}

        created = await site_client.create_network(
            name=name,
            vlan_id=module.params["vlan_id"],
            gateway_subnet=module.params["gateway_subnet"],
            dhcp_enabled=module.params["dhcp_enabled"],
            dhcp_start=module.params["dhcp_start"],
            dhcp_end=module.params["dhcp_end"],
            tag_ids=module.params["tag_ids"],
        )
        return {"changed": True, "network": _serialize(created)}

    result = run_omada_task(module, _apply)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
