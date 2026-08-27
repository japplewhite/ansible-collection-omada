# applewhiteit.omada

Ansible collection for automating TP-Link Omada SDN networks (controller,
gateway, switches, access points), built on the
[`tplink-omada-client`](https://github.com/MarkGodwin/tplink-omada-api)
Python library.

**Status: early / experimental.** Module scope is intentionally bounded to
what the upstream client actually supports today — see
[the capability matrix](../../../docs/phase2-capability-matrix.md) in this
repo for exactly what's covered and what isn't yet.

## Requirements

- Python >= 3.11
- `tplink-omada-client` (`pip install tplink-omada-client`)
- Ansible-core >= 2.15

## Installation

```bash
ansible-galaxy collection install applewhiteit.omada
pip install -r requirements.txt
```

## Credentials

Every module accepts `controller_url`, `username`, `password`, `site`, and
`validate_certs`, each with an environment-variable fallback so credentials
never need to sit in playbooks or inventory:

| Option | Environment variable |
|---|---|
| `controller_url` | `OMADA_CONTROLLER_URL` |
| `username` | `OMADA_USERNAME` |
| `password` | `OMADA_PASSWORD` |
| `site` | `OMADA_SITE` |
| `validate_certs` | `OMADA_VALIDATE_CERTS` |

Use Ansible Vault for the password/username in a playbook or inventory
variable file; do not hard-code credentials.

## Modules

| Module | Purpose |
|---|---|
| `omada_site_info` | List sites visible to the account |
| `omada_device_info` | List/describe devices (gateway, switches, APs) on a site |

More modules land as the upstream library's coverage is verified against a
live controller (see the project's Phase 2 capability matrix for what's
planned next).

## License

MIT
