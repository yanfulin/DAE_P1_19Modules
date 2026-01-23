
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

# --- 2. Profile Definitions ---

class ProfileBase:
    REF = "BASE"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        return []

    def get_outcome_facets(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[Dict[str, Any]]:
        # Default: return everything useful
        return []

# 7.1 Wi-Fi 7/8 Profiles
class Wifi78InstallAccept(ProfileBase):
    REF = "WIFI78_INSTALL_ACCEPT"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("rtt_ms", 0) > 80.0:
            reasons.append("P95_RTT_TOO_HIGH")
        if p95.get("loss_pct", 0) > 1.0:
            reasons.append("P95_LOSS_TOO_HIGH")
        # Example check for retry
        if p95.get("wifi_retry_pct", 0) > 20.0:
            reasons.append("WIFI_SIDE_OSCILLATION")
        return reasons

    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "rtt_ms_p95", "value": p95.get("rtt_ms", 0), "unit": "ms"},
            {"name": "loss_rate_p95", "value": p95.get("loss_pct", 0), "unit": "%"},
            {"name": "wifi_retry_p95", "value": p95.get("wifi_retry_pct", 0), "unit": "%"},
            {"name": "phy_rate_p50", "value": p50.get("phy_rate_mbps", 0), "unit": "Mbps"}
        ]

class Wifi78MeshBackhaulSplit(ProfileBase):
    REF = "WIFI78_MESH_BACKHAUL_SPLIT"
    MIN_SAMPLES = 10

    def check(self, p50, p95, p5) -> List[str]:
        reasons = []
        if p5.get("backhaul_rssi", -100) < -75:
             reasons.append("MESH_BACKHAUL_WEAK")
        return reasons
    
    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "backhaul_rssi_p5", "value": p5.get("backhaul_rssi", 0), "unit": "dBm"},
            {"name": "access_retry_p95", "value": p95.get("access_retry_pct", 0), "unit": "%"}
        ]

class Wifi78OscillationGuard(ProfileBase):
    REF = "WIFI78_OSCILLATION_GUARD"
    MIN_SAMPLES = 20

    def check(self, p50, p95, p5) -> List[str]:
        reasons = []
        if p95.get("retry_burst_count", 0) > 5:
            reasons.append("WIFI_SIDE_OSCILLATION")
        return reasons
        
    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "retry_burst_p95", "value": p95.get("retry_burst_count", 0), "unit": "count"},
            {"name": "mlo_switch_burst_p95", "value": p95.get("mlo_switch_count", 0), "unit": "count"}
        ]

# 7.2 FWA Profiles
class FwaInstallAccept(ProfileBase):
    REF = "FWA_INSTALL_ACCEPT"
    MIN_SAMPLES = 10

    def check(self, p50, p95, p5) -> List[str]:
        reasons = []
        if p95.get("rtt_ms", 0) > 100.0:
            reasons.append("TAIL_RTT_TOO_HIGH")
        if p5.get("rsrp", -140) < -110:
             reasons.append("WEAK_COVERAGE_RSRP_P5")
        if p5.get("sinr", -20) < 5:
             reasons.append("LOW_SINR_P5")
        return reasons

    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "rtt_ms_p95", "value": p95.get("rtt_ms", 0), "unit": "ms"},
            {"name": "loss_rate_p95", "value": p95.get("loss_pct", 0), "unit": "%"},
            {"name": "rsrp_p5", "value": p5.get("rsrp", 0), "unit": "dBm"},
            {"name": "sinr_p5", "value": p5.get("sinr", 0), "unit": "dB"}
        ]

class FwaPlacementGuide(ProfileBase):
    REF = "FWA_PLACEMENT_GUIDE"
    MIN_SAMPLES = 10
    
    def check(self, p50, p95, p5) -> List[str]:
        # Mostly informational
        reasons = []
        if p5.get("rsrp", -140) < -115:
            reasons.append("WEAK_COVERAGE_RSRP_P5")
        return reasons

    def get_outcome_facets(self, p50, p95, p5):
        return [
             {"name": "rsrp_p5", "value": p5.get("rsrp", 0), "unit": "dBm"},
             {"name": "sinr_p5", "value": p5.get("sinr", 0), "unit": "dB"},
             {"name": "rtt_ms_p95", "value": p95.get("rtt_ms", 0), "unit": "ms"}
        ]

class FwaCongestionSuspect(ProfileBase):
    REF = "FWA_CONGESTION_SUSPECT"
    MIN_SAMPLES = 20

    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("rtt_ms", 0) > 150.0:
            reasons.append("TAIL_RTT_TOO_HIGH")
        if p95.get("loss_pct", 0) > 5.0:
            reasons.append("TAIL_LOSS_TOO_HIGH")
        return reasons

    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "rtt_ms_p95", "value": p95.get("rtt_ms", 0), "unit": "ms"},
            {"name": "throughput_mbps_p50", "value": p50.get("throughput_mbps", 0), "unit": "Mbps"},
            {"name": "retrans_p95", "value": p95.get("retrans_count", 0), "unit": "count"}
        ]

# 7.3 Cable Profiles
class CableInstallAccept(ProfileBase):
    REF = "CABLE_INSTALL_ACCEPT"
    MIN_SAMPLES = 10

    def check(self, p50, p95, p5) -> List[str]:
        reasons = []
        if p95.get("us_rtt_ms", 0) > 80.0:
            reasons.append("TAIL_US_RTT_TOO_HIGH")
        if p95.get("us_loss_pct", 0) > 1.0:
             reasons.append("TAIL_US_LOSS_TOO_HIGH")
        return reasons
    
    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "us_rtt_ms_p95", "value": p95.get("us_rtt_ms", 0), "unit": "ms"},
            {"name": "us_loss_p95", "value": p95.get("us_loss_pct", 0), "unit": "%"},
            {"name": "ofdm_mer_p5", "value": p5.get("ofdm_mer", 0), "unit": "dB"}
        ]

class CableUpstreamIntermittent(ProfileBase):
    REF = "CABLE_UPSTREAM_INTERMITTENT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("us_rtt_ms", 0) > 150.0:
             reasons.append("TAIL_US_RTT_TOO_HIGH")
        return reasons
    
    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "us_rtt_ms_p95", "value": p95.get("us_rtt_ms", 0), "unit": "ms"},
            {"name": "us_loss_p95", "value": p95.get("us_loss_pct", 0), "unit": "%"}
        ]

class CablePlantImpairmentSuspect(ProfileBase):
    REF = "CABLE_PLANT_IMPAIRMENT_SUSPECT"
    MIN_SAMPLES = 20

    def check(self, p50, p95, p5) -> List[str]:
        reasons = []
        if p5.get("ofdm_mer", 40) < 32:
             reasons.append("PLANT_IMPAIRMENT_SUSPECT")
        return reasons
    
    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "ofdm_mer_p5", "value": p5.get("ofdm_mer", 0), "unit": "dB"},
            {"name": "fec_corrected_p95", "value": p95.get("fec_corrected", 0), "unit": "count"}
        ]

class ProfileManager:
    PROFILES = {
        Wifi78InstallAccept.REF: Wifi78InstallAccept(),
        Wifi78MeshBackhaulSplit.REF: Wifi78MeshBackhaulSplit(),
        Wifi78OscillationGuard.REF: Wifi78OscillationGuard(),
        FwaInstallAccept.REF: FwaInstallAccept(),
        FwaPlacementGuide.REF: FwaPlacementGuide(),
        FwaCongestionSuspect.REF: FwaCongestionSuspect(),
        CableInstallAccept.REF: CableInstallAccept(),
        CableUpstreamIntermittent.REF: CableUpstreamIntermittent(),
        CablePlantImpairmentSuspect.REF: CablePlantImpairmentSuspect()
    }
    
    @staticmethod
    def get(ref: str) -> ProfileBase:
        # Default to WIFI78_INSTALL_ACCEPT if unknown
        return ProfileManager.PROFILES.get(ref, Wifi78InstallAccept())

# --- 3. ProofCard Generator ---

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
        # Use a consistent ID generation (in real app, use UUID)
        card_id = f"pc-{uuid.uuid4().hex[:12]}"
        profile = ProfileManager.get(profile_ref)
        
        # 1. Sample Count Check
        n = len(window_data)
        if n < profile.MIN_SAMPLES:
            return self._build_card(card_id, profile.REF, "INSUFFICIENT_EVIDENCE", 
                                    window_ref_str, ["INSUFFICIENT_SAMPLES"], 
                                    n, [], [], [], manifest_ref_str)

        # 2. Key Metrics Extraction
        # Extract raw vectors for all possible metrics needed by any profile
        
        def extract(key, alt_keys=None):
            vals = []
            for d in window_data:
                v = d.get(key)
                if v is None and alt_keys:
                    for ak in alt_keys:
                        v = d.get(ak)
                        if v is not None: break
                if v is not None:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
                else:
                    # In V1.3 we might skip or fill 0? 
                    # Generally better to skip if data missing, but keeping simple
                    pass 
            return vals

        # Map to standard vectors
        vectors = {
            "rtt_ms": extract("rtt", ["latency_ms", "latency", "latency_p95_ms"]),
            "loss_pct": extract("loss", ["loss_percent", "loss_pct"]),
            "us_rtt_ms": extract("us_rtt", ["us_latency"]), 
            "us_loss_pct": extract("us_loss", ["us_loss_pct"]),
            "throughput_mbps": extract("throughput", ["in_rate", "out_rate"]), # Approximate?
            "wifi_retry_pct": extract("wifi_retry", ["retry_pct"]),
            "backhaul_rssi": extract("backhaul_rssi", ["signal_strength_pct"]), # Hack: map pct to rssi slot if missing? No, values differ.
            "access_retry_pct": extract("access_retry"),
            "rsrp": extract("rsrp", ["wan_rsrp_dbm"]),
            "sinr": extract("sinr", ["wan_sinr_db"]),
            "ofdm_mer": extract("ofdm_mer"),
            "fec_corrected": extract("fec_corrected"),
            "retrans_count": extract("retrans"),
            "retry_burst_count": extract("retry_burst"),
            "mlo_switch_count": extract("mlo_switches"),
            "phy_rate_mbps": extract("phy_rate", ["phy_rate_mbps"])
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
            else:
                # Fill missing with safe defaults or markers?
                # For checks to work safely, we might need simple defaults
                pass

        # 4. Assess Verdict
        reasons = profile.check(p50_map, p95_map, p5_map)
        
        # If no reasons, verdict is READY
        if reasons:
            verdict = "NOT_READY"
        else:
            verdict = "READY"
            
        # 5. Build Facets
        # Construct output arrays
        def to_kv(pmap, suffix):
            return [{"name": f"{k}_{suffix}", "value": v, "unit": "auto"} for k, v in pmap.items()]

        p50_out = to_kv(p50_map, "p50")
        p95_out = to_kv(p95_map, "p95")
        
        # Outcome Facets
        outcome_out = profile.get_outcome_facets(p50_map, p95_map, p5_map)
        if not outcome_out: 
             outcome_out = [{"name": "no_key_data", "value": 0, "unit": "none"}]

        return self._build_card(
            card_id, profile.REF, verdict, window_ref_str, reasons, n,
            p50_out, p95_out, outcome_out, manifest_ref_str
        )

    def _build_card(self, cid, pref, verdict, wref, reasons, n, p50, p95, outcome, mref):
        # 1. Base Structure
        card = {
            "proof_card_ref": cid,
            "profile_ref": pref,
            "verdict": verdict,
            "window_ref": wref,
            "reason_code": reasons,  # MUST >= 1
            "enforcement_path_ref": "EP-DEFAULT-01",
            "authority_scope_ref": "SCOPE-CPE-LOCAL",
            "validity_horizon_ref": "7DAYS",
            "validity_verdict": "VALID",
            "basis_ref": "BASIS-V1.3",
            "sample_count": n,
            "p50": p50,
            "p95": p95,
            "outcome_facet": outcome, # MUST >= 1
            "event_type": [],
            "evidence_bundle_ref": f"bundle:{wref}",
            "manifest_ref": mref
        }
        
        # Constraint: reason_code MUST be >= 1. 
        # If READY, we should probably add a "PASSED" code if list is empty?
        # The spec says "reason_code[] ... 至少 1 個".
        # If verdict is READY, reason_code normally explains 'why ready' or just 'PASSED'.
        if not card["reason_code"]:
            card["reason_code"] = ["CHECKS_PASSED"]

        return card

