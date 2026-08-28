import asyncio
from dataclasses import dataclass, field, replace

import pytest
from ansible.module_utils import basic
from ansible_collections.applewhiteit.omada.plugins.modules import omada_switch_port
from tplink_omada_client.definitions import Eth802Dot1X, LinkDuplex, LinkSpeed, PoEMode

from .utils import AnsibleExitJson, exit_json, set_module_args


@dataclass
class FakePortDetails:
    port: int
    name: str
    profile_id: str = "profile-default"
    profile_name: str = "All"
    has_profile_override: bool = False
    native_network_id: str = "net-lan-default"
    poe_mode: PoEMode = PoEMode.DISABLED
    duplex: LinkDuplex = LinkDuplex.AUTO
    link_speed: LinkSpeed = LinkSpeed.SPEED_AUTO
    eth_802_1x_control: Eth802Dot1X = Eth802Dot1X.FORCE_AUTHORIZED
    lldp_med_enabled: bool = True
    loopback_detect_enabled: bool = True
    spanning_tree_enabled: bool = False
    port_isolation_enabled: bool = False
    tag_ids: list = field(default_factory=list)


class FakeSiteClient:
    def __init__(self, current):
        self.current = current
        self.update_calls = []

    async def get_switch_port(self, mac, port):
        return self.current

    async def update_switch_port(self, mac, port, settings):
        self.update_calls.append({"mac": mac, "port": port, "settings": settings})
        after = replace(self.current)
        if settings.name is not None:
            after.name = settings.name
        if settings.profile_id is not None:
            after.profile_id = settings.profile_id
        if settings.native_network_id is not None:
            after.native_network_id = settings.native_network_id
        if settings.duplex is not None:
            after.duplex = settings.duplex
        if settings.link_speed is not None:
            after.link_speed = settings.link_speed
        if settings.tag_ids is not None:
            after.tag_ids = settings.tag_ids
        overrides = settings.profile_overrides
        if settings.profile_override_enabled and overrides is not None:
            if overrides.enable_poe is not None:
                after.poe_mode = PoEMode.ENABLED if overrides.enable_poe else PoEMode.DISABLED
            if overrides.dot1x_mode is not None:
                after.eth_802_1x_control = overrides.dot1x_mode
            if overrides.lldp_med_enable is not None:
                after.lldp_med_enabled = overrides.lldp_med_enable
            if overrides.loopback_detect is not None:
                after.loopback_detect_enabled = overrides.loopback_detect
            if overrides.spanning_tree_enable is not None:
                after.spanning_tree_enabled = overrides.spanning_tree_enable
            if overrides.port_isolation is not None:
                after.port_isolation_enabled = overrides.port_isolation
        return after


def _base_args(**extra):
    args = {
        "controller_url": "https://omada.example.com:8043",
        "username": "admin",
        "password": "secret",
        "site": "Default",
        "mac": "AA-BB-CC-00-00-01",
        "port": 1,
    }
    args.update(extra)
    return args


def _run(monkeypatch, site_client, args):
    monkeypatch.setattr(basic.AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(
        omada_switch_port,
        "run_omada_task",
        lambda module, factory: asyncio.run(factory(site_client)),
    )
    set_module_args(args)
    with pytest.raises(AnsibleExitJson) as exc_info:
        omada_switch_port.main()
    return exc_info.value.args[0]


def test_no_change_needed_is_not_changed(monkeypatch):
    current = FakePortDetails(port=1, name="Port1")
    site_client = FakeSiteClient(current)
    result = _run(monkeypatch, site_client, _base_args(name="Port1"))

    assert result["changed"] is False
    assert site_client.update_calls == []
    assert result["before"] == result["after"]


def test_name_only_change_does_not_touch_overrides(monkeypatch):
    current = FakePortDetails(port=1, name="Port1")
    site_client = FakeSiteClient(current)
    result = _run(monkeypatch, site_client, _base_args(name="Camera 1 - front porch"))

    assert result["changed"] is True
    assert len(site_client.update_calls) == 1
    settings = site_client.update_calls[0]["settings"]
    assert settings.name == "Camera 1 - front porch"
    assert settings.profile_id is None
    assert settings.native_network_id is None
    assert settings.profile_override_enabled is None  # no override fields requested -> untouched
    assert settings.profile_overrides is None
    assert result["after"]["name"] == "Camera 1 - front porch"


def test_native_network_id_assigns_vlan(monkeypatch):
    current = FakePortDetails(port=1, name="Camera 1", native_network_id="net-lan-default")
    site_client = FakeSiteClient(current)
    result = _run(monkeypatch, site_client, _base_args(native_network_id="net-surveillance"))

    assert result["changed"] is True
    settings = site_client.update_calls[0]["settings"]
    assert settings.native_network_id == "net-surveillance"
    assert result["after"]["native_network_id"] == "net-surveillance"


def test_enable_poe_sets_profile_override_enabled_and_only_that_field(monkeypatch):
    current = FakePortDetails(port=1, name="Port1", poe_mode=PoEMode.DISABLED)
    site_client = FakeSiteClient(current)

    result = _run(monkeypatch, site_client, _base_args(enable_poe=True))

    assert result["changed"] is True
    settings = site_client.update_calls[0]["settings"]
    assert settings.profile_override_enabled is True
    overrides = settings.profile_overrides
    assert overrides.enable_poe is True
    # everything else left None -> library's own semantics leave them unchanged,
    # this module must not fabricate values for fields the user didn't ask about
    assert overrides.dot1x_mode is None
    assert overrides.spanning_tree_enable is None


def test_check_mode_reports_change_without_calling_update(monkeypatch):
    current = FakePortDetails(port=1, name="Port1", port_isolation_enabled=False)
    site_client = FakeSiteClient(current)
    args = _base_args(port_isolation=True)
    args["_ansible_check_mode"] = True

    result = _run(monkeypatch, site_client, args)

    assert result["changed"] is True
    assert site_client.update_calls == []


def test_tag_ids_change_applies_labels(monkeypatch):
    current = FakePortDetails(port=16, name="Port16", tag_ids=[])
    site_client = FakeSiteClient(current)

    result = _run(monkeypatch, site_client, _base_args(port=16, tag_ids=["tag-foo"]))

    assert result["changed"] is True
    settings = site_client.update_calls[0]["settings"]
    assert settings.tag_ids == ["tag-foo"]
    assert result["after"]["tag_ids"] == ["tag-foo"]


def test_tag_ids_same_set_different_order_is_not_changed(monkeypatch):
    current = FakePortDetails(port=16, name="Port16", tag_ids=["tag-foo", "tag-bar"])
    site_client = FakeSiteClient(current)

    result = _run(monkeypatch, site_client, _base_args(port=16, tag_ids=["tag-bar", "tag-foo"]))

    assert result["changed"] is False
    assert site_client.update_calls == []


def test_empty_tag_ids_clears_labels(monkeypatch):
    current = FakePortDetails(port=16, name="Port16", tag_ids=["tag-foo"])
    site_client = FakeSiteClient(current)

    result = _run(monkeypatch, site_client, _base_args(port=16, tag_ids=[]))

    assert result["changed"] is True
    settings = site_client.update_calls[0]["settings"]
    assert settings.tag_ids == []
    assert result["after"]["tag_ids"] == []


def test_profile_and_override_change_together(monkeypatch):
    current = FakePortDetails(port=12, name="AP Uplink", profile_id="profile-default")
    site_client = FakeSiteClient(current)

    result = _run(
        monkeypatch,
        site_client,
        _base_args(port=12, profile_id="profile-ap", enable_poe=True),
    )

    assert result["changed"] is True
    settings = site_client.update_calls[0]["settings"]
    assert settings.profile_id == "profile-ap"
    assert settings.profile_overrides.enable_poe is True
    assert result["after"]["profile_id"] == "profile-ap"
    assert result["after"]["poe_mode"] == "enabled"
