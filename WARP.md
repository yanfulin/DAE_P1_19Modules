# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**DAE P1 Free v1** - Detection and Evidence (DAE) system for network incident capture and analysis. This is a metadata-only evidence collection system that captures network incidents without modifying network configuration. The system provides "fp_proof" (fingerprint proof) artifacts for incident analysis, not decisions or remediation.

**Key Philosophy**: "We don't decide what to do. We preserve proof of what happened."

## Core Architecture

### Module System (M01-M19)
The codebase is organized into 19 modules with specific, well-defined responsibilities:

**Data Collection & Storage (M01-M05)**:
- M01 (`M01_windowing.py`) - Time window reference generator (Ws/Wl)
- M02 (`M02_ring_buffer.py`) - Rolling buffer primitive (60 minutes)
- M03 (`M03_metrics_collector.py`) - Metadata metrics collector
- M04 (`M04_change_event_logger.py`) - Command/change event logger
- M05 (`M05_snapshot_manager.py`) - Pre-change snapshot manager (reference-only)

**Analysis & Detection (M06-M08)**:
- M06 (`M06_observability_checker.py`) - Observability check + opaque risk flagging
- M07 (`M07_incident_detector.py`) - Bad-window detector
- M08 (`M08_verdict_classifier.py`) - Verdict classifier (WAN/WiFi/Mesh/DFS/Opaque/Unknown)

**Episode Management & Export (M09-M12)**:
- M09 (`M09_episode_manager.py`) - Episode ID tracking + evidence refs
- M10 (`M10_timeline_builder.py`) - Flattened timeline builder
- M11 (`M11_bundle_exporter.py`) - Evidence bundle JSON exporter
- M12 (`M12_obh_controller.py`) - One-Button Help (OBH) orchestration

**Fingerprint Analysis (M13-M15)**:
- M13 (`M13_fp_lite.py`) - fp-lite computation engine
- M14 (`M14_bundle_reader.py`) - Bundle reader
- M15 (`M15_cli_offline_fp.py`) - Offline fp-lite CLI tool

**Supporting (M16-M19)**:
- M16 (`M16_recognition_engine.py`) - Incident recognition orchestrator
- M17 (`M17_demo_simulator.py`) - Demo incident simulator
- M18 (`M18_app_integration_notes.md`) - App integration documentation
- M19 (`M19_readme.md`) - Package README

### Domain Adapter Pattern

The system uses a **DomainAdapter** pattern (`dae_p1/adapters/base_adapter.py`) to separate domain-specific data collection from core analysis logic:

- **Adapters**: Collect observations only (FWA, DOCSIS, PON, Windows WiFi, Demo)
- **Core**: Provides semantics, analysis, and verdict logic
- **Rule**: Adapters NEVER implement verdict logic, remediation, or control actions

Available adapters in `dae_p1/adapters/`:
- `demo_adapter.py` - Simulated data for testing
- `windows_wifi_adapter.py` - Real Windows WiFi data collection
- `FWA_adapter.py` - Fixed Wireless Access mapping
- `DOCSIS_adapter.py` - Cable modem mapping
- `PON_adapter.py` - Passive Optical Network mapping

### Core Service Architecture

`OBHCoreService` (`dae_p1/core_service.py`) is the main orchestrator:
- Consumes a `DomainAdapter` for data ingress
- Maintains 3 ring buffers (metrics, events, snapshots)
- Runs continuous collection via `tick_once()`
- Generates `EpisodeRecognition` on-demand
- Exports evidence bundles via OBH workflow

## Development Commands

### Running the System

**Start the FastAPI server (development)**:
```pwsh
python server.py
```
Default: `http://localhost:8000`

**Run demo simulator (generates evidence bundle)**:
```pwsh
python demo_run.py
```
Output: `out/evidence_bundle_*.json`

**Run demo with adapter pattern**:
```pwsh
python demo_run_with_adapter.py
```

### Testing & Validation

**Run self-test with JSON schema validation (10 runs)**:
```pwsh
python run_self_test.py --runs 10
```
- Validates against `schemas/EvidenceBundle.schema.json`
- Validates against `schemas/fp_lite_output.schema.json`
- Output: `TEST_REPORT_10RUNS.md`

**Run single offline fp-lite analysis**:
```pwsh
python -m dae_p1.M15_cli_offline_fp <bundle_path>
```
or
```pwsh
python -m dae_p1.M15_cli_offline_fp out/evidence_bundle_*.json
```

**Install verification (closure readiness check)**:
```pwsh
python install_verify_run.py <bundle.json>
```

### Mobile App (React Native/Expo)

The `dae-mobile-app/` directory contains a React Native Expo app for mobile inspection:

**Start Expo dev server**:
```pwsh
cd dae-mobile-app
npm start
```

**Platform-specific commands**:
```pwsh
npm run android  # Android
npm run ios      # iOS
npm run web      # Web browser
```

API endpoint configured in `dae-mobile-app/src/api.js` (update to point to running server)

## API Endpoints (server.py)

**Core Operations**:
- `GET /` - Health check
- `GET /status` - Simple status (ok/unstable/suspected/investigation)
- `GET /metrics` - Latest metric sample
- `GET /metrics/history?limit=20` - Recent metrics history
- `GET /events` - Recent change events
- `GET /snapshots` - Recent snapshots

**Analysis & Recognition**:
- `GET /recognition` - Generate episode recognition
- `GET /install_verify` - Run installation verification (3-minute window)
- `GET /modules` - Status of all 19 modules (detailed inspection)

**Fleet Management** (real + mock):
- `GET /fleet` - Fleet view (1 real device + N mock devices)
- `GET /device/{device_id}` - Device drilldown details

## Working with Evidence Bundles

Evidence bundles are JSON files following the `DAE_P1_Free_v1` spec:
- Generated by M12 OBH Controller
- Stored in `out/` or `bundles/` directories
- Validated against `schemas/EvidenceBundle.schema.json`
- Contain: episode_id, timeline (metrics/events/snapshots), observability result

Example naming: `evidence_bundle_ep-{episode_id}_{timestamp}.json`

## Key Data Structures (M00_common.py)

All core data structures are in `dae_p1/M00_common.py`:
- `MetricSample` - 10-second network metric sample (17 fields: latency, loss, retry, airtime, etc.)
- `ChangeEventCard` - Command/change event stub with origin/trigger/scope
- `PreChangeSnapshot` - Scoped pre-change snapshot reference (sha256 digest)
- `ObservabilityResult` - Observability status + opaque risk flag
- `EpisodeRecognition` - Episode tracking + verdict + evidence refs

## Terminology & Branding

**External naming** (operator-facing):
- Product: `DAE fp_proof`
- Deliverables: Baseline Proof, Incident Proof, Fingerprint Proof
- Promise: "We generate fp_proof, not decisions"

**Internal naming** (engineering):
- Mechanism: `fp_recognition`
- OBH: One-Button Help (freeze + export workflow)

**Important distinctions** (see `FP_PROOF_BRANDING.md`):
- "proof" = referenceable artifact
- NOT "detect" (implies blame)
- NOT "decision" (implies control)

**Opaque Risk**: Observed behavior lacks minimum referenceable provenance for attribution (insufficient observability)

## Schema Documentation

All schemas are documented in `SCHEMA_APPENDIX.md` with:
- Field types, nullable status, units
- Allowed values (enums/open-set)
- Recommended ranges
- Domain-specific field groups (FWA/DOCSIS/PON)

JSON schemas in `schemas/` directory:
- `EvidenceBundle.schema.json`
- `fp_lite_output.schema.json`
- `MetricSample.schema.json`
- `ChangeEventCard.schema.json`
- `PreChangeSnapshot.schema.json`
- `ObservabilityResult.schema.json`
- `InstallVerificationResult.schema.json`

## Capability Mapping

20 operator-facing capabilities (C01-C20) mapped to 19 modules - see `CAPABILITY_MAP.md`:
- C01-C06: Data collection & windowing
- C07-C11: Detection & observability
- C12-C14: Timeline & export
- C15-C17: fp-lite analysis
- C18-C20: Demo, schemas, app integration

Update capability mapping:
```pwsh
python update_capability_map.py
```
Edit official names in `capabilities/capability_dictionary.csv`

## Free v1 Scope Constraints

This is a **reference-only, metadata-only** system:
- ✅ Capture incidents, freeze timelines, export evidence
- ✅ Opaque risk flagging
- ✅ Observability checks
- ❌ NO remediation guidance
- ❌ NO automatic rollback
- ❌ NO network configuration changes
- ❌ NO admission gating/enforcement
- ❌ NO payload inspection

## Dependencies

Python dependencies in `requirements.txt`:
- `jsonschema` - JSON schema validation
- `fastapi` - API server
- `uvicorn` - ASGI server
- `psutil` - System metrics

Install:
```pwsh
pip install -r requirements.txt
```

## File Organization

```
dae_p1/              # Core 19 modules (M01-M19)
  adapters/          # Domain adapters (FWA, DOCSIS, PON, Windows WiFi, Demo)
  M00_common.py      # Shared data structures
  M01-M19...         # Individual modules
  core_service.py    # OBHCoreService orchestrator
  status_helper.py   # Status calculation helpers
  copy_constants.py  # UX copy templates

dae-mobile-app/      # React Native/Expo mobile app
  components/        # UI components
  src/api.js         # API client configuration

schemas/             # JSON schemas for validation
out/                 # Generated evidence bundles
bundles/             # Archived evidence bundles
capabilities/        # Capability mapping configuration
DOCS/                # Technical documentation

server.py            # FastAPI server entry point
demo_run.py          # Demo runner (standalone)
demo_run_with_adapter.py  # Demo with adapter pattern
run_self_test.py     # Self-test runner with validation
install_verify_run.py     # Install verification CLI
```

## Code Patterns

### Adding a New Domain Adapter

1. Extend `dae_p1/adapters/base_adapter.py::DomainAdapter`
2. Implement `collect_metric_sample()` → returns `MetricSample`
3. Implement `collect_change_events_and_snapshots()` → returns `(List[ChangeEventCard], List[PreChangeSnapshot])`
4. Adapters provide observations ONLY - no verdict logic
5. Test with `demo_run_with_adapter.py`

### Running Analysis Flow

1. **Collection**: Core service calls `adapter.collect_metric_sample()` every 1-10 seconds
2. **Buffering**: Data stored in ring buffers (60-minute rolling window)
3. **Detection**: On-demand via `GET /recognition` or `core.generate_recognition()`
4. **Recognition**: M16 orchestrates M06 (observability) → M07 (detection) → M08 (verdict)
5. **Export**: M12 OBH Controller freezes buffers and exports via M11

### Verdict Classification Logic (M08)

Priority order:
1. OPAQUE_RISK (observability insufficient)
2. WAN_UNSTABLE (cellular SINR < 5dB or reattach_count high)
3. MESH_FLAP (mesh_flap_count >= 2)
4. WIFI_CONGESTION (airtime_busy >= 75% or retry >= 18%)
5. DFS_EVENT (DFS-related change detected)
6. UNKNOWN (bad window but no clear classification)

## Current Development Branch

Branch: `feature/refactor-simulation-m17` (refactoring live simulation with M17 logic)

Recent work focused on:
- Installation verifier v2 with system info and thresholds
- M17 simulator integration with live simulation
- iOS app with installer verifier, simulate incident, OBH
- Module inspection capabilities
