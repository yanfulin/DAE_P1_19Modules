# Capability Dictionary — Official Alignment Template (C01–C20)

Use this file to align the 20 capabilities to your **official** naming/definitions.
This project provides a **Free v1** implementation; capabilities are mapped to modules (M01–M19).

## How to use
1) Replace the `Official Capability Name` and `Official Definition` columns below with your official dictionary.
2) Keep the `Implementation Notes` and `Mapped Modules` columns as-is (or refine).
3) If you want the mapping to be machine-readable, also fill `capability_dictionary.csv`.

> Free v1 scope: Detect + Recognition + Evidence Freeze/Export + Opaque Risk Flag + fp-lite reference.
> No remediation, no network control, no optimization, no auto rollback.

---

## Official Capability Table

| Cap ID | Official Capability Name | Official Definition (Operator-facing) | Minimal Inputs (metadata-only) | Outputs | Mapped Modules (Mxx) | Implementation Notes |
|---:|---|---|---|---|---|---|
| C01 | (replace) | (replace) | rolling buffer metrics | evidence bundle | M01,M02,M03 | 60-min rolling buffer, 10s sampling |
| C02 | (replace) | (replace) | change events | change timeline | M04,M10 | command/change stubs (no payload) |
| C03 | (replace) | (replace) | pre-change snapshot | snapshot refs | M05 | scoped pre-change, reference-only |
| C04 | (replace) | (replace) | change event card | observability | M06 | missing refs → opaque_risk |
| C05 | (replace) | (replace) | metrics sample | bad window flags | M07 | 2+ signals threshold |
| C06 | (replace) | (replace) | badness flags | verdict | M08 | minimal verdict classifier |
| C07 | (replace) | (replace) | worst window | episode_id | M09,M16 | episode recognition |
| C08 | (replace) | (replace) | 60-min buffers | timeline | M10 | flattened timeline |
| C09 | (replace) | (replace) | timeline + recognition | bundle export | M11,M12 | OBH export (no network change) |
| C10 | (replace) | (replace) | bundle | fp-lite | M13,M14,M15 | offline/app fp-lite |
| C11 | (replace) | (replace) | - | app integration notes | M18 | guidance only |
| C12 | (replace) | (replace) | - | demo simulator | M17 | demo-only |
| C13 | (replace) | (replace) | schema | validation | schemas/* | JSON schema + appendix |
| C14 | (replace) | (replace) | module map | traceability | MODULE_MAP.md | documentation |
| C15 | (replace) | (replace) | capability map | traceability | CAPABILITY_MAP.md | documentation |
| C16 | (replace) | (replace) | verdict + confidence | operator UX | M08,M16 | reference-only |
| C17 | (replace) | (replace) | opaque_risk | operator reflection | M06,M16 | “Observability insufficient → Opaque risk” |
| C18 | (replace) | (replace) | snapshots | incident comparison | M05,M10 | before/after refs |
| C19 | (replace) | (replace) | bundle export | vendor dispute pack | M12 | easy sharing |
| C20 | (replace) | (replace) | fp-lite output | RCA attachment | M13 | reference-only |

