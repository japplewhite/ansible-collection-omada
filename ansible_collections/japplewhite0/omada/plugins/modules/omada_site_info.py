#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Jeff Applewhite <jeff.applewhite@gmail.com>
# MIT License (see LICENSE)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: omada_site_info
short_description: List sites visible to an Omada controller account
version_added: "1.0.0"
description:
  - Retrieve the list of sites that the given Omada controller credentials can see.
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
    description:
      - Site name used to establish the API session context.
      - This module lists every site the credentials can see, not just this one;
        it is required for consistency with the rest of the collection and because
        the underlying client library needs a valid site to complete login.
    type: str
    required: true
  validate_certs:
    description: Whether to validate the controller's TLS certificate.
    type: bool
    default: true
author:
  - Jeff Applewhite (@japplewhite)
requirements:
  - tplink-omada-client
"""

EXAMPLES = r"""
- name: List all sites visible to this account
  japplewhite0.omada.omada_site_info:
    controller_url: "https://omada.example.com:8043"
    username: "{{ omada_username }}"
    password: "{{ omada_password }}"
    site: "Default"
  register: site_result

- name: Show site names
  debug:
    msg: "{{ site_result.sites | map(attribute='name') | list }}"
"""

RETURN = r"""
sites:
  description: List of sites visible to the account.
  returned: success
  type: list
  elements: dict
  contains:
    name:
      description: Site display name.
      type: str
      returned: always
    id:
      description: Internal site ID.
      type: str
      returned: always
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.japplewhite0.omada.plugins.module_utils.omada import (
    omada_argument_spec,
    run_omada_client_task,
)


def main():
    module = AnsibleModule(
        argument_spec=omada_argument_spec(),
        supports_check_mode=True,
    )

    async def _list_sites(client):
        sites = await client.get_sites()
        return [{"name": site.name, "id": site.id} for site in sites]

    sites = run_omada_client_task(module, _list_sites)
    module.exit_json(changed=False, sites=sites)


if __name__ == "__main__":
    main()
