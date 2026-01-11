# fp_proof — Operator-Facing Naming (Free v1)

## What to call it (external)
**Product family:** `DAE fp_proof`  
**What it delivers:** proof artifacts, not decisions.

- **Baseline Proof** (install/post-install verification; default 3 minutes)
- **Incident Proof** (One-Button Help snapshot; last 60 minutes)
- **Fingerprint Proof (optional)** (fp-lite before/during/after behavioral fingerprint)

> Internal mechanism name (engineering): **fp_recognition**  
> External deliverable name (operator): **fp_proof**

---

## One-line promise
**We don’t make network decisions. We generate fp_proof.**

---

## Why “proof” (and not detect/decision)
- **detect** implies “we found the problem” and invites blame/expectations to fix.
- **decision** implies control and liability.
- **proof** is a referenceable, replayable artifact that supports incident handling, disputes, and acceptance — without controlling the network.

---

## Free v1 scope reminder
- Metadata-only
- No payload inspection
- No remediation suggestions
- No automatic rollback
- No enforcement/gating


## Canonical wording
- We don’t decide what to do. We preserve proof of what happened.
- Opaque risk indicates that observed behavior lacks minimum referenceable provenance for attribution.
- OBH performs data-layer capture only: freeze, timeline, export. It never modifies network configuration.
- OBH does not provide legal immunity or liability shielding. It provides referenceable evidence artifacts and attribution boundary signaling.
