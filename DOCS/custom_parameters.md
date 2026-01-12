# DAE P1 System Parameters

This document lists all **custom, default, and hardcoded parameters** found in the DAE P1 codebase.

## 1. Configurable Parameters (Runtime Config)

These parameters are defined in dataclasses and can be overridden during initialization.

### Window Policy
**File**: `dae_p1/M01_windowing.py` (Class: `WindowPolicy`)
- `ws_sec`: **10**
  - **Description**: Short window generation interval (seconds).
- `wl_sec`: **60**
  - **Description**: Long window generation interval (seconds).

### Incident Detection Thresholds
**File**: `dae_p1/M07_incident_detector.py` (Class: `DetectorThresholds`)
- `airtime_busy_pct`: **75.0**
  - **Description**: If airtime exceeds this %, flagged as `AIRTIME_HIGH`.
- `retry_pct`: **18.0**
  - **Description**: If retry rate exceeds this %, flagged as `RETRY_HIGH`.
- `latency_p95_ms`: **60.0**
  - **Description**: If P95 latency exceeds this (ms), flagged as `LAT_SPIKE`.
- `mesh_flap_per_min`: **2**
  - **Description**: If mesh re-connections exceed this count/min, flagged as `MESH_FLAP`.
- `wan_sinr_low_db`: **5.0**
  - **Description**: If WAN SINR is below this (dB), flagged as `WAN_LOW_SINR`.

### Core Service Configuration
**File**: `dae_p1/core_service.py` (Class: `CoreRuntimeConfig`)
- `sample_interval_sec`: **10**
  - **Description**: Time between metric collection ticks.
- `buffer_minutes`: **60**
  - **Description**: Duration to keep metrics in the rolling ring buffer.
- `accelerate`: **False**
  - **Description**: If True, ignores `sleep()` for rapid demo execution.

---

## 2. Hardcoded Logic Parameters

These parameters are embedded in the logic and require code changes to modify.

### Installation Verification Logic
**File**: `dae_p1/M20_install_verify.py`

| Parameter | Value | Logic |
|-----------|-------|-------|
| `DEFAULT_VERIFY_WINDOW_SEC` | **180** (3m) | Default duration for verification analysis. |
| **PASS** Criteria | | |
| Loss Limit | ≤ **1.0**% | |
| Latency Limit | ≤ **60.0**ms | |
| Retry Limit | ≤ **12.0**% | |
| Mesh Flap Limit | < **2** | |
| **FAIL** Criteria | | |
| Loss Limit | > **3.0**% | |
| Latency Limit | > **120.0**ms | |
| Retry Limit | > **25.0**% | |
| Mesh Flap Limit | ≥ **3** | |
| **Confidence** | | |
| Base Confidence | **0.75** (PASS/FAIL) | |
| Marginal Confidence | **0.6** | |
| Sample Boost | **+0.1** | If samples ≥ **18** |

### Observability Checks
**File**: `dae_p1/M06_observability_checker.py`
- `MIN_REFS`: `["origin_hint", "change_ref", "version_refs"]`
  - **Description**: Required fields to mark observability as `SUFFICIENT`.

### Buffer Sizes
**File**: `dae_p1/core_service.py`
- `events_buf` size: **500** items
- `snaps_buf` size: **500** items

---

## 3. String Constants & Defaults

**File**: `dae_p1/M00_common.py`
- `VersionRefs.agent`: **"dae_p1/0.1.0"**
- Default Hint/Scope: **"unknown"**
- `Verdict` Types:
  - `WAN_UNSTABLE`
  - `WIFI_CONGESTION`
  - `MESH_FLAP`
  - `DFS_EVENT`
  - `OPAQUE_RISK`
  - `UNKNOWN`
