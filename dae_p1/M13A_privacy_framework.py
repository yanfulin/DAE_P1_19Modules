"""
M13A — Privacy / Admissibility Framework for ProofCard V1.4

Implements four privacy hooks that sit alongside the existing V1.3 ProofCard
pipeline without modifying it:

  A) PC-Min / PC-Priv split
  B) Privacy Validity Check  (privacy_check)
  C) Egress Gate             (egress_gate)
  D) BYUSE Triggered Upgrade (byuse_qualify)

Design principle: metadata-only governance — never inspects payload.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Literal
import uuid
import time
import os
import json

# ---------------------------------------------------------------------------
# 1.  Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ProfilePolicy:
    """Per-profile privacy policy configuration."""
    privacy_applicability: str = "METADATA_ONLY"        # open set token
    privacy_validity_precondition: bool = False
    on_privacy_fail: str = "DEGRADE"                    # DENY | DEGRADE
    default_redaction_profile: str = "REDACT.MIN"
    default_disclosure_scope: str = "SCOPE.MIN"
    default_retention: str = "RET.7D"


@dataclass
class ByusePolicy:
    """Policy for a specific BYUSE context (e.g. SUPPORT_CLOSURE)."""
    required_refs: List[str] = field(default_factory=list)
    on_missing: str = "NOT_CLOSURE_GRADE"


@dataclass
class EgressGateConfig:
    """Egress gate settings."""
    default_mode: str = "MIN_ONLY"
    allow_priv_export_requires: List[str] = field(
        default_factory=lambda: ["disclosure_scope_ref", "authority_scope_ref"]
    )
    always_emit_egress_receipt: bool = True


@dataclass
class PrivacyConfig:
    """Top-level privacy configuration container."""
    profile_policies: Dict[str, ProfilePolicy] = field(default_factory=dict)
    byuse_policies: Dict[str, ByusePolicy] = field(default_factory=dict)
    egress_gate: EgressGateConfig = field(default_factory=EgressGateConfig)

    # Convenience: fall back to a sensible default for unknown profiles
    def get_profile_policy(self, profile_ref: str) -> ProfilePolicy:
        return self.profile_policies.get(profile_ref, ProfilePolicy())


# --- Pipeline context -------------------------------------------------

@dataclass
class AttemptCtx:
    """Immutable context for a single attempt flowing through the pipeline."""
    attempt_id: str = ""
    profile_ref: str = ""
    enforcement_path_id: str = "EP-DEFAULT-01"
    gate_ref: str = "GATE-DEFAULT-01"
    window_ref: str = ""

    # Version refs
    version_refs: Dict[str, str] = field(default_factory=dict)

    # Privacy governance refs (supplied by caller / DB)
    privacy_policy_ref: Optional[str] = None
    purpose_ref: Optional[str] = None
    retention_ref: Optional[str] = None
    disclosure_scope_ref: Optional[str] = None
    redaction_profile_ref: Optional[str] = None
    authority_scope_ref: Optional[str] = None

    # Staleness markers (epoch or version string; None = not provided)
    privacy_policy_version: Optional[str] = None
    expected_policy_version: Optional[str] = None

    # BYUSE
    byuse_context_ref: Optional[str] = None  # e.g. "SUPPORT_CLOSURE"

    # Egress
    proposed_egress: Optional[str] = None   # "min_only" | "full_with_auth"


# --- Result types -----------------------------------------------------

@dataclass
class PrivacyResult:
    verdict: str = "NOT_APPLICABLE"       # PASS | FAIL | INCONCLUSIVE | NOT_APPLICABLE
    priv_refs: Dict[str, Optional[str]] = field(default_factory=dict)
    missing: List[str] = field(default_factory=list)
    reason_code: List[str] = field(default_factory=list)
    admission_override: Optional[str] = None   # "DENY" | "DEGRADE" | None


@dataclass
class ByuseResult:
    is_triggered: bool = False
    required_additions: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    upgrade_requirements_ref: Optional[str] = None
    evidence_grade_floor: str = "DELIVERY_GRADE"
    reason_code: List[str] = field(default_factory=list)


@dataclass
class EgressResult:
    allowed: bool = True
    mode: str = "MIN_ONLY"               # MIN_ONLY | PRIV_ALLOWED | DENY
    egress_receipt_ref: str = ""
    disclosed_fields_ref: Optional[str] = None
    reason_code: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 2.  Core Functions
# ---------------------------------------------------------------------------

def privacy_check(ctx: AttemptCtx, cfg: PrivacyConfig) -> PrivacyResult:
    """
    Hook B — Privacy Validity Check.

    Does NOT inspect payload.  Only checks existence / validity / staleness
    of privacy governance refs under the profile policy.
    """
    policy = cfg.get_profile_policy(ctx.profile_ref)

    # If privacy is not applicable for this profile, short-circuit
    if not policy.privacy_validity_precondition:
        return PrivacyResult(
            verdict="NOT_APPLICABLE",
            priv_refs=_collect_priv_refs(ctx),
            reason_code=["RC_PRIVACY_NOT_APPLICABLE"],
        )

    missing: List[str] = []
    reason_codes: List[str] = []

    # --- existence checks ---
    if not ctx.privacy_policy_ref:
        missing.append("PRIVACY_POLICY_MISSING")
    if not ctx.disclosure_scope_ref:
        missing.append("SCOPE_UNBOUND")
    if not ctx.retention_ref:
        missing.append("RETENTION_UNKNOWN")

    # --- staleness check ---
    if (ctx.privacy_policy_version and ctx.expected_policy_version
            and ctx.privacy_policy_version != ctx.expected_policy_version):
        missing.append("PRIVACY_STALE")
        reason_codes.append("RC_POLICY_DRIFT")

    # --- verdict ---
    if missing:
        verdict = "FAIL"
        reason_codes.append("RC_PRIVACY_FAIL")
        admission_override = policy.on_privacy_fail   # DENY or DEGRADE
    else:
        verdict = "PASS"
        reason_codes.append("RC_PRIVACY_PASS")
        admission_override = None

    return PrivacyResult(
        verdict=verdict,
        priv_refs=_collect_priv_refs(ctx),
        missing=missing,
        reason_code=reason_codes,
        admission_override=admission_override,
    )


def byuse_qualify(ctx: AttemptCtx, cfg: PrivacyConfig) -> ByuseResult:
    """
    Hook D — BYUSE Triggered Requiredness.

    When ctx.byuse_context_ref is set, enforce the required hooks for that
    context.  Missing refs → NOT_CLOSURE_GRADE + upgrade_requirements_ref.
    """
    if not ctx.byuse_context_ref:
        return ByuseResult(
            is_triggered=False,
            evidence_grade_floor="DELIVERY_GRADE",
        )

    byuse_policy = cfg.byuse_policies.get(ctx.byuse_context_ref)
    if byuse_policy is None:
        # Unknown BYUSE context — treat as not triggered but warn
        return ByuseResult(
            is_triggered=True,
            evidence_grade_floor="NOT_CLOSURE_GRADE",
            reason_code=["RC_BYUSE_UNKNOWN_CONTEXT"],
            missing=["BYUSE_POLICY_UNDEFINED"],
        )

    # Check which required refs are missing
    ref_map = {
        "policy_snapshot_ref": ctx.version_refs.get("policy_snapshot_ref"),
        "window_policy_id": ctx.version_refs.get("window_policy_id"),
        "window_ref": ctx.window_ref or None,
        "privacy_policy_ref": ctx.privacy_policy_ref,
        "disclosure_scope_ref": ctx.disclosure_scope_ref,
    }

    missing: List[str] = []
    for ref_name in byuse_policy.required_refs:
        if not ref_map.get(ref_name):
            missing.append(ref_name.upper())

    if missing:
        upgrade_ref = f"UPGRADE-{ctx.attempt_id or uuid.uuid4().hex[:8]}"
        return ByuseResult(
            is_triggered=True,
            required_additions=byuse_policy.required_refs,
            missing=missing,
            upgrade_requirements_ref=upgrade_ref,
            evidence_grade_floor=byuse_policy.on_missing,   # NOT_CLOSURE_GRADE
            reason_code=["RC_BYUSE_MISSING_REFS"],
        )

    return ByuseResult(
        is_triggered=True,
        evidence_grade_floor="PARTIAL_RELIANCE",
        reason_code=["RC_BYUSE_QUALIFIED"],
    )


def egress_gate(ctx: AttemptCtx, proof_card: Dict[str, Any],
                cfg: PrivacyConfig) -> EgressResult:
    """
    Hook C — Minimal-Disclosure Egress Gate.

    Default: export PC-Min only.
    PC-Priv export requires authority/delegation + disclosure_scope_ref.
    Always generates an attempt-bound egress_receipt_ref.
    """
    eg = cfg.egress_gate
    receipt_ref = f"EGRESS-REC-{uuid.uuid4().hex[:12]}"
    reason_codes: List[str] = []

    requested_mode = ctx.proposed_egress or "min_only"

    if requested_mode == "min_only" or eg.default_mode == "MIN_ONLY" and requested_mode != "full_with_auth":
        return EgressResult(
            allowed=True,
            mode="MIN_ONLY",
            egress_receipt_ref=receipt_ref,
            reason_code=["RC_EGRESS_MIN_ONLY"],
        )

    # Full (priv) export requested — check authority
    missing_for_priv: List[str] = []
    for req in eg.allow_priv_export_requires:
        val = getattr(ctx, req, None)
        if not val:
            missing_for_priv.append(req.upper())

    if missing_for_priv:
        reason_codes.append("RC_EGRESS_DENIED_MISSING_AUTH")
        return EgressResult(
            allowed=False,
            mode="DENY",
            egress_receipt_ref=receipt_ref,
            reason_code=reason_codes,
        )

    # All checks passed — allow priv export
    return EgressResult(
        allowed=True,
        mode="PRIV_ALLOWED",
        egress_receipt_ref=receipt_ref,
        disclosed_fields_ref=ctx.disclosure_scope_ref,
        reason_code=["RC_EGRESS_PRIV_ALLOWED"],
    )


# ---------------------------------------------------------------------------
# 3.  Verdict / Grade Mapping  (TABLE 0)
# ---------------------------------------------------------------------------

def compute_admission(
    v13_verdict: str,
    privacy_result: PrivacyResult,
    byuse_result: ByuseResult,
    profile_policy: ProfilePolicy,
) -> Dict[str, str]:
    """
    Maps (V1.3 verdict × privacy verdict × BYUSE) → (evidence_grade, admission_verdict).

    Returns dict with keys: evidence_grade, admission_verdict, admission_effect.
    """
    pv = privacy_result.verdict   # PASS | FAIL | INCONCLUSIVE | NOT_APPLICABLE

    # --- Privacy override takes precedence ---
    if pv == "FAIL":
        return {
            "evidence_grade": "NOT_CLOSURE_GRADE",
            "admission_verdict": privacy_result.admission_override or profile_policy.on_privacy_fail,
            "admission_effect": "FREEZE_EGRESS" if profile_policy.on_privacy_fail == "DENY" else "EGRESS_MIN_ONLY",
        }

    if pv == "INCONCLUSIVE":
        return {
            "evidence_grade": "NOT_CLOSURE_GRADE",
            "admission_verdict": "DEGRADE",
            "admission_effect": "EGRESS_MIN_ONLY",
        }

    # --- Privacy passed or N/A — use V1.3 verdict ---
    if v13_verdict in ("NOT_READY",):
        return {
            "evidence_grade": "NOT_CLOSURE_GRADE",
            "admission_verdict": "DEGRADE",
            "admission_effect": "NONE",
        }

    if v13_verdict == "INSUFFICIENT_EVIDENCE":
        return {
            "evidence_grade": "NOT_CLOSURE_GRADE",
            "admission_verdict": "DEGRADE",
            "admission_effect": "NONE",
        }

    # v13_verdict == READY
    if byuse_result.is_triggered:
        grade = byuse_result.evidence_grade_floor   # PARTIAL_RELIANCE or NOT_CLOSURE_GRADE
        return {
            "evidence_grade": grade,
            "admission_verdict": "ADMIT",
            "admission_effect": "NONE" if grade == "PARTIAL_RELIANCE" else "SCOPE_REDUCTION",
        }

    return {
        "evidence_grade": "DELIVERY_GRADE",
        "admission_verdict": "ADMIT",
        "admission_effect": "NONE",
    }


# ---------------------------------------------------------------------------
# 4.  Configuration Loader
# ---------------------------------------------------------------------------

def load_privacy_config(config_path: Optional[str] = None) -> PrivacyConfig:
    """
    Load privacy configuration from a YAML file.
    Falls back to built-in defaults when no file is found or PyYAML
    is not installed.
    """
    if config_path and os.path.isfile(config_path):
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            return _parse_config(raw)
        except ImportError:
            pass  # no yaml — fall through to defaults
        except Exception:
            pass

    return _default_config()


def _parse_config(raw: Dict[str, Any]) -> PrivacyConfig:
    profile_policies: Dict[str, ProfilePolicy] = {}
    for name, praw in (raw.get("profile_policies") or {}).items():
        profile_policies[name] = ProfilePolicy(**{
            k: v for k, v in praw.items()
            if k in ProfilePolicy.__dataclass_fields__
        })

    byuse_policies: Dict[str, ByusePolicy] = {}
    for name, braw in (raw.get("byuse_policies") or {}).items():
        byuse_policies[name] = ByusePolicy(**{
            k: v for k, v in braw.items()
            if k in ByusePolicy.__dataclass_fields__
        })

    eg_raw = raw.get("egress_gate") or {}
    egress = EgressGateConfig(
        default_mode=eg_raw.get("default_mode", "MIN_ONLY"),
        allow_priv_export_requires=eg_raw.get("allow_priv_export_if", {}).get(
            "requires", ["disclosure_scope_ref", "authority_scope_ref"]
        ),
        always_emit_egress_receipt=eg_raw.get("always_emit_egress_receipt", True),
    )

    return PrivacyConfig(
        profile_policies=profile_policies,
        byuse_policies=byuse_policies,
        egress_gate=egress,
    )


def _default_config() -> PrivacyConfig:
    """Built-in defaults so the system works even without a YAML file."""
    return PrivacyConfig(
        profile_policies={
            "PROFILE_OPENRAN_RIC": ProfilePolicy(
                privacy_applicability="USER_AFFECTING",
                privacy_validity_precondition=True,
                on_privacy_fail="DENY",
            ),
            "WIFI78_INSTALL_ACCEPT": ProfilePolicy(
                privacy_applicability="METADATA_ONLY",
                privacy_validity_precondition=False,
                on_privacy_fail="DEGRADE",
            ),
        },
        byuse_policies={
            "SUPPORT_CLOSURE": ByusePolicy(
                required_refs=[
                    "policy_snapshot_ref",
                    "window_policy_id",
                    "window_ref",
                    "privacy_policy_ref",
                    "disclosure_scope_ref",
                ],
                on_missing="NOT_CLOSURE_GRADE",
            ),
        },
        egress_gate=EgressGateConfig(),
    )


# ---------------------------------------------------------------------------
# 5.  Helpers
# ---------------------------------------------------------------------------

def _collect_priv_refs(ctx: AttemptCtx) -> Dict[str, Optional[str]]:
    return {
        "privacy_policy_ref": ctx.privacy_policy_ref,
        "purpose_ref": ctx.purpose_ref,
        "retention_ref": ctx.retention_ref,
        "disclosure_scope_ref": ctx.disclosure_scope_ref,
        "redaction_profile_ref": ctx.redaction_profile_ref,
    }
