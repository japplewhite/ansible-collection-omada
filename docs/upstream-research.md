# Upstream Ecosystem Research

Last researched August 2026, against GitHub, PyPI, and TP-Link/Home Assistant
sources. Anything not directly verified against a repo/README/PyPI page is
flagged unconfirmed below rather than assumed. This explains why the
collection is built on `tplink-omada-client`, and where that dependency's
gaps come from.

## Recommendation

Build on **`tplink-omada-client`** (PyPI) / **`MarkGodwin/tplink-omada-api`**
(GitHub, MIT) as the primary upstream dependency. It's the most actively
maintained, tested, async, MIT-licensed Python client for the Omada Controller
API — it's what Home Assistant's own core `tplink_omada` integration depends
on — and it has a real external-contribution pipeline (multiple community PRs
merged in the last 60 days).

**Central caveat:** it talks to the **legacy/private controller API**, not
TP-Link's newer official OpenAPI. No Python project combines (a) the official
OpenAPI and (b) standalone pip-installable packaging — see "The OpenAPI gap"
below. Recommended mitigation: design the collection's `module_utils` transport
layer so either backend can be swapped in, and treat an OpenAPI auth/transport
contribution to `tplink-omada-api` as a future upstream candidate.

## Comparison table

| Project | Repo | License | Last activity | Language/paradigm | Python support | API used | Auth method | Read/Write | Tests/CI | External contributions | Packaging |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **tplink-omada-client** | github.com/MarkGodwin/tplink-omada-api | MIT | Pushed 2026-07-05; v1.5.9; 42 PyPI releases, ~monthly cadence | Python, async (aiohttp) | v1.4 needs ≥3.11; current v1.5.x needs ≥3.13 | Legacy/private controller API; maintainer intends eventual OpenAPI migration ("eventually", no timeline confirmed) | Session/cookie login, auto re-login, CSRF handling | Read: sites, devices (AP/GW/switch), firmware info. Write: firmware updates, switch port config, AP LAN port config, gateway WAN connect/disconnect, DHCP reservations (merged), AP radio settings (PR pending), site topology (PR pending) | `tests/` (6 modules), GitHub Actions (`python-package.yml`, `python-publish.yml`), pytest/coverage | 6 open PRs (Aug 2026) from multiple external contributors, several merged in last 60 days, devcontainer for onboarding, no formal CONTRIBUTING.md but active maintainer | `pyproject.toml` (hatchling), `src/` layout, typed (`py.typed`), ships CLI, used by Home Assistant core |
| ghaberek/omada-api | github.com/ghaberek/omada-api | MIT | Pushed 2024-08-17 (~2yr stale) | Python, sync (requests) | Unspecified | Legacy/undocumented API (old docs v2.6.0–v5.9.9) | Session login | Read: site settings, clients, devices. Write: narrow (e.g. LED on/off) | CI badge, minimal depth | 12 open issues/PRs, slowed since 2024 | Minimal setup.py, narrow scope |
| omada-client (ErilovNikita) | github.com/ErilovNikita/omada-client | MIT | Pushed 2026-03-17 | Python | ≥3.11 | Unclear, likely legacy | Unclear | Unconfirmed, small repo (3 stars, 0 issues/PRs) | Unconfirmed | No external engagement | PyPI package exists but appears low-effort (rapid same-day version bumps) |
| ha-omada-open-api (bullitt186) | github.com/bullitt186/ha-omada-open-api | MIT | Pushed 2026-08-21 (most recent reviewed) | Python async, embedded in HA custom_component (not standalone) | ≥3.14 | **Official Omada OpenAPI**, OAuth2 Client Credentials (+ legacy session for Fusion gateways) | OAuth2 Client Credentials (official) | Extensive read + write (PoE, LED, SSID/radio, block/reconnect, firmware, WLAN optimization) | `tests/`, pre-commit, coverage threshold, Makefile | Has CONTRIBUTING.md; young (created 2026-01-22), built "heavily with AI assistance", maintainer disclaims long-term support | Not a standalone library — client code lives inside `custom_components/omada_open_api/`, would need extraction to reuse |
| zachcheatham/ha-omada | github.com/zachcheatham/ha-omada | **No license file** | Pushed 2026-04-15, 255 stars (most popular) | Python, HA custom_component | Unspecified | Legacy/private API, own client | Session login | Extensive read + some write | Unconfirmed test suite, has CHANGELOG | 61 open issues/PRs — largest backlog, triage strain | No standalone library; **no license = redistribution blocker** |
| terraform-provider-omada (home-sol) | github.com/home-sol/terraform-provider-omada | Apache-2.0 | Pushed 2022-07-08, effectively abandoned (3 commits, 0 stars) | Go | n/a | Unconfirmed | Unconfirmed | None visible | None | Not viable even as a design reference |
| tplink-omada-mcp (MiguelTVMS) | github.com/MiguelTVMS/tplink-omada-mcp | MIT | Pushed 2026-04-01 | TypeScript (MCP server) | n/a | Unconfirmed, likely official OpenAPI | Unconfirmed | Read-focused (MCP query tools) | 9 issues/PRs open, young project | Not usable as Python dependency; reference only for OpenAPI endpoint mapping |

## Existing Ansible resources for Omada

None manage Omada **devices or SDN configuration** — all are controller-software installers:

- **`trfore.omada_install`** (github.com/trfore/ansible-role-omada-install) — installs Omada SDN Controller software (CentOS/Debian/Ubuntu). MIT, pushed 2026-06-21, actively maintained, but scoped to install only.
- **`kdpuvvadi/omada-ansible`** — install playbook (not a Galaxy collection). MIT, pushed 2025-08-14, low engagement.
- **`rgl/ansible-collection-tp-link-easy-smart-switch`** — GPL-3.0, targets TP-Link's separate "Easy Smart" SNMP switch line, **not** Omada SDN. Different product family, not reusable; GPL-3.0 would need consideration if ever referenced.

**No naming collision risk** — nothing on Galaxy or GitHub exposes Omada site/device/network config as Ansible modules today.

## The OpenAPI gap

TP-Link's official Omada OpenAPI supports two auth modes: Authorization Code
(interactive) and **Client Credentials** (system-to-system — the relevant mode
for Ansible). Per `bullitt186/ha-omada-open-api`'s README (first-hand, Aug
2026): the **free Omada Cloud/Central "Essentials" tier does not support the
Open API at all** — it needs either a paid Standard cloud subscription or a
self-hosted controller. For a **self-hosted OC200 hardware controller** (our
reference deployment's controller), the relevant constraint is firmware
**≥6.2.10.18** with Open API explicitly enabled under Settings → Platform
Integration — not the cloud-tier restriction. This should be verified against
the actual OC200 before assuming OpenAPI is reachable.

## Caveats / unconfirmed items

1. No library is both official-OpenAPI-based and standalone/pip-installable.
2. `bullitt186`'s project is very young and explicitly disclaims long-term support.
3. MarkGodwin's OpenAPI-migration timeline is unconfirmed ("eventually", no date).
4. Python floor is inconsistent: PyPI metadata for `tplink-omada-client` 1.5.x shows `>=3.13`, while the README says 1.4 needs 3.11 — matters for the collection's supported-Python-versions statement.
5. No coverage-percentage badges found for any project; only presence/absence of test dirs and CI confirmed.
6. `omada-client` (ErilovNikita) feature scope is unconfirmed and deprioritized — thin README, low-effort-looking release pattern.
