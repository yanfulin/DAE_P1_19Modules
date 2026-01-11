# Capability Map — DAE P1 Free v1
This document maps **19 software modules (M01–M19)** to **20 operator-facing capabilities (C01–C20)**.
Free v1 scope: Detect + Recognition + Evidence Freeze/Export + Opaque Risk Flag + fp-lite reference.
No remediation, no network control, no optimization.

## 20 Capabilities
- **C01** — Always-on Rolling Buffer (60 min) — metrics sampling (10s)
- **C02** — Always-on Rolling Buffer — event cards (command/change stubs)
- **C03** — Command/Change Event Capture with origin/trigger/scope stubs
- **C04** — Scoped Pre-change Snapshot References (reference-only, no rollback)
- **C05** — Version References capture (fw/driver/agent)
- **C06** — Window Reference generation (Ws/Wl)
- **C07** — Bad-window Detection (multi-signal)
- **C08** — Minimal Verdict Classification (WAN/WiFi/Mesh/DFS/Opaque/Unknown)
- **C09** — Episode Tracking (episode_id, worst window, evidence refs)
- **C10** — Observability Check (minimum refs present?)
- **C11** — Opaque Risk Flagging (observability insufficient → opaque_risk)
- **C12** — Flattened Incident Timeline generation (metrics + events + snapshots)
- **C13** — OBH: Freeze data (buffer snapshot) + episode binding
- **C14** — Evidence Bundle Export (JSON)
- **C15** — fp-lite Computation (before/during/after + BOSD label, reference-only)
- **C16** — Bundle Reader (load)
- **C17** — Offline fp-lite CLI tool
- **C18** — Demo Simulator + Demo Runner (no hardware)
- **C19** — Schema Appendix + JSON Schemas (fields/nullable/units/range)
- **C20** — App Integration Guidance (offline/app execution model)

## Capability → Module Mapping
| Capability | Description | Modules/Artifacts |
|---|---|---|
| C01 | Always-on Rolling Buffer (60 min) — metrics sampling (10s) | M02, M03, M01 |
| C02 | Always-on Rolling Buffer — event cards (command/change stubs) | M02, M04, M01 |
| C03 | Command/Change Event Capture with origin/trigger/scope stubs | M04, M01 |
| C04 | Scoped Pre-change Snapshot References (reference-only, no rollback) | M05 |
| C05 | Version References capture (fw/driver/agent) | M00, M04 |
| C06 | Window Reference generation (Ws/Wl) | M01 |
| C07 | Bad-window Detection (multi-signal) | M07 |
| C08 | Minimal Verdict Classification (WAN/WiFi/Mesh/DFS/Opaque/Unknown) | M08 |
| C09 | Episode Tracking (episode_id, worst window, evidence refs) | M09, M16 |
| C10 | Observability Check (minimum refs present?) | M06 |
| C11 | Opaque Risk Flagging (observability insufficient → opaque_risk) | M06, M16 |
| C12 | Flattened Incident Timeline generation (metrics + events + snapshots) | M10 |
| C13 | OBH: Freeze data (buffer snapshot) + episode binding | M12, M09, M16 |
| C14 | Evidence Bundle Export (JSON) | M11, M12 |
| C15 | fp-lite Computation (before/during/after + BOSD label, reference-only) | M13 |
| C16 | Bundle Reader (load) | M14 |
| C17 | Offline fp-lite CLI tool | M15 |
| C18 | Demo Simulator + Demo Runner (no hardware) | M17, demo_run.py |
| C19 | Schema Appendix + JSON Schemas (fields/nullable/units/range) | SCHEMA_APPENDIX.md, schemas/*.schema.json |
| C20 | App Integration Guidance (offline/app execution model) | M18 |

## 19 Modules (M01–M19)

# Module Map (M1–M19)

| ID | File | Purpose |
|---:|---|---|
| M01 | M01_windowing.py | Window ref generator (Ws/Wl) |
| M02 | M02_ring_buffer.py | Ring buffer primitive |
| M03 | M03_metrics_collector.py | Metadata metrics collector (adapter stub) |
| M04 | M04_change_event_logger.py | Command/change event logger (stub) |
| M05 | M05_snapshot_manager.py | Scoped pre-change snapshot (reference-only) |
| M06 | M06_observability_checker.py | Observability check + opaque risk |
| M07 | M07_incident_detector.py | Bad-window detector |
| M08 | M08_verdict_classifier.py | Minimal verdict classifier |
| M09 | M09_episode_manager.py | Episode id + evidence refs |
| M10 | M10_timeline_builder.py | Flattened timeline builder |
| M11 | M11_bundle_exporter.py | Evidence bundle exporter |
| M12 | M12_obh_controller.py | OBH orchestration (freeze/export) |
| M13 | M13_fp_lite.py | fp-lite computation |
| M14 | M14_bundle_reader.py | Bundle reader |
| M15 | M15_cli_offline_fp.py | Offline fp-lite CLI |
| M16 | M16_recognition_engine.py | Incident recognition engine |
| M17 | M17_demo_simulator.py | Demo incident simulator |
| M18 | M18_app_integration_notes.md | App integration notes |
| M19 | M19_readme.md | Package README |
