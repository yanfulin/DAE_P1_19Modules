
from dataclasses import dataclass, asdict, field, is_dataclass
import json
from typing import Dict, Any, Optional

@dataclass
class VersionRefs:
    fw: str = "unknown"
    driver: str = "unknown"
    agent: str = "dae_p1/0.1.0"

@dataclass
class ChangeEventCard:
    event_time: float
    event_type: str
    version_refs: VersionRefs = field(default_factory=VersionRefs)

def serialize(item):
    if is_dataclass(item):
        return json.dumps(asdict(item))
    return str(item)

def deserialize(data_str, item_class):
    d = json.loads(data_str)
    if item_class and is_dataclass(item_class) and isinstance(d, dict):
        return item_class(**d)
    return d

def test():
    # Create original object
    original = ChangeEventCard(
        event_time=12345.0, 
        event_type="test", 
        version_refs=VersionRefs(fw="1.0.0", driver="driver_v1")
    )
    
    print(f"Original: {original}")
    print(f"Original version_refs type: {type(original.version_refs)}")

    # Serialize
    serialized = serialize(original)
    print(f"Serialized: {serialized}")

    # Deserialize
    restored = deserialize(serialized, ChangeEventCard)
    print(f"Restored: {restored}")
    print(f"Restored version_refs type: {type(restored.version_refs)}")

    # Check access
    try:
        print(f"FW Version: {restored.version_refs.fw}")
    except AttributeError as e:
        print(f"CAUGHT EXPECTED ERROR: {e}")

if __name__ == "__main__":
    test()
