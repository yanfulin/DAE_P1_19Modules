
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import statistics
from .M00_common import MetricSample

@dataclass
class InstallVerificationResult:
    verify_window_sec: int
    sample_count: int
    readiness_verdict: str  # PASS / MARGINAL / FAIL
    closure_readiness: str  # ready / not_ready
    dominant_factor: str    # WAN / WIFI / MESH / OPAQUE / UNKNOWN
    confidence: float       # 0..1
    fp_vector: Dict[str, float]
    
    # NEW: Why did it pass/fail?
    thresholds: Dict[str, Any] = field(default_factory=dict)
    
    # NEW: Key Info (DNS, Channel, Bandwidth)
    system_info: Dict[str, Any] = field(default_factory=dict)
    
    # NEW: Internal Health (C01, C06)
    internal_health: Dict[str, Any] = field(default_factory=dict)

DEFAULT_VERIFY_WINDOW_SEC = 180  # 3 minutes

# Define Criteria
THRESHOLDS = {
    # Performance
    "latency_max_ms": 60.0,
    "loss_max_pct": 1.0,
    "retry_max_pct": 12.0,
    "airtime_max_pct": 75.0,
    "mesh_flap_max": 2,
    "signal_min_pct": 80,
    
    # Connectivity
    "dns_must_be": "OK",
    "link_rate_min_mbps": 100
}

def _mean(vals: List[float]) -> Optional[float]:
    if not vals:
        return None
    return float(statistics.mean(vals))

def _vec(samples: List[MetricSample]) -> Dict[str, float]:
    def get(field: str) -> Optional[float]:
        # Handle None gracefully
        v = [getattr(s, field) for s in samples if getattr(s, field) is not None]
        return _mean(v)
        
    out: Dict[str, float] = {}
    # Numeric performance metrics
    for f in ["latency_p95_ms","loss_pct","retry_pct","airtime_busy_pct",
              "mesh_flap_count","wan_sinr_db", "signal_strength_pct"]:
        m = get(f)
        if m is not None:
            out[f] = m
    return out

def verify_install(samples: List[MetricSample],
                   verify_window_sec: int = DEFAULT_VERIFY_WINDOW_SEC,
                   window_refs: Optional[Dict[str, str]] = None,
                   buffer_stats: Optional[Dict[str, int]] = None) -> InstallVerificationResult:
    """
    Installation Verification (fp_recognition):
    - Uses the last verify_window_sec worth of MetricSample items.
    - Outputs PASS/MARGINAL/FAIL without prescribing remediation.
    - INCLUDES: Thresholds, System Info (DNS/Wifi), and Internals (C01/C06).
    """
    
    # Default Internals if not provided
    internals = {
        "buffer_health": buffer_stats or {"count": 0, "capacity": 0},
        "window_refs": window_refs or {"Ws": "unknown", "Wl": "unknown"}
    }

    if not samples:
        return InstallVerificationResult(
            verify_window_sec, 0, "FAIL", "not_ready", "UNKNOWN", 0.0, {},
            thresholds=THRESHOLDS,
            system_info={},
            internal_health=internals
        )

    end_ts = samples[-1].ts
    start_ts = end_ts - verify_window_sec
    window = [s for s in samples if s.ts >= start_ts]
    
    # If buffer is too short, just use what we have (min 6 samples for confident verdict though)
    if len(window) < 6:
        # Fallback to recent samples if window is empty? No, window logic is robust.
        # But if total samples < 6, effectively we have low confidence.
        if len(samples) < 6:
            window = samples # take all
        else:
            window = samples[-6:] # take last 6

    # 1. Performance Vector
    v = _vec(window)

    latency = v.get("latency_p95_ms", 0.0)
    loss = v.get("loss_pct", 0.0)
    retry = v.get("retry_pct", 0.0)
    airtime = v.get("airtime_busy_pct", 0.0)
    flap = v.get("mesh_flap_count", 0.0)
    sinr = v.get("wan_sinr_db", None)
    signal = v.get("signal_strength_pct", 0.0)

    # 2. Extract System Info (from latest sample)
    last = samples[-1]
    
    # Helper for safe access
    def get_last(k, default="N/A"):
        val = getattr(last, k, None)
        return val if val is not None else default

    sys_info = {
        "dns_status": get_last("dns_status", "UNKNOWN"),
        "channel": get_last("channel", 0),
        "radio_type": get_last("radio_type", "unknown"),
        "band": get_last("band", "unknown"),
        "phy_rate_mbps": get_last("phy_rate_mbps", 0),
        "phy_rx_rate_mbps": get_last("phy_rx_rate_mbps", 0)
    }

    # 3. Verdict Logic
    dominant = "UNKNOWN"
    verdict = "MARGINAL" # Start neutral

    # Check Hard Failures
    is_fail = False
    
    # WAN
    if sinr is not None and sinr < 5:
        dominant = "WAN"
        is_fail = True
    elif sys_info["dns_status"] == "FAIL":
        dominant = "WAN (DNS)"
        is_fail = True
        
    # MESH
    elif flap >= THRESHOLDS["mesh_flap_max"]:
        dominant = "MESH"
        is_fail = True
        
    # WIFI
    elif airtime >= THRESHOLDS["airtime_max_pct"]:
        dominant = "WIFI (Congestion)"
        is_fail = True
    elif retry >= THRESHOLDS["retry_max_pct"]:
        dominant = "WIFI (Noise)"
        is_fail = True
    elif signal < THRESHOLDS["signal_min_pct"]:
        dominant = "WIFI (Coverage)"
        is_fail = True
    elif sys_info["phy_rate_mbps"] > 0 and sys_info["phy_rate_mbps"] < THRESHOLDS["link_rate_min_mbps"]:
         dominant = "WIFI (Link Speed)"
         is_fail = True
    
    # LATENCY/LOSS (Could be any)
    elif loss > THRESHOLDS["loss_max_pct"]:
        dominant = "OPAQUE (Loss)"
        is_fail = True
    elif latency > THRESHOLDS["latency_max_ms"]:
        dominant = "OPAQUE (Latency)"
        is_fail = True

    # Assign Verdict
    if is_fail:
        verdict = "FAIL"
        conf = 0.8
    else:
        # Check Pass Criteria (Strict)
        if (loss <= THRESHOLDS["loss_max_pct"] and 
            latency <= THRESHOLDS["latency_max_ms"] and 
            retry <= THRESHOLDS["retry_max_pct"] and 
            flap < THRESHOLDS["mesh_flap_max"]):
            verdict = "PASS"
            conf = 0.85
        else:
            verdict = "MARGINAL"
            conf = 0.6

    # Boost confidence with more data
    if len(window) >= 18:
        conf = min(0.95, conf + 0.1)

    return InstallVerificationResult(
        verify_window_sec=verify_window_sec,
        sample_count=len(window),
        readiness_verdict=verdict,
        closure_readiness="ready" if verdict == "PASS" else "not_ready",
        dominant_factor=dominant,
        confidence=conf,
        fp_vector=v,
        thresholds=THRESHOLDS,
        system_info=sys_info,
        internal_health=internals
    )
