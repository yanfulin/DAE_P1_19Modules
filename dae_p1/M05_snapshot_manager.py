
from __future__ import annotations
from typing import Dict, Any
from .M00_common import PreChangeSnapshot, now_ts, sha256_str

class SnapshotManager:
    """
    Creates scoped pre-change snapshots (reference only).
    The snapshot_digest acts as a stable reference without leaking full config content.
    """
    def create_pre_change(self, snapshot_scope: str, readable_fields: Dict[str, Any]) -> PreChangeSnapshot:
        ts = now_ts()
        digest = sha256_str(f"{snapshot_scope}|{ts}|{readable_fields}")
        ref_id = f"snap-{digest[:12]}"
        return PreChangeSnapshot(
            snapshot_ref_id=ref_id,
            snapshot_scope=snapshot_scope,
            capture_time=ts,
            snapshot_digest=digest,
            readable_fields=readable_fields
        )
