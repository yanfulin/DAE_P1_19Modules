
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import statistics
from .M00_common import MetricSample

@dataclass
class InstallVerificationResult:
    verify_window_sec: int
    sample_count: int
    readiness_verdict: str  # PASS / MARGINAL / FAIL
    dominant_factor: str    # WAN / WIFI / MESH / OPAQUE / UNKNOWN
    confidence: float       # 0..1
    fp_vector: Dict[str, float]

DEFAULT_VERIFY_WINDOW_SEC = 180  # 3 minutes

def _mean(vals: List[float]) -> Optional[float]:
    if not vals:
        return None
    return float(statistics.mean(vals))

def _vec(samples: List[MetricSample]) -> Dict[str, float]:
    def get(field: str) -> Optional[float]:
        v = [getattr(s, field) for s in samples if getattr(s, field) is not None]
        return _mean(v)
    out: Dict[str, float] = {}
    for f in ["latency_p95_ms","loss_pct","retry_pct","airtime_busy_pct","mesh_flap_count","wan_sinr_db"]:
        m = get(f)
        if m is not None:
            out[f] = m
    return out

def verify_install(samples: List[MetricSample],
                   verify_window_sec: int = DEFAULT_VERIFY_WINDOW_SEC) -> InstallVerificationResult:
    """
    Installation Verification (fp_recognition):
    - Uses the last verify_window_sec worth of MetricSample items.
    - Outputs PASS/MARGINAL/FAIL without prescribing remediation.
    Default: 3 minutes.
    """
    if not samples:
        return InstallVerificationResult(verify_window_sec, 0, "FAIL", "UNKNOWN", 0.2, {})

    end_ts = samples[-1].ts
    start_ts = end_ts - verify_window_sec
    window = [s for s in samples if s.ts >= start_ts]
    if len(window) < 6:
        window = samples[-6:]

    v = _vec(window)

    latency = v.get("latency_p95_ms", 0.0)
    loss = v.get("loss_pct", 0.0)
    retry = v.get("retry_pct", 0.0)
    airtime = v.get("airtime_busy_pct", 0.0)
    flap = v.get("mesh_flap_count", 0.0)
    sinr = v.get("wan_sinr_db", None)

    dominant = "UNKNOWN"
    if sinr is not None and sinr < 5:
        dominant = "WAN"
    elif flap >= 2:
        dominant = "MESH"
    elif airtime >= 75 or retry >= 18:
        dominant = "WIFI"

    if (loss <= 1.0) and (latency <= 60.0) and (retry <= 12.0) and (flap < 2):
        verdict = "PASS"
        conf = 0.75
    elif (loss > 3.0) or (latency > 120.0) or (retry > 25.0) or (flap >= 3):
        verdict = "FAIL"
        conf = 0.75
    else:
        verdict = "MARGINAL"
        conf = 0.6

    if len(window) >= 18:
        conf = min(0.9, conf + 0.1)

    return InstallVerificationResult(
        verify_window_sec=verify_window_sec,
        sample_count=len(window),
        readiness_verdict=verdict,
        dominant_factor=dominant,
        confidence=conf,
        fp_vector=v
    )
