import asyncio
from dataclasses import dataclass

import pytest
from ansible.module_utils import basic
from ansible_collections.applewhiteit.omada.plugins.modules import omada_device_info

from .utils import AnsibleExitJson, exit_json, set_module_args


@dataclass
class FakeDevice:
    mac: str
    name: str
    type: str
    model: str = "SG3452XP"
    model_display_name: str = "TP-Link SG3452XP"
    status: int = 1
    status_category: str = "connected"
    ip_address: str = "10.0.10.5"
    firmware_version: str = "1.0.0"
    need_upgrade: bool = False
    display_uptime: str = "3 days"
    cpu_usage: float = 12.5
    mem_usage: float = 33.0


SWITCH = FakeDevice(mac="AA-BB-CC-00-00-01", name="core-switch", type="switch")
AP1 = FakeDevice(mac="AA-BB-CC-00-00-02", name="ap-front", type="ap", model="EAP723")
AP2 = FakeDevice(mac="AA-BB-CC-00-00-03", name="ap-back", type="ap", model="EAP723")


class FakeSiteClient:
    def __init__(self, devices):
        self._devices = devices

    async def get_devices(self):
        return self._devices

    async def get_device(self, mac):
        for device in self._devices:
            if device.mac == mac:
                return device
        raise LookupError(mac)


def _base_args():
    return {
        "controller_url": "https://omada.example.com:8043",
        "username": "admin",
        "password": "secret",
        "site": "Default",
    }


def _patch(monkeypatch, site_client):
    monkeypatch.setattr(basic.AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(
        omada_device_info,
        "run_omada_task",
        lambda module, factory: asyncio.run(factory(site_client)),
    )


def test_lists_all_devices(monkeypatch):
    _patch(monkeypatch, FakeSiteClient([SWITCH, AP1, AP2]))
    set_module_args(_base_args())

    with pytest.raises(AnsibleExitJson) as exc_info:
        omada_device_info.main()

    result = exc_info.value.args[0]
    assert result["changed"] is False
    assert [d["mac"] for d in result["devices"]] == [SWITCH.mac, AP1.mac, AP2.mac]
    assert result["devices"][0]["model_display_name"] == "TP-Link SG3452XP"


def test_filters_by_device_type(monkeypatch):
    _patch(monkeypatch, FakeSiteClient([SWITCH, AP1, AP2]))
    args = _base_args()
    args["device_type"] = "ap"
    set_module_args(args)

    with pytest.raises(AnsibleExitJson) as exc_info:
        omada_device_info.main()

    result = exc_info.value.args[0]
    assert [d["mac"] for d in result["devices"]] == [AP1.mac, AP2.mac]


def test_filters_by_mac(monkeypatch):
    _patch(monkeypatch, FakeSiteClient([SWITCH, AP1, AP2]))
    args = _base_args()
    args["mac"] = AP1.mac
    set_module_args(args)

    with pytest.raises(AnsibleExitJson) as exc_info:
        omada_device_info.main()

    result = exc_info.value.args[0]
    assert len(result["devices"]) == 1
    assert result["devices"][0]["mac"] == AP1.mac
    assert result["devices"][0]["name"] == "ap-front"
