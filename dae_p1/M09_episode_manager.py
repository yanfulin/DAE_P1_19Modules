
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from .M00_common import sha256_str, now_ts

@dataclass
class Episode:
    episode_id: str
    start_ts: float
    worst_window_ref: str
    evidence_refs: List[str]

class EpisodeManager:
    """
    Tracks a current episode based on bad windows. Free v1 keeps this simple.
    """
    def __init__(self):
        self.current: Optional[Episode] = None

    def start_or_update(self, worst_window_ref: str, evidence_ref: str) -> Episode:
        if self.current is None:
            eid = f"ep-{sha256_str(str(now_ts()))[:12]}"
            self.current = Episode(episode_id=eid, start_ts=now_ts(),
                                   worst_window_ref=worst_window_ref,
                                   evidence_refs=[evidence_ref])
        else:
            self.current.worst_window_ref = worst_window_ref
            self.current.evidence_refs.append(evidence_ref)
        return self.current

    def get(self) -> Optional[Episode]:
        return self.current

    def clear(self) -> None:
        self.current = None
