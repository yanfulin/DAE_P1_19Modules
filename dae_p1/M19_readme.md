
# DAE P1 — 19 Modules (Free v1)

This package implements **Free v1** scope:
- Always-on 60-minute rolling buffer (metadata-only)
- Command/change event stubs
- Scoped pre-change snapshot references (reference-only)
- Observability check + Opaque risk flag
- One-Button Help (OBH): freeze data + export evidence bundle (no network changes)
- fp-lite offline analysis tool (reference-only)

## Quickstart (demo)
1) Run the demo script to generate a bundle:
   - `python demo_run.py`
2) Run fp-lite offline:
   - `python -m dae_p1.M15_cli_offline_fp <bundle_path>`

## Non-goals
- No remediation guidance
- No automatic rollback
- No admission gate / enforcement
- No optimization / tuning
