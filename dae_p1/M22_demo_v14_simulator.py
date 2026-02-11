#!/usr/bin/env python3
"""
M22_demo_v14_simulator.py
V1.4 Demo Simulator - Generates 10 test cases matching TABLE 1 reference document
"""

import json
import os
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from dae_p1.M13_fp_lite import ProofCardGeneratorV14
from dae_p1.M13A_privacy_framework import (
    load_privacy_config,
    egress_gate,
    AttemptCtx,
    EgressResult
)


class V14DemoSimulator:
    """V1.4 Demo Simulator generating 10 test cases"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize simulator with privacy config"""
        self.privacy_config = load_privacy_config(config_path)
        self.generator = ProofCardGeneratorV14()

    def _generate_synthetic_window_data(self, num_samples: int = 20) -> List[Dict[str, Any]]:
        """Generate synthetic window data for testing (uses field names from M13_fp_lite)."""
        window_data = []
        for i in range(num_samples):
            sample = {
                "rtt": 20 + (i % 5) * 2,
                "loss_pct": 0.1 + (i % 3) * 0.05,
                "retry_pct": 1.0 + (i % 4) * 0.3,
            }
            window_data.append(sample)
        return window_data

    def _case_1_all_refs_no_byuse(self) -> Dict[str, Any]:
        """Case 1: All refs present, no BYUSE → READY + DELIVERY_GRADE"""
        return {
            "case_id": "case_01",
            "description": "All refs present, no BYUSE → READY + DELIVERY_GRADE",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": "PRIV@v4",
            "disclosure_scope_ref": "SCOPE.MIN",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": None,
            "window_policy_id": "WP-001",
            "expected": {
                "verdict": "READY",
                "evidence_grade": "DELIVERY_GRADE",
                "admission": "ADMIT",
                "privacy_check": "PASS"
            }
        }

    def _case_2_missing_privacy_policy(self) -> Dict[str, Any]:
        """Case 2: Missing privacy_policy_ref → NOT_CLOSURE_GRADE + DENY"""
        return {
            "case_id": "case_02",
            "description": "Missing privacy_policy_ref → NOT_CLOSURE_GRADE + DENY",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": None,  # Missing!
            "disclosure_scope_ref": "SCOPE.MIN",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": None,
            "window_policy_id": "WP-001",
            "expected": {
                "evidence_grade": "NOT_CLOSURE_GRADE",
                "admission": "DENY",
                "privacy_check": "FAIL"
            }
        }

    def _case_3_stale_privacy_policy(self) -> Dict[str, Any]:
        """Case 3: Stale privacy_policy → INSUFFICIENT + PRIVACY_STALE"""
        return {
            "case_id": "case_03",
            "description": "Stale privacy_policy → INSUFFICIENT + PRIVACY_STALE",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": "PRIV@v3",  # Stale version
            "privacy_policy_version": "v3",
            "expected_policy_version": "v4",
            "disclosure_scope_ref": "SCOPE.MIN",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": None,
            "window_policy_id": "WP-001",
            "expected": {
                "evidence_grade": "NOT_CLOSURE_GRADE",
                "privacy_check": "FAIL",
                "missing_reason": "PRIVACY_STALE"
            }
        }

    def _case_4_all_refs_with_byuse(self) -> Dict[str, Any]:
        """Case 4: All refs + BYUSE(SUPPORT_CLOSURE) → PARTIAL_RELIANCE"""
        return {
            "case_id": "case_04",
            "description": "All refs + BYUSE(SUPPORT_CLOSURE) → PARTIAL_RELIANCE",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": "PRIV@v4",
            "disclosure_scope_ref": "SCOPE.MIN",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": "SUPPORT_CLOSURE",
            "window_policy_id": "WP-001",
            "expected": {
                "evidence_grade": "PARTIAL_RELIANCE",
                "admission": "ADMIT",
                "privacy_check": "PASS"
            }
        }

    def _case_5_missing_window_policy_with_byuse(self) -> Dict[str, Any]:
        """Case 5: Missing window_policy_id + BYUSE → NOT_CLOSURE_GRADE + upgrade_req"""
        return {
            "case_id": "case_05",
            "description": "Missing window_policy_id + BYUSE → NOT_CLOSURE_GRADE",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": "PRIV@v4",
            "disclosure_scope_ref": "SCOPE.MIN",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": "SUPPORT_CLOSURE",
            "window_policy_id": None,  # Missing!
            "expected": {
                "evidence_grade": "NOT_CLOSURE_GRADE",
                "upgrade_requirements_ref": "present"
            }
        }

    def _case_6_all_refs_supplemented_with_byuse(self) -> Dict[str, Any]:
        """Case 6: All refs supplemented + BYUSE → PARTIAL_RELIANCE"""
        return {
            "case_id": "case_06",
            "description": "All refs supplemented + BYUSE → PARTIAL_RELIANCE",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": "PRIV@v4",
            "disclosure_scope_ref": "SCOPE.MIN",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": "SUPPORT_CLOSURE",
            "window_policy_id": "WP-001",  # Now present
            "expected": {
                "evidence_grade": "PARTIAL_RELIANCE",
                "admission": "ADMIT"
            }
        }

    def _case_7_export_without_authority(self) -> Dict[str, Any]:
        """Case 7: Export priv without authority → egress DENY"""
        return {
            "case_id": "case_07",
            "description": "Export priv without authority → egress DENY",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": "PRIV@v4",
            "disclosure_scope_ref": "SCOPE.MIN",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": None,
            "window_policy_id": "WP-001",
            "proposed_egress": "full_with_auth",
            "authority_scope_ref": None,  # No authority!
            "expected": {
                "verdict": "READY",
                "evidence_grade": "DELIVERY_GRADE",
                "egress_verdict": "DENY"
            }
        }

    def _case_8_export_with_authority(self) -> Dict[str, Any]:
        """Case 8: Export priv with authority → egress ALLOW + receipt"""
        return {
            "case_id": "case_08",
            "description": "Export priv with authority → egress ALLOW + receipt",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": "PRIV@v4",
            "disclosure_scope_ref": "SCOPE.OPERATOR_ONLY",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": None,
            "window_policy_id": "WP-001",
            "proposed_egress": "full_with_auth",
            "authority_scope_ref": "AUTH-OPERATOR-01",  # Authority present
            "expected": {
                "verdict": "READY",
                "evidence_grade": "DELIVERY_GRADE",
                "egress_verdict": "ALLOW",
                "egress_mode": "PRIV_ALLOWED",
                "egress_receipt_ref": "present"
            }
        }

    def _case_9_privacy_not_applicable(self) -> Dict[str, Any]:
        """Case 9: Privacy not applicable profile → NOT_APPLICABLE"""
        return {
            "case_id": "case_09",
            "description": "Privacy not applicable profile → NOT_APPLICABLE",
            "profile": "WIFI78_INSTALL_ACCEPT",  # privacy_validity_precondition=false
            "privacy_policy_ref": None,
            "disclosure_scope_ref": None,
            "retention_ref": None,
            "purpose_ref": None,
            "byuse_context_ref": None,
            "window_policy_id": "WP-001",
            "expected": {
                "privacy_check": "NOT_APPLICABLE",
                "evidence_grade": "DELIVERY_GRADE"
            }
        }

    def _case_10_policy_drift(self) -> Dict[str, Any]:
        """Case 10: Policy drift (version jump) → DEGRADE + POLICY_DRIFT"""
        return {
            "case_id": "case_10",
            "description": "Policy drift (version jump) → DEGRADE + POLICY_DRIFT",
            "profile": "PROFILE_OPENRAN_RIC",
            "privacy_policy_ref": "PRIV@v2",  # Old version
            "privacy_policy_version": "v2",
            "expected_policy_version": "v4",
            "disclosure_scope_ref": "SCOPE.MIN",
            "retention_ref": "RET.7D",
            "purpose_ref": "PURP.NETWORK_OPERATION",
            "byuse_context_ref": None,
            "window_policy_id": "WP-001",
            "expected": {
                "evidence_grade": "NOT_CLOSURE_GRADE",
                "reason_includes": "RC_POLICY_DRIFT"
            }
        }

    def _get_all_test_cases(self) -> List[Dict[str, Any]]:
        """Get all 10 test cases"""
        return [
            self._case_1_all_refs_no_byuse(),
            self._case_2_missing_privacy_policy(),
            self._case_3_stale_privacy_policy(),
            self._case_4_all_refs_with_byuse(),
            self._case_5_missing_window_policy_with_byuse(),
            self._case_6_all_refs_supplemented_with_byuse(),
            self._case_7_export_without_authority(),
            self._case_8_export_with_authority(),
            self._case_9_privacy_not_applicable(),
            self._case_10_policy_drift()
        ]

    def _generate_proof_card(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proof card for a test case using ProofCardGeneratorV14.generate()."""
        window_data = self._generate_synthetic_window_data()

        # Build ctx_overrides from test case fields
        version_refs = {
            "policy_snapshot_ref": "POLICY@2026-02-10#1",
        }
        if test_case.get("window_policy_id"):
            version_refs["window_policy_id"] = test_case["window_policy_id"]

        ctx_overrides = {
            "version_refs": version_refs,
            "privacy_policy_ref": test_case.get("privacy_policy_ref"),
            "disclosure_scope_ref": test_case.get("disclosure_scope_ref"),
            "retention_ref": test_case.get("retention_ref"),
            "purpose_ref": test_case.get("purpose_ref"),
            "authority_scope_ref": test_case.get("authority_scope_ref"),
        }

        if test_case.get("byuse_context_ref"):
            ctx_overrides["byuse_context_ref"] = test_case["byuse_context_ref"]
        if test_case.get("proposed_egress"):
            ctx_overrides["proposed_egress"] = test_case["proposed_egress"]
        if test_case.get("privacy_policy_version"):
            ctx_overrides["privacy_policy_version"] = test_case["privacy_policy_version"]
        if test_case.get("expected_policy_version"):
            ctx_overrides["expected_policy_version"] = test_case["expected_policy_version"]

        proof_card = self.generator.generate(
            window_data,
            test_case["profile"],
            f"W-DEMO-{test_case['case_id']}",
            manifest_ref_str=f"MAN-DEMO-{test_case['case_id']}",
            ctx_overrides=ctx_overrides,
        )
        return proof_card

    def _handle_egress(self, test_case: Dict[str, Any], proof_card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle egress gate check if needed, returns dict with egress info."""
        if not test_case.get("proposed_egress"):
            return None

        egress_overrides = {
            "proposed_egress": test_case["proposed_egress"],
            "disclosure_scope_ref": test_case.get("disclosure_scope_ref"),
            "authority_scope_ref": test_case.get("authority_scope_ref"),
        }
        result = self.generator.apply_egress_gate(proof_card, ctx_overrides=egress_overrides)

        return {
            "allowed": result.allowed,
            "mode": result.mode,
            "egress_receipt_ref": result.egress_receipt_ref,
            "reason_code": result.reason_code,
        }

    def run_all_cases(self, output_dir: str = "demo_output_v14") -> List[Dict[str, Any]]:
        """
        Run all 10 test cases and generate outputs

        Returns:
            List of result dictionaries with metadata
        """
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        proof_cards_dir = os.path.join(output_dir, "proof_cards")
        egress_receipts_dir = os.path.join(output_dir, "egress_receipts")
        os.makedirs(proof_cards_dir, exist_ok=True)
        os.makedirs(egress_receipts_dir, exist_ok=True)

        test_cases = self._get_all_test_cases()
        results = []
        csv_rows = []

        for test_case in test_cases:
            case_id = test_case["case_id"]
            print(f"Running {case_id}: {test_case['description']}")

            # Generate proof card
            proof_card = self._generate_proof_card(test_case)

            # Write proof card JSON
            proof_card_path = os.path.join(proof_cards_dir, f"{case_id}.json")
            with open(proof_card_path, 'w') as f:
                json.dump(proof_card, f, indent=2)

            # Handle egress if needed
            egress_result = self._handle_egress(test_case, proof_card)
            egress_receipt = None

            if egress_result:
                egress_receipt_path = os.path.join(egress_receipts_dir, f"{case_id}_egress.json")
                egress_receipt = {
                    "egress_receipt_ref": egress_result.get("egress_receipt_ref", ""),
                    "allowed": egress_result.get("allowed"),
                    "mode": egress_result.get("mode"),
                    "reason_code": egress_result.get("reason_code", []),
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                }
                with open(egress_receipt_path, 'w') as f:
                    json.dump(egress_receipt, f, indent=2)

            # Build result
            result = {
                "case_id": case_id,
                "description": test_case["description"],
                "proof_card_path": proof_card_path,
                "proof_card": proof_card,
                "egress_result": egress_result,
                "egress_receipt": egress_receipt
            }
            results.append(result)

            # Build CSV row
            privacy_refs_str = "NONE"
            if test_case.get("privacy_policy_ref"):
                privacy_refs_str = f"policy={test_case['privacy_policy_ref']}, scope={test_case.get('disclosure_scope_ref', 'N/A')}"

            min_section = proof_card.get("min", {})
            csv_row = {
                "case": case_id,
                "profile": test_case["profile"],
                "privacy_refs": privacy_refs_str,
                "byuse": test_case.get("byuse_context_ref") or "NONE",
                "egress_request": test_case.get("proposed_egress") or "NONE",
                "verdict": proof_card.get("verdict", "N/A"),
                "evidence_grade": proof_card.get("evidence_grade", "N/A"),
                "admission_verdict": min_section.get("admission_verdict", "N/A"),
                "privacy_check": min_section.get("privacy_check_verdict", "N/A"),
                "notes": test_case["description"],
            }
            csv_rows.append(csv_row)

        # Write summary CSV
        summary_path = os.path.join(output_dir, "summary.csv")
        with open(summary_path, 'w', newline='') as f:
            fieldnames = ["case", "profile", "privacy_refs", "byuse", "egress_request",
                         "verdict", "evidence_grade", "admission_verdict", "privacy_check", "notes"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        print(f"\nCompleted all test cases. Results in: {output_dir}/")
        return results


if __name__ == "__main__":
    # Quick test
    sim = V14DemoSimulator()
    results = sim.run_all_cases()
    print(f"Generated {len(results)} test cases")
