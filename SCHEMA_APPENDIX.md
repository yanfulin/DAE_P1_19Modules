
# Schema Appendix — DAE P1 Free v1 (Metadata-Only)

This appendix defines the **Free v1** schemas with:
- **nullable**: whether the field may be missing/null
- **allowed values**: enums / open-set notes
- **units**: ms, %, dB, etc.
- **range**: recommended operating ranges (non-binding; open-set)

> NOTE: Free v1 is **reference-only**. No payload, no remediation actions, no auto rollback.

---

## A) MetricSample (10s sample)

| Field | Type | Nullable | Units | Range (recommended) | Notes |
|---|---:|:---:|---|---|---|
| ts | number | no | seconds (epoch) | >=0 | sample timestamp |
| window_ref | string | no | - | - | format: `Ws:<bucket_epoch>` |
| latency_p95_ms | number | yes | ms | 0–5000 | p95 latency to gateway/target |
| loss_pct | number | yes | % | 0–100 | packet loss percentage |
| retry_pct | number | yes | % | 0–100 | Wi-Fi retry percentage |
| airtime_busy_pct | number | yes | % | 0–100 | airtime busy / channel utilization |
| roam_count | integer | yes | count | >=0 | roaming events within sample window |
| mesh_flap_count | integer | yes | count | >=0 | parent/backhaul flap count within sample window |
| wan_sinr_db | number | yes | dB | -20–40 | cellular SINR (FWA scenarios) |
| wan_rsrp_dbm | number | yes | dBm | -140–-40 | cellular RSRP |
| wan_reattach_count | integer | yes | count | >=0 | cellular reattach/reselection count |

---

## B) ChangeEventCard (Command/Change Stub)

| Field | Type | Nullable | Allowed Values | Notes |
|---|---:|:---:|---|---|
| event_time | number | no | - | epoch seconds |
| event_type | string | no | open set (examples below) | e.g., `config_change`, `policy_update`, `reboot`, `dfs_switch`, `radio_reset`, `unknown` |
| origin_hint | string | yes | `cloud`, `acs`, `local`, `app`, `firmware`, `driver`, `onchip`, `unknown` | best-effort |
| trigger | string | yes | `manual`, `scheduled`, `auto`, `watchdog`, `unknown` | |
| target_scope | string | yes | `wan`, `wlan`, `mesh`, `system`, `unknown` | |
| change_ref | string | yes | - | optional reference (policy/config id/hash) |
| version_refs.fw | string | yes | - | firmware version string |
| version_refs.driver | string | yes | - | driver version string |
| version_refs.agent | string | yes | - | agent version string |
| window_ref | string | yes | - | `Ws:<bucket_epoch>` |

---

## C) PreChangeSnapshot (Reference-only, scoped)

| Field | Type | Nullable | Notes |
|---|---:|:---:|---|
| snapshot_ref_id | string | no | stable reference id e.g., `snap-xxxx` |
| snapshot_scope | string | no | `wan` / `wlan` / `mesh` / `system` |
| capture_time | number | no | epoch seconds |
| snapshot_digest | string | no | sha256 digest of snapshot representation |
| readable_fields | object | yes | **scoped** readable subset only (no full configs) |

---

## D) ObservabilityResult (Opaque Risk)

| Field | Type | Nullable | Allowed Values | Notes |
|---|---:|:---:|---|---|
| observability_status | string | no | `SUFFICIENT` / `INSUFFICIENT` | |
| opaque_risk | boolean | no | true/false | |
| missing_refs | array[string] | yes | open set | e.g., `change_ref`, `origin_hint`, `version_refs`, `no_change_event_detected` |
| origin_hint | string | yes | same as origin_hint | |

---

## E) EpisodeRecognition (Recognition output)

| Field | Type | Nullable | Notes |
|---|---:|:---:|---|
| episode_id | string | no | e.g., `ep-xxxxxxxxxxxx` |
| episode_start | number | no | epoch seconds |
| worst_window_ref | string | no | `Wl:<bucket_epoch>` |
| primary_verdict | string | no | `WAN_UNSTABLE` / `WIFI_CONGESTION` / `MESH_FLAP` / `DFS_EVENT` / `OPAQUE_RISK` / `UNKNOWN` |
| confidence | number | no | 0–1 |
| evidence_refs | array[string] | yes | references to windows/flags |
| observability | object | no | ObservabilityResult |

---

## F) Evidence Bundle (OBH export)

| Field | Type | Nullable | Notes |
|---|---:|:---:|---|
| spec | string | no | `DAE_P1_Free_v1` |
| episode_id | string | no | |
| episode_start | string | no | ISO8601 |
| worst_window_ref | string | no | |
| primary_verdict | string | no | |
| confidence | number | no | 0–1 |
| evidence_refs | array[string] | yes | |
| observability | object | no | ObservabilityResult (flattened) |
| timeline.metrics_points | array[object] | no | sampled metrics points |
| timeline.change_events | array[object] | yes | change stubs |
| timeline.pre_change_snapshots | array[object] | yes | pre-change references |

---

## G) fp-lite Output (offline/app)

| Field | Type | Nullable | Notes |
|---|---:|:---:|---|
| fp_before / fp_during / fp_after | object | no | averaged vectors of metrics |
| delta_during_minus_before | object | no | |
| delta_after_minus_before | object | no | |
| pattern_label | string | no | `drift` / `stability` / `boundary` / `oscillation` |
| confidence | number | no | 0–1 |


---

## H) InstallVerificationResult (fp_recognition, 3-minute default)

| Field | Type | Nullable | Notes |
|---|---:|:---:|---|
| verify_window_sec | integer | no | default 180 (3 minutes) |
| sample_count | integer | no | number of MetricSample used |
| readiness_verdict | string | no | PASS / MARGINAL / FAIL |
| dominant_factor | string | no | WAN / WIFI / MESH / OPAQUE / UNKNOWN |
| confidence | number | no | 0–1 |
| fp_vector | object | no | averaged metric vector |


---

## Domain Field Groups (Open Set) — FWA / DOCSIS / PON

Free v1 keeps a **stable core schema** and supports domain-specific inputs as **open-set field groups** via adapters.
Adapters may map domain fields into existing MetricSample fields (recommended for simplicity), or extend MetricSample
in a backward-compatible way (advanced).

### FWA Field Group (examples)
- Cellular link quality: SINR (dB), RSRP (dBm), RSRQ (dB) (optional)
- Mobility / attach: reattach/reselection counts
- WAN performance: RTT p95 (ms), loss (%)
- Wi-Fi symptoms: retry (%), airtime busy (%), mesh flap (count)

### DOCSIS Field Group (examples)
- Access quality: RxMER (dB), SNR (dB), correctables/uncorrectables, T3/T4 counts
- Service state: partial service, OFDM lock (events)
- WAN performance: RTT p95 (ms), loss (%)
- Wi-Fi symptoms: retry (%), airtime busy (%), mesh flap (count)

### PON Field Group (examples)
- Optical stability: LOS/LOF counts, dying gasp (events)
- Registration: re-range/re-register counts
- Optical power: Rx/Tx power (dBm) (optional)
- WAN performance: RTT p95 (ms), loss (%)
- Wi-Fi symptoms: retry (%), airtime busy (%), mesh flap (count)

> These are examples. All domain inputs remain **open set** and operator-defined.
