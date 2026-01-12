
import sys
import os

# Ensure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from dae_p1.adapters.demo_adapter import DemoAdapter
from dae_p1.M10_timeline_builder import TimelineBuilder
from dae_p1.M00_common import PreChangeSnapshot

def verify_snapshots():
    adapter = DemoAdapter()
    
    # Run for 40 steps to cover all trigger points
    print("Running simulation for 40 steps...")
    all_snaps = []
    
    # Capture t=0 explicitly as it's separate in generate_step logic
    # The adapter internal loop handles this, but let's just drive it manually
    for t in range(41):
        # We access the internal sim directly or just step the adapter
        # Adapter logic:
        # m, evs, snaps = self.sim.generate_step(self.t)
        # self.t += 1
        
        # We need to peek at what the adapter collected
        # But collect_metric_sample returns metrics, and STORES evs/snaps internally
        # which are retrieved by collect_change_events_and_snapshots
        
        adapter.collect_metric_sample()
        _, snaps = adapter.collect_change_events_and_snapshots()
        all_snaps.extend(snaps)

    print(f"Collected {len(all_snaps)} snapshots.")
    
    found_types = set()
    for s in all_snaps:
        print(f"Snapshot at {s.capture_time}: Type={s.snapshot_type}, Scope={s.snapshot_scope}")
        found_types.add(s.snapshot_type)
        
    expected = {"post-install", "pre-incident", "post-incident", "periodic"}
    missing = expected - found_types
    
    if not missing:
        print("\nSUCCESS: All expected snapshot types found!")
    else:
        print(f"\nFAILURE: Missing snapshot types: {missing}")

if __name__ == "__main__":
    verify_snapshots()
