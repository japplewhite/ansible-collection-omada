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

| Module | Type | Purpose |
|---|---|---|
| `omada_site_info` | info | List sites visible to the account |
| `omada_device_info` | info | List/describe devices (gateway, switches, APs) on a site |
| `omada_firmware_info` | info | Firmware version and upgrade-available status per device |
| `omada_switch_port` | config | Configure a switch port: name, profile, PoE, duplex, link speed, 802.1x, LLDP-MED, loopback detection, spanning tree, port isolation. Idempotent, check-mode aware, merges onto existing overrides rather than replacing them wholesale. |
| `omada_device` | config | Device-level LED setting. Idempotent, check-mode aware. |

Not yet implemented, and why:

- **VLANs/networks, SSIDs/WLANs, guest networks, wireless security** — not
  exposed by `tplink-omada-client` today (VLANs/networks) or unconfirmed
  against the official API (the rest). See
  [the capability matrix](../../../docs/phase2-capability-matrix.md).
- **Port profiles as a standalone config module** — the upstream client only
  supports reading existing profiles and applying one to a port (the latter
  is covered by `omada_switch_port`'s `profile_id` option); there's no
  create/edit/delete API to wrap.
- **Device naming, per-device reboot** — not exposed by the upstream client.
  (Client renaming *is* supported and will get its own module later; device
  reboot in this library only reboots the controller itself, a different and
  higher-risk scope than a per-device module.)

More modules land as upstream coverage is verified against a live controller.

## License

MIT
