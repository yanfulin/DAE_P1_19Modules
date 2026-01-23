
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from dae_p1.M00_common import ChangeEventCard, VersionRefs

def test_fix():
    print("Testing fix for ChangeEventCard nested deserialization...")
    
    # Simulate data coming from JSON/Dict deserialization
    data = {
        "event_time": 12345.0,
        "event_type": "PROTOCOL_CHANGE",
        "version_refs": {
            "fw": "2.5.0",
            "driver": "1.1.0",
            "agent": "dae_p1/0.1.0"
        }
    }
    
    # Create the object (this triggers __post_init__)
    card = ChangeEventCard(**data)
    
    print(f"Created card: {card}")
    print(f"Type of version_refs: {type(card.version_refs)}")
    
    # Verify it is a VersionRefs object
    if isinstance(card.version_refs, VersionRefs):
        print("SUCCESS: version_refs is a VersionRefs object.")
        # Verify attribute access works
        print(f"FW Version: {card.version_refs.fw}")
    else:
        print("FAILURE: version_refs is still a dict!")
        sys.exit(1)

if __name__ == "__main__":
    test_fix()
