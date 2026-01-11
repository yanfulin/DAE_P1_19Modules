# DAE Free v1 — Opaque-Aware Incident Capture & fp-Lite Reference

See dae_p1/M19_readme.md


## Capability Mapping
- See `CAPABILITY_MAP.md` for 20 capabilities mapped to the 19 modules.

## Official 20-Capability Alignment (Template)
To align C01–C20 to your official feature dictionary:
- Edit: `capabilities/capability_dictionary.csv` (fill `official_name` and `official_definition`)
- Optionally review: `capabilities/OFFICIAL_CAPABILITY_ALIGNMENT_TEMPLATE.md`
- Run: `python update_capability_map.py` to regenerate `CAPABILITY_MAP.md`


## Install Verification (Default 3 minutes):
- Module: `dae_p1/M20_install_verify.py`
- Default verify window: 180 seconds (3 minutes)
- CLI helper: `install_verify_run.py <bundle.json>`


## Operator-facing naming
- External name: **DAE fp_proof** (artifacts)
- Internal mechanism: **fp_recognition** (pipeline)
- See: FP_PROOF_BRANDING.md and WHY_FP_PROOF_NOT_DETECT.md


## Canonical wording
- We don’t decide what to do. We preserve proof of what happened.
- Opaque risk indicates that observed behavior lacks minimum referenceable provenance for attribution.
- OBH performs data-layer capture only: freeze, timeline, export. It never modifies network configuration.
- OBH does not provide legal immunity or liability shielding. It provides referenceable evidence artifacts and attribution boundary signaling.


## Self test (10 runs) with JSON Schema validation
- Run: `python run_self_test.py --runs 10`
- Validates: EvidenceBundle.schema.json and fp_lite_output.schema.json
- Output: TEST_REPORT_10RUNS.md


## Domain Adapter Pack
- See: `dae_p1/adapters/` for FWA / DOCSIS / PON mapping-only adapters.


## Adapter injection (v2.2)
- Core runner: `dae_p1/core_service.py` (OBHCoreService)
- Demo runner: `demo_run_with_adapter.py`
- Domain adapters: `dae_p1/adapters/`
- Rule: adapters provide observations only; core provides semantics.
