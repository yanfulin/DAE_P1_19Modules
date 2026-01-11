
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
from .M00_common import MetricSample

@dataclass
class DetectorThresholds:
    airtime_busy_pct: float = 75.0
    retry_pct: float = 18.0
    latency_p95_ms: float = 60.0
    mesh_flap_per_min: int = 2
    wan_sinr_low_db: float = 5.0

class IncidentDetector:
    """
    Detects 'bad windows' using metadata-only signals.
    """
    def __init__(self, th: DetectorThresholds = DetectorThresholds()):
        self.th = th

    def badness_flags(self, m: MetricSample) -> List[str]:
        flags: List[str] = []
        if m.airtime_busy_pct is not None and m.airtime_busy_pct >= self.th.airtime_busy_pct:
            flags.append("AIRTIME_HIGH")
        if m.retry_pct is not None and m.retry_pct >= self.th.retry_pct:
            flags.append("RETRY_HIGH")
        if m.latency_p95_ms is not None and m.latency_p95_ms >= self.th.latency_p95_ms:
            flags.append("LAT_SPIKE")
        if m.mesh_flap_count is not None and m.mesh_flap_count >= self.th.mesh_flap_per_min:
            flags.append("MESH_FLAP")
        if m.wan_sinr_db is not None and m.wan_sinr_db <= self.th.wan_sinr_low_db:
            flags.append("WAN_LOW_SINR")
        return flags

    def is_bad_window(self, m: MetricSample) -> Tuple[bool, List[str]]:
        flags = self.badness_flags(m)
        # Require 2+ signals to reduce false positives
        return (len(flags) >= 2), flags
