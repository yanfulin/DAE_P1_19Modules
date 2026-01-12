# DAE P1 System Workflow

## System Architecture Overview

```mermaid
graph TB
    subgraph "Data Collection Layer"
        A[Domain Adapter] --> B[Metrics Collector M03]
        A --> C[Change Event Logger M04]
        A --> D[Snapshot Manager M05]
    end
    
    subgraph "Storage Layer"
        B --> E[Metrics Ring Buffer M02]
        C --> F[Events Ring Buffer M02]
        D --> G[Snapshots Ring Buffer M02]
    end
    
    subgraph "Analysis Layer"
        E --> H[Incident Detector M07]
        H --> I[Verdict Classifier M08]
        F --> J[Observability Checker M06]
        J --> I
    end
    
    subgraph "Recognition Layer"
        I --> K[Episode Manager M09]
        K --> L[Recognition Engine M16]
        L --> M[Episode Recognition]
    end
    
    subgraph "Export Layer"
        E --> N[Timeline Builder M10]
        F --> N
        G --> N
        M --> O[OBH Controller M12]
        N --> O
        O --> P[Bundle Exporter M11]
        P --> Q[Evidence Bundle JSON]
    end
    
    subgraph "Verification Layer"
        E --> R[Install Verify M20]
        R --> S[Verification Result]
    end
```

---

## Complete System Workflow

### Phase 1: Initialization

```mermaid
sequenceDiagram
    participant User
    participant Server
    participant Core as OBHCoreService
    participant Adapter as DomainAdapter
    participant Buffers as Ring Buffers
    
    User->>Server: Start server.py
    Server->>Adapter: Initialize WindowsWifiAdapter
    Server->>Core: Create OBHCoreService(adapter, config)
    Core->>Buffers: Initialize 3 ring buffers
    Note over Buffers: metrics_buf (360 samples)<br/>events_buf (500 items)<br/>snaps_buf (500 items)
    Server->>Core: Start background tick loop
```

**Key Components Initialized**:
1. **WindowsWifiAdapter** - Collects real WiFi data from Windows
2. **OBHCoreService** - Core orchestrator
3. **Ring Buffers** - 60-minute rolling storage
4. **Windowing** (M01) - Time window reference generator
5. **Recognition Engine** (M16) - Incident analyzer

---

### Phase 2: Continuous Data Collection (Every 1-10 seconds)

```mermaid
sequenceDiagram
    participant BgLoop as Background Loop
    participant Core as OBHCoreService
    participant Adapter
    participant M03 as MetricsCollector
    participant M01 as Windowing
    participant Buffers
    
    BgLoop->>Core: tick_once()
    Core->>Adapter: collect_metric_sample()
    Adapter->>M03: collect()
    M03->>M01: window_ref()
    M01-->>M03: Ws:timestamp
    M03-->>Adapter: MetricSample
    Adapter-->>Core: MetricSample
    Core->>Buffers: append to metrics_buf
    
    Core->>Adapter: collect_change_events_and_snapshots()
    Adapter-->>Core: events and snapshots
    Core->>Buffers: append to events_buf
    Core->>Buffers: append to snaps_buf
```

**This cycle repeats every 1-10 seconds based on `sample_interval_sec` configuration.**

**Data Collected Each Cycle**:
- **MetricSample**: 17 network metrics (latency, loss, retry, airtime, etc.)
- **ChangeEventCard**: System changes (optional)
- **PreChangeSnapshot**: Configuration snapshots (optional)

---

### Phase 3: Incident Detection & Recognition

```mermaid
sequenceDiagram
    participant API as API Request
    participant Core
    participant M07 as IncidentDetector
    participant M08 as VerdictClassifier
    participant M06 as ObservabilityChecker
    participant M09 as EpisodeManager
    participant M16 as RecognitionEngine
    
    API->>Core: GET /recognition
    Core->>Core: generate_recognition()
    Core->>Buffers: Get latest metric
    Core->>M16: recognize(latest_metric, events, window_ref)
    
    M16->>M07: is_bad_window(metric)
    M07->>M07: Check thresholds
    Note over M07: airtime > 75%?<br/>retry > 18%?<br/>latency > 60ms?<br/>mesh_flap > 2?<br/>wan_sinr < 5?
    M07-->>M16: (is_bad, flags[])
    
    M16->>M06: check_event(recent_events)
    M06->>M06: Verify observability
    Note over M06: Has origin_hint?<br/>Has change_ref?<br/>Has version_refs?
    M06-->>M16: ObservabilityResult
    
    M16->>M08: classify(flags, opaque_risk)
    M08->>M08: Determine verdict
    Note over M08: WAN_UNSTABLE?<br/>WIFI_CONGESTION?<br/>MESH_FLAP?<br/>OPAQUE_RISK?
    M08-->>M16: (verdict, confidence)
    
    M16->>M09: start_or_update(window_ref, evidence_ref)
    M09-->>M16: Episode
    
    M16-->>Core: EpisodeRecognition
    Core-->>API: Recognition JSON
```

**Recognition Output**:
```json
{
  "episode_id": "ep-abc123",
  "episode_start": 1234567890.0,
  "worst_window_ref": "Wl:1234567800",
  "primary_verdict": "WIFI_CONGESTION",
  "confidence": 0.7,
  "evidence_refs": ["Ws:1234567890:AIRTIME_HIGH,RETRY_HIGH"],
  "observability": {
    "observability_status": "SUFFICIENT",
    "opaque_risk": false,
    "missing_refs": [],
    "origin_hint": "user_command"
  }
}
```

---

### Phase 4: Installation Verification

```mermaid
sequenceDiagram
    participant API
    participant Core
    participant M20 as InstallVerify
    participant Buffers
    
    API->>Core: GET /install_verify
    Core->>Buffers: metrics_buf.snapshot()
    Buffers-->>Core: All metrics (last 60 min)
    Core->>M20: verify_install(metrics, window=180s)
    
    M20->>M20: Filter last 3 minutes
    M20->>M20: Calculate fp_vector
    Note over M20: Mean of:<br/>latency, loss, retry<br/>airtime, mesh_flap, wan_sinr
    
    M20->>M20: Determine dominant factor
    Note over M20: WAN: sinr < 5<br/>MESH: flap >= 2<br/>WIFI: airtime >= 75 or retry >= 18
    
    M20->>M20: Calculate verdict
    Note over M20: PASS: loss<=1, lat<=60, retry<=12<br/>FAIL: loss>3, lat>120, retry>25<br/>MARGINAL: between
    
    M20-->>Core: InstallVerificationResult
    Core-->>API: Verification JSON
```

**Verification Output**:
```json
{
  "verify_window_sec": 180,
  "sample_count": 18,
  "readiness_verdict": "PASS",
  "closure_readiness": "ready",
  "dominant_factor": "UNKNOWN",
  "confidence": 0.85,
  "fp_vector": {
    "latency_p95_ms": 25.5,
    "loss_pct": 0.3,
    "retry_pct": 8.2,
    "airtime_busy_pct": 45.0
  }
}
```

---

### Phase 5: One-Button Help (OBH) Export

```mermaid
sequenceDiagram
    participant API
    participant Core
    participant M16 as RecognitionEngine
    participant M10 as TimelineBuilder
    participant M12 as OBHController
    participant M11 as BundleExporter
    participant FS as File System
    
    API->>Core: obh_export(out_dir)
    Core->>M16: generate_recognition()
    M16-->>Core: EpisodeRecognition
    
    Core->>Buffers: Get all snapshots
    Buffers-->>Core: (metrics[], events[], snapshots[])
    
    Core->>M12: run(out_dir, recognition, buffers)
    M12->>M10: build(metrics, events, snapshots)
    
    M10->>M10: Format timeline
    Note over M10: Convert to ISO timestamps<br/>Extract relevant fields<br/>Create flat structure
    M10-->>M12: Timeline dict
    
    M12->>M12: Construct bundle
    Note over M12: Add spec, episode_id<br/>Add recognition data<br/>Add timeline
    
    M12->>M11: export(out_dir, episode_id, bundle)
    M11->>FS: Write JSON file
    Note over FS: evidence_bundle_<br/>ep-abc123_<br/>1234567890.json
    M11-->>M12: file_path
    
    M12-->>Core: OBHResult
    Core-->>API: Export result
```

**Bundle Structure**:
```json
{
  "spec": "DAE_P1_Free_v1",
  "episode_id": "ep-abc123",
  "episode_start": "2026-01-12T08:00:00Z",
  "worst_window_ref": "Wl:1234567800",
  "primary_verdict": "WIFI_CONGESTION",
  "confidence": 0.7,
  "evidence_refs": ["..."],
  "observability": {...},
  "timeline": {
    "metrics_points": [...],
    "change_events": [...],
    "pre_change_snapshots": [...]
  }
}
```

---

### Phase 6: fp-lite Analysis (Offline)

```mermaid
sequenceDiagram
    participant User
    participant M13 as fp_lite
    participant Bundle as Evidence Bundle
    
    User->>M13: fp_lite_from_bundle(bundle)
    M13->>Bundle: Read timeline.metrics_points
    
    M13->>M13: Split into thirds
    Note over M13: before: 0 to n/3<br/>during: n/3 to 2n/3<br/>after: 2n/3 to n
    
    M13->>M13: Calculate vectors
    Note over M13: Mean of each metric<br/>for each period
    
    M13->>M13: Calculate deltas
    Note over M13: during - before<br/>after - before
    
    M13->>M13: Pattern labeling
    Note over M13: drift: latency spike<br/>stability: retry/airtime high<br/>boundary: wan_sinr drop<br/>oscillation: mesh flaps
    
    M13-->>User: fp-lite result
```

**fp-lite Output**:
```json
{
  "fp_before": {"latency_p95_ms": 20.0, "retry_pct": 5.0},
  "fp_during": {"latency_p95_ms": 80.0, "retry_pct": 25.0},
  "fp_after": {"latency_p95_ms": 30.0, "retry_pct": 8.0},
  "delta_during_minus_before": {"latency_p95_ms": 60.0, "retry_pct": 20.0},
  "delta_after_minus_before": {"latency_p95_ms": 10.0, "retry_pct": 3.0},
  "pattern_label": "stability",
  "confidence": 0.8
}
```

---

## API Workflow

### Fleet Management Flow

```mermaid
sequenceDiagram
    participant Mobile as Mobile App
    participant API as Server API
    participant Core
    participant M20 as InstallVerify
    
    Mobile->>API: GET /fleet
    API->>Core: calculate_simple_status()
    API->>M20: verify_install()
    API-->>Mobile: Fleet list with real + mock devices
    
    Mobile->>API: GET /device/local
    API->>Core: Get snapshots
    API->>M20: verify_install()
    API-->>Mobile: Device detail with OBH timeline
    
    Mobile->>API: GET /device/local/proof
    API->>API: get_device_detail()
    API-->>Mobile: Proof card summary
```

---

## Data Flow Summary

### 1. **Collection Flow**
```
Windows WiFi → Adapter → MetricsCollector → Ring Buffer (60 min)
```

### 2. **Detection Flow**
```
Ring Buffer → IncidentDetector → Badness Flags → VerdictClassifier → Verdict
```

### 3. **Recognition Flow**
```
Latest Metric + Events → RecognitionEngine → Episode → EpisodeRecognition
```

### 4. **Verification Flow**
```
Metrics (3 min) → InstallVerify → fp_vector → Readiness Verdict
```

### 5. **Export Flow**
```
Recognition + Buffers → TimelineBuilder → OBHController → JSON Bundle
```

### 6. **Analysis Flow**
```
JSON Bundle → fp_lite → Pattern Analysis → BOSD Label
```

---

## State Transitions

```mermaid
stateDiagram-v2
    [*] --> OK: System starts
    OK --> Unstable: Bad window detected
    Unstable --> Suspected: Persistent issues
    Suspected --> Investigation: Severe problems
    Investigation --> OK: Issues resolved
    Unstable --> OK: Transient issue
    Suspected --> Unstable: Improving
```

**Status Definitions**:
- **OK**: No bad windows detected
- **Unstable**: Bad window detected (2+ signals)
- **Suspected**: Multiple consecutive bad windows
- **Investigation**: Severe or persistent issues

---

## Key Design Principles

### 1. **No Remediation**
- System only detects and records
- Never modifies network settings
- No automatic fixes

### 2. **Metadata Only**
- Collects metrics, not payloads
- Uses references and digests
- Privacy-preserving

### 3. **Reference-Oriented**
- Window references (Ws/Wl)
- Snapshot digests (SHA256)
- Episode IDs
- Evidence references

### 4. **Opaque Risk Handling**
- Flags insufficient observability
- Marks as OPAQUE_RISK verdict
- Tracks missing references

### 5. **Rolling Buffers**
- 60-minute continuous storage
- Automatic old data eviction
- Constant memory footprint

---

## Performance Characteristics

| Component | Frequency | Buffer Size | Memory Impact |
|-----------|-----------|-------------|---------------|
| Metrics Collection | 1-10 sec | 360 samples | ~50 KB |
| Event Logging | On-demand | 500 events | ~100 KB |
| Snapshot Creation | On-demand | 500 snapshots | ~200 KB |
| Recognition | On-demand | N/A | Minimal |
| Verification | On-demand | N/A | Minimal |
| OBH Export | On-demand | N/A | I/O bound |

**Total Memory**: ~350 KB for buffers + overhead

---

## Error Handling

### Insufficient Data
```python
if len(metrics) < 6:
    return {"error": "insufficient_points"}
```

### No Metrics Collected
```python
if latest is None:
    raise RuntimeError("No metrics collected")
```

### Opaque Risk
```python
if observability_status == "INSUFFICIENT":
    verdict = "OPAQUE_RISK"
    opaque_risk = True
```

---

## Integration Points

### 1. **Adapter Interface**
```python
class DomainAdapter:
    def collect_metric_sample() -> MetricSample
    def collect_change_events_and_snapshots() -> Tuple[List, List]
```

### 2. **API Endpoints**
- `/metrics` - Latest sample
- `/recognition` - Incident analysis
- `/install_verify` - Installation check
- `/fleet` - Device list
- `/device/{id}` - Device details

### 3. **Mobile App**
- Real-time metrics display
- Fleet management
- Device drilldown
- Proof cards

---

## Typical Use Cases

### Use Case 1: Installation Verification
1. Install DAE agent
2. Run for 3 minutes
3. Call `/install_verify`
4. Check `closure_readiness`
5. Proceed if "ready"

### Use Case 2: Incident Investigation
1. User reports issue
2. System detects bad windows
3. Recognition engine identifies verdict
4. OBH export creates evidence bundle
5. Analyst reviews timeline and fp-lite

### Use Case 3: Fleet Monitoring
1. Mobile app polls `/fleet`
2. Displays device status
3. User drills into problematic device
4. Views OBH snapshot timeline
5. Checks compliance verdict

---

## Module Dependencies

```mermaid
graph LR
    M00[M00 Common] --> M01[M01 Windowing]
    M00 --> M03[M03 Metrics]
    M00 --> M04[M04 Events]
    M00 --> M05[M05 Snapshots]
    M00 --> M06[M06 Observability]
    M00 --> M07[M07 Detector]
    M00 --> M08[M08 Classifier]
    M00 --> M09[M09 Episodes]
    M00 --> M10[M10 Timeline]
    M00 --> M16[M16 Recognition]
    M00 --> M20[M20 Verify]
    
    M01 --> M03
    M01 --> M04
    M02[M02 RingBuffer] --> Core[Core Service]
    M03 --> Core
    M04 --> Core
    M05 --> Core
    M07 --> M16
    M08 --> M16
    M09 --> M16
    M06 --> M16
    M10 --> M12[M12 OBH]
    M11[M11 Exporter] --> M12
    M16 --> M12
    M16 --> Core
    M12 --> Core
```

---

## Conclusion

The DAE P1 system provides a **detect-only** architecture that:
- ✅ Continuously monitors network health
- ✅ Detects incidents with multi-signal analysis
- ✅ Generates evidence bundles for investigation
- ✅ Verifies installation readiness
- ✅ Supports fleet management
- ❌ Never modifies network settings
- ❌ Never prescribes remediation
- ❌ Never optimizes automatically

This design ensures **safe, observable, and auditable** network diagnostics.
