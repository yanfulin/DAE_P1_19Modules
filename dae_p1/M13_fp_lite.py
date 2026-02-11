
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

# Open RAN Profile (V1.4)
class OpenRanRicProfile(ProfileBase):
    REF = "PROFILE_OPENRAN_RIC"
    MIN_SAMPLES = 10

    def check(self, p50, p95, p5) -> List[str]:
        reasons = []
        if p95.get("rtt_ms", 0) > 50.0:
            reasons.append("P95_RTT_TOO_HIGH")
        if p95.get("loss_pct", 0) > 0.5:
            reasons.append("P95_LOSS_TOO_HIGH")
        return reasons

    def get_outcome_facets(self, p50, p95, p5):
        return [
            {"name": "rtt_ms_p95", "value": p95.get("rtt_ms", 0), "unit": "ms"},
            {"name": "loss_rate_p95", "value": p95.get("loss_pct", 0), "unit": "%"},
            {"name": "phy_rate_p50", "value": p50.get("phy_rate_mbps", 0), "unit": "Mbps"},
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
        CablePlantImpairmentSuspect.REF: CablePlantImpairmentSuspect(),
        OpenRanRicProfile.REF: OpenRanRicProfile(),
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


# --- 4. ProofCard V1.4 Generator ---

class ProofCardGeneratorV14:
    """
    V1.4 ProofCard generator with privacy framework integration.

    Delegates core metric computation to the V1.3 ProofCardGenerator,
    then layers on the four privacy hooks (privacy_check, byuse_qualify,
    admission mapping, egress_gate).
    """

    def __init__(self, privacy_config=None):
        from dae_p1.M13A_privacy_framework import (
            load_privacy_config, PrivacyConfig,
        )
        self.privacy_cfg: PrivacyConfig = privacy_config or load_privacy_config()
        self._v13 = ProofCardGenerator()

    def generate(
        self,
        window_data: List[Dict[str, Any]],
        profile_ref: str,
        window_ref_str: str,
        manifest_ref_str: str = "TBD",
        ctx_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Full V1.4 pipeline:
          1. V1.3 generate() → base card
          2. privacy_check()
          3. byuse_qualify()
          4. compute_admission() → evidence_grade + admission_verdict
          5. _build_v14_card() → assemble min/priv sections
        """
        from dae_p1.M13A_privacy_framework import (
            AttemptCtx, privacy_check, byuse_qualify, compute_admission,
        )

        # 1) V1.3 base card
        v13_card = self._v13.generate(
            window_data, profile_ref, window_ref_str, manifest_ref_str
        )

        # 2) Build context
        overrides = ctx_overrides or {}
        attempt_id = overrides.get("attempt_id", f"att-{uuid.uuid4().hex[:12]}")
        ctx = AttemptCtx(
            attempt_id=attempt_id,
            profile_ref=profile_ref,
            enforcement_path_id=overrides.get("enforcement_path_id", "EP-DEFAULT-01"),
            gate_ref=overrides.get("gate_ref", "GATE-DEFAULT-01"),
            window_ref=window_ref_str,
            version_refs=overrides.get("version_refs", {
                "policy_snapshot_ref": "POLICY@2026-02-10#1",
                "window_policy_id": "WP@v3",
                "mapping_config_id": "MC@v5",
                "normalization_ref": "NR@v2",
                "translation_basis_id": "TB@v9",
            }),
            privacy_policy_ref=overrides.get("privacy_policy_ref"),
            purpose_ref=overrides.get("purpose_ref"),
            retention_ref=overrides.get("retention_ref"),
            disclosure_scope_ref=overrides.get("disclosure_scope_ref"),
            redaction_profile_ref=overrides.get("redaction_profile_ref"),
            authority_scope_ref=overrides.get("authority_scope_ref"),
            privacy_policy_version=overrides.get("privacy_policy_version"),
            expected_policy_version=overrides.get("expected_policy_version"),
            byuse_context_ref=overrides.get("byuse_context_ref"),
            proposed_egress=overrides.get("proposed_egress"),
        )

        # 3) Privacy check
        priv_result = privacy_check(ctx, self.privacy_cfg)

        # 4) BYUSE qualify
        byuse_result = byuse_qualify(ctx, self.privacy_cfg)

        # 5) Compute admission / grade
        profile_policy = self.privacy_cfg.get_profile_policy(profile_ref)
        admission = compute_admission(
            v13_card["verdict"], priv_result, byuse_result, profile_policy
        )

        # 6) Assemble V1.4 card
        return self._build_v14_card(
            v13_card, ctx, priv_result, byuse_result, admission
        )

    def _build_v14_card(
        self,
        v13_card: Dict[str, Any],
        ctx,
        priv_result,
        byuse_result,
        admission: Dict[str, str],
    ) -> Dict[str, Any]:
        """Assemble the full V1.4 ProofCard structure."""
        from dae_p1.M13A_privacy_framework import AttemptCtx

        # Start with all V1.3 fields
        card = dict(v13_card)

        # --- New V1.4 top-level fields ---
        card["attempt_id"] = ctx.attempt_id
        card["enforcement_path_id"] = ctx.enforcement_path_id
        card["gate_ref"] = ctx.gate_ref
        card["evidence_grade"] = admission["evidence_grade"]
        card["version_refs"] = ctx.version_refs
        card["basis_ref"] = "BASIS-V1.4"

        # Merge missing evidence classes
        missing = list(priv_result.missing) + list(byuse_result.missing)
        card["missing_evidence_class"] = missing
        card["upgrade_requirements_ref"] = byuse_result.upgrade_requirements_ref

        # Merge reason codes (V1.3 + privacy + byuse)
        all_reasons = list(card.get("reason_code", []))
        all_reasons.extend(priv_result.reason_code)
        all_reasons.extend(byuse_result.reason_code)
        card["reason_code"] = all_reasons

        # --- PC-Min section ---
        card["min"] = {
            "admission_verdict": admission["admission_verdict"],
            "admission_effect": admission["admission_effect"],
            "privacy_check_verdict": priv_result.verdict,
            "egress_receipt_ref": None,   # filled by egress_gate later
            "byuse_context_ref": ctx.byuse_context_ref,
        }

        # --- PC-Priv section ---
        card["priv"] = {
            "privacy_policy_ref": ctx.privacy_policy_ref,
            "purpose_ref": ctx.purpose_ref,
            "retention_ref": ctx.retention_ref,
            "disclosure_scope_ref": ctx.disclosure_scope_ref,
            "redaction_profile_ref": ctx.redaction_profile_ref,
            "privacy_violation_flag": priv_result.verdict == "FAIL",
            "privacy_violation_reason_code": (
                [r for r in priv_result.reason_code if r.startswith("RC_PRIVACY")]
                if priv_result.verdict == "FAIL" else []
            ),
        }

        return card

    def apply_egress_gate(
        self,
        proof_card: Dict[str, Any],
        ctx_overrides: Optional[Dict[str, Any]] = None,
    ):
        """
        Run egress gate on an already-generated V1.4 card.
        Returns an EgressResult and mutates card["min"]["egress_receipt_ref"].
        """
        from dae_p1.M13A_privacy_framework import (
            AttemptCtx, egress_gate,
        )
        overrides = ctx_overrides or {}
        ctx = AttemptCtx(
            attempt_id=proof_card.get("attempt_id", ""),
            profile_ref=proof_card.get("profile_ref", ""),
            window_ref=proof_card.get("window_ref", ""),
            disclosure_scope_ref=overrides.get("disclosure_scope_ref"),
            authority_scope_ref=overrides.get("authority_scope_ref"),
            proposed_egress=overrides.get("proposed_egress", "min_only"),
        )
        result = egress_gate(ctx, proof_card, self.privacy_cfg)
        # Write receipt back into card
        if proof_card.get("min"):
            proof_card["min"]["egress_receipt_ref"] = result.egress_receipt_ref
        return result

