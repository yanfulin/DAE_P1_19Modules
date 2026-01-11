# Why fp_proof ≠ detect ≠ decision (Operator & Legal Safe Positioning)

## The confusion to avoid
Operators may assume:
- **detect** ⇒ you must troubleshoot and fix
- **decision** ⇒ you control the network and own liability

## The correct framing
### fp_proof
A proof artifact bundle that preserves what happened and how it changed, using metadata-only evidence:
- **Baseline Proof**: “What did the network look like at delivery time?”
- **Incident Proof**: “What did the last 60 minutes look like around the incident?”
- **Fingerprint Proof**: “What behavioral shape changed before/during/after?”

### Not detect
We do not claim to find root cause or guarantee detection of every failure mode.
We only output **referenceable artifacts** and **minimal recognition labels** (for routing discussion), bound to windows and evidence references.

### Not decision
We do not optimize, tune, steer, or execute remediation actions.
We do not change the network configuration under Free v1.

## The punchline sentence
**We don’t decide what to do. We preserve proof of what happened.**


## Canonical wording
- We don’t decide what to do. We preserve proof of what happened.
- Opaque risk indicates that observed behavior lacks minimum referenceable provenance for attribution.
- OBH performs data-layer capture only: freeze, timeline, export. It never modifies network configuration.
- OBH does not provide legal immunity or liability shielding. It provides referenceable evidence artifacts and attribution boundary signaling.
