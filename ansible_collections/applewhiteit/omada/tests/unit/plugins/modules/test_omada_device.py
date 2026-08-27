import asyncio
from dataclasses import dataclass

import pytest
from ansible.module_utils import basic
from ansible_collections.applewhiteit.omada.plugins.modules import omada_device
from tplink_omada_client.definitions import LedSetting

from .utils import AnsibleExitJson, AnsibleFailJson, exit_json, fail_json, set_module_args


@dataclass
class FakeListDevice:
    mac: str
    type: str


@dataclass
class FakeDetailedDevice:
    led_setting: LedSetting = LedSetting.SITE_SETTINGS


class FakeSiteClient:
    def __init__(self, list_device, detailed):
        self.list_device = list_device
        self.detailed = detailed
        self.led_calls = []

    async def get_device(self, mac):
        return self.list_device

    async def get_switch(self, mac):
        return self.detailed

    async def get_access_point(self, mac):
        return self.detailed

    async def get_gateway(self, mac):
        return self.detailed

    async def set_led_setting(self, mac, setting):
        self.led_calls.append((mac, setting))
        self.detailed.led_setting = setting
        return True


def _base_args(**extra):
    args = {
        "controller_url": "https://omada.example.com:8043",
        "username": "admin",
        "password": "secret",
        "site": "Default",
        "mac": "AA-BB-CC-00-00-01",
    }
    args.update(extra)
    return args


def _run(monkeypatch, site_client, args, expect_fail=False):
    monkeypatch.setattr(basic.AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(basic.AnsibleModule, "fail_json", fail_json)
    monkeypatch.setattr(
        omada_device,
        "run_omada_task",
        lambda module, factory: asyncio.run(factory(site_client)),
    )
    set_module_args(args)
    exc_type = AnsibleFailJson if expect_fail else AnsibleExitJson
    with pytest.raises(exc_type) as exc_info:
        omada_device.main()
    return exc_info.value.args[0]


def test_led_already_matches_is_not_changed(monkeypatch):
    site_client = FakeSiteClient(
        FakeListDevice(mac="AA-BB-CC-00-00-01", type="switch"),
        FakeDetailedDevice(led_setting=LedSetting.OFF),
    )
    result = _run(monkeypatch, site_client, _base_args(led="off"))

    assert result["changed"] is False
    assert site_client.led_calls == []


def test_led_change_calls_set_led_setting(monkeypatch):
    site_client = FakeSiteClient(
        FakeListDevice(mac="AA-BB-CC-00-00-01", type="ap"),
        FakeDetailedDevice(led_setting=LedSetting.SITE_SETTINGS),
    )
    result = _run(monkeypatch, site_client, _base_args(led="on"))

    assert result["changed"] is True
    assert site_client.led_calls == [("AA-BB-CC-00-00-01", LedSetting.ON)]
    assert result["after"]["led"] == "on"


def test_check_mode_does_not_call_set_led_setting(monkeypatch):
    site_client = FakeSiteClient(
        FakeListDevice(mac="AA-BB-CC-00-00-01", type="gateway"),
        FakeDetailedDevice(led_setting=LedSetting.SITE_SETTINGS),
    )
    args = _base_args(led="off")
    args["_ansible_check_mode"] = True

    result = _run(monkeypatch, site_client, args)

    assert result["changed"] is True
    assert site_client.led_calls == []


def test_unrecognized_device_type_fails_cleanly(monkeypatch):
    site_client = FakeSiteClient(
        FakeListDevice(mac="AA-BB-CC-00-00-01", type="unknown-thing"),
        FakeDetailedDevice(),
    )
    result = _run(monkeypatch, site_client, _base_args(led="off"), expect_fail=True)

    assert "unrecognized type" in result["msg"]
