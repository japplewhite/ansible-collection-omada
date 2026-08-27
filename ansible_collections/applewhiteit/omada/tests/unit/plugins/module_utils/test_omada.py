import pytest
from ansible_collections.applewhiteit.omada.plugins.module_utils import omada


class FailJsonCalled(Exception):
    def __init__(self, kwargs):
        self.kwargs = kwargs
        super().__init__(kwargs.get("msg"))


class FakeModule:
    """Minimal AnsibleModule stand-in for module_utils-level tests."""

    def __init__(self, params=None):
        self.params = params or {
            "controller_url": "https://omada.example.com:8043",
            "username": "admin",
            "password": "secret",
            "site": "Default",
            "validate_certs": True,
        }

    def fail_json(self, **kwargs):
        raise FailJsonCalled(kwargs)


class FakeOmadaClient:
    """Stands in for tplink_omada_client.omadaclient.OmadaClient."""

    instances = []

    def __init__(self, url, username, password, verify_ssl=True):
        self.url = url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.site_client = object()
        FakeOmadaClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get_site_client(self, site):
        self.requested_site = site
        return self.site_client


def test_omada_argument_spec_has_expected_connection_args():
    spec = omada.omada_argument_spec()

    assert set(spec.keys()) == {
        "controller_url",
        "username",
        "password",
        "site",
        "validate_certs",
    }
    assert spec["password"]["no_log"] is True
    assert spec["controller_url"]["required"] is True
    assert spec["validate_certs"]["default"] is True


def test_check_omada_client_dependency_fails_cleanly_when_missing(monkeypatch):
    monkeypatch.setattr(omada, "HAS_OMADA_CLIENT", False)
    monkeypatch.setattr(omada, "OMADA_CLIENT_IMPORT_ERROR", "traceback text")
    module = FakeModule()

    with pytest.raises(FailJsonCalled) as exc_info:
        omada.check_omada_client_dependency(module)

    assert "tplink-omada-client" in exc_info.value.kwargs["msg"]


def test_run_omada_client_task_returns_coro_factory_result(monkeypatch):
    monkeypatch.setattr(omada, "HAS_OMADA_CLIENT", True)
    monkeypatch.setattr(omada, "OmadaClient", FakeOmadaClient)
    module = FakeModule()

    async def _factory(client):
        assert isinstance(client, FakeOmadaClient)
        assert client.url == module.params["controller_url"]
        return {"ok": True}

    result = omada.run_omada_client_task(module, _factory)

    assert result == {"ok": True}


def test_run_omada_task_uses_site_scoped_client(monkeypatch):
    monkeypatch.setattr(omada, "HAS_OMADA_CLIENT", True)
    monkeypatch.setattr(omada, "OmadaClient", FakeOmadaClient)
    module = FakeModule()

    async def _factory(site_client):
        return site_client

    result = omada.run_omada_task(module, _factory)

    assert result is FakeOmadaClient.instances[-1].site_client
    assert FakeOmadaClient.instances[-1].requested_site == "Default"


def test_run_omada_task_converts_omada_exception_to_fail_json(monkeypatch):
    monkeypatch.setattr(omada, "HAS_OMADA_CLIENT", True)
    monkeypatch.setattr(omada, "OmadaClient", FakeOmadaClient)
    module = FakeModule()

    async def _factory(site_client):
        raise omada.OmadaClientException("controller said no")

    with pytest.raises(FailJsonCalled) as exc_info:
        omada.run_omada_task(module, _factory)

    assert "controller said no" in exc_info.value.kwargs["msg"]
