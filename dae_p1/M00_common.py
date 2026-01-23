
"""
DAE P1 - 19 Modules (Free v1)
Focus: Detect + Recognition + Evidence Freeze/Export + Opaque Risk Flag + Pre-change Snapshot refs
No remediation, no network control, no optimization.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Literal, Tuple
import time
import json
import hashlib
import os

def now_ts() -> float:
    return time.time()

def iso(ts: Optional[float]=None) -> str:
    if ts is None: ts = now_ts()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

Verdict = Literal["WAN_UNSTABLE","WIFI_CONGESTION","MESH_FLAP","DFS_EVENT","OPAQUE_RISK","UNKNOWN"]

@dataclass
class VersionRefs:
    fw: str = "unknown"
    driver: str = "unknown"
    agent: str = "dae_p1/0.1.0"

@dataclass
class MetricSample:
    ts: float
    window_ref: str
    latency_p95_ms: Optional[float] = None
    loss_pct: Optional[float] = None
    retry_pct: Optional[float] = None
    airtime_busy_pct: Optional[float] = None
    roam_count: Optional[int] = None
    mesh_flap_count: Optional[int] = None
    wan_sinr_db: Optional[float] = None
    wan_rsrp_dbm: Optional[float] = None
    wan_reattach_count: Optional[int] = None
    jitter_ms: Optional[float] = None
    in_rate: Optional[float] = None
    out_rate: Optional[float] = None
    cpu_load: Optional[float] = None
    mem_load: Optional[float] = None
    signal_strength_pct: Optional[int] = None
    # Extended metrics for Install Verify
    phy_rate_mbps: Optional[int] = None # Transmit Rate
    phy_rx_rate_mbps: Optional[int] = None # Receive Rate
    channel: Optional[int] = None
    bssid: Optional[str] = None
    radio_type: Optional[str] = None
    band: Optional[str] = None
    dns_status: Optional[str] = None # OK / FAIL

@dataclass
class ChangeEventCard:
    event_time: float
    event_type: str
    origin_hint: str = "unknown"
    trigger: str = "unknown"
    target_scope: str = "unknown"
    change_ref: Optional[str] = None
    version_refs: VersionRefs = field(default_factory=VersionRefs)
    window_ref: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.version_refs, dict):
            self.version_refs = VersionRefs(**self.version_refs)

@dataclass
class PreChangeSnapshot:
    snapshot_ref_id: str
    snapshot_scope: str
    capture_time: float
    snapshot_digest: str
    snapshot_type: str = "periodic"
    readable_fields: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ObservabilityResult:
    observability_status: Literal["SUFFICIENT","INSUFFICIENT"]
    opaque_risk: bool
    missing_refs: List[str] = field(default_factory=list)
    origin_hint: str = "unknown"

@dataclass
class EpisodeRecognition:
    episode_id: str
    episode_start: float
    worst_window_ref: str
    primary_verdict: Verdict
    confidence: float
    evidence_refs: List[str]
    observability: ObservabilityResult

def to_json(obj: Any) -> str:
    def default(o):
        if hasattr(o, "__dataclass_fields__"):
            d = asdict(o)
            return d
        raise TypeError()
    return json.dumps(obj, default=default, ensure_ascii=False, indent=2)
