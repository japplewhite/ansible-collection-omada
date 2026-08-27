# Omada Ansible Automation

Ansible automation for TP-Link Omada SDN networks (controller, gateway,
switches, access points), built on an actively-maintained upstream Python
API client rather than a bespoke/private fork. Goal: a reusable collection
that works for any Omada deployment, not just one customer's network.

## Status

Phase 1 (upstream ecosystem research) in progress. See `docs/` as phases land.

## Delivery priority (important — read before assuming this project gates anything)

The customer network this project validates against has a real, near-term
delivery deadline. **Superseded 2026-08-27:** the earlier plan here was to
configure the network by hand through the Omada Controller UI and treat this
collection as a parallel, non-blocking track. That's no longer the plan —
Jeff wants the actual network configured *through this collection's code*,
not by hand. Do not suggest manual UI configuration as the delivery path.

To make that possible on a tight deadline without waiting on upstream, we
forked `tplink-omada-client` privately:
**github.com/japplewhite/tplink-omada-api-fork**, branch
`feature/vlan-network-support`. That branch = upstream master + two merged-in
open upstream PRs (#88 DHCP reservations, #90 AP radio settings) + our own
`get_networks()`/`LanNetwork` addition for reading LAN networks/VLANs (the
one capability this project actually needed that didn't exist anywhere
upstream). `create_network()` is stubbed with `NotImplementedError` — its
payload is a guess we haven't verified, and it's a mutating call, so it
stays unimplemented until confirmed against the live OC200 (ideally by
capturing the Controller UI's own request via browser devtools when
creating a network by hand once, ironically, purely to reverse-engineer the
payload — not as the delivery mechanism itself).

The collection's `requirements.txt` now points at that fork+branch instead
of PyPI. This also pulled in a real upstream API shape change: `master`
already renamed `SwitchPortOverrides` → `SwitchPortSettings` +
`PortProfileOverrides` (with proper None-means-unchanged semantics, which
actually simplified `omada_switch_port`) and requires Python **3.13**, not
3.11 — installed locally via `uv python install 3.13`.

**Upstream coordination check-back: 2026-09-03**, still tracked, but now
informational only — it doesn't gate anything, since the fork already
unblocks development. If PR #86
(github.com/MarkGodwin/tplink-omada-api/pull/86) gets a reply, the plan is
to reconcile our fork's changes back into a real upstream contribution using
that same branch; if not, the fork keeps serving as the dependency
indefinitely rather than being a blocker either way.

**CI note:** the private fork needs a `FORK_ACCESS_TOKEN` repo secret (a PAT
with read access to `tplink-omada-api-fork`) for GitHub Actions to install
it — the default `GITHUB_TOKEN` can't reach a second private repo. Until
that secret is added, CI will fail on `pip install -r requirements.txt`.
Local development is unaffected (works via `gh`'s own git credential
integration).

## Phases (tracking)

- [x] Phase 1 — Upstream research & recommendation ([report](docs/phase1-upstream-research.md))
- [x] Phase 2 — API capability matrix ([report](docs/phase2-capability-matrix.md))
- [ ] Phase 3 — Upstream contributions (prepared here, submitted by the user —
      no PRs are opened without explicit review/approval per PR)
- [ ] Phase 4 — Ansible collection (in progress: `applewhiteit.omada` at `ansible_collections/applewhiteit/omada/` — 6 modules so far: `omada_site_info`, `omada_device_info`, `omada_firmware_info`, `omada_switch_port`, `omada_device`, `omada_network_info`; now built on our private fork, see "Delivery priority" above)
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
treated as the only supported shape. The full source design document is
customer-confidential and kept outside this repo entirely (not duplicated
here, and not named here either).

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
