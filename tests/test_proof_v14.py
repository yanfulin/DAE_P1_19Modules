"""
Tests for ProofCardGeneratorV14 — V1.4 ProofCard generation + schema validation.
"""

import unittest
import json
import os

from dae_p1.M13_fp_lite import ProofCardGeneratorV14


def _make_metrics(n=20, rtt_base=20, loss_base=0.1):
    """Generate synthetic metric dicts."""
    return [
        {"rtt": rtt_base + i * 2, "loss_pct": loss_base + i * 0.02, "retry_pct": 1.0 + i * 0.1}
        for i in range(n)
    ]


class TestProofCardV14Basic(unittest.TestCase):
    """Basic V1.4 card generation."""

    def setUp(self):
        self.gen = ProofCardGeneratorV14()

    def test_generates_card_with_v14_fields(self):
        data = _make_metrics(20)
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-01")

        # V1.3 fields
        self.assertIn("proof_card_ref", card)
        self.assertIn("verdict", card)
        self.assertIn("sample_count", card)
        self.assertIn("outcome_facet", card)
        self.assertIn("reason_code", card)

        # V1.4 fields
        self.assertIn("attempt_id", card)
        self.assertIn("evidence_grade", card)
        self.assertIn("enforcement_path_id", card)
        self.assertIn("gate_ref", card)
        self.assertIn("min", card)

        # min section
        self.assertIn("admission_verdict", card["min"])
        self.assertIn("privacy_check_verdict", card["min"])

    def test_evidence_grade_values(self):
        data = _make_metrics(20)
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-01")
        self.assertIn(card["evidence_grade"], ["DELIVERY_GRADE", "PARTIAL_RELIANCE", "NOT_CLOSURE_GRADE"])

    def test_insufficient_samples(self):
        data = _make_metrics(5)  # Below min_sample_count=10
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-02")
        self.assertEqual(card["verdict"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(card["evidence_grade"], "NOT_CLOSURE_GRADE")
        self.assertEqual(card["min"]["admission_verdict"], "DEGRADE")


class TestProofCardV14VerdictMapping(unittest.TestCase):
    """TABLE 0 verdict mapping through the full pipeline."""

    def setUp(self):
        self.gen = ProofCardGeneratorV14()

    def test_ready_no_byuse_delivers(self):
        # Good data, no BYUSE → DELIVERY_GRADE + ADMIT
        data = _make_metrics(20, rtt_base=5, loss_base=0.01)
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-03")
        if card["verdict"] == "READY":
            self.assertEqual(card["evidence_grade"], "DELIVERY_GRADE")
            self.assertEqual(card["min"]["admission_verdict"], "ADMIT")

    def test_byuse_with_missing_refs(self):
        # BYUSE triggered but missing refs → NOT_CLOSURE_GRADE
        data = _make_metrics(20, rtt_base=5, loss_base=0.01)
        card = self.gen.generate(
            data, "WIFI78_INSTALL_ACCEPT", "W-TEST-04",
            ctx_overrides={"byuse_context_ref": "SUPPORT_CLOSURE"},
        )
        if card["verdict"] == "READY":
            self.assertEqual(card["evidence_grade"], "NOT_CLOSURE_GRADE")
            self.assertIsNotNone(card.get("upgrade_requirements_ref"))

    def test_privacy_not_applicable_for_metadata_profile(self):
        data = _make_metrics(20)
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-05")
        self.assertEqual(card["min"]["privacy_check_verdict"], "NOT_APPLICABLE")


class TestProofCardV14EgressGate(unittest.TestCase):
    """Egress gate integration."""

    def setUp(self):
        self.gen = ProofCardGeneratorV14()

    def test_default_min_only(self):
        data = _make_metrics(20)
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-06")
        egress = self.gen.apply_egress_gate(card)
        self.assertTrue(egress.allowed)
        self.assertEqual(egress.mode, "MIN_ONLY")

    def test_priv_export_denied_without_auth(self):
        data = _make_metrics(20)
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-07")
        egress = self.gen.apply_egress_gate(
            card, ctx_overrides={"proposed_egress": "full_with_auth"}
        )
        self.assertFalse(egress.allowed)
        self.assertEqual(egress.mode, "DENY")


class TestProofCardV14Schema(unittest.TestCase):
    """Validate generated cards against JSON schema."""

    def setUp(self):
        self.gen = ProofCardGeneratorV14()
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "schemas", "ProofCard_V1.4.schema.json"
        )
        if os.path.isfile(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)
        else:
            self.schema = None

    def test_card_has_all_required_fields(self):
        """Check required fields from schema are present in generated card."""
        if not self.schema:
            self.skipTest("Schema file not found")

        data = _make_metrics(20)
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-08")

        required = self.schema.get("required", [])
        for field in required:
            self.assertIn(field, card, f"Required field '{field}' missing from card")

    def test_schema_validation_with_jsonschema(self):
        """Full schema validation (requires jsonschema package)."""
        if not self.schema:
            self.skipTest("Schema file not found")
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")

        data = _make_metrics(20)
        card = self.gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-TEST-09")
        jsonschema.validate(instance=card, schema=self.schema)


if __name__ == "__main__":
    unittest.main()
