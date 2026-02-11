"""
Tests for M13A_privacy_framework — Privacy/Admissibility hooks.
"""

import unittest
from dae_p1.M13A_privacy_framework import (
    AttemptCtx, PrivacyConfig, ProfilePolicy, ByusePolicy, EgressGateConfig,
    privacy_check, byuse_qualify, egress_gate, compute_admission,
    PrivacyResult, ByuseResult, load_privacy_config,
)


def _default_cfg() -> PrivacyConfig:
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
                    "policy_snapshot_ref", "window_policy_id", "window_ref",
                    "privacy_policy_ref", "disclosure_scope_ref",
                ],
                on_missing="NOT_CLOSURE_GRADE",
            ),
        },
        egress_gate=EgressGateConfig(),
    )


class TestPrivacyCheck(unittest.TestCase):
    """Hook B — Privacy Validity Check."""

    def test_not_applicable_when_precondition_false(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(profile_ref="WIFI78_INSTALL_ACCEPT")
        result = privacy_check(ctx, cfg)
        self.assertEqual(result.verdict, "NOT_APPLICABLE")
        self.assertIsNone(result.admission_override)

    def test_pass_when_all_refs_present(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(
            profile_ref="PROFILE_OPENRAN_RIC",
            privacy_policy_ref="PP-001",
            disclosure_scope_ref="SCOPE-001",
            retention_ref="RET-7D",
        )
        result = privacy_check(ctx, cfg)
        self.assertEqual(result.verdict, "PASS")
        self.assertIsNone(result.admission_override)
        self.assertIn("RC_PRIVACY_PASS", result.reason_code)

    def test_fail_missing_privacy_policy(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(
            profile_ref="PROFILE_OPENRAN_RIC",
            # privacy_policy_ref missing
            disclosure_scope_ref="SCOPE-001",
            retention_ref="RET-7D",
        )
        result = privacy_check(ctx, cfg)
        self.assertEqual(result.verdict, "FAIL")
        self.assertEqual(result.admission_override, "DENY")
        self.assertIn("PRIVACY_POLICY_MISSING", result.missing)

    def test_fail_missing_scope(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(
            profile_ref="PROFILE_OPENRAN_RIC",
            privacy_policy_ref="PP-001",
            # disclosure_scope_ref missing
            retention_ref="RET-7D",
        )
        result = privacy_check(ctx, cfg)
        self.assertEqual(result.verdict, "FAIL")
        self.assertIn("SCOPE_UNBOUND", result.missing)

    def test_fail_policy_drift(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(
            profile_ref="PROFILE_OPENRAN_RIC",
            privacy_policy_ref="PP-001",
            disclosure_scope_ref="SCOPE-001",
            retention_ref="RET-7D",
            privacy_policy_version="v2",
            expected_policy_version="v3",
        )
        result = privacy_check(ctx, cfg)
        self.assertEqual(result.verdict, "FAIL")
        self.assertIn("PRIVACY_STALE", result.missing)
        self.assertIn("RC_POLICY_DRIFT", result.reason_code)

    def test_unknown_profile_uses_defaults(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(profile_ref="UNKNOWN_PROFILE")
        result = privacy_check(ctx, cfg)
        # Default ProfilePolicy has privacy_validity_precondition=False
        self.assertEqual(result.verdict, "NOT_APPLICABLE")


class TestByuseQualify(unittest.TestCase):
    """Hook D — BYUSE Triggered Requiredness."""

    def test_not_triggered_when_no_context(self):
        cfg = _default_cfg()
        ctx = AttemptCtx()
        result = byuse_qualify(ctx, cfg)
        self.assertFalse(result.is_triggered)
        self.assertEqual(result.evidence_grade_floor, "DELIVERY_GRADE")

    def test_qualified_when_all_refs_present(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(
            byuse_context_ref="SUPPORT_CLOSURE",
            window_ref="W-001",
            privacy_policy_ref="PP-001",
            disclosure_scope_ref="SCOPE-001",
            version_refs={
                "policy_snapshot_ref": "SNAP-001",
                "window_policy_id": "WP-001",
            },
        )
        result = byuse_qualify(ctx, cfg)
        self.assertTrue(result.is_triggered)
        self.assertEqual(result.evidence_grade_floor, "PARTIAL_RELIANCE")
        self.assertIn("RC_BYUSE_QUALIFIED", result.reason_code)

    def test_missing_refs_downgrades(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(
            byuse_context_ref="SUPPORT_CLOSURE",
            window_ref="W-001",
            # Missing: policy_snapshot_ref, window_policy_id, privacy_policy_ref, disclosure_scope_ref
        )
        result = byuse_qualify(ctx, cfg)
        self.assertTrue(result.is_triggered)
        self.assertEqual(result.evidence_grade_floor, "NOT_CLOSURE_GRADE")
        self.assertIsNotNone(result.upgrade_requirements_ref)
        self.assertGreater(len(result.missing), 0)

    def test_unknown_byuse_context(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(byuse_context_ref="UNKNOWN_CONTEXT")
        result = byuse_qualify(ctx, cfg)
        self.assertTrue(result.is_triggered)
        self.assertEqual(result.evidence_grade_floor, "NOT_CLOSURE_GRADE")
        self.assertIn("RC_BYUSE_UNKNOWN_CONTEXT", result.reason_code)


class TestEgressGate(unittest.TestCase):
    """Hook C — Minimal-Disclosure Egress Gate."""

    def test_default_min_only(self):
        cfg = _default_cfg()
        ctx = AttemptCtx()
        result = egress_gate(ctx, {}, cfg)
        self.assertTrue(result.allowed)
        self.assertEqual(result.mode, "MIN_ONLY")
        self.assertTrue(result.egress_receipt_ref.startswith("EGRESS-REC-"))

    def test_full_export_denied_without_authority(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(proposed_egress="full_with_auth")
        result = egress_gate(ctx, {}, cfg)
        self.assertFalse(result.allowed)
        self.assertEqual(result.mode, "DENY")

    def test_full_export_allowed_with_authority(self):
        cfg = _default_cfg()
        ctx = AttemptCtx(
            proposed_egress="full_with_auth",
            disclosure_scope_ref="SCOPE-001",
            authority_scope_ref="AUTH-001",
        )
        result = egress_gate(ctx, {}, cfg)
        self.assertTrue(result.allowed)
        self.assertEqual(result.mode, "PRIV_ALLOWED")


class TestComputeAdmission(unittest.TestCase):
    """TABLE 0 — Verdict × Privacy × BYUSE → Evidence Grade + Admission."""

    def test_ready_pass_no_byuse(self):
        result = compute_admission(
            "READY",
            PrivacyResult(verdict="PASS"),
            ByuseResult(is_triggered=False),
            ProfilePolicy(),
        )
        self.assertEqual(result["evidence_grade"], "DELIVERY_GRADE")
        self.assertEqual(result["admission_verdict"], "ADMIT")

    def test_ready_pass_with_byuse_qualified(self):
        result = compute_admission(
            "READY",
            PrivacyResult(verdict="PASS"),
            ByuseResult(is_triggered=True, evidence_grade_floor="PARTIAL_RELIANCE"),
            ProfilePolicy(),
        )
        self.assertEqual(result["evidence_grade"], "PARTIAL_RELIANCE")
        self.assertEqual(result["admission_verdict"], "ADMIT")

    def test_ready_pass_with_byuse_missing(self):
        result = compute_admission(
            "READY",
            PrivacyResult(verdict="PASS"),
            ByuseResult(is_triggered=True, evidence_grade_floor="NOT_CLOSURE_GRADE"),
            ProfilePolicy(),
        )
        self.assertEqual(result["evidence_grade"], "NOT_CLOSURE_GRADE")
        self.assertEqual(result["admission_effect"], "SCOPE_REDUCTION")

    def test_not_ready_degrades(self):
        result = compute_admission(
            "NOT_READY",
            PrivacyResult(verdict="PASS"),
            ByuseResult(is_triggered=False),
            ProfilePolicy(),
        )
        self.assertEqual(result["evidence_grade"], "NOT_CLOSURE_GRADE")
        self.assertEqual(result["admission_verdict"], "DEGRADE")

    def test_insufficient_degrades(self):
        result = compute_admission(
            "INSUFFICIENT_EVIDENCE",
            PrivacyResult(verdict="NOT_APPLICABLE"),
            ByuseResult(is_triggered=False),
            ProfilePolicy(),
        )
        self.assertEqual(result["evidence_grade"], "NOT_CLOSURE_GRADE")
        self.assertEqual(result["admission_verdict"], "DEGRADE")

    def test_privacy_fail_deny(self):
        policy = ProfilePolicy(on_privacy_fail="DENY")
        result = compute_admission(
            "READY",
            PrivacyResult(verdict="FAIL", admission_override="DENY"),
            ByuseResult(is_triggered=False),
            policy,
        )
        self.assertEqual(result["evidence_grade"], "NOT_CLOSURE_GRADE")
        self.assertEqual(result["admission_verdict"], "DENY")
        self.assertEqual(result["admission_effect"], "FREEZE_EGRESS")

    def test_privacy_fail_degrade(self):
        policy = ProfilePolicy(on_privacy_fail="DEGRADE")
        result = compute_admission(
            "READY",
            PrivacyResult(verdict="FAIL", admission_override="DEGRADE"),
            ByuseResult(is_triggered=False),
            policy,
        )
        self.assertEqual(result["evidence_grade"], "NOT_CLOSURE_GRADE")
        self.assertEqual(result["admission_verdict"], "DEGRADE")
        self.assertEqual(result["admission_effect"], "EGRESS_MIN_ONLY")

    def test_privacy_inconclusive(self):
        result = compute_admission(
            "READY",
            PrivacyResult(verdict="INCONCLUSIVE"),
            ByuseResult(is_triggered=False),
            ProfilePolicy(),
        )
        self.assertEqual(result["evidence_grade"], "NOT_CLOSURE_GRADE")
        self.assertEqual(result["admission_verdict"], "DEGRADE")


class TestConfigLoader(unittest.TestCase):
    """Config loader with fallback defaults."""

    def test_load_nonexistent_falls_back(self):
        cfg = load_privacy_config("/nonexistent/path.yaml")
        self.assertIn("PROFILE_OPENRAN_RIC", cfg.profile_policies)
        self.assertIn("SUPPORT_CLOSURE", cfg.byuse_policies)

    def test_load_none_falls_back(self):
        cfg = load_privacy_config(None)
        self.assertIsNotNone(cfg)


if __name__ == "__main__":
    unittest.main()
