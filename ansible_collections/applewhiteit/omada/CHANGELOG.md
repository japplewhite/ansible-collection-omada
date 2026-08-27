# Changelog

## 0.1.0 (unreleased)

Early/experimental. Nothing here has been verified against a live Omada
controller yet - see the project's Phase 2 capability matrix and README for
current scope.

### Added

- `module_utils/omada`: shared connection handling, env-var credential
  fallbacks, and error handling for every module.
- `omada_site_info`: list sites visible to the account.
- `omada_device_info`: list/describe devices, filterable by MAC or type.
- `omada_firmware_info`: firmware version and upgrade-available status.
- `omada_switch_port`: configure name, profile, PoE, duplex, link speed,
  802.1x, LLDP-MED, loopback detection, spanning tree, and port isolation on
  a switch port. Idempotent and check-mode aware.
- `omada_device`: onboard LED setting. Idempotent and check-mode aware.
