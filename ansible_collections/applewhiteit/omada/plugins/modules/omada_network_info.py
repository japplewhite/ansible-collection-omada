#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Jeff Applewhite <jeff.applewhite@gmail.com>
# MIT License (see LICENSE)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: omada_network_info
short_description: List LAN networks (VLANs) defined on an Omada site
version_added: "1.0.0"
description:
  - Retrieve the LAN networks/VLANs configured on a site, for use with
    O(native_network_id) in M(applewhiteit.omada.omada_switch_port).
  - Read-only; makes no changes.
  - >-
    B(This module depends on unreleased upstream code.) It requires our
    private fork's C(feature/vlan-network-support) branch, not any released
    version of tplink-omada-client. The C(get_networks) endpoint this module
    calls has not been confirmed against a live controller as of when this
    module was written - check the collection's README/capability matrix
    for current status before trusting results.
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
author:
  - Jeff Applewhite (@japplewhite)
requirements:
  - tplink-omada-client (private fork, feature/vlan-network-support branch)
"""

EXAMPLES = r"""
- name: List networks/VLANs on the site
  applewhiteit.omada.omada_network_info:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
  register: net_result

- name: Look up the surveillance VLAN's network ID by name
  set_fact:
    surveillance_network_id: >-
      {{ (net_result.networks | selectattr('name', 'equalto', 'Surveillance') | first).id }}
"""

RETURN = r"""
networks:
  description: List of networks/VLANs defined on the site.
  returned: success
  type: list
  elements: dict
  contains:
    id:
      description: Network ID (use this as native_network_id elsewhere).
      type: str
    name:
      description: Network name.
      type: str
    vlan_id:
      description: 802.1Q VLAN ID, if tagged.
      type: int
    purpose:
      description: Raw controller purpose/type code - not yet mapped to a friendly name.
      type: int
    gateway_subnet:
      description: Gateway IP / subnet for the network, if present.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.applewhiteit.omada.plugins.module_utils.omada import (
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
    }


def main():
    module = AnsibleModule(argument_spec=omada_argument_spec(), supports_check_mode=True)

    async def _list_networks(site_client):
        networks = await site_client.get_networks()
        return [_serialize(n) for n in networks]

    networks = run_omada_task(module, _list_networks)
    module.exit_json(changed=False, networks=networks)


if __name__ == "__main__":
    main()
