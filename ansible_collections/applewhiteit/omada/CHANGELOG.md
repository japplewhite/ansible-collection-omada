# Changelog

## 0.1.0 (unreleased)

Early stage - see the project's [capability matrix](../../../docs/capability-matrix.md)
and README for current scope.

### Changed

- **Dependency switched from PyPI `tplink-omada-client` to a private fork**
  (`github.com/japplewhite/tplink-omada-api-fork`,
  `feature/vlan-network-support` branch) to get LAN network/VLAN and
  port-label support with no upstream release timeline. Pulled in a real
  upstream API shape change along with it: `SwitchPortOverrides` →
  `SwitchPortSettings` + `PortProfileOverrides`, and a Python floor bump to
  3.13. See the main project README's "Why a private fork" section.
- `omada_switch_port`: reworked for the new `SwitchPortSettings` shape;
  gained `native_network_id` for VLAN assignment and `tag_ids` for port
  labels; no longer hand-rolls an overrides merge (the new upstream shape
  does None-means-unchanged natively).

### Added

- `module_utils/omada`: shared connection handling, env-var credential
  fallbacks, and error handling for every module.
- `omada_site_info`: list sites visible to the account.
- `omada_device_info`: list/describe devices, filterable by MAC or type.
- `omada_firmware_info`: firmware version and upgrade-available status.
- `omada_switch_port`: configure name, profile, native VLAN/network, port
  labels, PoE, duplex, link speed, 802.1x, LLDP-MED, loopback detection,
  spanning tree, and port isolation on a switch port. Idempotent and
  check-mode aware.
- `omada_device`: onboard LED setting. Idempotent and check-mode aware.
- `omada_network_info`: list LAN networks/VLANs on a site, verified against
  a live controller.
- `omada_network`: create a LAN network/VLAN, with optional DHCP range and
  port labels. Idempotent by name, check-mode aware.
