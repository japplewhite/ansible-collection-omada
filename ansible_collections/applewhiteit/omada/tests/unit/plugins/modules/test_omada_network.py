import asyncio
from dataclasses import dataclass

import pytest
from ansible.module_utils import basic
from ansible_collections.applewhiteit.omada.plugins.modules import omada_network

from .utils import AnsibleExitJson, AnsibleFailJson, exit_json, fail_json, set_module_args


@dataclass
class FakeNetwork:
    id: str
    name: str
    vlan_id: int | None = None
    purpose: str | None = None
    gateway_subnet: str | None = None
    dhcp_enabled: bool | None = None
    is_primary: bool | None = None


class FakeSiteClient:
    def __init__(self, networks):
        self.networks = list(networks)
        self.create_calls = []

    async def get_networks(self):
        return self.networks

    async def create_network(self, **kwargs):
        self.create_calls.append(kwargs)
        created = FakeNetwork(
            id="net-new",
            name=kwargs["name"],
            vlan_id=kwargs["vlan_id"],
            purpose="interface",
            gateway_subnet=kwargs["gateway_subnet"],
            dhcp_enabled=kwargs["dhcp_enabled"],
            is_primary=False,
        )
        self.networks.append(created)
        return created


def _base_args(**extra):
    args = {
        "controller_url": "https://omada.example.com:8043",
        "username": "admin",
        "password": "secret",
        "site": "Default",
        "name": "Business LAN",
        "vlan_id": 20,
        "gateway_subnet": "192.168.20.1/24",
        "dhcp_start": "192.168.20.100",
        "dhcp_end": "192.168.20.199",
    }
    args.update(extra)
    return args


def _run(monkeypatch, site_client, args):
    monkeypatch.setattr(basic.AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(
        omada_network,
        "run_omada_task",
        lambda module, factory: asyncio.run(factory(site_client)),
    )
    set_module_args(args)
    with pytest.raises(AnsibleExitJson) as exc_info:
        omada_network.main()
    return exc_info.value.args[0]


def test_existing_network_is_not_changed(monkeypatch):
    site_client = FakeSiteClient(
        [FakeNetwork(id="net-existing", name="Business LAN", vlan_id=20, is_primary=False)]
    )
    result = _run(monkeypatch, site_client, _base_args())

    assert result["changed"] is False
    assert site_client.create_calls == []
    assert result["network"]["id"] == "net-existing"


def test_missing_network_is_created(monkeypatch):
    site_client = FakeSiteClient(
        [FakeNetwork(id="net-lan-default", name="Default", vlan_id=1, is_primary=True)]
    )
    result = _run(monkeypatch, site_client, _base_args())

    assert result["changed"] is True
    assert len(site_client.create_calls) == 1
    call = site_client.create_calls[0]
    assert call["name"] == "Business LAN"
    assert call["vlan_id"] == 20
    assert call["gateway_subnet"] == "192.168.20.1/24"
    assert call["dhcp_start"] == "192.168.20.100"
    assert call["dhcp_end"] == "192.168.20.199"
    assert call["tag_ids"] is None
    assert result["network"]["id"] == "net-new"
    assert result["network"]["name"] == "Business LAN"


def test_tag_ids_passed_through_to_create(monkeypatch):
    site_client = FakeSiteClient([])
    result = _run(monkeypatch, site_client, _base_args(tag_ids=["tag-foo"]))

    assert result["changed"] is True
    assert site_client.create_calls[0]["tag_ids"] == ["tag-foo"]


def test_check_mode_reports_change_without_creating(monkeypatch):
    site_client = FakeSiteClient([])
    args = _base_args()
    args["_ansible_check_mode"] = True

    result = _run(monkeypatch, site_client, args)

    assert result["changed"] is True
    assert site_client.create_calls == []
    assert result["network"] is None


def test_dhcp_enabled_requires_start_and_end(monkeypatch):
    site_client = FakeSiteClient([])
    args = _base_args()
    del args["dhcp_start"]
    del args["dhcp_end"]

    monkeypatch.setattr(basic.AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(basic.AnsibleModule, "fail_json", fail_json)
    monkeypatch.setattr(
        omada_network,
        "run_omada_task",
        lambda module, factory: asyncio.run(factory(site_client)),
    )
    set_module_args(args)

    with pytest.raises(AnsibleFailJson):
        omada_network.main()


def test_dhcp_disabled_does_not_require_start_and_end(monkeypatch):
    site_client = FakeSiteClient([])
    args = _base_args(dhcp_enabled=False)
    del args["dhcp_start"]
    del args["dhcp_end"]

    result = _run(monkeypatch, site_client, args)

    assert result["changed"] is True
    assert site_client.create_calls[0]["dhcp_enabled"] is False
    assert site_client.create_calls[0]["dhcp_start"] is None
    assert site_client.create_calls[0]["dhcp_end"] is None
