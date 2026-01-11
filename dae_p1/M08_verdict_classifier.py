
from __future__ import annotations
from typing import List, Tuple
from .M00_common import Verdict

class VerdictClassifier:
    """
    Produces a minimal verdict from badness flags.
    """
    def classify(self, flags: List[str], opaque_risk: bool=False) -> Tuple[Verdict, float]:
        if opaque_risk:
            return "OPAQUE_RISK", 0.7
        if "WAN_LOW_SINR" in flags:
            return "WAN_UNSTABLE", 0.7
        if "MESH_FLAP" in flags:
            return "MESH_FLAP", 0.7
        if "AIRTIME_HIGH" in flags and "RETRY_HIGH" in flags:
            return "WIFI_CONGESTION", 0.7
        if "LAT_SPIKE" in flags and ("RETRY_HIGH" in flags or "AIRTIME_HIGH" in flags):
            return "WIFI_CONGESTION", 0.6
        return "UNKNOWN", 0.4
