import asyncio
from dataclasses import dataclass, replace

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
    is_disabled: bool = False
    poe_mode: PoEMode = PoEMode.DISABLED
    duplex: LinkDuplex = LinkDuplex.AUTO
    link_speed: LinkSpeed = LinkSpeed.SPEED_AUTO
    eth_802_1x_control: Eth802Dot1X = Eth802Dot1X.FORCE_AUTHORIZED
    lldp_med_enabled: bool = True
    loopback_detect_enabled: bool = True
    spanning_tree_enabled: bool = False
    port_isolation_enabled: bool = False


@dataclass
class FakeOverrides:
    enable_poe: bool = True
    dot1x_mode: Eth802Dot1X = Eth802Dot1X.FORCE_AUTHORIZED
    duplex: LinkDuplex = LinkDuplex.AUTO
    link_speed: LinkSpeed = LinkSpeed.SPEED_AUTO
    lldp_med_enable: bool = True
    loopback_detect: bool = True
    spanning_tree_enable: bool = False
    port_isolation: bool = False


class FakeSiteClient:
    def __init__(self, current):
        self.current = current
        self.overrides = FakeOverrides()
        self.update_calls = []

    async def get_switch_port(self, mac, port):
        return self.current

    async def get_switch_port_overrides(self, mac, port):
        return self.overrides

    async def update_switch_port(self, mac, port, new_name=None, profile_id=None, overrides=None):
        self.update_calls.append(
            {"mac": mac, "port": port, "new_name": new_name, "profile_id": profile_id, "overrides": overrides}
        )
        after = replace(self.current)
        if new_name is not None:
            after.name = new_name
        if profile_id is not None:
            after.profile_id = profile_id
        if overrides is not None:
            after.poe_mode = PoEMode.ENABLED if overrides.enable_poe else PoEMode.DISABLED
            after.duplex = overrides.duplex
            after.link_speed = overrides.link_speed
            after.eth_802_1x_control = overrides.dot1x_mode
            after.lldp_med_enabled = overrides.lldp_med_enable
            after.loopback_detect_enabled = overrides.loopback_detect
            after.spanning_tree_enabled = overrides.spanning_tree_enable
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
    call = site_client.update_calls[0]
    assert call["new_name"] == "Camera 1 - front porch"
    assert call["profile_id"] is None
    assert call["overrides"] is None  # no override fields requested -> untouched
    assert result["after"]["name"] == "Camera 1 - front porch"


def test_enable_poe_merges_onto_current_overrides_not_defaults(monkeypatch):
    current = FakePortDetails(port=1, name="Port1", poe_mode=PoEMode.DISABLED)
    site_client = FakeSiteClient(current)
    # Simulate a port whose existing overrides differ from the dataclass defaults,
    # to prove the module merges onto *current* overrides, not blank ones.
    site_client.overrides = FakeOverrides(
        enable_poe=False,
        dot1x_mode=Eth802Dot1X.FORCE_UNAUTHORIZED,
        spanning_tree_enable=True,
    )

    result = _run(monkeypatch, site_client, _base_args(enable_poe=True))

    assert result["changed"] is True
    call = site_client.update_calls[0]
    overrides = call["overrides"]
    assert overrides.enable_poe is True  # the requested change
    # everything else preserved from the *current* overrides, not the class defaults
    assert overrides.dot1x_mode == Eth802Dot1X.FORCE_UNAUTHORIZED
    assert overrides.spanning_tree_enable is True


def test_check_mode_reports_change_without_calling_update(monkeypatch):
    current = FakePortDetails(port=1, name="Port1", port_isolation_enabled=False)
    site_client = FakeSiteClient(current)
    args = _base_args(port_isolation=True)
    args["_ansible_check_mode"] = True

    result = _run(monkeypatch, site_client, args)

    assert result["changed"] is True
    assert site_client.update_calls == []


def test_profile_and_override_change_together(monkeypatch):
    current = FakePortDetails(port=12, name="AP Uplink", profile_id="profile-default")
    site_client = FakeSiteClient(current)

    result = _run(
        monkeypatch,
        site_client,
        _base_args(port=12, profile_id="profile-ap", enable_poe=True),
    )

    assert result["changed"] is True
    call = site_client.update_calls[0]
    assert call["profile_id"] == "profile-ap"
    assert call["overrides"].enable_poe is True
    assert result["after"]["profile_id"] == "profile-ap"
    assert result["after"]["poe_mode"] == "enabled"
