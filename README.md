# Omada Ansible Automation

Ansible automation for TP-Link Omada SDN networks — controller, gateway,
switches, and access points — driven entirely through code, not the
Controller UI.

## Why this exists

Omada networks are usually configured by clicking through the Controller UI,
one port and one VLAN at a time. That works until you need to reproduce a
change across sites, prove what changed and when, or recover from a mistake
without hand-tracing every click that led to it. This collection turns that
UI-driven process into version-controlled, idempotent Ansible playbooks:
the same VLAN, port, or firmware rollout runs the same way every time, dry-runs
safely with `--check` before it touches anything, and lives in git instead of
in someone's memory of what they clicked last quarter. It plugs into
infrastructure you likely already run — no new orchestration tool, no
screen-scraping, just modules that speak the Controller's own API.

## Features

- **Read** site, device, firmware, and network/VLAN state.
- **Configure** individual switch ports — name, profile, native VLAN, PoE,
  duplex, link speed, 802.1x, LLDP-MED, loopback detection, spanning tree,
  port isolation, and port labels.
- **Create** LAN networks/VLANs, including DHCP ranges and port labels.
- **Set** device-level LED behavior.
- Idempotent and check-mode aware throughout — every config module compares
  current state before changing anything, and reports what it *would* change
  under `--check` without touching the controller.
- Credentials never sit in playbooks: every module supports environment
  variables and Ansible Vault.

See the [collection README](ansible_collections/japplewhite0/omada/README.md)
for the full module list and options, and the
[capability matrix](docs/capability-matrix.md) for exactly what's covered,
partially covered, or not yet available.

## Requirements

- Python >= 3.13
- Ansible-core >= 2.15
- `tplink-omada-client`, installed per the collection's `requirements.txt`

### Why a fork

VLAN/network creation and port labels aren't in any released version of the
upstream `tplink-omada-client` library yet, so this collection currently
depends on our own fork
([`japplewhite/tplink-omada-api-fork`](https://github.com/japplewhite/tplink-omada-api-fork),
pinned to tag `v1.5.9-fork.1`) rather than the PyPI release. The fork tracks
upstream `master` plus two open upstream PRs (DHCP reservations, AP radio
settings) and adds network/port-label read and write support on top,
verified against a live controller. We've also raised the network/VLAN gap
directly with the upstream maintainer
([PR #86](https://github.com/MarkGodwin/tplink-omada-api/pull/86)) with an
eye toward contributing it back; until that lands, the fork is the
dependency.

See [upstream-research.md](docs/upstream-research.md) for why
`tplink-omada-client` was chosen over the alternatives in the first place.

## Installation

```bash
ansible-galaxy collection install japplewhite0.omada
pip install -r ansible_collections/japplewhite0/omada/requirements.txt
```

## Quick start

```yaml
- hosts: localhost
  gather_facts: false
  environment:
    OMADA_CONTROLLER_URL: "https://omada.example.com:8043"
    OMADA_USERNAME: "{{ omada_username }}"   # from Ansible Vault
    OMADA_PASSWORD: "{{ omada_password }}"   # from Ansible Vault
    OMADA_SITE: "Default"
  tasks:
    - name: List devices on the site
      japplewhite0.omada.omada_device_info:
      register: devices

    - name: Create a VLAN
      japplewhite0.omada.omada_network:
        name: "Business LAN"
        vlan_id: 20
        gateway_subnet: "192.168.20.1/24"
        dhcp_start: "192.168.20.100"
        dhcp_end: "192.168.20.199"
      register: business_lan

    - name: Assign a switch port to that VLAN
      japplewhite0.omada.omada_switch_port:
        mac: "AA-BB-CC-00-00-01"
        port: 16
        native_network_id: "{{ business_lan.network.id }}"
        enable_poe: true
```

## Validated hardware

Validated against a real deployment (not the only supported shape):

- Gateway: TP-Link ER707-M2 (hardware v1.30, firmware 1.4.5)
- Core switch: TP-Link SG3452XP (48-port GbE PoE+, 4x 10G SFP+; hardware v2.20, firmware 2.20.27)
- Controller: TP-Link OC200 (hardware controller, firmware 6.2.14.12)
- Access points: TP-Link EAP723 (Wi-Fi 7; hardware v2.0, firmware 1.2.3)

## Roadmap

- Additional write modules as upstream/fork coverage is verified — network
  update/delete, port-label listing, SSID/WLAN, and guest network support are
  the next candidates once their APIs are confirmed (see
  [capability-matrix.md](docs/capability-matrix.md)'s "Known gaps").
- Traffic-based capacity-planning guidance (e.g. recommending an AP uplink
  upgrade only when telemetry shows sustained saturation, not on theoretical
  maximums) once traffic-statistics modules exist.

## Engineering principles

Idempotency, simplicity, upstream contribution over forking where possible,
testability, secure credential handling (env vars / Ansible Vault — never
hard-coded), minimal API assumptions, reuse across environments. No screen
scraping or browser automation as a delivery mechanism; no undocumented
private API reliance unless isolated and justified; no hard-coded site IDs
or credentials; no logic specific to a single deployment.

## Development

```bash
cd ansible_collections/japplewhite0/omada
pip install -r requirements.txt
pip install ruff ansible-lint ansible-core pytest pytest-mock
ruff check .
ansible-lint .
pytest tests/unit -v
```

CI runs the same checks on every push/PR — see
[`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## License

MIT
