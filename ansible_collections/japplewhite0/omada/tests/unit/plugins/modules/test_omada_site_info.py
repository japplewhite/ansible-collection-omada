import asyncio
from collections import namedtuple

import pytest
from ansible.module_utils import basic
from ansible_collections.japplewhite0.omada.plugins.modules import omada_site_info

from .utils import AnsibleExitJson, exit_json, set_module_args

FakeSite = namedtuple("FakeSite", ["name", "id"])


class FakeClient:
    async def get_sites(self):
        return [FakeSite(name="Default", id="site-1"), FakeSite(name="Warehouse", id="site-2")]


def test_omada_site_info_lists_sites(monkeypatch):
    monkeypatch.setattr(basic.AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(
        omada_site_info,
        "run_omada_client_task",
        lambda module, factory: asyncio.run(factory(FakeClient())),
    )
    set_module_args(
        {
            "controller_url": "https://omada.example.com:8043",
            "username": "admin",
            "password": "secret",
            "site": "Default",
        }
    )

    with pytest.raises(AnsibleExitJson) as exc_info:
        omada_site_info.main()

    result = exc_info.value.args[0]
    assert result["changed"] is False
    assert result["sites"] == [
        {"name": "Default", "id": "site-1"},
        {"name": "Warehouse", "id": "site-2"},
    ]
