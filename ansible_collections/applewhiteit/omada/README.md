# applewhiteit.omada

Ansible collection for automating TP-Link Omada SDN networks (controller,
gateway, switches, access points), built on
[`tplink-omada-client`](https://github.com/MarkGodwin/tplink-omada-api).

**Status: early / experimental.** Module scope is intentionally bounded to
what the underlying client actually supports today — see
[the capability matrix](../../../docs/phase2-capability-matrix.md) in this
repo for exactly what's covered and what isn't yet.

**Currently depends on a private fork, not the PyPI release** —
`requirements.txt` points at
`github.com/japplewhite/tplink-omada-api-fork` (branch
`feature/vlan-network-support`), which adds LAN network/VLAN read support
that no released version of the upstream library has yet. See the main
project [README](../../../README.md)'s "Delivery priority" section for why
and the plan to reconcile this back upstream. This means installing this
collection's dependency requires access to that private repo.

## Requirements

- Python >= 3.13 (the fork's current branch requires this - a real upstream
  API shape change, not something we chose)
- `tplink-omada-client` — installed from the private fork per
  `requirements.txt`, not PyPI, for now
- Ansible-core >= 2.15

## Installation

```bash
ansible-galaxy collection install applewhiteit.omada
pip install -r requirements.txt  # needs read access to the private fork above
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
| `omada_switch_port` | config | Configure a switch port: name, profile, native VLAN/network, PoE, duplex, link speed, 802.1x, LLDP-MED, loopback detection, spanning tree, port isolation. Idempotent, check-mode aware. |
| `omada_device` | config | Device-level LED setting. Idempotent, check-mode aware. |
| `omada_network_info` | info | List LAN networks/VLANs on a site. **Unverified against a live controller** — see its own docstring. |

Not yet implemented, and why:

- **Creating networks/VLANs** — `get_networks()` (read) exists on our fork
  but `create_network()` is intentionally stubbed with
  `NotImplementedError`: it's a mutating call and its payload hasn't been
  confirmed against a live controller yet, so we won't ship a guess for
  something that writes to production network config. The plan is to
  capture the real request the Controller UI itself sends (via browser
  devtools, on a throwaway test network, not the production VLANs) to
  nail down the exact payload, implement `create_network()` for real
  against that, and use it for the actual VLAN delivery — not a manual
  fallback.
- **SSIDs/WLANs, guest networks, wireless security** — unconfirmed against
  the official API. See
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
