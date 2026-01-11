# Domain Adapter Pack (FWA / DOCSIS / PON)

These adapters are **mapping-only** examples to connect platform telemetry to the OBH core.

## Contract
Adapters implement:
- `collect_metric_sample() -> MetricSample`
- `collect_change_events_and_snapshots() -> (events, snapshots)`

## Rules
- Adapters MUST NOT implement verdict logic or any remediation/control action.
- Adapters MUST NOT inspect payload content.
- Adapters should emit best-effort provenance hints (origin_hint, change_ref, version_refs).

## Files
- `FWA_adapter.py`
- `DOCSIS_adapter.py`
- `PON_adapter.py`
- `platform_access_stub.py` (replace with real integrations)
