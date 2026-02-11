# CLAUDE.md

## Project Overview

**DAE P1 Free v1 (DAE fp_proof)** — Network incident detection, evidence capture, and proof generation system.

- **Backend**: Python 3 / FastAPI
- **Mobile**: React Native / Expo (`dae-mobile-app/`)
- **Philosophy**: "We don't decide what to do. We preserve proof of what happened."

This is a **metadata-only**, **detect-only**, **evidence-focused** system. It does NOT inspect payloads, perform remediation, modify network configuration, or provide liability shielding. It preserves referenceable proof of what happened.

---

## Quick Reference Commands

### Python Backend

```bash
# Setup
python -m venv venv && source venv/bin/activate  # Linux/Mac
python -m venv venv && .\venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Start server (http://localhost:8000)
uvicorn server:app --reload

# Run self-test suite (schema validation, 10 runs)
python run_self_test.py --runs 10

# Run unit tests
python -m pytest tests/ -v

# Run individual test files
python -m pytest tests/test_privacy_framework.py -v
python -m pytest tests/test_fp_lite_v13.py -v
python -m pytest tests/test_proof_v14.py -v

# Generate demo bundle
python demo_run.py

# Offline fp-lite analysis
python -m dae_p1.M15_cli_offline_fp out/evidence_bundle_*.json

# Install verification
python install_verify_run.py <bundle.json>

# Regenerate capability map (after editing capability_dictionary.csv)
python update_capability_map.py

# API verification
python verify_api.py
```

### Mobile App

```bash
cd dae-mobile-app
npm install
npx expo start            # Dev server
npx expo start --ios      # iOS
npx expo start --android  # Android
npx expo start --web      # Web
```

---

## Directory Structure

```
├── dae_p1/                  # Core Python modules (M00-M22)
│   ├── M00_common.py        # Shared data types (MetricSample, ChangeEventCard, etc.)
│   ├── M01-M22_*.py         # 19 modules: windowing, detection, export, etc.
│   ├── core_service.py      # OBHCoreService — main orchestrator
│   ├── adapters/            # Domain adapters (observation collection only)
│   │   ├── base_adapter.py  # DomainAdapter abstract base class
│   │   ├── demo_adapter.py  # Simulated data (fallback for non-Windows)
│   │   └── windows_wifi_adapter.py  # Real Windows WiFi metrics
│   └── ...
├── dae-mobile-app/          # React Native (Expo) mobile app
├── schemas/                 # JSON schema definitions for all data types
├── capabilities/            # Capability mapping (C01-C20 → M01-M19)
├── configs/                 # Configuration files (privacy_v14.yaml)
├── tests/                   # Test suite
├── DOCS/                    # Technical documentation
├── server.py                # FastAPI server entry point
├── run_self_test.py         # Self-test runner
├── demo_run.py              # Demo incident simulation
└── requirements.txt         # Python dependencies
```

---

## Architecture & Key Patterns

### Core vs. Adapters

- **Core** (`dae_p1/core_service.py`, modules M01-M22): Business logic, verdicts, analysis
- **Adapters** (`dae_p1/adapters/`): Provide raw observations ONLY — no verdict logic, no remediation, no payload inspection

Adapter contract (`base_adapter.py`):
- `collect_metric_sample() -> MetricSample`
- `collect_change_events_and_snapshots() -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]`

### Data Flow (6 phases)

1. **Initialization**: Adapter → Core Service → Ring Buffers
2. **Collection**: Adapter → Metrics/Events/Snapshots → Ring Buffers (every 1-10 sec)
3. **Detection**: Detector (M07) → Classifier (M08) → Evidence Flags
4. **Recognition**: Metrics + Events → Recognition Engine (M16) → Episode
5. **Export (OBH)**: Buffers → Timeline → Bundle Exporter → JSON
6. **Analysis (fp-lite)**: Bundle → fp-lite (M13) → Pattern label + BOSD

### Ring Buffer Pattern

- 60-minute rolling buffer (360 samples @ 10s intervals) for metrics
- 500-item buffers for events and snapshots
- Automatic FIFO eviction, constant memory footprint

### Windowing

- **Ws** (short): 10-second buckets, format `Ws:<epoch>`
- **Wl** (long): 60-second buckets, format `Wl:<epoch>`

### Verdict Types

`WAN_UNSTABLE | WIFI_CONGESTION | MESH_FLAP | DFS_EVENT | OPAQUE_RISK | UNKNOWN`

---

## Code Style

### Python

- **PEP 8** compliant, 4-space indentation
- **Type hints** strongly encouraged on function signatures
- **Async/await** extensively used with FastAPI
- **Logging**: Use `logging` module, never `print()` in production
- **Imports**: Standard library → Third-party → Local (absolute imports preferred)

### Naming

- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`

### Error Handling

- Handle specific exceptions where possible
- In background loops: catch generic `Exception` to prevent crash, but always log
- Use `logging.getLogger(__name__)` per module

---

## Key API Endpoints (server.py)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health check |
| GET | `/metrics` | Latest metric sample |
| GET | `/recognition` | Incident analysis |
| GET | `/install_verify` | Installation readiness |
| GET | `/fleet` | Device list |
| GET | `/device/{id}` | Device details |
| GET | `/device/local` | Local device info |
| GET | `/device/local/proof` | Proof card summary |
| POST | `/obh_export` | Export evidence bundle |

---

## Module Map (M00-M22)

| Module | Purpose |
|--------|---------|
| M00_common | Shared data types (MetricSample, ChangeEventCard, Verdict, etc.) |
| M01_windowing | Window reference generation (Ws/Wl) |
| M02_ring_buffer | FIFO ring buffer primitive |
| M03_metrics_collector | Metadata metrics collector |
| M04_change_event_logger | Command/change event logging |
| M05_snapshot_manager | Pre-change snapshot references |
| M06_observability_checker | Observability status & opaque risk |
| M07_incident_detector | Bad-window detection (multi-signal) |
| M08_verdict_classifier | Verdict assignment |
| M09_episode_manager | Episode lifecycle tracking |
| M10_timeline_builder | Flattened incident timeline |
| M11_bundle_exporter | Evidence bundle JSON export |
| M12_obh_controller | OBH orchestrator (freeze + export) |
| M13_fp_lite | fp-lite fingerprint analysis (before/during/after) |
| M13A_privacy_framework | Privacy governance, egress gates, redaction |
| M14_bundle_reader | Evidence bundle reader/loader |
| M15_cli_offline_fp | Offline fp-lite CLI tool |
| M16_recognition_engine | Incident recognition orchestrator |
| M17_demo_simulator | Demo synthetic data generator |
| M20_install_verify | Installation verification (3-min window) |
| M21_manifest_manager | Manifest metadata management |
| M22_demo_v14_simulator | V1.4 demo simulator |

---

## Design Constraints (Non-Goals)

These are intentional boundaries — do NOT add code that violates them:

- **No payload inspection** — metadata and references only
- **No remediation or rollback** — never modify network configuration
- **No optimization suggestions** — detect and preserve, not fix
- **No liability shielding claims** — provide evidence artifacts, not legal immunity
- **No admission gating/enforcement** — no network control actions
- Adapters provide observations only; all verdict logic stays in core

---

## Naming Conventions (Branding)

- **External** (operator-facing): "DAE fp_proof" / "fp_proof artifacts"
- **Internal** (engineering): "fp_recognition" / "OBH" (One-Button Help)
- **Evidence types**: "Baseline Proof", "Incident Proof", "Fingerprint Proof"
- See `FP_PROOF_BRANDING.md` and `UNIFIED_COPY_GUIDE.md` for legal-safe wording

---

## Dependencies

### Python (`requirements.txt`)

- `jsonschema` — JSON schema validation
- `fastapi` — Async web framework
- `uvicorn` — ASGI server
- `psutil` — System metrics collection

### Mobile (`dae-mobile-app/package.json`)

- `expo ~54.0.31`, `react 19.1.0`, `react-native 0.81.5`
- `react-native-svg`, `react-native-web`, `expo-updates`

---

## Testing

- **Self-test**: `python run_self_test.py --runs 10` — validates bundles against JSON schemas in `schemas/`
- **Unit tests**: `python -m pytest tests/ -v` — privacy framework, fp-lite v1.3, proof v1.4
- **Demo verification**: `python demo_run.py` then `python -m dae_p1.M15_cli_offline_fp out/evidence_bundle_*.json`
- **API verification**: `python verify_api.py`
- No automated CI/CD — testing is manual via scripts

---

## Key Documentation

| File | Content |
|------|---------|
| `DOCS/system_workflow.md` | Complete architecture, data flows, state diagrams |
| `DOCS/module_interfaces.md` | Core data structures & module APIs |
| `DOCS/custom_parameters.md` | Configuration parameters |
| `DOCS/PRD_SUMMARY.md` | Product requirements |
| `CAPABILITY_MAP.md` | 20 capabilities → 19 modules mapping |
| `SCHEMA_APPENDIX.md` | Field definitions for all schemas |
| `FP_PROOF_BRANDING.md` | Operator-facing naming standards |
| `UNIFIED_COPY_GUIDE.md` | Legal-safe wording guidelines |
| `dae_p1/adapters/README.md` | Adapter contract & implementation guide |
