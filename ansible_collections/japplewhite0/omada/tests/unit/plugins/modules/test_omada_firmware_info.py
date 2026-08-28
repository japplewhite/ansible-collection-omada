import asyncio
from dataclasses import dataclass

import pytest
from ansible.module_utils import basic
from ansible_collections.japplewhite0.omada.plugins.modules import omada_firmware_info

from .utils import AnsibleExitJson, exit_json, set_module_args


@dataclass
class FakeFirmware:
    current_version: str
    latest_version: str
    release_notes: str = ""


@dataclass
class FakeListDevice:
    mac: str


class FakeSiteClient:
    def __init__(self, devices, firmware_by_mac):
        self.devices = devices
        self.firmware_by_mac = firmware_by_mac

    async def get_devices(self):
        return self.devices

    async def get_firmware_details(self, mac):
        return self.firmware_by_mac[mac]


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
        omada_firmware_info,
        "run_omada_task",
        lambda module, factory: asyncio.run(factory(site_client)),
    )
    set_module_args(args)
    with pytest.raises(AnsibleExitJson) as exc_info:
        omada_firmware_info.main()
    return exc_info.value.args[0]


def test_single_device_up_to_date(monkeypatch):
    site_client = FakeSiteClient(
        devices=[],
        firmware_by_mac={"AA-BB-CC-00-00-01": FakeFirmware(current_version="1.0.0", latest_version="1.0.0")},
    )
    result = _run(monkeypatch, site_client, _base_args(mac="AA-BB-CC-00-00-01"))

    assert result["changed"] is False
    assert result["devices"] == [
        {
            "mac": "AA-BB-CC-00-00-01",
            "current_version": "1.0.0",
            "latest_version": "1.0.0",
            "needs_upgrade": False,
            "release_notes": "",
        }
    ]


def test_single_device_needs_upgrade(monkeypatch):
    site_client = FakeSiteClient(
        devices=[],
        firmware_by_mac={"AA-BB-CC-00-00-01": FakeFirmware(current_version="1.0.0", latest_version="1.1.0")},
    )
    result = _run(monkeypatch, site_client, _base_args(mac="AA-BB-CC-00-00-01"))

    assert result["devices"][0]["needs_upgrade"] is True


def test_no_mac_lists_all_site_devices(monkeypatch):
    site_client = FakeSiteClient(
        devices=[FakeListDevice(mac="AA-01"), FakeListDevice(mac="AA-02")],
        firmware_by_mac={
            "AA-01": FakeFirmware(current_version="1.0.0", latest_version="1.0.0"),
            "AA-02": FakeFirmware(current_version="1.0.0", latest_version="2.0.0"),
        },
    )
    result = _run(monkeypatch, site_client, _base_args())

    assert [d["mac"] for d in result["devices"]] == ["AA-01", "AA-02"]
    assert result["devices"][1]["needs_upgrade"] is True
