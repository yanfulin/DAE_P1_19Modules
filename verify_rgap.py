import sys
import os
import shutil
import time
from dae_p1.rgap import RGAPController, OutcomeFacet

def test_rgap_controller():
    print("Testing RGAP Controller...")
    
    # Setup clean env
    test_dir = "data/rgap_test"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    ctrl = RGAPController(data_dir=test_dir)
    
    # 1. Generate ProofCard
    print("- Generating ProofCard...")
    facets = [OutcomeFacet("rsrp", -80, "dBm")]
    card = ctrl.generate_proof_card(
        verdict="READY",
        reason_codes=[],
        facets=facets,
        sample_count=100
    )
    
    assert card.verdict == "READY"
    assert card.sample_count == 100
    assert len(card.outcome_facet) == 1
    print(f"  [OK] Generated {card.proof_card_ref}")
    
    # 2. Check Manifest
    print("- Checking Manifest...")
    assert ctrl.manifest.manifest_ref.startswith("M-")
    # Our simple implementation adds a day-ref
    assert len(ctrl.manifest.available_day_refs) > 0
    print(f"  [OK] Manifest ref: {ctrl.manifest.manifest_ref}")
    
    # 3. Persistence
    print("- Testing Persistence...")
    del ctrl
    ctrl2 = RGAPController(data_dir=test_dir)
    latest = ctrl2.get_latest_proof()
    assert latest is not None
    assert latest.proof_card_ref == card.proof_card_ref
    print("  [OK] Persistence verified")
    
    # Cleanup
    shutil.rmtree(test_dir)
    print("Test Complete.")

if __name__ == "__main__":
    try:
        test_rgap_controller()
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
