
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
import statistics
import math
import time
import uuid
import json

# --- 1. Quantile Calculator (Nearest-Rank) ---
class QuantileCalculator:
    @staticmethod
    def calculate(data: List[float], percentile: int) -> float:
        """
        Calculates the p-th percentile using the Nearest-Rank method.
        Definition:
          1) Sort data (ascending).
          2) rank = ceil(p / 100 * N)
          3) result = sorted_data[rank - 1] (0-indexed)
        """
        if not data:
            return 0.0
        
        n = len(data)
        sorted_data = sorted(data)
        rank = math.ceil((percentile / 100.0) * n)
        # minimal rank is 1, max is n
        rank = max(1, min(n, rank))
        return sorted_data[rank - 1]

# --- 2. Data Structures ---
class OutcomeFacet(NamedTuple):
    name: str
    value: Any
    unit: str

class ProofCardResult:
    def __init__(self, card_data: Dict[str, Any]):
        self.card_data = card_data

    def to_dict(self) -> Dict[str, Any]:
        return self.card_data

# --- 3. Profile Definitions ---
# Each profile defines:
# - min_sample_count
# - strict_checks: function(p50_map, p95_map) -> list of failure_reason_codes

class ProfileBase:
    REF = "BASE"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        return []

class Wifi78InstallAccept(ProfileBase):
    REF = "WIFI78_INSTALL_ACCEPT"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        # Example Thresholds
        if p95.get("rtt_ms", 0) > 80.0:
            reasons.append("P95_RTT_TOO_HIGH")
        if p95.get("loss_pct", 0) > 1.0:
            reasons.append("P95_LOSS_TOO_HIGH")
        return reasons

class FwaJanusCongestion(ProfileBase):
    REF = "FWA_CONGESTION_SUSPECT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("rtt_ms", 0) > 150.0:
            reasons.append("TAIL_RTT_TOO_HIGH")
        if p95.get("loss_pct", 0) > 5.0:
            reasons.append("TAIL_LOSS_TOO_HIGH")
        return reasons

class CableUpstreamIntermittent(ProfileBase):
    REF = "CABLE_UPSTREAM_INTERMITTENT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("us_rtt_ms", 0) > 150.0:
             reasons.append("TAIL_US_RTT_TOO_HIGH")
        return reasons

class ProfileManager:
    PROFILES = {
        Wifi78InstallAccept.REF: Wifi78InstallAccept(),
        FwaJanusCongestion.REF: FwaJanusCongestion(),
        CableUpstreamIntermittent.REF: CableUpstreamIntermittent()
    }
    
    @staticmethod
    def get(ref: str) -> ProfileBase:
        return ProfileManager.PROFILES.get(ref, ProfileBase())

# --- 4. Main Generator ---

class ProofCardGenerator:
    """
    Generates V1.3 ProofCards from raw window data.
    """
    
    def __init__(self):
        pass

    def generate(self, 
                 window_data: List[Dict[str, Any]], 
                 profile_ref: str, 
                 window_ref_str: str,
                 manifest_ref_str: str = "TBD") -> Dict[str, Any]:
        
        # 0. Prep
        card_id = f"pc-{uuid.uuid4().hex[:12]}"
        ts_now = time.time()
        profile = ProfileManager.get(profile_ref)
        
        # 1. Sample Count Check
        n = len(window_data)
        if n < profile.MIN_SAMPLES:
            return self._build_card(card_id, profile_ref, "INSUFFICIENT_EVIDENCE", 
                                    window_ref_str, ["INSUFFICIENT_SAMPLES"], 
                                    n, [], [], [], manifest_ref_str)

        # 2. Key Metrics Extraction
        # We need to map raw data keys to 'rtt_ms', 'loss_pct' etc.
        # Assuming window_data comes from core.metrics_buf (MetricSample items)
        
        def extract(key):
            return [float(d.get(key, 0.0)) for d in window_data if key in d]

        # Map: metric_name -> list of values
        # This mapping depends on what module generates (M03 MetricsCollector)
        # For now, we perform a loose mapping
        vectors = {
            "rtt_ms": extract("latency_ms") or extract("rtt"),
            "loss_pct": extract("loss_percent") or extract("loss"),
            "us_rtt_ms": extract("us_latency"), # imaginary key for Cable
            "throughput_mbps": extract("throughput")
        }
        
        # 3. Compute p50 / p95 / p5
        p50_map = {}
        p95_map = {}
        p5_map  = {}
        
        qc = QuantileCalculator()
        
        for k, vals in vectors.items():
            if vals:
                p50_map[k] = qc.calculate(vals, 50)
                p95_map[k] = qc.calculate(vals, 95)
                p5_map[k]  = qc.calculate(vals, 5)

        # 4. Assess Verdict
        reasons = profile.check(p50_map, p95_map, p5_map)
        if reasons:
            verdict = "NOT_READY"
        else:
            verdict = "READY"
            reasons = ["PASSED_ALL_CHECKS"] # Placeholder

        # 5. Build Facets
        # Construct output arrays
        def to_kv(pmap, suffix):
            return [{"name": f"{k}_{suffix}", "value": v, "unit": "auto"} for k, v in pmap.items()]

        p50_out = to_kv(p50_map, "p50")
        p95_out = to_kv(p95_map, "p95")
        
        # Core outcome facets - usually a mix of p50/p95 relevant to the profile
        # For simplicity, we dump all p95s as outcome facets if invalid, or p50 if valid
        outcome_out = p95_out if verdict != "READY" else p50_out
        if not outcome_out: 
             outcome_out = [{"name": "no_metric_data", "value": 0, "unit": "none"}]

        return self._build_card(
            card_id, profile_ref, verdict, window_ref_str, reasons, n,
            p50_out, p95_out, outcome_out, manifest_ref_str
        )

    def _build_card(self, cid, pref, verdict, wref, reasons, n, p50, p95, outcome, mref):
        return {
            "proof_card_ref": cid,
            "profile_ref": pref,
            "verdict": verdict,
            "window_ref": wref,
            "reason_code": reasons,
            "enforcement_path_ref": "EP-DEFAULT-01",
            "authority_scope_ref": "SCOPE-CPE-LOCAL",
            "validity_horizon_ref": "7DAYS",
            "validity_verdict": "VALID",
            "basis_ref": "BASIS-V1.3",
            "sample_count": n,
            "p50": p50,
            "p95": p95,
            "outcome_facet": outcome,
            "event_type": [],
            "evidence_bundle_ref": f"bundle:{wref}",
            "manifest_ref": mref
        }

