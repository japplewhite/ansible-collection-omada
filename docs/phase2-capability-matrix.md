# Phase 2 — API Capability Matrix

**Upstream dependency:** `tplink-omada-client` 1.4.4 (resolved via `pip install
tplink-omada-client` under Python 3.11.15, no version pin — this is the latest
release compatible with 3.11; the newer 1.5.x line requires Python >=3.13,
unavailable on this machine). Source: `MarkGodwin/tplink-omada-api`.

**API surface mapped:** the library's **legacy/private controller API**, per
the Phase 1 decision — not TP-Link's official Omada OpenAPI. Where the
official OpenAPI's actual endpoint list could not be verified (its docs page
at `use1-omada-northbound.tplinkcloud.com/doc.html` is a JS-rendered Swagger
UI that returned no static content to fetch), rows are marked **unclear**
rather than asserting API availability either way.

Date: 2026-08-26.

## Methodology

Three evidence sources, in order of reliability:

1. **Static introspection of the installed package** (`python -m inspect` over
   `tplink_omada_client.omadaclient`, `.omadasiteclient`, `.omadaapiconnection`,
   `.devices`, `.clients`, `.definitions`) — every public class, method
   signature, docstring, and (by reading source directly for dataclasses)
   settings/override object fields. This is authoritative for "does 1.4.4
   actually expose this," since it's the exact installed version, not a
   different git tag.
2. **The package's own CLI** (`tplink_omada_client/cli/command_*.py`) as
   corroborating evidence that a method is not just present but exercised —
   file list: `command_access_point(s).py`, `command_switch(es).py`,
   `command_switch_ports.py`, `command_poe.py`, `command_wan.py`,
   `command_gateway.py`, `command_client.py`/`command_clients.py`/
   `command_known_clients.py`, `command_block_client.py`/
   `command_unblock_client.py`/`command_reconnect_client.py`,
   `command_set_client_name.py`, `command_set_device_led.py`,
   `command_certificate.py`, `command_reboot.py`. Notably **no** CLI command
   exists for VLANs/networks, WLANs/SSIDs, DHCP scopes, guest networks,
   wireless security, statistics/history, events, or config backup — the CLI
   surface exactly matches what `OmadaSiteClient` exposes, so its absence
   here is corroborating, not just an omission.
3. **GitHub issue/PR search** against `MarkGodwin/tplink-omada-api` (`gh api
   search/issues`, all 90 PRs and all 21 non-PR issues reviewed) for direct
   evidence of what's requested, attempted, or explicitly declined by the
   maintainer, e.g. a maintainer comment on Issue #49 (2024-08-15):
   > "The thing that is holding me back from adding lots of features is that
   > TP-Link has produced a new API which we will probably be forced to
   > switch over to using eventually. I don't want to add features that
   > aren't present in the new Open API..."

   This is important context for Phase 3: the maintainer is *already*
   reluctant to add legacy-API-only features, which affects which PRs are
   likely to be accepted.

## Matrix

| Capability | Classification | Upstream method(s)/class | Evidence | Notes |
|---|---|---|---|---|
| Controller authentication | **Fully supported upstream** | `OmadaClient.login()`, `OmadaApiConnection.login()` | Introspection; every CLI command depends on it | Session/cookie login to the legacy API, not OAuth2 client-credentials (the official OpenAPI's auth model) |
| Sites | **Fully supported upstream** | `OmadaClient.get_sites()`, `get_site_client(site)` | Introspection | Read/discovery only — no site create/delete, which matches automating *existing* sites, the collection's actual need |
| Gateways | **Fully supported upstream** | `OmadaSiteClient.get_gateway(s)`, `get_gateway_port()`, `set_gateway_port_settings()`, `set_gateway_wan_port_connect_state()` | Introspection; `command_gateway.py`, `command_wan.py` | Read + write (port PoE/duplex/speed via `GatewayPortSettings`, WAN connect/disconnect) |
| Switches | **Fully supported upstream** | `get_switch(es)`, `get_switch_port(s)`, `update_switch_port()`, `get_switch_port_overrides()` | Introspection; `command_switch(es).py`, `command_switch_ports.py` | Whole-switch global settings (e.g. STP mode site-wide) not modeled — per-port config is |
| Access points | **Partially supported upstream** | `get_access_point(s)`, `get_access_point_port()`, `update_access_point_port()` (LAN port PoE/VLAN via `AccessPointPortSettings`) | Introspection; `command_access_point(s).py` | Radio settings (channel/power/band) **not implemented** — open PR #90 "Add access point radio settings support" (created 2026-07-31, still open) confirms this gap and that it's being actively worked |
| Clients | **Fully supported upstream** | `get_client()`, `get_connected_clients()`, `get_known_clients()`, `update_client()`, `block_client()`, `unblock_client()`, `reconnect_client()` | Introspection; `command_client(s).py`, `command_known_clients.py`, `command_block_client.py`, `command_unblock_client.py`, `command_reconnect_client.py`, `command_set_client_name.py` | Rich — read, rename, block/unblock, reconnect, fixed-IP, AP lock (`lock_to_aps`) |
| VLANs / networks | **Available via Omada API but not implemented upstream** | none (`SwitchPortOverrides`/`AccessPointPortSettings` only carry a numeric `vlan_id` to *tag a port*, no VLAN/network object CRUD) | PR #86 "feat: add network management data models" (2026-07-24, **closed without merging**); open Issue #47 "suggestion extract VLANs and LAG?" | The attempted-but-abandoned PR is evidence the underlying controller data exists and was reachable, just never shipped — not a confirmation of the *official* OpenAPI's schema, which is unverified |
| DHCP configuration | **Partially supported upstream** | `update_client(mac, OmadaClientSettings(fixed_address=OmadaClientFixedAddress(network_id, ip_address)))` | Introspection (dataclass fields read from source); maintainer confirms on Issue #49: `omada client [mac] --fixed-ip [ip] --network [network_id]` works today | Per-client fixed-IP reservation: full read/write. Bulk-listing all reservations and DHCP *scope* config (pool ranges, lease time): not supported — open PR #88 "feat: add DHCP reservation management" (2026-07-28) targets exactly this gap |
| SSIDs / WLANs | **Unclear and requiring testing** | none for create/config; `OmadaWirelessClient.ssid` is read-only, incidental to client data | Introspection; no `command_ssid*`/`command_wlan*` CLI file exists | No evidence found either way in the official OpenAPI (docs page unreachable) — do not assume "not exposed" |
| Wireless security | **Unclear and requiring testing** | none found | Introspection | Same caveat — official docs unreachable |
| Guest networks | **Unclear and requiring testing** | none for config; `is_guest` is a read-only client flag | Introspection | Same caveat |
| Switch port profiles | **Partially supported upstream** | `get_port_profile(id)`, `get_port_profiles()`; applied to a port via `update_switch_port(profile_id=...)` | Introspection; `command_switch_ports.py` | Read existing profiles and apply them to ports — no profile create/edit/delete |
| Individual switch port configuration | **Fully supported upstream** | `get_switch_port(s)`, `update_switch_port()`, `get_switch_port_overrides()`, `SwitchPortOverrides` (PoE, 802.1x, duplex, link speed, LLDP-MED, loopback detect, spanning tree, port isolation) | Introspection; `command_switch_ports.py` | One caveat in the class docstring: "we have to specify overrides for everything... you may need to initialise all of these parameters to avoid overwriting settings" — matters for Phase 4 idempotency design |
| PoE state | **Fully supported upstream** | Read: `OmadaSwitchPortStatus.poe_active`/`poe_power`, `OmadaGatewayPortStatus`. Write: `SwitchPortOverrides.enable_poe`, `AccessPointPortSettings.enable_poe`, `GatewayPortSettings.enable_poe` | Introspection; `command_poe.py` | Covers switches, gateway ports, and AP LAN ports |
| Link state / speed | **Fully supported upstream** | `OmadaSwitchPortStatus`/`OmadaGatewayPortStatus`: `link_speed`, `link_status`, `link_duplex`(gateway); `SwitchPortOverrides.duplex`/`link_speed` for write on switch ports | Introspection | Read on all port types; write (forcing speed/duplex) only modeled for switch ports |
| Device adoption | **Partially supported upstream** | none for adopt/forget/reject actions; `OmadaDevice.status`/`status_category` (via `DeviceStatus`/`DeviceStatusCategory` enums) give read-only status | Introspection | No adopt/forget/reject write method exists anywhere in `OmadaSiteClient` — status visibility only |
| Device naming | **Unclear and requiring testing** | none — `OmadaClientSettings.name` renames a *client*, not a device | Introspection | Easy to conflate with client renaming, which *is* supported; renaming an AP/switch/gateway itself was not found and isn't confirmed absent from the official API either |
| Firmware status | **Fully supported upstream** | `get_firmware_details()`, `start_firmware_upgrade()`, `OmadaFirmwareUpdate` (current/latest version, release notes), `OmadaListDevice.need_upgrade`/`fw_download` | Introspection; PR #72 "Add basic controller firmware update information" (merged), PR #83 "Expose software controller update info" (merged) | Device firmware fully covered; controller-software update info also covered per merged PRs |
| WAN status | **Fully supported upstream** | `OmadaGatewayPortStatus` (`wan_connected`, `ipv6_wan_connected`, `wan_ip_address`, `wan_ipv6_address`, `wan_protocol`, `bytes_rx`/`bytes_tx`), `set_gateway_wan_port_connect_state()` | Introspection; `command_wan.py` | Status + connect/disconnect control. Byte counters are cumulative, not a bandwidth-utilization time series — see Traffic statistics below |
| Traffic statistics | **Partially supported upstream** | `bytes_rx`/`bytes_tx` on switch/gateway port status; `traffic_up`/`traffic_down` (cumulative) and `activity` (realtime Byte/s) on client objects | Introspection | Current/cumulative counters only — no historical time-series or aggregated statistics endpoint found anywhere in the client |
| AP client counts | **Partially supported upstream** | No direct `client_count` field on `OmadaAccessPoint` — derivable by calling `get_connected_clients()`/`get_known_clients()` and filtering by `ap_mac` | Introspection | Achievable today, just requires a client-side aggregation, not a single API call |
| AP throughput | **Unclear and requiring testing** | none — no port-status-equivalent object exists for AP LAN/uplink ports with byte counters (unlike switches and gateways) | Introspection | Could be approximated by summing connected clients' `traffic_up`/`traffic_down`, but that's client-side estimation, not a real AP-uplink counter |
| Channel utilization | **Unclear and requiring testing** | none — `OmadaWirelessClient.channel` is which channel a client is *on*, not a utilization/airtime percentage | Introspection | Fairly confident this isn't exposed by the legacy client, but the official OpenAPI wasn't reachable to confirm either way, so not marked "not exposed" |
| Event / alert retrieval | **Unclear and requiring testing** | none found | Introspection; no `command_event*`/`command_alert*`/`command_log*` CLI file | Official docs unreachable |
| Configuration backup | **Unclear and requiring testing** | none found | Introspection; no `command_backup*`/`command_export*` CLI file | Official docs unreachable |

## Bonus capabilities found (outside the original list)

- Client block / unblock / reconnect (`block_client`, `unblock_client`, `reconnect_client`)
- Device LED control (`set_led_setting`)
- Controller certificate upload (`set_certificate`)
- Controller reboot (`reboot`)
- Client-to-AP locking (`OmadaClientSettings.lock_to_aps`)
- Controller/software update info — merged via PR #72 and #83

## Open questions (unclear rows, for Phase 6 live-testing or renewed doc access)

SSIDs/WLANs, wireless security, guest networks, device naming (device-level,
not client), AP throughput, channel utilization, event/alert retrieval, and
configuration backup all need one of: (a) a reachable rendering of TP-Link's
official OpenAPI docs (the Swagger UI needs JS execution / possibly
controller-side auth — a browser-based check against the actual OC200 in
Phase 6 may resolve this directly), or (b) live testing against the reference
OC200 controller once it's staged.

## Feeds into

- **Phase 3** (upstream PRs) should prioritize the two already-open,
  already-scoped gaps found here: **PR #90** (AP radio settings) and **PR
  #88** (DHCP reservation management) — reviewing/contributing to those
  directly is more valuable than opening competing new PRs. **VLANs/networks**
  is the next-highest-value gap (no open PR currently targets it, since #86
  was closed unmerged) but the maintainer's stated OpenAPI hesitancy (Issue
  #49) means a legacy-API-only VLAN PR may face resistance — worth raising
  the question in a scoping issue before writing code.
- **Phase 4** (Ansible module scope) should be bounded to the "Fully
  supported" and "Partially supported" rows: controller auth, sites,
  gateways, switches, access points (LAN ports only, not radio), clients,
  DHCP (per-client reservations only), switch port profiles (read + apply),
  individual switch port config, PoE, link state, device adoption (status
  only), firmware status, WAN status, traffic statistics (current counters),
  AP client counts (via aggregation). "Unclear" rows should not become
  modules until resolved.
