import asyncio
from dataclasses import dataclass

import pytest
from ansible.module_utils import basic
from ansible_collections.applewhiteit.omada.plugins.modules import omada_network_info

from .utils import AnsibleExitJson, exit_json, set_module_args


@dataclass
class FakeNetwork:
    id: str
    name: str
    vlan_id: int | None = None
    purpose: int | None = None
    gateway_subnet: str | None = None


class FakeSiteClient:
    def __init__(self, networks):
        self.networks = networks

    async def get_networks(self):
        return self.networks


def _base_args(**extra):
    args = {
        "controller_url": "https://omada.example.com:8043",
        "username": "admin",
        "password": "secret",
        "site": "Default",
    }
    args.update(extra)
    return args


def _run(monkeypatch, site_client, args):
    monkeypatch.setattr(basic.AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(
        omada_network_info,
        "run_omada_task",
        lambda module, factory: asyncio.run(factory(site_client)),
    )
    set_module_args(args)
    with pytest.raises(AnsibleExitJson) as exc_info:
        omada_network_info.main()
    return exc_info.value.args[0]


def test_lists_networks(monkeypatch):
    site_client = FakeSiteClient(
        [
            FakeNetwork(id="net-lan-default", name="Default", vlan_id=None),
            FakeNetwork(
                id="net-surveillance", name="Surveillance", vlan_id=30, gateway_subnet="192.168.30.1/24",
            ),
        ]
    )
    result = _run(monkeypatch, site_client, _base_args())

    assert result["changed"] is False
    assert result["networks"] == [
        {
            "id": "net-lan-default",
            "name": "Default",
            "vlan_id": None,
            "purpose": None,
            "gateway_subnet": None,
        },
        {
            "id": "net-surveillance",
            "name": "Surveillance",
            "vlan_id": 30,
            "purpose": None,
            "gateway_subnet": "192.168.30.1/24",
        },
    ]
