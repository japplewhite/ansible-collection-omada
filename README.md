# Omada Ansible Automation

Ansible automation for TP-Link Omada SDN networks (controller, gateway,
switches, access points), built on an actively-maintained upstream Python
API client rather than a bespoke/private fork. Goal: a reusable collection
that works for any Omada deployment, not just one customer's network.

## Status

Phase 1 (upstream ecosystem research) in progress. See `docs/` as phases land.

## Phases (tracking)

- [x] Phase 1 — Upstream research & recommendation ([report](docs/phase1-upstream-research.md))
- [x] Phase 2 — API capability matrix ([report](docs/phase2-capability-matrix.md))
- [ ] Phase 3 — Upstream contributions (prepared here, submitted by the user —
      no PRs are opened without explicit review/approval per PR)
- [ ] Phase 4 — Ansible collection (in progress: `applewhiteit.omada` at `ansible_collections/applewhiteit/omada/` — `omada_site_info`, `omada_device_info` done so far, config-writing modules next)
- [ ] Phase 5 — Example roles/playbooks
- [ ] Phase 6 — Validation against the reference deployment (see below)
- [ ] Phase 7 — Monitoring / capacity-planning use case (1GbE→2.5GbE decision support)
- [ ] Phase 8 — Documentation

## Engineering principles

Idempotency, simplicity, upstream contribution over forking, testability,
secure credential handling (env vars / Ansible Vault — never hard-coded),
minimal API assumptions, reuse across customer environments. No screen
scraping or browser automation; no undocumented private API reliance unless
isolated and justified; no hard-coded site IDs or credentials; no logic
specific only to a single deployment.

## Reference deployment (for Phase 6/7 validation only)

Used to validate the collection against real hardware/topology — not to be
treated as the only supported shape. Full source design document lives
outside this repo (customer-owned, not duplicated here):
`~/Library/Mobile Documents/com~apple~CloudDocs/REDACTED-customer-design-doc-path`

Hardware:
- Gateway: TP-Link ER707-M2 (Omada multi-gig VPN gateway)
- Core switch: TP-Link SG3452XP (48-port GbE PoE+, 4x 10G SFP+)
- Controller: TP-Link OC200 (hardware controller)
- APs: 2x TP-Link EAP723 (Wi-Fi 7, 2.5GbE uplink, currently patched to 1GbE switch ports by design)
- Deferred/contingent: TP-Link SG2210XMP-M2 (8x 2.5GbE PoE+, 2x 10G SFP+) —
  only if monitoring shows AP uplink is a bottleneck, not WAN or RF

VLANs:
| VLAN | Purpose | Policy |
|---|---|---|
| 10 | Network management | Admins only |
| 20 | Business LAN | Normal internal access |
| 30 | Surveillance (cameras + NVR) | Restricted |
| 40 | Guest Wi-Fi | Internet only, isolated |

Phase 7 decision logic to support with telemetry (do not recommend hardware
changes on theoretical max speeds alone):
1. WAN utilization near 1Gbps saturation → ISP upgrade is the bottleneck, not the switch.
2. AP uplink utilization near 1Gbps while WAN has headroom → consider the SG2210XMP-M2.
3. High wireless channel utilization → reposition/add APs, not an Ethernet upgrade.
