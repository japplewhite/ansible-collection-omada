# Draft comment — for review before posting

**Where:** https://github.com/MarkGodwin/tplink-omada-api/pull/86 (closed PR, comment thread still open)
**Posting as:** your GitHub account (japplewhite) — not posted yet, this is a draft for your review.

---

Hi @titosemi — thanks for #88, that's a clean addition.

I'm building an Ansible collection on top of `tplink-omada-client` and mapped
the library's current API surface against what I need to automate. VLAN/LAN
network listing is the one real gap I found (`update_switch_port()` can tag a
port with a numeric VLAN ID, but there's no way to list/read the actual
network/VLAN definitions themselves).

This PR's description mentions "VLAN listing, ACL listing, etc." as planned
follow-ups to the `networks.py` foundation. Before I start writing anything in
that area myself — is that still active on your side? Don't want to duplicate
effort or step on a PR you're already partway through. Happy to help test
(and eventually contribute) once I have a live controller in place to verify
against, if that's useful.

---

## Why this venue and framing

- Posted on #86 rather than the open Issue #47, because #86 is *titosemi's own*
  stated roadmap note, and #47 is a 2024 thread about port-profile VLAN
  tagging (already covered by `get_port_profiles()`), not top-level
  network/VLAN definitions — different question, different asker, mostly
  already resolved.
- Deliberately does not promise a specific PR or timeline — we don't have a
  live OC200 to test against yet (that's Phase 6), so committing to code now
  would be premature.
- Deliberately does not mention the client/customer name or specifics —
  scoped to the technical question only.
