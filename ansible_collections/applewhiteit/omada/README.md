# applewhiteit.omada

Ansible collection for automating TP-Link Omada SDN networks (controller,
gateway, switches, access points), built on
[`tplink-omada-client`](https://github.com/MarkGodwin/tplink-omada-api).

Module scope is intentionally bounded to what the underlying client actually
supports — see [the capability matrix](../../../docs/capability-matrix.md)
in this repo for exactly what's covered and what isn't yet.

**Currently depends on a private fork, not the PyPI release** —
`requirements.txt` points at
`github.com/japplewhite/tplink-omada-api-fork` (branch
`feature/vlan-network-support`), which adds LAN network/VLAN and port-label
support that no released version of the upstream library has yet. See the
main project [README](../../../README.md)'s "Why a private fork" section for
details. This means installing this collection's dependency requires access
to that repo.

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
| `omada_network_info` | info | List LAN networks/VLANs on a site |
| `omada_network` | config | Create a LAN network/VLAN, with optional DHCP range and port labels (`tag_ids`). Create-only — idempotent by name, but does not reconcile other fields on an existing network. Check-mode aware. |
| `omada_switch_port` | config | Configure a switch port: name, profile, native VLAN/network, port labels (`tag_ids`), PoE, duplex, link speed, 802.1x, LLDP-MED, loopback detection, spanning tree, port isolation. Idempotent, check-mode aware. |
| `omada_device` | config | Device-level LED setting. Idempotent, check-mode aware. |

### Example: create a VLAN and label a port

```yaml
- name: Create a VLAN
  applewhiteit.omada.omada_network:
    name: "Business LAN"
    vlan_id: 20
    gateway_subnet: "192.168.20.1/24"
    dhcp_start: "192.168.20.100"
    dhcp_end: "192.168.20.199"
  register: business_lan

- name: Assign a switch port to that VLAN
  applewhiteit.omada.omada_switch_port:
    mac: "AA-BB-CC-00-00-01"
    port: 16
    native_network_id: "{{ business_lan.network.id }}"
    enable_poe: true
```

Port label (`tag_ids`) values currently have to be looked up or created via
the underlying `tplink-omada-client` library's `get_port_labels()`/
`create_port_label()` directly — no Ansible module wraps that yet.

Not yet implemented, and why:

- **Network update/delete** — the underlying client has no update or delete
  operation for networks yet, so `omada_network` can only create.
- **Port label listing/creation as a module** — the underlying client
  supports this (`get_port_labels()`/`create_port_label()`); it just isn't
  wrapped in an Ansible module yet.
- **SSIDs/WLANs, guest networks, wireless security** — unconfirmed against
  the official API. See
  [the capability matrix](../../../docs/capability-matrix.md).
- **Port profiles as a standalone config module** — the upstream client only
  supports reading existing profiles and applying one to a port (the latter
  is covered by `omada_switch_port`'s `profile_id` option); there's no
  create/edit/delete API to wrap.
- **Device naming, per-device reboot** — not exposed by the upstream client.
  (Client renaming *is* supported and will get its own module later; device
  reboot in this library only reboots the controller itself, a different and
  higher-risk scope than a per-device module.)

More modules land as upstream/fork coverage is verified against a live
controller.

## License

MIT
